`include "axi4_lite_bfm.sv"
`include "example_if.sv"

class test_base #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
);
    axi4_lite_master_driver #(AWIDTH, DWIDTH) axi4_lite_master;

    mailbox #(axi4_lite_transaction #(AWIDTH, DWIDTH)) driver_mbx;

    virtual example_if vif;
    virtual axi4_lite_if axi_if;

    function new(virtual example_if vif);
        this.vif = vif;
        this.axi_if = vif.axi4_lite;
        axi4_lite_master = new(this.axi_if);
    endfunction

    task run(ref logic aresetn);
        fork 
            axi4_lite_master.run();
        join_none

        run_test(aresetn);

        #1000;
    endtask

    virtual task run_test(ref logic aresetn);
        axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn_w;
        axi4_lite_transaction_read #(AWIDTH, DWIDTH) txn_r;

        vif.R_Test_Register_I = 32'hFEEDBACE;
        vif.R_Register_with_Fields_I = 2**12-1;

        reset_sequence(aresetn);

        $display("Checking default values");
        txn_r = new(
            .addr(0),
            .expected_data(vif.R_Test_Register_I),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        txn_r = new(
            .addr(4),
            .expected_data(0),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        txn_r = new(
            .addr(64),
            .expected_data(vif.R_Register_with_Fields_I),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        $display("Complete :: %s", txn_r.convert2string());

        $display("Writing new values");
        txn_w = new(
            .addr(4),
            .data(32'h1234567A),
            .check_resp(1)
        );
        axi4_lite_master.write_txn(txn_w);
        txn_w = new(
            .addr(64),
            .data(32'hCCAABB11),
            .check_resp(1)
        );
        axi4_lite_master.write_txn(txn_w);

        repeat(5) @(posedge vif.aclk);

        assert (vif.R_Scratch_Register_O == 32'h1234567A) else begin
            $error("Error setting scratch register. Expected: %H Actual: %H", 32'h1234567A, vif.R_Scratch_Register_O);
        end
        assert (vif.R_Register_with_Fields_O == 32'h00003B11) else begin
            $error("Error setting scratch register. Expected: %H Actual: %H", 32'h00003B11, vif.R_Register_with_Fields_O);
        end

        $display("Reading new values back");
        txn_r = new(
            .addr(0),
            .expected_data(vif.R_Test_Register_I),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        txn_r = new(
            .addr(4),
            .expected_data(32'h1234567A),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        txn_r = new(
            .addr(64),
            .expected_data(vif.R_Register_with_Fields_I),
            .check_data(1),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);

        $display("Test complete");

    endtask

    task reset_sequence(ref logic aresetn);
        $display("Starting reset (%t)", $time);
        axi4_lite_master.reset();
        
        aresetn = 1'b0;
        repeat (5) @(posedge vif.aclk);
        
        aresetn = 1'b1;
        $display("Exiting reset (%t)", $time);
        repeat (2) @(posedge vif.aclk);
    endtask

endclass

class test_read_invalid #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends test_base #(AWIDTH, DWIDTH);
    function new(virtual example_if vif);
        super.new(vif);
    endfunction

    virtual task run_test(ref logic aresetn);
        axi4_lite_transaction_read #(AWIDTH, DWIDTH) txn_r;

        reset_sequence(aresetn);

        txn_r = new(
            .addr(8),
            .expected_resp(SLVERR),
            .check_resp(1)
        );
        axi4_lite_master.read_txn(txn_r);
        $display("Completed invalid read: %s", txn_r.convert2string());
        
    endtask
endclass

class test_write_invalid #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends test_base #(AWIDTH, DWIDTH);
    function new(virtual example_if vif);
        super.new(vif);
    endfunction

    virtual task run_test(ref logic aresetn);
        axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn_w;

        reset_sequence(aresetn);

        txn_w = new(
            .addr(8),
            .data(0),
            .expected_resp(SLVERR),
            .check_resp(1)
        );
        axi4_lite_master.write_txn(txn_w);
        $display("Completed invalid write: %s", txn_w.convert2string());
        
    endtask
endclass

class test_write_enables #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends test_base #(AWIDTH, DWIDTH);
    function new(virtual example_if vif);
        super.new(vif);
    endfunction

    function logic calc_value(integer byte_enable);
        const integer strobe_len = DWIDTH/8;
        logic [DWIDTH-1:0] val = 0;
        for (integer i=0; i < strobe_len; i++) begin
            if (byte_enable & (1 << i)) begin
                val |= (8'hFF << (i*8));
            end
        end

        return val;
    endfunction

    virtual task run_test(ref logic aresetn);
        const int address = 4;
        axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn_w;
        axi4_lite_transaction_read #(AWIDTH, DWIDTH) txn_r;

        reset_sequence(aresetn);

        for (integer i=0; i < 16; i++) begin
            txn_w = new(
                .addr(address),
                .data(0),
                .check_resp(1)
            );
            axi4_lite_master.write_txn(txn_w);
            txn_r = new(
                .addr(address),
                .expected_data(0),
                .check_data(1),
                .check_resp(1)
            );
            axi4_lite_master.read_txn(txn_r);

            txn_w = new(
                .addr(address),
                .data(32'hFFFFFFFF),
                .strb(i),
                .check_resp(1)
            );
            axi4_lite_master.write_txn(txn_w);
            txn_r = new(
                .addr(address),
                .expected_data(calc_value(i)),
                .check_data(1),
                .check_resp(1)
            );
            axi4_lite_master.read_txn(txn_r);
            $display("Completed strb (%d) write/read: %s", i, txn_r.convert2string());
        end
        
    endtask
endclass

class test_upd_pulse #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends test_base #(AWIDTH, DWIDTH);
    function new(virtual example_if vif);
        super.new(vif);
    endfunction

    task monitor_upd_pulse(ref logic upd);
        integer found_write = 0;
        while (!(vif.axi4_lite.wvalid && vif.axi4_lite.wready)) begin
            @(posedge vif.aclk);
            assert (upd == 0) else $error("Update pulse fired too early!");
        end

        //assert (0);

        @(posedge vif.aclk);
        assert (upd == 1) else $error("Update pulse did not fire!");
        @(posedge vif.aclk);
        assert (upd == 0) else $error("Update pulse stayed high for too long");
    endtask

    virtual task run_test(ref logic aresetn);
        axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn_w;

        reset_sequence(aresetn);

        txn_w = new(
            .addr(4),
            .data(0)
        );
        fork
            axi4_lite_master.write_txn(txn_w);
            monitor_upd_pulse(vif.R_Scratch_Register_O_upd);
        join

        txn_w = new(
            .addr(64),
            .data(0)
        );
        fork
            axi4_lite_master.write_txn(txn_w);
            monitor_upd_pulse(vif.R_Register_with_Fields_O_upd);
        join
    endtask
endclass

module tb();
    parameter ADDRESS_W = 32;
    parameter DATA_W = 32;

    // Set things up
    logic clk = 0;
    always #1 clk = !clk;
    logic aresetn;

    example_if #(ADDRESS_W) reg_if(clk,aresetn);

    // DUT instantiation
    example #(
        .ADDRESS_W(ADDRESS_W),
        .ADDRESS_APERTURE(8),
        .REGISTER_INPUTS(1'b0)
    ) dut (
        .regs_aclk(reg_if.aclk),
        .regs_aresetn(reg_if.aresetn),

        // Register connections
        .R_Test_Register_I(reg_if.R_Test_Register_I),
        .R_Scratch_Register_O(reg_if.R_Scratch_Register_O),
        .R_Scratch_Register_O_upd(reg_if.R_Scratch_Register_O_upd),
        .R_Register_with_Fields_I(reg_if.R_Register_with_Fields_I),
        .R_Register_with_Fields_O(reg_if.R_Register_with_Fields_O),
        .R_Register_with_Fields_O_upd(reg_if.R_Register_with_Fields_O_upd),

        // AXI-Lite interface
        .regs_awvalid(reg_if.axi4_lite.awvalid),
        .regs_awready(reg_if.axi4_lite.awready),
        .regs_awaddr(reg_if.axi4_lite.awaddr),
        .regs_awprot(reg_if.axi4_lite.awprot),
        .regs_wvalid(reg_if.axi4_lite.wvalid),
        .regs_wready(reg_if.axi4_lite.wready),
        .regs_wdata(reg_if.axi4_lite.wdata),
        .regs_wstrb(reg_if.axi4_lite.wstrb),
        .regs_bvalid(reg_if.axi4_lite.bvalid),
        .regs_bready(reg_if.axi4_lite.bready),
        .regs_bresp(reg_if.axi4_lite.bresp),
        .regs_arvalid(reg_if.axi4_lite.arvalid),
        .regs_arready(reg_if.axi4_lite.arready),
        .regs_araddr(reg_if.axi4_lite.araddr),
        .regs_arprot(reg_if.axi4_lite.arprot),
        .regs_rvalid(reg_if.axi4_lite.rvalid),
        .regs_rready(reg_if.axi4_lite.rready),
        .regs_rdata(reg_if.axi4_lite.rdata),
        .regs_rresp(reg_if.axi4_lite.rresp)
    );

    // Test instantiation and execution
    test_base #(ADDRESS_W, DATA_W) test;
    string test_names_to_run[$];
    string all_test_names[] = {"test_base", "test_read_invalid", "test_write_invalid", "test_write_enables", "test_upd_pulse"};

    task run_single_test(string test_name);
        case (test_name)
            "test_base": begin
                test_base #(ADDRESS_W, DATA_W) tb;
                tb = new(reg_if);
                test = tb;
            end
            "test_read_invalid": begin
                test_read_invalid #(ADDRESS_W, DATA_W) tb;
                tb = new(reg_if);
                test = tb;
            end
            "test_write_invalid": begin
                test_write_invalid #(ADDRESS_W, DATA_W) tb;
                tb = new(reg_if);
                test = tb;
            end
            "test_write_enables": begin
                test_write_enables #(ADDRESS_W, DATA_W) tb;
                tb = new(reg_if);
                test = tb;
            end
            "test_upd_pulse": begin
                test_upd_pulse #(ADDRESS_W, DATA_W) tb;
                tb = new(reg_if);
                test = tb;
            end
            default: begin
                $error("Unknown test: %s", test_name);
                $finish;
            end
        endcase

        $display("Running test: %s", test_name);
        test.run(aresetn);
        $display("Completed test: %s", test_name);
    endtask

    initial begin
        string test_arg;

        // Check if any TEST arguments are specified
        if ($value$plusargs("TEST=%s", test_arg)) begin
            // Split comma-separated test names or handle multiple TEST= args
            string test_list;
            if ($value$plusargs("TEST=%s", test_list)) begin
                // Parse comma-separated list
                static int start = 0, pos = 0;
                string current_test;

                // Add the test list plus a comma for easier parsing
                test_list = {test_list, ","};

                while (pos < test_list.len()) begin
                    if (test_list[pos] == ",") begin
                        current_test = test_list.substr(start, pos-1);
                        // Trim whitespace
                        while (current_test.len() > 0 && (current_test[0] == " " || current_test[0] == "\t")) begin
                            current_test = current_test.substr(1, current_test.len()-1);
                        end
                        while (current_test.len() > 0 && (current_test[current_test.len()-1] == " " || current_test[current_test.len()-1] == "\t")) begin
                            current_test = current_test.substr(0, current_test.len()-2);
                        end

                        if (current_test.len() > 0) begin
                            test_names_to_run.push_back(current_test);
                        end
                        start = pos + 1;
                    end
                    pos++;
                end
            end
        end else begin
            // No tests specified, run all tests
            $display("No specific tests specified, running all tests");
            foreach (all_test_names[i]) begin
                test_names_to_run.push_back(all_test_names[i]);
            end
        end

        $display("Will run %0d test(s): %p", test_names_to_run.size(), test_names_to_run);

        // Run all specified tests
        foreach (test_names_to_run[i]) begin
            $display("\n=== Test %0d/%0d ===", i+1, test_names_to_run.size());
            run_single_test(test_names_to_run[i]);
        end

        $display("\nAll %0d test(s) completed successfully!", test_names_to_run.size());
        $finish;
    end

endmodule