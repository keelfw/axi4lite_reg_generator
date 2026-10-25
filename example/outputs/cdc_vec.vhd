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
-- cdc_vec: WIDTH-wide atomic vector transfer between two clock domains with an
-- internally generated request. Same handshake as cdc_vecp, but src_send is
-- derived internally: the source requests a new transfer whenever the previous
-- one has completed, so src_in is sampled continuously at the handshake rate.
--
-- The source only re-requests after the acknowledge has crossed back, so the
-- holding register is stable for the whole round trip and every captured value
-- is coherent (atomic). Auto-acknowledges (no external dest_ack).
--
-- Generics mirror XPM_CDC_HANDSHAKE. There is no reset; registers take their
-- power-up value from the declaration initializer / GSR / init.

library ieee;
use ieee.std_logic_1164.all;

entity cdc_vec is
  generic (
    DEST_SYNC_FF   : positive := 4;
    INIT_SYNC_FF   : natural  := 0;
    SIM_ASSERT_CHK : natural  := 0;
    SRC_SYNC_FF    : positive := 4;
    WIDTH          : positive := 1
  );
  port (
    src_clk  : in  std_logic;
    src_in   : in  std_logic_vector(WIDTH-1 downto 0);
    src_rcv  : out std_logic;
    dest_clk : in  std_logic;
    dest_req : out std_logic;
    dest_out : out std_logic_vector(WIDTH-1 downto 0)
  );
end entity cdc_vec;

architecture rtl of cdc_vec is
  -- Source domain
  signal src_data_r     : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal src_req_r      : std_logic := '0';
  signal src_busy_r     : std_logic := '0';
  signal ack_sync_r     : std_logic_vector(SRC_SYNC_FF-1 downto 0) := (others => '0');
  signal src_ack_prev_r : std_logic := '0';

  -- Destination domain
  signal req_sync_r     : std_logic_vector(DEST_SYNC_FF-1 downto 0) := (others => '0');
  signal req_prev_r     : std_logic := '0';
  signal dst_data_r     : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal dst_req_r      : std_logic := '0';
  signal dst_ack_r      : std_logic := '0';

  signal src_ack    : std_logic;
  signal ack_event  : std_logic;
  signal src_start  : std_logic;
  signal req_last   : std_logic;
  signal req_event  : std_logic;

  attribute async_reg : string;
  attribute async_reg of ack_sync_r : signal is "true";
  attribute async_reg of req_sync_r : signal is "true";
begin

  assert DEST_SYNC_FF >= 2 report "DEST_SYNC_FF must be >= 2" severity failure;
  assert SRC_SYNC_FF >= 2 report "SRC_SYNC_FF must be >= 2" severity failure;
  assert WIDTH >= 1 report "WIDTH must be >= 1" severity failure;

  -- ---- Source domain: request whenever the previous transfer completed -----
  src_ack   <= ack_sync_r(SRC_SYNC_FF-1);
  ack_event <= src_ack xor src_ack_prev_r;
  src_start <= not src_busy_r or ack_event;

  src_p : process(src_clk) is
  begin
    if rising_edge(src_clk) then
      ack_sync_r(SRC_SYNC_FF-1 downto 1) <= ack_sync_r(SRC_SYNC_FF-2 downto 0);
      ack_sync_r(0) <= dst_ack_r;
      src_ack_prev_r <= src_ack;
      if src_start = '1' then
        src_data_r <= src_in;
        src_req_r  <= not src_req_r;
        src_busy_r <= '1';
      end if;
    end if;
  end process;

  src_rcv <= not src_busy_r;

  -- ---- Destination domain --------------------------------------------------
  req_last  <= req_sync_r(DEST_SYNC_FF-1);
  req_event <= req_last xor req_prev_r;

  dst_p : process(dest_clk) is
  begin
    if rising_edge(dest_clk) then
      req_sync_r(DEST_SYNC_FF-1 downto 1) <= req_sync_r(DEST_SYNC_FF-2 downto 0);
      req_sync_r(0) <= src_req_r;
      req_prev_r <= req_last;
      dst_req_r  <= req_event;
      if req_event = '1' then
        dst_data_r <= src_data_r;
        dst_ack_r  <= not dst_ack_r;
      end if;
    end if;
  end process;

  dest_req <= dst_req_r;
  dest_out <= dst_data_r;

end architecture rtl;
