package axi4_lite_pkg;

    typedef enum logic [1:0] {
        OKAY   = 2'b00,
        EXOKAY = 2'b01,
        SLVERR = 2'b10,
        DECERR = 2'b11
    } axi_resp_e;

endpackage : axi4_lite_pkg

interface axi4_lite_if #(
    parameter AWIDTH = 32,
    parameter DWIDTH = 32
)
    (input logic aclk, aresetn);

    logic awvalid, awready;
    logic [AWIDTH-1:0] awaddr;
    logic [2:0] awprot;
    logic wvalid, wready;
    logic [DWIDTH-1:0] wdata;
    logic [DWIDTH/8-1:0] wstrb;
    logic bvalid, bready;
    logic [1:0] bresp;
    logic arvalid, arready;
    logic [AWIDTH-1:0] araddr;
    logic [2:0] arprot;
    logic rvalid, rready;
    logic [DWIDTH-1:0] rdata;
    logic [1:0] rresp;

    modport master (
        output awvalid, awaddr, awprot,
        input awready,
        output wvalid, wdata, wstrb,
        input wready,
        output bready,
        input bvalid, bresp,
        output arvalid, araddr, arprot,
        input arready,
        output rready,
        input rvalid, rdata, rresp
    );

    modport slave (
        input awvalid, awaddr, awprot,
        output awready,
        input wvalid, wdata, wstrb,
        output wready,
        input bready,
        output bvalid, bresp,
        input arvalid, araddr, arprot,
        output arready,
        input rready,
        output rvalid, rdata, rresp
    );
endinterface : axi4_lite_if