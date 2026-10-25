-- Copyright (C) 2026 KEELFW
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
--
-- cdc_ff: WIDTH-wide, DEST_SYNC_FF-deep array synchronizer. Vendor-neutral
-- equivalent of the Xilinx XPM_CDC_ARRAY_SINGLE macro (not instantiated).
-- Each bit of src_in is synchronized independently into the dest_clk domain
-- through src_in -> src_r -> sync_r(0) -> ... -> dest_out.
--
-- This is only a per-bit metastability filter, not an atomic transfer: src_in
-- must be quasi-static (stable for at least DEST_SYNC_FF dest_clk edges) for
-- dest_out to be coherent. Use cdc_vec / cdc_vecp for coherent transfers.
--
-- Generics mirror XPM_CDC_ARRAY_SINGLE. There is no reset; the registers take
-- their power-up value from the declaration initializer / GSR / init.

library ieee;
use ieee.std_logic_1164.all;

entity cdc_ff is
  generic (
    DEST_SYNC_FF   : positive := 4;
    INIT_SYNC_FF   : natural  := 0;
    SIM_ASSERT_CHK : natural  := 0;
    SRC_INPUT_REG  : natural  := 1;
    WIDTH          : positive := 1
  );
  port (
    src_clk  : in  std_logic;
    src_in   : in  std_logic_vector(WIDTH-1 downto 0);
    dest_clk : in  std_logic;
    dest_out : out std_logic_vector(WIDTH-1 downto 0)
  );
end entity cdc_ff;

architecture rtl of cdc_ff is
  type sync_t is array (0 to DEST_SYNC_FF-1) of std_logic_vector(WIDTH-1 downto 0);

  signal sync_r : sync_t := (others => (others => '0'));
  signal src_r  : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal src_i  : std_logic_vector(WIDTH-1 downto 0);

  attribute async_reg : string;
  attribute async_reg of sync_r : signal is "true";
  attribute async_reg of src_r  : signal is "true";
begin

  assert DEST_SYNC_FF >= 2 and DEST_SYNC_FF <= 10
    report "DEST_SYNC_FF must be in the range 2 to 10" severity failure;
  assert WIDTH >= 1 report "WIDTH must be >= 1" severity failure;

  -- Optional source-domain input register (SRC_INPUT_REG).
  gen_src_reg : if SRC_INPUT_REG /= 0 generate
    src_p : process(src_clk) is
    begin
      if rising_edge(src_clk) then
        src_r <= src_in;
      end if;
    end process;
    src_i <= src_r;
  end generate;

  gen_no_src_reg : if SRC_INPUT_REG = 0 generate
    src_i <= src_in;
  end generate;

  -- Destination-domain synchronizer pipeline.
  sync_p : process(dest_clk) is
  begin
    if rising_edge(dest_clk) then
      sync_r(0) <= src_i;
      for i in 1 to DEST_SYNC_FF-1 loop
        sync_r(i) <= sync_r(i-1);
      end loop;
    end if;
  end process;

  dest_out <= sync_r(DEST_SYNC_FF-1);

end architecture rtl;
