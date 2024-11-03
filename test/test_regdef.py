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
import json
import pytest
from test import test_dir


def test_check_ghdl_installed():
    """Verify GHDL compiler is installed and accessible.

    Tests:
        1. Checks if GHDL executable exists in system PATH
        2. Verifies GHDL help command returns successfully

    Raises:
        AssertionError: If GHDL is not found or returns non-zero exit code
    """
    try:
        assert (
            subprocess.run(['ghdl', 'help']).returncode == 0
        ), 'GHDL executable not found in path'
    except FileNotFoundError:
        assert False, 'GHDL not found in path'


def test_basic_definition():
    """Test basic register definition loading and VHDL generation.

    Tests:
        1. Loads register definition from JSON file
        2. Verifies VHDL can be generated without errors
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    print(reg.to_vhdl())


def test_default_values():
    """Verify default values are correctly set in register configuration.

    Tests:
        1. Checks register type is set to 'ro' for first register
        2. Verifies default value is 0 for specific bit field
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    assert reg._cfg[0]['reg_type'] == 'ro'
    assert reg._cfg[2]['bits'][1]['default_value'] == 0


def test_numeric_conversion():
    """Test numeric value conversion in register configuration.

    Tests:
        1. Verifies default value of 0xFF is converted to 255 properly
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    assert reg._cfg[2]['bits'][0]['default_value'] == 255


def test_address_values():
    """Verify register address assignments.

    Tests:
        1. Checks sequential addresses are assigned correctly
        2. Verifies address offset is set to 64
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    for i in range(2):
        assert reg._cfg[i]['addr_offset'] == 4 * i
    assert reg._cfg[2]['addr_offset'] == 64


def test_generate_vhd():
    """Test VHDL code generation and file output.

    Tests:
        1. Generates VHDL code from register definition
        2. Writes VHDL code to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())


def test_basic_vhd():
    """Verify generated VHDL code compiles with GHDL.

    Tests:
        1. Generates temporary VHDL file with unique name
        2. Attempts to compile with GHDL
        3. Verifies compilation succeeds

    Cleanup:
        Removes temporary VHDL file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
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


def test_duplicate_address_detection():
    """Test detection of duplicate register addresses.

    Tests:
        1. Attempts to create registers with duplicate address 4
        2. Verifies ValueError is raised with correct message
        3. Repeats test with address 64

    Raises:
        AssertionError: If duplicate addresses not detected
    """
    json_file = os.path.join(test_dir, 'test_json.json')
    with open(json_file, 'r') as f:
        json_string = f.read()
    cfg = json.loads(json_string)
    cfg.append(dict(name='dup_addr', addr_offset=4, bits=32))

    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(cfg)

    assert e_info.type is ValueError
    assert (
        str(e_info.value)
        == r'Multiple registers have the same address (addresses: [4])'
    )

    json_file = os.path.join(test_dir, 'test_json.json')
    with open(json_file, 'r') as f:
        json_string = f.read()
    cfg = json.loads(json_string)
    cfg.append(dict(name='dup_addr', addr_offset=64, bits=32))

    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(cfg)

    assert e_info.type is ValueError
    assert (
        str(e_info.value)
        == r'Multiple registers have the same address (addresses: [64])'
    )


def test_duplicate_name_detection():
    """Test detection of duplicate register names.

    Tests:
        1. Attempts to create registers with duplicate name 'Scratch_Register'
        2. Verifies ValueError is raised with correct message

    Raises:
        AssertionError: If duplicate names not detected
    """
    json_file = os.path.join(test_dir, 'test_json.json')
    with open(json_file, 'r') as f:
        json_string = f.read()
    cfg = json.loads(json_string)
    cfg.append(dict(name='Scratch_Register', addr_offset=8, bits=32))

    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(cfg)

    assert e_info.type is ValueError
    assert (
        str(e_info.value)
        == "Multiple registers have the same name (names: ['Scratch_Register'])"
    )


def test_address_too_large():
    """Test detection of registers exceeding maximum bit width.

    Tests:
        1. Attempts to create registers with 33 bits (exceeding 32-bit limit)
        2. Tests various register configurations (simple, dict, field list)
        3. Verifies ValueError is raised with correct message

    Raises:
        AssertionError: If oversized registers not detected
    """
    json_file = os.path.join(test_dir, 'test_json.json')

    too_long_regs = [
        dict(name='too_long0', bits=33),
        dict(name='too_long1', bits=dict(num_bits=33, default_value=0)),
        dict(
            name='too_long2',
            bits=[
                dict(field_name='field0', num_bits=16),
                dict(field_name='field1', num_bits=17, default_value=0),
            ],
        ),
    ]

    for too_long_reg in too_long_regs:
        with open(json_file, 'r') as f:
            json_string = f.read()
        cfg = json.loads(json_string)
        cfg.append(too_long_reg)

        with pytest.raises(ValueError) as e_info:
            axi4lite_reg_generator.RegDef(cfg)

        assert e_info.type is ValueError
        assert (
            str(e_info.value)
            == f'Register contains too many bits (name: {too_long_reg["name"]}, bits: 33 > 32)'
        )


def test_rtlsim():
    """Test RTL simulation of generated register file.

    Tests:
        1. Generates VHDL code
        2. Runs cocotb simulation
        3. Verifies simulation completes successfully
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())

    cocotb_test.simulator.run(
        vhdl_sources=['./test/_test.vhd'],
        toplevel_lang='vhdl',
        toplevel='reg_file',
        module='test.test_sim',
        simulator='ghdl',
    )


def test_json_output():
    """Test JSON serialization and deserialization of register configuration.

    Tests:
        1. Converts register configuration to JSON
        2. Creates new register definition from JSON
        3. Verifies configurations match
        4. Verifies generated VHDL matches
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    reg_str = reg.get_reg_json()

    cfg_new = json.loads(reg_str)
    reg_new = axi4lite_reg_generator.RegDef(cfg_new)

    assert reg._cfg == reg_new._cfg
    assert reg._reg_cfg == reg_new._reg_cfg
    assert reg.to_vhdl() == reg_new.to_vhdl()


def test_md_output():
    """Test markdown documentation generation.

    Tests:
        1. Generates markdown documentation
        2. Writes documentation to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    with open(os.path.join(test_dir, '_test.md'), 'w') as f:
        f.write(reg.to_md())


def test_basic_heirarchy():
    """Test register hierarchy with default separator.

    Tests:
        1. Loads hierarchical register configuration
        2. Verifies correct address assignments
        3. Verifies correct name generation with hierarchy
        4. Verifies correct register types

    Checks:
        - Address offsets
        - Register names with hierarchy
        - Register types (ro/rw/custom)
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_heir_top.json')
    )

    expected_addresses = [0, 128, 132, 192, 196, 200, 260, 500, 504, 564]
    expected_names = [
        'Heir_Register_Top',
        'Heirarchy_One_Test_Register',
        'Heirarchy_One_Scratch_Register',
        'Heirarchy_One_Register_with_Fields',
        'Heirarchy_Two_Test_Register',
        'Heirarchy_Two_Scratch_Register',
        'Heirarchy_Two_Register_with_Fields',
        'Heirarchy_Three_Test_Register',
        'Heirarchy_Three_Scratch_Register',
        'Heirarchy_Three_Register_with_Fields',
    ]
    expected_types = [
        'ro',
        'ro',
        'rw',
        'custom',
        'ro',
        'rw',
        'custom',
        'ro',
        'rw',
        'custom',
    ]

    # Check each register's address, name and type
    for i, cfg in enumerate(reg._cfg):
        assert (
            cfg['addr_offset'] == expected_addresses[i]
        ), f"Wrong address for {cfg['name']}"
        assert (
            cfg['name'] == expected_names[i]
        ), f"Wrong name at address {cfg['addr_offset']}"
        assert cfg['reg_type'] == expected_types[i], f"Wrong type for {cfg['name']}"


def test_heirarchy_separator():
    """Test register hierarchy with custom separator.

    Tests:
        1. Sets custom hierarchy separator to '__'
        2. Verifies correct name generation with custom separator
        3. Verifies addresses and types remain correct

    Checks:
        - Address offsets unchanged
        - Register names with custom separator
        - Register types unchanged
    """
    with open(os.path.join(test_dir, 'test_heir_top.json'), 'r') as f:
        cfg = json.load(f)
    cfg[0]['config']['instance_separator'] = '__'

    reg = axi4lite_reg_generator.RegDef(cfg, test_dir)

    expected_addresses = [0, 128, 132, 192, 196, 200, 260, 500, 504, 564]
    expected_names = [
        'Heir_Register_Top',
        'Heirarchy_One__Test_Register',
        'Heirarchy_One__Scratch_Register',
        'Heirarchy_One__Register_with_Fields',
        'Heirarchy_Two__Test_Register',
        'Heirarchy_Two__Scratch_Register',
        'Heirarchy_Two__Register_with_Fields',
        'Heirarchy_Three__Test_Register',
        'Heirarchy_Three__Scratch_Register',
        'Heirarchy_Three__Register_with_Fields',
    ]
    expected_types = [
        'ro',
        'ro',
        'rw',
        'custom',
        'ro',
        'rw',
        'custom',
        'ro',
        'rw',
        'custom',
    ]

    # Check each register's address, name and type
    for i, cfg in enumerate(reg._cfg):
        assert (
            cfg['addr_offset'] == expected_addresses[i]
        ), f"Wrong address for {cfg['name']}"
        assert (
            cfg['name'] == expected_names[i]
        ), f"Wrong name at address {cfg['addr_offset']}"
        assert cfg['reg_type'] == expected_types[i], f"Wrong type for {cfg['name']}"
