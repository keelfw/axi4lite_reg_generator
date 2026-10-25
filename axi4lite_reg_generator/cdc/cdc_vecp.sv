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
* cdc_vecp: WIDTH-wide atomic vector transfer between two clock domains,
*   gated by an external source-domain request. Vendor-neutral equivalent of
*   the Xilinx XPM_CDC_HANDSHAKE macro (not instantiated), without the
*   external destination acknowledge (the macro's DEST_EXT_HSK=0 auto-ack).
*
*   A transfer starts on a src_clk edge when src_send is asserted and the
*   source is ready (src_rcv high). The source latches src_in into a holding
*   register that stays stable for the whole request/ack round trip; a request
*   toggle crosses into the destination domain through DEST_SYNC_FF stages; the
*   destination detects the change, captures the held data into dest_out and
*   pulses dest_req for one dest_clk cycle. An acknowledge toggle then crosses
*   back through SRC_SYNC_FF stages, re-arming the source.
*
*   src_send is sampled only while src_rcv is high. A request that arrives
*   while the source is busy (src_rcv low) is ignored, so back-to-back sends
*   faster than the handshake latency are coalesced (last accepted value wins).
*   For register writes, hold src_send until src_rcv high, or space writes by
*   more than the round-trip latency.
*
*   Parameters mirror XPM_CDC_HANDSHAKE:
*     DEST_SYNC_FF  request synchronizer stages (2..10).
*     INIT_SYNC_FF  1 = initialize the state in simulation.
*     SIM_ASSERT_CHK accepted for compatibility (no simulation checks here).
*     SRC_SYNC_FF   acknowledge synchronizer stages (2..10).
*     WIDTH         input/output width (>= 1).
*
*   There is no reset pin, matching XPM; INIT_SYNC_FF provides the
*   power-up/simulation value.
*/

module cdc_vecp #(
  parameter int DEST_SYNC_FF   = 4,
  parameter int INIT_SYNC_FF   = 0,
  parameter int SIM_ASSERT_CHK = 0,
  parameter int SRC_SYNC_FF    = 4,
  parameter int WIDTH          = 1
)(
  input  logic             src_clk,
  input  logic [WIDTH-1:0] src_in,
  input  logic             src_send,
  output logic             src_rcv,
  input  logic             dest_clk,
  output logic             dest_req,
  output logic [WIDTH-1:0] dest_out
);

  // ---- Source domain: holding register, request toggle, completion detect ---
  logic [WIDTH-1:0] src_data_q;
  logic             src_req_q;
  logic             src_busy_q;
  (* async_reg = "true" *) logic [SRC_SYNC_FF-1:0] ack_sync_q;
  logic             src_ack_prev_q;

  wire src_ack   = ack_sync_q[SRC_SYNC_FF-1];
  wire ack_event = src_ack ^ src_ack_prev_q;
  wire src_start = (~src_busy_q | ack_event) & src_send;

  always_ff @(posedge src_clk) begin
    ack_sync_q     <= {ack_sync_q[SRC_SYNC_FF-2:0], dst_ack_q};
    src_ack_prev_q <= src_ack;
    if (src_start) begin
      src_data_q <= src_in;
      src_req_q  <= ~src_req_q;
      src_busy_q <= 1'b1;
    end else if (ack_event) begin
      src_busy_q <= 1'b0;
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
