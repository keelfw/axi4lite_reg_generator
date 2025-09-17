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

endinterface : example_if