package axi4_lite_pkg;

    typedef enum logic [1:0] {
        OKAY   = 2'b00,
        EXOKAY = 2'b01,
        SLVERR = 2'b10,
        DECERR = 2'b11
    } axi_resp_e;

endpackage : axi4_lite_pkg