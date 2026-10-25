# Copyright (C) 2025 KEELFW
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
import json
import pytest
import schema
import re

test_dir = os.path.dirname(__file__)
json_file_path = os.path.join(test_dir, 'test_json.json')


def test_basic_definition():
    """Test basic register definition loading and VHDL generation.

    Tests:
        1. Loads register definition from JSON file
        2. Verifies VHDL can be generated without errors
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    print(reg.to_vhdl())


def test_default_values():
    """Verify default values are correctly set in register configuration.

    Tests:
        1. Checks register type is set to 'ro' for first register
        2. Verifies default value is 0 for specific bit field
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)

    assert reg._cfg[0]['reg_type'] == 'ro'
    assert reg._cfg[2]['bits'][2]['default_value'] == 0


def test_bad_default_values():
    """Test validation of register default values.

    Tests:
        1. Tests various invalid default values: integer > 16, string, tuple
        2. Verifies schema validation catches non-numeric values
        3. Allows valid numeric value (18) to pass

    Raises:
        schema.SchemaError: When non-numeric or invalid default values are used
    """
    default_to_try = [18, 'hello', (1,)]

    for idx, default_value in enumerate(default_to_try):
        with open(json_file_path, 'r') as f:
            json_string = f.read()
        cfg = json.loads(json_string)
        cfg.append(
            dict(
                name='bad_default1', bits=dict(num_bits=32, default_value=default_value)
            )
        )

        if idx > 0:
            with pytest.raises(schema.SchemaError):
                axi4lite_reg_generator.RegDef(cfg)
        else:
            axi4lite_reg_generator.RegDef(cfg)


def test_numeric_conversion():
    """Test numeric value conversion in register configuration.

    Tests:
        1. Verifies default value of 0xFF is converted to 255 properly
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)

    assert reg._cfg[2]['bits'][1]['default_value'] == 255
    assert reg._cfg[2]['bits'][0]['default_value'] == 3


def test_address_values():
    """Verify register address assignments.

    Tests:
        1. Checks sequential addresses are assigned correctly
        2. Verifies address offset is set to 64
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)

    for i in range(2):
        assert reg._cfg[i]['addr_offset'] == 4 * i
    assert reg._cfg[2]['addr_offset'] == 64


def test_generate_vhd():
    """Test VHDL code generation and file output.

    Tests:
        1. Generates VHDL code from register definition
        2. Writes VHDL code to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())


def test_generate_verilog():
    """Test Verilog code generation and file output.

    Tests:
        1. Generates Verilog code from register definition
        2. Writes Verilog code to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.v')
    with open(test_file, 'w') as f:
        f.write(reg.to_verilog())


def test_generate_sv():
    """Test SystemVerilog code generation and file output.

    Tests:
        1. Generates SystemVerilog code from register definition
        2. Writes SystemVerilog code to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.sv')
    with open(test_file, 'w') as f:
        f.write(reg.to_systemverilog())


def test_generate_header():
    """Test C header file generation and file output.

    Tests:
        1. Generates C header file from register definition
        2. Writes header file to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    test_file = os.path.join(test_dir, '_test.h')
    with open(test_file, 'w') as f:
        f.write(reg.to_header())


def test_duplicate_address_detection():
    """Test detection of duplicate register addresses.

    Tests:
        1. Attempts to create registers with duplicate address 4
        2. Verifies ValueError is raised with correct message
        3. Repeats test with address 64

    Raises:
        AssertionError: If duplicate addresses not detected
    """
    with open(json_file_path, 'r') as f:
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

    with open(json_file_path, 'r') as f:
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
    with open(json_file_path, 'r') as f:
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
        with open(json_file_path, 'r') as f:
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


def test_json_output():
    """Test JSON serialization and deserialization of register configuration.

    Tests:
        1. Converts register configuration to JSON
        2. Creates new register definition from JSON
        3. Verifies configurations match
        4. Verifies generated VHDL matches
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)

    # Disable timestamp output which can cause mismatch in generated vhdl
    reg._reg_cfg['include_timestamp'] = False

    reg_str = reg.get_reg_json()

    cfg_new = json.loads(reg_str)
    reg_new = axi4lite_reg_generator.RegDef(cfg_new)

    assert reg._cfg == reg_new._cfg
    assert reg._reg_cfg == reg_new._reg_cfg
    assert reg.to_vhdl() == reg_new.to_vhdl()
    assert reg.to_verilog() == reg_new.to_verilog()
    assert reg.to_md() == reg_new.to_md()


def test_md_output():
    """Test markdown documentation generation.

    Tests:
        1. Generates markdown documentation
        2. Writes documentation to file
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)

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
        assert cfg['addr_offset'] == expected_addresses[i], (
            f'Wrong address for {cfg["name"]}'
        )
        assert cfg['name'] == expected_names[i], (
            f'Wrong name at address {cfg["addr_offset"]}'
        )
        assert cfg['reg_type'] == expected_types[i], f'Wrong type for {cfg["name"]}'


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
        assert cfg['addr_offset'] == expected_addresses[i], (
            f'Wrong address for {cfg["name"]}'
        )
        assert cfg['name'] == expected_names[i], (
            f'Wrong name at address {cfg["addr_offset"]}'
        )
        assert cfg['reg_type'] == expected_types[i], f'Wrong type for {cfg["name"]}'


def test_missing_config():
    """Test error handling when configuration section is missing.

    Tests:
        1. Loads JSON configuration and removes config section
        2. Attempts to create RegDef with missing config
        3. Verifies ValueError is raised with correct message

    Raises:
        AssertionError: If missing config not detected
    """
    with open(json_file_path, 'r') as f:
        cfg = json.load(f)

    new_cfg = [c for c in cfg if not (isinstance(c, dict) and 'config' in c)]

    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(new_cfg)

    assert e_info.type is ValueError
    assert str(e_info.value) == r'Could not find configuration'


def test_custom_entity_name():
    """Test custom entity name

    Tests:
        1. Verify entity name in VHDL
        2. Verify entity name in Verilog
        3. Verify entity name in Markdown documentation
    """
    test_override_entity_name = 'test_entity_name'
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        json_file_path, test_override_entity_name
    )

    vhdl_str = reg.to_vhdl()
    re_search = re.search(r'entity (\w+) is', vhdl_str)
    assert re_search is not None, 'Did not find entity!'
    assert re_search.group(1) == test_override_entity_name, (
        f'Entity name should be {test_override_entity_name}, but is {re_search.group(1)}'
    )

    verilog_str = reg.to_verilog()
    re_search = re.search(r'module (\w+)', verilog_str)
    assert re_search is not None, 'Did not find module!'
    assert re_search.group(1) == test_override_entity_name, (
        f'Module name should be {test_override_entity_name}, but is {re_search.group(1)}'
    )

    md_str = reg.to_md()
    re_search = re.search(r'# (\w+) Register Definitions', md_str)
    assert re_search is not None, 'Did not find Register Definition in documentation!'
    assert re_search.group(1) == test_override_entity_name, (
        f'Markdown title should be {test_override_entity_name}, but is {re_search.group(1)}'
    )


# ---------------------------------------------------------------------------
# Clock Domain Crossing (CDC)
# ---------------------------------------------------------------------------

CDC_CONFIG = [
    {
        'config': {
            'data_size': 32,
            'include_username': False,
            'include_hostname': False,
            'include_timestamp': False,
        }
    },
    {'name': 'RO_AXI', 'reg_type': 'ro', 'bits': 32},
    {'name': 'RW_AXI', 'reg_type': 'rw', 'use_upd_pulse': True, 'bits': 32},
    {
        'name': 'RW_OTHER',
        'clk': {'name': 'other', 'CDC': 'VEC2'},
        'reg_type': 'rw',
        'use_upd_pulse': True,
        'bits': 32,
    },
    {
        'name': 'RO_OTHER',
        'clk': {'name': 'other', 'CDC': 'VEC2'},
        'reg_type': 'ro',
        'bits': 8,
    },
    {
        'name': 'CUST_FAST',
        'clk': {'name': 'fast', 'CDC': 'VECP3'},
        'reg_type': 'custom',
        'bits': 16,
    },
    {
        'name': 'FLAG_OTHER',
        'clk': {'name': 'other', 'CDC': 'FF2'},
        'reg_type': 'rw',
        'use_upd_pulse': True,
        'bits': 1,
    },
]


def cdc_config():
    """Create a fresh copy of the CDC test configuration.

    RegDef mutates the configuration it is given, so each test needs its own
    copy.

    Returns:
        Copy of the CDC test configuration
    """
    return json.loads(json.dumps(CDC_CONFIG))


def test_cdc_resolution():
    """Test clock-domain resolution on the resolved register view.

    Tests:
        1. Verifies non-default domains are collected with clock/reset ports
        2. Verifies register names are qualified with the domain label
        3. Verifies write-side VEC is promoted to VECP
        4. Verifies read/write CDC modules and stage counts
        5. Verifies update pulses are enabled where required
    """
    reg = axi4lite_reg_generator.RegDef(cdc_config())
    regs = {r['name']: r for r in reg._regs}

    assert reg._has_cdc is True
    assert reg._entity_name == 'reg_file'
    assert reg._entity_name_cdc == 'reg_file_cdc'
    assert set(d['label'] for d in reg._domain_list) == {'OTHER', 'FAST'}
    assert {d['clk_port'] for d in reg._domain_list} == {'CLK_OTHER', 'CLK_FAST'}
    assert {d['rstn_port'] for d in reg._domain_list} == {'RSTN_OTHER', 'RSTN_FAST'}

    rw_other = regs['RW_OTHER']
    assert rw_other['domain'] == 'other'
    assert rw_other['domain_label'] == 'OTHER'
    assert rw_other['qualified_name'] == 'OTHER_RW_OTHER'
    assert rw_other['clk_port'] == 'CLK_OTHER'
    assert rw_other['rstn_port'] == 'RSTN_OTHER'
    # Write-side VEC is promoted to VECP
    assert rw_other['write_family'] == 'VECP'
    assert rw_other['write_module'] == 'cdc_vecp'
    assert rw_other['write_stages'] == 2
    assert rw_other['read_family'] is None
    assert rw_other['read_module'] is None
    # Pulse needed because of use_upd_pulse and because of VECP
    assert rw_other['needs_pulse'] is True

    ro_other = regs['RO_OTHER']
    assert ro_other['read_family'] == 'VEC'
    assert ro_other['read_module'] == 'cdc_vec'
    assert ro_other['read_stages'] == 2
    assert ro_other['write_family'] is None
    assert ro_other['needs_pulse'] is False

    cust_fast = regs['CUST_FAST']
    assert cust_fast['read_module'] == 'cdc_vecp'
    assert cust_fast['write_module'] == 'cdc_vecp'
    assert cust_fast['qualified_name'] == 'FAST_CUST_FAST'

    # 1-bit FF write uses the array synchronizer
    flag_other = regs['FLAG_OTHER']
    assert flag_other['write_family'] == 'FF'
    assert flag_other['write_module'] == 'cdc_ff'
    assert flag_other['write_stages'] == 2
    assert flag_other['needs_pulse'] is True

    rw_axi = regs['RW_AXI']
    assert rw_axi['domain'] is None
    assert rw_axi['write_module'] is None
    assert rw_axi['needs_pulse'] is True
    assert rw_axi['qualified_name'] == 'RW_AXI'

    ro_axi = regs['RO_AXI']
    assert ro_axi['domain'] is None
    assert ro_axi['qualified_name'] == 'RO_AXI'


def test_cdc_wrapper_generation():
    """Test CDC wrapper generation for all three languages.

    Tests:
        1. Verifies VHDL wrapper entity, ports, and primitives
        2. Verifies Verilog wrapper module, parameters, and connections
        3. Verifies SystemVerilog wrapper module and connections
        4. Verifies each wrapper contains a SHA-256 hash
    """
    reg = axi4lite_reg_generator.RegDef(cdc_config())
    vhdl = reg.to_vhdl_cdc()
    verilog = reg.to_verilog_cdc()
    sv = reg.to_systemverilog_cdc()

    assert vhdl is not None and verilog is not None and sv is not None

    assert 'entity reg_file_cdc is' in vhdl
    assert 'CLK_OTHER' in vhdl
    assert 'CLK_FAST' in vhdl
    # The CDC primitives are reset-free (matching XPM), so the wrapper no longer
    # has per-domain reset ports.
    assert 'RSTN_OTHER' not in vhdl
    assert 'RSTN_FAST' not in vhdl
    assert 'R_RW_AXI_O' in vhdl
    assert 'OTHER_RW_OTHER_O' in vhdl
    assert 'OTHER_RW_OTHER_O_upd' in vhdl
    assert 'OTHER_RO_OTHER_I' in vhdl
    assert 'FAST_CUST_FAST_I_upd' in vhdl
    assert 'entity work.reg_file' in vhdl
    assert 'entity work.cdc_vecp' in vhdl
    assert 'entity work.cdc_vec' in vhdl
    assert 'entity work.cdc_ff' in vhdl
    assert '-- SHA-256: ' in vhdl

    assert 'module reg_file_cdc' in verilog
    assert 'module reg_file base_i' not in verilog
    assert 'reg_file #(' in verilog
    assert '.ADDRESS_W(ADDRESS_W)' in verilog
    assert 'cdc_vecp #(' in verilog and 'cdc_vec #(' in verilog
    assert 'cdc_ff #(' in verilog
    # Write-side VECP drives its update pulse from the handshake dest_req.
    assert '.dest_req (OTHER_RW_OTHER_O_upd)' in verilog
    # Read-side VECP takes the external send pulse.
    assert '.src_send (FAST_CUST_FAST_I_upd)' in verilog
    # The source clock is the non-default domain clock, not regs_aclk.
    assert '.src_clk  (CLK_OTHER)' in verilog
    assert '// SHA-256: ' in verilog

    assert 'module reg_file_cdc' in sv
    assert 'logic' in sv
    assert '.dest_req (OTHER_RW_OTHER_O_upd)' in sv
    assert '// SHA-256: ' in sv


def test_no_cdc_no_wrapper():
    """Test that no wrapper is generated without a non-default clock domain.

    Tests:
        1. Verifies CDC is not detected in the default configuration
        2. Verifies VHDL, Verilog, and SystemVerilog wrappers return None
        3. Verifies no CDC primitives are reported as used
    """
    reg = axi4lite_reg_generator.RegDef.from_json_file(json_file_path)
    assert reg._has_cdc is False
    assert reg.to_verilog_cdc() is None
    assert reg.to_vhdl_cdc() is None
    assert reg.to_systemverilog_cdc() is None
    assert reg.cdc_modules_used() == set()


def test_cdc_modules_used():
    """Test the set of required CDC primitives.

    Tests:
        1. Verifies the FF array primitive is required
        2. Verifies both handshake primitives are required
    """
    reg = axi4lite_reg_generator.RegDef(cdc_config())
    assert reg.cdc_modules_used() == {'cdc_ff', 'cdc_vec', 'cdc_vecp'}


@pytest.mark.parametrize('cdc', ['FF1', 'VEC1', 'VECP1', 'FF0', 'BOGUS', 'VEC'])
def test_cdc_bad_type_rejected(cdc):
    """Test rejection of invalid CDC types.

    Tests:
        1. Attempts CDC types with too few stages
        2. Attempts malformed and unknown CDC types
        3. Verifies SchemaError is raised

    Raises:
        schema.SchemaError: When the CDC type is invalid
    """
    cfg = [
        {'config': {'data_size': 32}},
        {'name': 'X', 'clk': {'name': 'other', 'CDC': cdc}, 'bits': 32},
    ]
    with pytest.raises(schema.SchemaError):
        axi4lite_reg_generator.RegDef(cfg)


def test_cdc_axi_clock_collision():
    """Test rejection of a non-default clock reusing the AXI clock port name.

    Tests:
        1. Creates a register with a clock named REGS_ACLK
        2. Verifies ValueError is raised with the collision message

    Raises:
        ValueError: When a clock name collides with the AXI clock port
    """
    cfg = [
        {'config': {'data_size': 32}},
        {'name': 'X', 'clk': {'name': 'REGS_ACLK', 'CDC': 'VEC2'}, 'bits': 32},
    ]
    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(cfg)
    assert 'collides with the AXI clock port' in str(e_info.value)


def test_cdc_default_named_clock_rejected():
    """Test rejection of a clock object named 'default'.

    Tests:
        1. Creates a register with a clock object named 'default'
        2. Verifies ValueError is raised with the ambiguity message

    Raises:
        ValueError: When the AXI domain is selected with a clock object
    """
    cfg = [
        {'config': {'data_size': 32}},
        {'name': 'X', 'clk': {'name': 'default', 'CDC': 'VEC2'}, 'bits': 32},
    ]
    with pytest.raises(ValueError) as e_info:
        axi4lite_reg_generator.RegDef(cfg)
    assert 'AXI domain must be selected with the string' in str(e_info.value)


def test_cdc_md_domain_column():
    """Test clock-domain reporting in generated documentation.

    Tests:
        1. Verifies the register table has a clock column
        2. Verifies the non-default domain is listed
        3. Verifies the clock domain section is generated
    """
    reg = axi4lite_reg_generator.RegDef(cdc_config())
    md = reg.to_md()
    assert '| Address | Name | Type | Clock |' in md
    assert '| OTHER ' in md
    assert '**Clock Domain**: OTHER' in md


def test_cdc_json_roundtrip():
    """Test JSON serialization and deserialization of clock settings.

    Tests:
        1. Converts register configuration to JSON
        2. Creates new register definition from JSON
        3. Verifies configurations match
        4. Verifies generated Verilog and CDC wrappers match
    """
    reg = axi4lite_reg_generator.RegDef(cdc_config(), test_dir)
    cfg_new = json.loads(reg.get_reg_json())
    reg_new = axi4lite_reg_generator.RegDef(cfg_new, test_dir)

    assert reg._cfg == reg_new._cfg
    assert reg.to_verilog() == reg_new.to_verilog()
    assert reg.to_verilog_cdc() == reg_new.to_verilog_cdc()
