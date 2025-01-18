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
  output reg R_{{ reg['name'] }}_O_upd,
  {% endif -%}
  {% endif -%}
  {% endfor %}  
  // Write Address Channel
  input  wire                        REGS_AWVALID,
  output reg                         REGS_AWREADY,
  input  wire [ADDRESS_W-1:0]        REGS_AWADDR,
  input  wire [2:0]                  REGS_AWPROT,
  // Write Data Channel
  input  wire                        REGS_WVALID,
  output wire                        REGS_WREADY,
  input  wire [31:0]                 REGS_WDATA,
  input  wire [3:0]                  REGS_WSTRB,
  // Write Response Channel
  output reg                         REGS_BVALID,
  input  wire                        REGS_BREADY,
  output reg  [1:0]                  REGS_BRESP,
  // Read Address Channel
  input  wire                        REGS_ARVALID,
  output reg                         REGS_ARREADY,
  input  wire [ADDRESS_W-1:0]        REGS_ARADDR,
  input  wire [2:0]                  REGS_ARPROT,
  // Read Data Channel
  output wire                        REGS_RVALID,
  input  wire                        REGS_RREADY,
  output reg  [31:0]                 REGS_RDATA,
  output reg  [1:0]                  REGS_RRESP
);

localparam [1:0] AXI_RESP_OKAY   = 2'b00;
localparam [1:0] AXI_RESP_EXOKAY = 2'b01;
localparam [1:0] AXI_RESP_SLVERR = 2'b10;
localparam [1:0] AXI_RESP_DECERR = 2'b11;

// Register signal declarations
{% for reg in regs -%}
reg [{{ reg['bits']|count_bits-1}}:0] REG_{{ reg['name'] }}_R;
{% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
reg [{{ reg['bits']|count_bits-1 }}:0] REG_{{ reg['name'] }}_W;
{% endif %}
{% endfor %}

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
  if (REGISTER_INPUTS > 0) begin : reg_inputs_g
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
    REGS_AWREADY <= 0;
    w_ready <= 0;
    REGS_BVALID <= 0;
  end
  else begin
    case (state_w)
      W_STATE_RST: begin
        state_w <= W_STATE_WAIT4ADDR;
        REGS_AWREADY <= 1;
      end
      W_STATE_WAIT4ADDR: begin
        if (REGS_AWVALID) begin
          state_w <= W_STATE_WAIT4DATA;
          REGS_AWREADY <= 0;
          w_ready <= 1;
          address_wr <= REGS_AWADDR[ADDRESS_APERTURE-1:0];
        end
      end
      W_STATE_WAIT4DATA: begin
        if (REGS_WVALID) begin
          state_w <= W_STATE_WAIT4RESP;
          w_ready <= 0;
          REGS_BVALID <= 1;
        end
      end
      W_STATE_WAIT4RESP: begin
        if (REGS_BREADY) begin
          state_w <= W_STATE_WAIT4ADDR;
          REGS_BVALID <= 1;
          REGS_AWREADY <= 1;
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
    REGS_ARREADY <= 0;
    r_valid <= 0;
  end
  else begin
    case (state_r)
      R_STATE_RST: begin
        state_r <= R_STATE_WAIT4ADDR;
        REGS_ARREADY <= 1;
      end
      R_STATE_WAIT4ADDR: begin
        if (REGS_ARVALID) begin
          state_r <= R_STATE_WAITREG;
          REGS_ARREADY <= 0;
          address_rd <= REGS_ARADDR[ADDRESS_APERTURE-1:0];
        end
      end
      R_STATE_WAITREG: begin
        state_r <= R_STATE_WAIT4DATA;
        r_valid <= 1;
      end
      R_STATE_WAIT4DATA: begin
        if (REGS_RREADY == 1) begin
          state_r <= R_STATE_WAIT4ADDR;
          r_valid <= 0;
          REGS_ARREADY <= 1;
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
    REG_{{ reg['name'] }}_W <= {{ reg|default_val_v }};
    {%- if reg['use_upd_pulse'] %}
    R_{{ reg['name'] }}_O_upd <= 0;
    {%- endif %}
    {%- endif %}
    {%- endfor %}
  end
  else begin
    {%- for reg in regs -%}
    {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' %}
    {%- if reg['use_upd_pulse'] %}
    R_{{ reg['name'] }}_O_upd <= 0;
    {%- endif %}
    {%- endif %}
    {%- endfor %}
    if (REGS_WVALID && w_ready) begin
      {% for reg in regs -%}
      {% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
      if (address_wr == {{ reg['addr_offset'] }}) begin
        {%- if reg['use_upd_pulse'] %}
        R_{{ reg['name'] }}_O_upd <= 1;
        {%- endif %}
        REGS_BRESP <= AXI_RESP_OKAY;
        {%- for s in range(strobe_size) %}
        {%- if 8*s < reg['bits']|count_bits %}
        if (REGS_WSTRB[{{s}}] == 1) begin
          REG_{{ reg['name'] }}_W[{{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }}:{{ 8*s }}] <= REGS_WDATA[{{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }}:{{ 8*s }}];
        end
        {%- endif %}
        {%- endfor %}
      end else {% endif -%}{% endfor -%} begin
        REGS_BRESP <= AXI_RESP_SLVERR;
      end
    end
  end
end

always @* begin
  case (address_rd)
    {% for reg in regs -%}
    {{ reg['addr_offset'] }}: begin
      {% if reg['bits']|count_bits < data_size %}
      rd_mux = {{'{ {'}}{{ data_size - reg['bits']|count_bits }}{1'b0{{'}}'}}, REG_{{ reg['name'] }}_R };
      {% else %}
      rd_mux = REG_{{ reg['name'] }}_R;
      {% endif %}
      rd_resp = AXI_RESP_OKAY;
    end
    {% endfor %}
    default: begin
      rd_mux = 0;
      rd_resp = AXI_RESP_SLVERR;
    end
  endcase
end

// Read process
always @(posedge REGS_ACLK) begin
  if (!REGS_ARESETN) begin
  end else begin
    if (state_r == R_STATE_WAITREG) begin
      REGS_RDATA <= rd_mux;
      REGS_RRESP <= rd_resp;
    end
  end
end

endmodule

