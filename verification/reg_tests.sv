`include "axi4_lite_bfm.sv"

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

    //virtual task run_test();
    task run_test(ref logic aresetn);
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
        $display("Complete :: %s", txn_r.convert2string());

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
        .REGISTER_INPUTS(0)
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

    initial begin
        test = new(reg_if);
        test.run(aresetn);
        $finish;
    end

endmodule