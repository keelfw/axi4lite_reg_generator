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
* cdc_vec: WIDTH-wide atomic vector transfer between two clock domains with an
*   internally generated request. It uses the same handshake as cdc_vecp but
*   derives src_send internally: the source requests a new transfer whenever
*   the previous one has completed, so src_in is sampled and transferred
*   continuously at the handshake rate.
*
*   Because the source only re-requests after the acknowledge has crossed back,
*   the holding register is stable for the whole round trip and every captured
*   value is coherent (atomic). This is the reset-free, XPM_CDC_HANDSHAKE-style
*   transfer for signals that change on their own and do not provide a valid
*   strobe.
*
*   Parameters mirror XPM_CDC_HANDSHAKE: DEST_SYNC_FF (2..10), INIT_SYNC_FF,
*   SIM_ASSERT_CHK, SRC_SYNC_FF (2..10), WIDTH. There is no reset pin;
*   INIT_SYNC_FF provides the power-up/simulation value. The macro's external
*   destination acknowledge (DEST_EXT_HSK=1) is not implemented; this module
*   always auto-acknowledges.
*/

module cdc_vec #(
  parameter int DEST_SYNC_FF   = 4,
  parameter int INIT_SYNC_FF   = 0,
  parameter int SIM_ASSERT_CHK = 0,
  parameter int SRC_SYNC_FF    = 4,
  parameter int WIDTH          = 1
)(
  input  logic             src_clk,
  input  logic [WIDTH-1:0] src_in,
  output logic             src_rcv,
  input  logic             dest_clk,
  output logic             dest_req,
  output logic [WIDTH-1:0] dest_out
);

  // ---- Source domain: continuously request when the last transfer is done --
  logic [WIDTH-1:0] src_data_q;
  logic             src_req_q;
  logic             src_busy_q;
  (* async_reg = "true" *) logic [SRC_SYNC_FF-1:0] ack_sync_q;
  logic             src_ack_prev_q;

  wire src_ack   = ack_sync_q[SRC_SYNC_FF-1];
  wire ack_event = src_ack ^ src_ack_prev_q;
  wire src_start = ~src_busy_q | ack_event;

  always_ff @(posedge src_clk) begin
    ack_sync_q     <= {ack_sync_q[SRC_SYNC_FF-2:0], dst_ack_q};
    src_ack_prev_q <= src_ack;
    if (src_start) begin
      src_data_q <= src_in;
      src_req_q  <= ~src_req_q;
      src_busy_q <= 1'b1;
    end
  end

  assign src_rcv = ~src_busy_q;

  // ---- Destination domain: request synchronizer, capture, acknowledge ------
  (* async_reg = "true" *) logic [DEST_SYNC_FF-1:0] req_sync_q;
  logic             req_prev_q;
  logic [WIDTH-1:0] dst_data_q;
  logic             dst_req_q;
  logic             dst_ack_q;

  wire req_last  = req_sync_q[DEST_SYNC_FF-1];
  wire req_event = req_last ^ req_prev_q;

  always_ff @(posedge dest_clk) begin
    req_sync_q <= {req_sync_q[DEST_SYNC_FF-2:0], src_req_q};
    req_prev_q <= req_last;
    dst_req_q  <= req_event;
    if (req_event) begin
      dst_data_q <= src_data_q;
      dst_ack_q  <= ~dst_ack_q;
    end
  end

  assign dest_out = dst_data_q;
  assign dest_req = dst_req_q;

  generate
    if (INIT_SYNC_FF != 0) begin : gen_init
      initial begin
        src_data_q     = '0;
        src_req_q      = 1'b0;
        src_busy_q     = 1'b0;
        ack_sync_q     = '0;
        src_ack_prev_q = 1'b0;
        req_sync_q     = '0;
        req_prev_q     = 1'b0;
        dst_data_q     = '0;
        dst_req_q      = 1'b0;
        dst_ack_q      = 1'b0;
      end
    end
  endgenerate

endmodule
