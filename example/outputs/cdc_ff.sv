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
* cdc_ff: WIDTH-wide, DEST_SYNC_FF-deep array synchronizer. This is a
*   vendor-neutral equivalent of the Xilinx XPM_CDC_ARRAY_SINGLE macro (the
*   macro itself is not instantiated). Each bit of src_in is synchronized
*   independently into the dest_clk domain through the chain
*   src_in -> src_ff -> sync[0] -> ... -> dest_out.
*
*   This is only a per-bit metastability filter: it does NOT make the transfer
*   atomic. If two bits can change in the same source cycle the destination may
*   observe an incoherent mix, so src_in must be quasi-static (stable for at
*   least DEST_SYNC_FF destination clock edges). Use cdc_vec / cdc_vecp for
*   coherent (atomic) multi-bit transfers.
*
*   Parameters mirror XPM_CDC_ARRAY_SINGLE:
*     DEST_SYNC_FF  number of destination synchronizer stages (2..10).
*     INIT_SYNC_FF  1 = initialize the synchronizer registers in simulation.
*     SIM_ASSERT_CHK accepted for compatibility (no simulation checks here).
*     SRC_INPUT_REG 1 = register src_in in the source domain before crossing.
*     WIDTH         width of src_in / dest_out (>= 1).
*
*   There is no reset pin, matching XPM. In hardware the registers take their
*   power-up value from GSR / configured init; INIT_SYNC_FF provides the same
*   value in simulation.
*/

module cdc_ff #(
  parameter int DEST_SYNC_FF   = 4,
  parameter int INIT_SYNC_FF   = 0,
  parameter int SIM_ASSERT_CHK = 0,
  parameter int SRC_INPUT_REG  = 1,
  parameter int WIDTH          = 1
)(
  input  logic             src_clk,
  input  logic [WIDTH-1:0] src_in,
  input  logic             dest_clk,
  output logic [WIDTH-1:0] dest_out
);

  // Optional source-domain input register (SRC_INPUT_REG). Registering the
  // input improves the timing of the path feeding the first synchronizer flop.
  (* async_reg = "true" *) logic [WIDTH-1:0] src_ff;

  // Destination-domain synchronizer pipeline. async_reg tells synthesis tools
  // to keep these flops close together and out of the normal optimization /
  // retiming path.
  (* async_reg = "true" *) logic [DEST_SYNC_FF-1:0][WIDTH-1:0] sync_ff;

  logic [WIDTH-1:0] src_int;

  generate
    if (SRC_INPUT_REG != 0) begin : gen_src_reg
      always_ff @(posedge src_clk) begin
        src_ff <= src_in;
      end
      assign src_int = src_ff;
    end else begin : gen_no_src_reg
      assign src_int = src_in;
    end
  endgenerate

  always_ff @(posedge dest_clk) begin
    sync_ff[0] <= src_int;
    for (int i = 1; i < DEST_SYNC_FF; i++) begin
      sync_ff[i] <= sync_ff[i-1];
    end
  end

  assign dest_out = sync_ff[DEST_SYNC_FF-1];

  generate
    if (INIT_SYNC_FF != 0) begin : gen_init
      initial begin
        sync_ff = '0;
        src_ff  = '0;
      end
    end
  endgenerate

endmodule
