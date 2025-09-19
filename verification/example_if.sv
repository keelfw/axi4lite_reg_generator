`include "axi4_lite_if.sv"

interface example_if #(
    parameter ADDRESS_W = 32
)
    (input logic aclk, aresetn);

    axi4_lite_if #(ADDRESS_W, 32) axi4_lite(aclk, aresetn);

    logic [31:0] R_Test_Register_I;
    logic [31:0] R_Scratch_Register_O;
    logic R_Scratch_Register_O_upd;
    logic [14:0] R_Register_with_Fields_I;
    logic [14:0] R_Register_with_Fields_O;
    logic R_Register_with_Fields_O_upd;

    property R_Scratch_Register_O_upd_pulse;
        @(posedge aclk) disable iff (!aresetn)
        (axi4_lite.awvalid && axi4_lite.awready && (axi4_lite.awaddr == 4)) |->
        ##[1:25] (axi4_lite.wready && axi4_lite.wvalid)
        ##1 (R_Scratch_Register_O_upd && !$past(R_Scratch_Register_O_upd))
        ##1 (!R_Scratch_Register_O_upd);
    endproperty
    assert property (R_Scratch_Register_O_upd_pulse);

    property R_Register_with_Fields_O_upd_pulse;
        @(posedge aclk) disable iff (!aresetn)
        (axi4_lite.awvalid && axi4_lite.awready && (axi4_lite.awaddr == 64)) |->
        ##[1:25] (axi4_lite.wready && axi4_lite.wvalid)
        ##1 (R_Register_with_Fields_O_upd && !$past(R_Register_with_Fields_O_upd))
        ##1 (!R_Register_with_Fields_O_upd);
    endproperty
    assert property (R_Register_with_Fields_O_upd_pulse);

endinterface : example_if