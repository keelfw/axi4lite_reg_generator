`include "axi4_lite_bfm.sv"

class test_base;
    axi4_lite_master_driver axi4_lite_master;

    mailbox #(axi4_lite_transaction) driver_mbx;

    virtual axi4_lite_if vif;

    axi4_lite_transaction_write txn_w;
    axi4_lite_transaction_read txn_r;

    function new(virtual axi4_lite_if vif);
        this.vif = vif;
        axi4_lite_master = new(vif);
    endfunction

    task run(ref logic aresetn);
        fork 
            axi4_lite_master.run();
        join_none

        run_test(aresetn);

        $display("Writing Register");
        axi4_lite_master.write(
            4,32,.txn(txn_w)
        );
        $display("Writing Register Complete: %s", txn_w.convert2string());
        axi4_lite_master.read(
            0,.txn(txn_r)
        );
        $display("Reading Register Complete: %s", txn_r.convert2string());
        axi4_lite_master.read(
            4,.txn(txn_r)
        );
        $display("Reading Register Complete: %s", txn_r.convert2string());

        #1000;
    endtask

    //virtual task run_test();
    task run_test(ref logic aresetn);
        reset_sequence(aresetn);
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
    test_base test;

    initial begin
        test = new(reg_if.axi4_lite);
        test.run(aresetn);
        $finish;
    end

endmodule