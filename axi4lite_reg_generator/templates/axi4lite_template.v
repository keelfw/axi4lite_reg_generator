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

/*
TODO: 
* Register signal declarations (wire vs reg)
* Port VHDL code at the end of this file to Verilog
* Check all syntax and other assign misses
*/

// Data Size = {{ data_size }}
// Write Strobe Size = {{ strobe_size }}

module {{ entity_name }} #(
  parameter ADDRESS_W = 32,
  parameter ADDRESS_APERTURE = 8,
  parameter REGISTER_INPUTS = 0
)(
  input  wire                         REGS_ACLK,
  input  wire                         REGS_ARESETN,
  // Registers
  {% for reg in regs -%}
  {% if reg['reg_type'] == 'ro' or reg['reg_type'] == 'custom' -%}
  input wire [{{ reg['bits']|count_bits - 1 }}:0] R_{{ reg['name'] }}_I,
  {% endif -%}
  {% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
  output wire [{{ reg['bits']|count_bits - 1 }}:0] R_{{ reg['name'] }}_O,
  {% if reg['use_upd_pulse'] -%}
  output wire R_{{ reg['name'] }}_O_upd,
  {% endif -%}
  {% endif -%}
  {% endfor %}  
  // Write Address Channel
  input  wire                        REGS_AWVALID,
  output wire                        REGS_AWREADY,
  input  wire [ADDRESS_W-1:0]        REGS_AWADDR,
  input  wire [2:0]                  REGS_AWPROT,
  // Write Data Channel
  input  wire                        REGS_WVALID,
  output wire                        REGS_WREADY,
  input  wire [31:0]                 REGS_WDATA,
  input  wire [3:0]                  REGS_WSTRB,
  // Write Response Channel
  output wire                        REGS_BVALID,
  input  wire                        REGS_BREADY,
  output wire [1:0]                  REGS_BRESP,
  // Read Address Channel
  input  wire                        REGS_ARVALID,
  output wire                        REGS_ARREADY,
  input  wire [ADDRESS_W-1:0]        REGS_ARADDR,
  input  wire [2:0]                  REGS_ARPROT,
  // Read Data Channel
  output wire                        REGS_RVALID,
  input  wire                        REGS_RREADY,
  output wire [31:0]                 REGS_RDATA,
  output wire [1:0]                  REGS_RRESP
);

localparam [1:0] AXI_RESP_OKAY   = 2'b00;
localparam [1:0] AXI_RESP_EXOKAY = 2'b01;
localparam [1:0] AXI_RESP_SLVERR = 2'b10;
localparam [1:0] AXI_RESP_DECERR = 2'b11;

// Register signal declarations
// TODO: this

// Internal AXI support signals
// Write state machine states
localparam [1:0] W_STATE_RST = 2'b00;
localparam [1:0] W_STATE_WAIT4ADDR = 2'b01;
localparam [1:0] W_STATE_WAIT4DATA = 2'b10;
localparam [1:0] W_STATE_WAIT4RESP = 2'b11;

// Read state machine states
localparam [1:0] R_STATE_RST = 2'b00;
localparam [1:0] R_STATE_WAIT4ADDR = 2'b01;
localparam [1:0] R_STATE_WAITREG = 2'b10;
localparam [1:0] R_STATE_WAIT4DATA = 2'b11;

reg [1:0] state_w;
reg [1:0] state_r;

reg [ADDRESS_APERTURE-1:0] address_wr;
reg [ADDRESS_APERTURE-1:0] address_rd;

reg w_ready;
reg r_valid;

reg [{{ data_size-1 }}:0] rd_mux;
reg [1:0] rd_resp;

// Handle inputs

{% for reg in regs -%}
{% if reg['reg_type'] == 'rw' -%}
  assign REG_{{ reg['name'] }}_R = REG_{{ reg['name'] }}_W;
{% endif -%}
{% endfor %}

generate
  if (REGISTER_INPUTS) begin : reg_inputs_g
    always @(posedge REGS_ACLK) begin
      {% for reg in regs -%}
      {% if reg['reg_type'] == 'ro' or reg['reg_type'] == 'custom' -%}
        REG_{{ reg['name'] }}_R <= R_{{ reg['name'] }}_I; 
      {% endif -%}
      {% endfor %}
    end
  end else begin : con_inputs_g
    {% for reg in regs -%}
    {% if reg['reg_type'] != 'rw' -%}
      assign REG_{{ reg['name'] }}_R = R_{{ reg['name'] }}_I;
    {% endif -%}
    {% endfor %}
  end
endgenerate

// Connect outputs
{% for reg in regs -%}
{% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
  assign R_{{ reg['name'] }}_O = REG_{{ reg['name'] }}_W;
{% endif -%}
{% endfor %}
// Connect AXI-Lite ready/valid control signals
assign REGS_WREADY = w_ready;
assign REGS_RVALID = r_valid;

// Write FSM
always @(posedge REGS_ACLK) begin
  if (!REGS_ARESETN) begin
    state_w <= W_STATE_RST;
    REGS_AWREADY <= 1'b0;
    w_ready <= 1'b0;
    REGS_BVALID <= 1'b0;
  end
  else begin
    case (state_w)
      W_STATE_RST: begin
        state_w <= W_STATE_WAIT4ADDR;
        REGS_AWREADY <= 1'b1;
      end
      W_STATE_WAIT4ADDR: begin
        state_w <= W_STATE_WAIT4DATA;
        REGS_AWREADY <= 1'b0;
        w_ready <= 1'b1;
        address_wr <= REGS_AWADDR[ADDRESS_APERTURE-1:0];
      end
      W_STATE_WAIT4RESP: begin
        if (REGS_BREADY == 1'b1) begin
          state_w <= W_STATE_WAIT4ADDR;
          REGS_BVALID <= 1'b1;
          REGS_AWREADY <= 1'b1;
        end
      end
      default: begin
        state_w <= W_STATE_RST;
      end
    endcase
  end
end

// Read FSM
always @(posedge REGS_ACLK) begin
  if (!REGS_ARESETN) begin
    state_r <= R_STATE_RST;
    REGS_ARREADY <= 1'b0;
    r_valid <= 1'b0;
  end
  else begin
    case (state_r)
      R_STATE_RST: begin
        state_r <= R_STATE_WAIT4ADDR;
        REGS_ARREADY <= 1'b1;
      end
      R_STATE_WAIT4ADDR: begin
        state_r <= R_STATE_WAITREG;
        REGS_ARREADY <= 1'b0;
        address_rd <= REGS_ARADDR[ADDRESS_APERTURE-1:0];
      end
      R_STATE_WAITREG: begin
        state_r <= R_STATE_WAIT4DATA;
        r_valid <= 1'b1;
      end
      R_STATE_WAIT4DATA: begin
        if (REGS_RREADY == 1'b1) begin
          state_r <= R_STATE_WAIT4ADDR;
          r_valid <= 1'b0;
          REGS_ARREADY <= 1'b1;
        end
      end
      default: begin
        state_r <= R_STATE_RST;
      end
    endcase
  end
end

// Write process
always @(posedge REGS_ACLK) begin
  if (!REGS_ARESETN) begin
    {%- for reg in regs -%}
    {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' %}
    REG_{{ reg['name'] }}_W <= {{ reg|default_val }};
    {%- if reg['use_upd_pulse'] %}
    R_{{ reg['name'] }}_O_upd <= 1'b0;
    {%- endif %}
    {%- endif %}
    {%- endfor %}
  end
  else begin
    {%- for reg in regs -%}
    {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' %}
    {%- if reg['use_upd_pulse'] %}
    R_{{ reg['name'] }}_O_upd <= 1'b0;
    {%- endif %}
    {%- endif %}
    {%- endfor %}
    if (REGS_WVALID == 1'b1 && w_ready == 1'b1) begin
      {% for reg in regs -%}
      {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
      if (address_wr == {{ reg['addr_offset'] }}) begin
        {%- if reg['use_upd_pulse'] %}
        R_{{ reg['name'] }}_O_upd <= 1'b1;
        {%- endif %}
        REGS_BRESP <= AXI_RESP_OKAY;
        {%- for s in range(strobe_size) %}
        {%- if 8*s < reg['bits']|count_bits %}
        if (REGS_WSTRB[{{s}}] == 1'b1) begin
          REG_{{ reg['name'] }}_W[{{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }}:{{ 8*s }}] <= REGS_WDATA[{{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }}:{{ 8*s }}];
        end
        {%- endif %}
        {%- endfor %}
      end else {%- endif -%}{%- endfor -%} begin
        REGS_BRESP <= AXI_RESP_SLVERR;
      end
    end
  end
end

/*

  rd_mux <= {% for reg in regs -%}
    {%- if reg['bits']|count_bits != data_size %}
    "{%- for i in range(data_size - reg['bits']|count_bits) %}0{%- endfor -%}" & {% endif -%}REG_{{ reg['name'] }}_R when address_rd = std_logic_vector(to_unsigned({{ reg['addr_offset'] }}, ADDRESS_APERTURE)) else {% endfor -%}
    (others=>'0');

  rd_resp <= {% for reg in regs -%}
    AXI_RESP_OKAY when address_rd = std_logic_vector(to_unsigned({{ reg['addr_offset'] }}, ADDRESS_APERTURE)) else {% endfor -%}
    AXI_RESP_SLVERR;

  read_p : process (REGS_ACLK) is
  begin
    if rising_edge(REGS_ACLK) then
      if REGS_ARESETN = '0' then
      else
        if state_r = WAITREG then
          REGS_RDATA <= rd_mux;
          REGS_RRESP <= rd_resp;
        end if;
      end if;
    end if;
  end process;
*/

endmodule