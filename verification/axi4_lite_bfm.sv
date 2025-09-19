import axi4_lite_pkg::*;
`include "axi4_lite_if.sv"


typedef class axi4_lite_master_driver;
typedef enum {WRITE, READ} transaction_type_e;

// Base transaction class with virtual execute method
virtual class axi4_lite_transaction #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
);
    transaction_type_e txn_type;
    semaphore complete;

    logic [AWIDTH-1:0] addr;
    logic [2:0] prot;
    logic [DWIDTH-1:0] data;
    axi_resp_e resp;
    axi_resp_e expected_resp;
    bit check_resp;
    
    // Virtual method for response completion handling
    virtual task complete_transaction();
        this.complete.put(1);
    endtask

    virtual function string convert2string();
        return $sformatf("Type: %s, Addr: 0x%08h, Prot: 0x%01h",
                        txn_type.name(), addr, prot);
    endfunction
endclass

class axi4_lite_transaction_write #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends axi4_lite_transaction #(AWIDTH, DWIDTH);
    logic [DWIDTH/8-1:0] strb;

    function new(
        logic [AWIDTH-1:0] addr,
        logic [DWIDTH-1:0] data,
        logic [DWIDTH/8-1:0] strb = '1,
        axi_resp_e expected_resp = OKAY,
        bit check_resp = 1'b0,
        logic [2:0] prot = 3'b000
    );
        this.txn_type = WRITE;
        this.complete = new(0);
        this.addr = addr;
        this.data = data;
        this.strb = strb;
        this.expected_resp = expected_resp;
        this.check_resp = check_resp;
        this.prot = prot;
    endfunction

    virtual function string convert2string();
        return $sformatf("%s, Data: 0x%0h, Strb: 0x%0h, Resp: %s",
                        super.convert2string(), data, strb, resp.name());
    endfunction
endclass

class axi4_lite_transaction_read #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
) extends axi4_lite_transaction #(AWIDTH, DWIDTH);
    logic [DWIDTH-1:0] expected_data;
    bit check_data;

    function new(
        logic [AWIDTH-1:0] addr,
        logic [DWIDTH-1:0] expected_data = 'x,
        bit check_data = 1'b0,
        axi_resp_e expected_resp = OKAY,
        bit check_resp = 1'b0,
        logic [2:0] prot = 3'b000
    );
        this.txn_type = READ;
        this.complete = new(0);
        this.addr = addr;
        this.expected_data = expected_data;
        this.check_data = check_data;
        this.prot = prot;
        this.expected_resp = expected_resp;
        this.check_resp = check_resp;
    endfunction

    virtual function string convert2string();
        return $sformatf("%s, Data: 0x%0h, Resp: %s",
                        super.convert2string(), data, resp.name());
    endfunction
endclass

class axi4_lite_master_driver#(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
);
    virtual axi4_lite_if vif;
    mailbox #(axi4_lite_transaction #(AWIDTH, DWIDTH)) mbx;

    function new(
        virtual axi4_lite_if vif
    );
        this.vif = vif;
        this.mbx = new();
    endfunction

    task run();
        axi4_lite_transaction #(AWIDTH, DWIDTH) txn;
        axi4_lite_transaction_write #(AWIDTH, DWIDTH) write_txn;
        axi4_lite_transaction_read #(AWIDTH, DWIDTH) read_txn;
        forever begin
            mbx.get(txn);
            $display("Got a transaction request");
            if (txn.txn_type == WRITE) begin
                $cast(write_txn, txn);
                execute_write(write_txn);
            end else if (txn.txn_type == READ) begin
                $cast(read_txn, txn);
                execute_read(read_txn);
            end
            $display("Transaction completed!");
            txn.complete_transaction();
        end
    endtask

    // Specific execution methods called by the transactions
    protected task execute_write(axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn);
        fork
            // Write Address
            begin
                @(posedge vif.aclk);
                vif.awvalid <= 1;
                vif.awaddr  <= txn.addr;
                vif.awprot  <= txn.prot;
                wait(vif.awready);
                @(posedge vif.aclk);
                vif.awvalid <= 0;
            end

            // Write Data
            begin
                vif.wvalid <= 1;
                vif.wdata  <= txn.data;
                vif.wstrb  <= txn.strb;
                wait(vif.wready);
                @(posedge vif.aclk);
                vif.wvalid <= 0;
            end
        join

        // Write Response
        vif.bready <= 1;
        wait(vif.bvalid);
        @(posedge vif.aclk);
        txn.resp = axi_resp_e'(vif.bresp);
        vif.bready <= 0;
    endtask

    protected task execute_read(axi4_lite_transaction_read #(AWIDTH, DWIDTH) txn);
        // Read Address
        @(posedge vif.aclk);
        vif.arvalid <= 1;
        vif.araddr  <= txn.addr;
        vif.arprot  <= txn.prot;
        wait(vif.arready);
        @(posedge vif.aclk);
        vif.arvalid <= 0;

        // Read Data
        vif.rready <= 1;
        wait(vif.rvalid);
        @(posedge vif.aclk);
        txn.data = vif.rdata;
        txn.resp = axi_resp_e'(vif.rresp);
        vif.rready <= 0;
    endtask

    // Public API methods - polymorphic version
    task execute(
        inout axi4_lite_transaction #(AWIDTH, DWIDTH) txn,
        input logic blocking = 1
    );
        this.mbx.put(txn);
        if (blocking) begin
            txn.complete.get(1);
        end
    endtask

    // Overloaded methods for specific transaction types
    task write_txn(
        inout axi4_lite_transaction_write #(AWIDTH, DWIDTH) txn,
        input logic blocking = 1
    );
        axi4_lite_transaction #(AWIDTH, DWIDTH) base_txn = txn;
        this.mbx.put(base_txn);
        if (blocking) begin
            txn.complete.get(1);
        end
    endtask

    task read_txn(
        inout axi4_lite_transaction_read #(AWIDTH, DWIDTH) txn,
        input logic blocking = 1
    );
        axi4_lite_transaction #(AWIDTH, DWIDTH) base_txn = txn;
        this.mbx.put(base_txn);
        if (blocking) begin
            txn.complete.get(1);
        end
    endtask

    task reset();
        vif.awvalid <= 0;
        vif.awaddr  <= '0;
        vif.awprot  <= '0;
        vif.wvalid  <= 0;
        vif.wdata   <= '0;
        vif.wstrb   <= '0;
        vif.bready  <= 0;
        vif.arvalid <= 0;
        vif.araddr  <= '0;
        vif.arprot  <= '0;
        vif.rready  <= 0;
    endtask
endclass

