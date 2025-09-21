/* Copyright (C) 2025 KEELFW
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
*/
`ifndef AXI4_LITE_IF_SV
`define AXI4_LITE_IF_SV

import axi4_lite_pkg::*;

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

    // Reset assertions - ensure ready/valid signals are low during reset
    // For synchronous resets, check on the next cycle after reset is asserted
    property reset_awvalid;
        @(posedge aclk) !aresetn |=> !awvalid;
    endproperty

    property reset_awready;
        @(posedge aclk) !aresetn |=> !awready;
    endproperty

    property reset_wvalid;
        @(posedge aclk) !aresetn |=> !wvalid;
    endproperty

    property reset_wready;
        @(posedge aclk) !aresetn |=> !wready;
    endproperty

    property reset_bvalid;
        @(posedge aclk) !aresetn |=> !bvalid;
    endproperty

    property reset_bready;
        @(posedge aclk) !aresetn |=> !bready;
    endproperty

    property reset_arvalid;
        @(posedge aclk) !aresetn |=> !arvalid;
    endproperty

    property reset_arready;
        @(posedge aclk) !aresetn |=> !arready;
    endproperty

    property reset_rvalid;
        @(posedge aclk) !aresetn |=> !rvalid;
    endproperty

    property reset_rready;
        @(posedge aclk) !aresetn |=> !rready;
    endproperty

    assert property (reset_awvalid);
    assert property (reset_awready);
    assert property (reset_wvalid);
    assert property (reset_wready);
    assert property (reset_bvalid);
    assert property (reset_bready);
    assert property (reset_arvalid);
    assert property (reset_arready);
    assert property (reset_rvalid);
    assert property (reset_rready);

    // Data stability assertions - data must not change when valid is high and ready is low
    property awaddr_stable;
        @(posedge aclk) disable iff (!aresetn)
        (awvalid && !awready) |=> $stable(awaddr);
    endproperty

    property awprot_stable;
        @(posedge aclk) disable iff (!aresetn)
        (awvalid && !awready) |=> $stable(awprot);
    endproperty

    property wdata_stable;
        @(posedge aclk) disable iff (!aresetn)
        (wvalid && !wready) |=> $stable(wdata);
    endproperty

    property wstrb_stable;
        @(posedge aclk) disable iff (!aresetn)
        (wvalid && !wready) |=> $stable(wstrb);
    endproperty

    property araddr_stable;
        @(posedge aclk) disable iff (!aresetn)
        (arvalid && !arready) |=> $stable(araddr);
    endproperty

    property arprot_stable;
        @(posedge aclk) disable iff (!aresetn)
        (arvalid && !arready) |=> $stable(arprot);
    endproperty

    property rdata_stable;
        @(posedge aclk) disable iff (!aresetn)
        (rvalid && !rready) |=> $stable(rdata);
    endproperty

    property rresp_stable;
        @(posedge aclk) disable iff (!aresetn)
        (rvalid && !rready) |=> $stable(rresp);
    endproperty

    property bresp_stable;
        @(posedge aclk) disable iff (!aresetn)
        (bvalid && !bready) |=> $stable(bresp);
    endproperty

    assert property (awaddr_stable);
    assert property (awprot_stable);
    assert property (wdata_stable);
    assert property (wstrb_stable);
    assert property (araddr_stable);
    assert property (arprot_stable);
    assert property (rdata_stable);
    assert property (rresp_stable);
    assert property (bresp_stable);

    // AXI4-Lite protocol sequence assertions
    // Write transaction: Address -> Data -> Response
    sequence write_addr_phase;
        awvalid && awready;
    endsequence

    sequence write_data_phase;
        wvalid && wready;
    endsequence

    sequence write_resp_phase;
        bvalid && bready;
    endsequence

    property write_sequence;
        @(posedge aclk) disable iff (!aresetn)
        (awvalid && awready) |-> ##[0:$] (wvalid && wready) ##[1:$] (bvalid && bready);
    endproperty

    // Read transaction: Address -> Response (with data)
    sequence read_addr_phase;
        arvalid && arready;
    endsequence

    sequence read_resp_phase;
        rvalid && rready;
    endsequence

    property read_sequence;
        @(posedge aclk) disable iff (!aresetn)
        (arvalid && arready) |-> ##[1:$] (rvalid && rready);
    endproperty

    assert property (write_sequence);
    assert property (read_sequence);

endinterface : axi4_lite_if

`endif // AXI4_LITE_IF_SV