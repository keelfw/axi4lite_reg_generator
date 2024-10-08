import sys

sys.path.append('../axi4lite_reg_generator')

import os
import axi4lite_reg_generator
import subprocess
import cocotb_test.simulator
import uuid

test_dir = os.path.dirname(__file__)


def test_check_ghdl_installed():
    try:
        assert (
            subprocess.run(['ghdl', 'help']).returncode == 0
        ), 'GHDL executable not found in path'
    except FileNotFoundError:
        assert False, 'GHDL not found in path'


def test_basic_definition():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    print(reg.to_vhdl())


def test_default_values():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    assert reg._cfg[0]['reg_type'] == 'ro'
    assert reg._cfg[2]['bits'][1]['default_value'] == 0


def test_numeric_conversion():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    assert reg._cfg[2]['bits'][0]['default_value'] == 255


def test_address_values():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )

    for i in range(2):
        assert reg._cfg[i]['addr_offset'] == 4 * i
    assert reg._cfg[2]['addr_offset'] == 64


def test_generate_vhd():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, '_test.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())


def test_basic_vhd():
    reg = axi4lite_reg_generator.RegDef.from_json_file(
        os.path.join(test_dir, 'test_json.json')
    )
    test_file = os.path.join(test_dir, f'_test_{uuid.uuid4().hex}.vhd')
    with open(test_file, 'w') as f:
        f.write(reg.to_vhdl())
    x = subprocess.run(['ghdl', '-a', test_file], capture_output=True, text=True)
    assert x.returncode == 0, (
        f'VHDL did not successfully compile in GHDL. See file: {test_file}\nError:\n'
        + x.stderr
    )

    os.remove(test_file)


def test_rtlsim():
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
