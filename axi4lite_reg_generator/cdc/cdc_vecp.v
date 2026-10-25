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
* cdc_vecp: WIDTH-wide atomic vector transfer between two clock domains, gated
*   by an external source request. Vendor-neutral equivalent of the Xilinx
*   XPM_CDC_HANDSHAKE macro (not instantiated) with auto-acknowledge.
*
*   On a src_clk edge where src_send is asserted and src_rcv is high, the
*   source latches src_in into a holding register (stable for the whole
*   round trip) and toggles a request. The request crosses into dest_clk
*   through DEST_SYNC_FF stages; the destination captures the held data into
*   dest_out and pulses dest_req for one dest_clk cycle. An acknowledge toggle
*   crosses back through SRC_SYNC_FF stages and re-arms the source.
*
*   src_send is only sampled while src_rcv is high; sends that arrive while
*   busy are coalesced (last accepted value wins).
*
*   Parameters mirror XPM_CDC_HANDSHAKE: DEST_SYNC_FF, INIT_SYNC_FF,
*   SIM_ASSERT_CHK, SRC_SYNC_FF, WIDTH. There is no reset pin.
*/

module cdc_vecp #(
  parameter DEST_SYNC_FF   = 4,
  parameter INIT_SYNC_FF   = 0,
  parameter SIM_ASSERT_CHK = 0,
  parameter SRC_SYNC_FF    = 4,
  parameter WIDTH          = 1
)(
  input  wire             src_clk,
  input  wire [WIDTH-1:0] src_in,
  input  wire             src_send,
  output wire             src_rcv,
  input  wire             dest_clk,
  output wire             dest_req,
  output wire [WIDTH-1:0] dest_out
);

  localparam [WIDTH-1:0] INIT_VALUE = {WIDTH{1'b0}};

  // ---- Source domain -------------------------------------------------------
  reg [WIDTH-1:0] src_data_q;
  reg             src_req_q;
  reg             src_busy_q;
  reg [SRC_SYNC_FF-1:0] ack_sync_q;
  reg             src_ack_prev_q;

  wire src_ack   = ack_sync_q[SRC_SYNC_FF-1];
  wire ack_event = src_ack ^ src_ack_prev_q;
  wire src_start = (~src_busy_q | ack_event) & src_send;

  // ---- Destination domain --------------------------------------------------
  reg [DEST_SYNC_FF-1:0] req_sync_q;
  reg             req_prev_q;
  reg [WIDTH-1:0] dst_data_q;
  reg             dst_req_q;
  reg             dst_ack_q;

  wire req_last  = req_sync_q[DEST_SYNC_FF-1];
  wire req_event = req_last ^ req_prev_q;

  always @(posedge src_clk) begin
    ack_sync_q     <= {ack_sync_q[SRC_SYNC_FF-2:0], dst_ack_q};
    src_ack_prev_q <= src_ack;
    if (src_start) begin
      src_data_q <= src_in;
      src_req_q  <= ~src_req_q;
      src_busy_q <= 1'b1;
    end
    else if (ack_event) begin
      src_busy_q <= 1'b0;
    end
  end

  always @(posedge dest_clk) begin
    req_sync_q <= {req_sync_q[DEST_SYNC_FF-2:0], src_req_q};
    req_prev_q <= req_last;
    dst_req_q  <= req_event;
    if (req_event) begin
      dst_data_q <= src_data_q;
      dst_ack_q  <= ~dst_ack_q;
    end
  end

  assign src_rcv  = ~src_busy_q;
  assign dest_out = dst_data_q;
  assign dest_req = dst_req_q;

  generate
    if (INIT_SYNC_FF != 0) begin : gen_init
      initial begin
        src_data_q     = INIT_VALUE;
        src_req_q      = 1'b0;
        src_busy_q     = 1'b0;
        ack_sync_q     = {SRC_SYNC_FF{1'b0}};
        src_ack_prev_q = 1'b0;
        req_sync_q     = {DEST_SYNC_FF{1'b0}};
        req_prev_q     = 1'b0;
        dst_data_q     = INIT_VALUE;
        dst_req_q      = 1'b0;
        dst_ack_q      = 1'b0;
      end
    end
  endgenerate

endmodule
