-- Copyright (C) 2024 KEELFW
--
-- This library is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public
-- License as published by the Free Software Foundation; either
-- version 2.1 of the License, or (at your option) any later version.
--
-- This library is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public
-- License along with this library; if not, write to the Free Software
-- Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
--
-- See LICENSE file for full license details.
library ieee;
use ieee.std_logic_1164.all;
use ieee.math_real.all;
use ieee.numeric_std.all;

-- Data Size = {{ data_size }}
-- Write Strobe Size = {{ strobe_size }}

entity {{ entity_name }} is
generic (
  ADDRESS_W        : positive := 32;
  ADDRESS_APERTURE : positive :=  8;
  REGISTER_INPUTS  : boolean  := false
);
port (
  REGS_ACLK    :  in std_logic;
  REGS_ARESETN :  in std_logic;
  -- Registers
  {% for reg in regs -%}
  {% if reg['reg_type'] == 'ro' or reg['reg_type'] == 'custom' -%}
  R_{{ reg['name'] }}_I :  in std_logic_vector({{ reg['bits']|count_bits - 1 }} downto 0);
  {% endif -%}
  {% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
  R_{{ reg['name'] }}_O :  out std_logic_vector({{ reg['bits']|count_bits - 1 }} downto 0);
  {% if reg['use_upd_pulse'] -%}
  R_{{ reg['name'] }}_O_upd : out std_logic;
  {% endif -%}
  {% endif -%}
  {% endfor %}
  -- Write Address Channel
  REGS_AWVALID :  in std_logic;
  REGS_AWREADY : out std_logic;
  REGS_AWADDR  :  in std_logic_vector(ADDRESS_W-1 downto 0);
  REGS_AWPROT  :  in std_logic_vector(2 downto 0);
  -- Write Data Channel
  REGS_WVALID  :  in std_logic;
  REGS_WREADY  : out std_logic;
  REGS_WDATA   :  in std_logic_vector({{ data_size }}-1 downto 0);
  REGS_WSTRB   :  in std_logic_vector({{ strobe_size }}-1 downto 0);
  -- Write Response Channel
  REGS_BVALID  : out std_logic;
  REGS_BREADY  :  in std_logic;
  REGS_BRESP   : out std_logic_vector(1 downto 0);
  -- Read Address Channel
  REGS_ARVALID :  in std_logic;
  REGS_ARREADY : out std_logic;
  REGS_ARADDR  :  in std_logic_vector(ADDRESS_W-1 downto 0);
  REGS_ARPROT  :  in std_logic_vector(2 downto 0);
  -- Read Data Channel
  REGS_RVALID  : out std_logic;
  REGS_RREADY  :  in std_logic;
  REGS_RDATA   : out std_logic_vector({{ data_size }}-1 downto 0);
  REGS_RRESP   : out std_logic_vector(1 downto 0)
);
end entity {{ entity_name }};

architecture rtl of {{ entity_name }} is
  constant AXI_RESP_OKAY   : std_logic_vector(1 downto 0) := "00";
  constant AXI_RESP_EXOKAY : std_logic_vector(1 downto 0) := "01";
  constant AXI_RESP_SLVERR : std_logic_vector(1 downto 0) := "10";
  constant AXI_RESP_DECERR : std_logic_vector(1 downto 0) := "11";
  
  -- Register signal declarations
  {% for reg in regs -%}
  signal REG_{{ reg['name'] }}_R : std_logic_vector({{ reg['bits']|count_bits-1 }} downto 0);
  {% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
  signal REG_{{ reg['name'] }}_W : std_logic_vector({{ reg['bits']|count_bits-1 }} downto 0);
  {% endif -%}
  {% endfor %}
  -- internal AXI support signals
  type STATE_WR_T is (RST, WAIT4ADDR, WAIT4DATA, WAIT4RESP);
  signal state_w : STATE_WR_T;

  type STATE_RD_T is (RST, WAIT4ADDR, WAITREG, WAIT4DATA);
  signal state_r : STATE_RD_T;

  signal address_wr : std_logic_vector(ADDRESS_APERTURE-1 downto 0);
  signal address_rd : std_logic_vector(ADDRESS_APERTURE-1 downto 0);

  signal w_ready : std_logic;
  signal r_valid : std_logic;

  signal rd_mux  : std_logic_vector({{ data_size-1 }} downto 0);
  signal rd_resp : std_logic_vector(1 downto 0);
begin

  -- Handle inputs

  {% for reg in regs -%}
  {% if reg['reg_type'] == 'rw' -%}
    REG_{{ reg['name'] }}_R <= REG_{{ reg['name'] }}_W;
  {% endif -%}
  {% endfor %}

  reg_inputs_g : if REGISTER_INPUTS generate
    process(REGS_ACLK) is
    begin
      if rising_edge(REGS_ACLK) then
        {% for reg in regs -%}
        {% if reg['reg_type'] == 'ro' or reg['reg_type'] == 'custom' -%}
          REG_{{ reg['name'] }}_R <= R_{{ reg['name'] }}_I; 
        {% endif -%}
        {% endfor %}
      end if;
    end process;
  end generate;

  con_inputs_g : if not REGISTER_INPUTS generate
    {% for reg in regs -%}
    {% if reg['reg_type'] != 'rw' -%}
      REG_{{ reg['name'] }}_R <= R_{{ reg['name'] }}_I;
    {% endif -%}
    {% endfor %}
  end generate;

  -- Connect outputs
  {% for reg in regs -%}
  {% if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
    R_{{ reg['name'] }}_O <= REG_{{ reg['name'] }}_W;
  {% endif -%}
  {% endfor %}
  -- Connect AXI-Lite ready/valid control signals
  REGS_WREADY <= w_ready;
  REGS_RVALID <= r_valid;

  write_fsm_p : process(REGS_ACLK) is
  begin
    if rising_edge(REGS_ACLK) then
      if REGS_ARESETN = '0' then
        state_w <= RST;
        REGS_AWREADY <= '0';
        w_ready  <= '0';
        REGS_BVALID <= '0';
      else
        case state_w is
          when RST =>
            state_w <= WAIT4ADDR;
            REGS_AWREADY <= '1';
          when WAIT4ADDR =>
            if REGS_AWVALID = '1' then
              state_w <= WAIT4DATA;
              REGS_AWREADY <= '0';
              w_ready  <= '1';
              address_wr <= REGS_AWADDR(address_wr'range);
            end if;
          when WAIT4DATA =>
            if REGS_WVALID = '1' then
              state_w <= WAIT4RESP;
              w_ready <= '0';
              REGS_BVALID <= '1';
            end if;
          when WAIT4RESP =>
            if REGS_BREADY = '1' then
              state_w <= WAIT4ADDR;
              REGS_BVALID <= '1';
              REGS_AWREADY <= '1';
            end if;
          when others =>
            state_w <= RST;
        end case;
      end if;
    end if;
  end process;

  read_ctrl_p : process (REGS_ACLK) is
  begin
    if rising_edge(REGS_ACLK) then
      if REGS_ARESETN = '0' then
        state_r <= RST;
        REGS_ARREADY <= '0';
        r_valid <= '0';
      else
        case state_r is
          when RST =>
            state_r <= WAIT4ADDR;
            REGS_ARREADY <= '1';
          when WAIT4ADDR =>
            if REGS_ARVALID = '1' then
              state_r <= WAITREG;
              REGS_ARREADY <= '0';
              address_rd   <= REGS_ARADDR(address_rd'range);
            end if;
          when WAITREG =>
            state_r <= WAIT4DATA;
            r_valid <= '1';
          when WAIT4DATA =>
            if REGS_RREADY = '1' then
              state_r <= WAIT4ADDR;
              r_valid <= '0';
              REGS_ARREADY <= '1';
            end if;
          when others=>
            state_r <= RST;
        end case;
      end if;
    end if;
  end process;

  write_p : process (REGS_ACLK) is
  begin
    if rising_edge(REGS_ACLK) then
      if REGS_ARESETN = '0' then
        {%- for reg in regs -%}
        {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' %}
        REG_{{ reg['name'] }}_W <= {{ reg|default_val }};
        {%- if reg['use_upd_pulse'] %}
        R_{{ reg['name'] }}_O_upd <= '0';
        {%- endif %}
        {%- endif %}
        {%- endfor %}
      else
        {%- for reg in regs -%}
        {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' %}
        {%- if reg['use_upd_pulse'] %}
        R_{{ reg['name'] }}_O_upd <= '0';
        {%- endif %}
        {%- endif %}
        {%- endfor %}
        if REGS_WVALID = '1' and w_ready = '1' then
          {% for reg in regs -%}
          {%- if reg['reg_type'] == 'rw' or reg['reg_type'] == 'custom' -%}
          if address_wr = std_logic_vector(to_unsigned({{ reg['addr_offset'] }}, ADDRESS_APERTURE)) then
            {%- if reg['use_upd_pulse'] %}
            R_{{ reg['name'] }}_O_upd <= '1';
            {%- endif %}
            REGS_BRESP <= AXI_RESP_OKAY;
            {%- for s in range(strobe_size) %}
            {%- if 8*s < reg['bits']|count_bits %}
            if REGS_WSTRB({{s}}) = '1' then
              REG_{{ reg['name'] }}_W({{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }} downto {{ 8*s }}) <= REGS_WDATA({{ [reg['bits']|count_bits-1, 8*(s+1)-1]|min }} downto {{ 8*s }});
            end if;
            {%- endif %}
            {%- endfor %}
          els{%- endif -%}{%- endfor -%}e
            REGS_BRESP <= AXI_RESP_SLVERR;
          end if;
        end if;
      end if;
    end if;
  end process;

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

end architecture rtl;