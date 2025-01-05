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
from test import test_dir


def test_check_verilator_installed():
    """Verify Verilator compiler is installed and accessible.

    Tests:
        1. Checks if Verilator executable exists in system PATH
        2. Verifies Verilator help command returns successfully

    Raises:
        AssertionError: If Verilator is not found or returns non-zero exit code
    """
    try:
        assert (
            subprocess.run(['verilator', '--version']).returncode == 0
        ), 'Verilator executable not found in path'
    except FileNotFoundError:
        assert False, 'Verilator not found in path'


def test_basic_verilog():
    """Verify generated Verilog code compiles with Verilator.

    Tests:
        1. Generates temporary Verilog file with unique name
        2. Attempts to compile with Verilator
        3. Verifies compilation succeeds

    Cleanup:
        Removes temporary Verilog file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, f'_test_{uuid.uuid4().hex}.v')
    with open(test_file, 'w') as f:
        f.write(reg.to_verilog())
    try:
        x = subprocess.run(
            ['verilator', '--lint-only', test_file], capture_output=True, text=True
        )
    finally:
        os.remove(test_file)
    assert x.returncode == 0, (
        f'Verilog did not successfully compile in Verilator. See file: {test_file}\nError:\n'
        + x.stderr
    )


def test_verilogsim_noreg():
    """Test Verilog RTL simulation of generated register file.

    Tests:
        1. Generates Verilog code
        2. Runs cocotb simulation with inputs NOT registered
        3. Verifies simulation completes successfully
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, '_test.v')
    with open(test_file, 'w') as f:
        f.write(reg.to_verilog())

    cocotb_test.simulator.run(
        verilog_sources=['./test/_test.v'],
        toplevel_lang='verilog',
        toplevel='reg_file',
        module='test.test_sim',
        simulator='verilator',
        parameters=dict(REGISTER_INPUTS=0),
    )


def test_verilogsim_reg():
    """Test Verilog RTL simulation of generated register file.

    Tests:
        1. Generates Verilog code
        2. Runs cocotb simulation with inputs registered
        3. Verifies simulation completes successfully
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, '_test.v')
    with open(test_file, 'w') as f:
        f.write(reg.to_verilog())

    cocotb_test.simulator.run(
        verilog_sources=['./test/_test.v'],
        toplevel_lang='verilog',
        toplevel='reg_file',
        module='test.test_sim',
        simulator='verilator',
        parameters=dict(REGISTER_INPUTS=1),
    )
