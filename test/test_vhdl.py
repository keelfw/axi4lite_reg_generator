# Copyright (C) 2024 KEELFW
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# See LICENSE file for full license details.
import os
import axi4lite_reg_generator
import subprocess
import cocotb_test.simulator
import uuid

test_dir = os.path.dirname(__file__)
json_file_path = os.path.join(test_dir, 'test_json.json')


def test_check_ghdl_installed():
    """Verify GHDL compiler is installed and accessible.

    Tests:
        1. Checks if GHDL executable exists in system PATH
        2. Verifies GHDL help command returns successfully

    Raises:
        AssertionError: If GHDL is not found or returns non-zero exit code
    """
    try:
        assert subprocess.run(['ghdl', 'help']).returncode == 0, (
            'GHDL executable not found in path'
        )
    except FileNotFoundError:
        assert False, 'GHDL not found in path'


def test_basic_vhd():
    """Verify generated VHDL code compiles with GHDL.

    Tests:
        1. Generates temporary VHDL file with unique name
        2. Attempts to compile with GHDL
        3. Verifies compilation succeeds

    Cleanup:
        Removes temporary VHDL file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, f'_test_{uuid.uuid4().hex}.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())
    try:
        x = subprocess.run(['ghdl', '-a', test_file], capture_output=True, text=True)
    finally:
        os.remove(test_file)
    assert x.returncode == 0, (
        f'VHDL did not successfully compile in GHDL. See file: {test_file}\nError:\n'
        + x.stderr
    )


def test_vhdlsim_noreg():
    """Test VHDL RTL simulation of generated register file.

    Tests:
        1. Generates VHDL code
        2. Runs cocotb simulation with inputs NOT registered
        3. Verifies simulation completes successfully
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())

    cocotb_test.simulator.run(
        vhdl_sources=['./test/_test.vhd'],
        toplevel_lang='vhdl',
        toplevel='reg_file',
        module='test.test_sim',
        simulator='ghdl',
        parameters=dict(REGISTER_INPUTS=False),
    )


def test_vhdlsim_reg():
    """Test VHDL RTL simulation of generated register file.

    Tests:
        1. Generates VHDL code
        2. Runs cocotb simulation with inputs registered
        3. Verifies simulation completes successfully
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())

    cocotb_test.simulator.run(
        vhdl_sources=['./test/_test.vhd'],
        toplevel_lang='vhdl',
        toplevel='reg_file',
        module='test.test_sim',
        simulator='ghdl',
        parameters=dict(REGISTER_INPUTS=True),
    )
