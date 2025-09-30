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