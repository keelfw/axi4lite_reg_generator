/* Copyright (C) 2026 KEELFW
*
* This library is free software; you can redistribute it and/or
* modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 2.1 of the License, or (at your option) any later version.
*
* This library is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
* Lesser General Public License for more details.
*
* You should have received a copy of the GNU Lesser General Public
* License along with this library; if not, write to the Free Software
* Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*
* See LICENSE file for full license details.
*
* cdc_ff: WIDTH-wide, DEST_SYNC_FF-deep array synchronizer. Vendor-neutral
*   equivalent of the Xilinx XPM_CDC_ARRAY_SINGLE macro (not instantiated).
*   Each bit of src_in is synchronized independently into the dest_clk domain
*   through src_in -> src_ff -> sync[0] -> ... -> dest_out.
*
*   Only a per-bit metastability filter, not an atomic transfer: src_in must be
*   quasi-static (stable for >= DEST_SYNC_FF dest_clk edges) for dest_out to be
*   coherent. Use cdc_vec / cdc_vecp for coherent multi-bit transfers.
*
*   Parameters mirror XPM_CDC_ARRAY_SINGLE: DEST_SYNC_FF (2..10), INIT_SYNC_FF,
*   SIM_ASSERT_CHK, SRC_INPUT_REG, WIDTH. There is no reset pin; INIT_SYNC_FF
*   provides the power-up/simulation value.
*/

module cdc_ff #(
  parameter DEST_SYNC_FF   = 4,
  parameter INIT_SYNC_FF   = 0,
  parameter SIM_ASSERT_CHK = 0,
  parameter SRC_INPUT_REG  = 1,
  parameter WIDTH          = 1
)(
  input  wire             src_clk,
  input  wire [WIDTH-1:0] src_in,
  input  wire             dest_clk,
  output wire [WIDTH-1:0] dest_out
);

  localparam [WIDTH-1:0] INIT_VALUE = {WIDTH{1'b0}};

  // Optional source-domain input register (SRC_INPUT_REG).
  reg [WIDTH-1:0] src_ff;

  // Destination-domain synchronizer pipeline.
  reg [WIDTH-1:0] sync_q [0:DEST_SYNC_FF-1];

  wire [WIDTH-1:0] src_int;
  assign src_int = SRC_INPUT_REG ? src_ff : src_in;

  always @(posedge src_clk) begin
    src_ff <= src_in;
  end

  genvar stage;
  generate
    for (stage = 0; stage < DEST_SYNC_FF; stage = stage + 1) begin : gen_sync
      always @(posedge dest_clk) begin
        if (stage == 0)
          sync_q[stage] <= src_int;
        else
          sync_q[stage] <= sync_q[stage-1];
      end
    end
  endgenerate

  assign dest_out = sync_q[DEST_SYNC_FF-1];

  generate
    if (INIT_SYNC_FF != 0) begin : gen_init
      integer i;
      initial begin
        for (i = 0; i < DEST_SYNC_FF; i = i + 1)
          sync_q[i] = INIT_VALUE;
        src_ff = INIT_VALUE;
      end
    end
  endgenerate

endmodule
