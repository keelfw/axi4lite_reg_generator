import os
import shutil
import subprocess

import pytest

from cocotb_tools.runner import get_runner, Verilog, VHDL

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
VERIFICATION_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_dut():
    subprocess.run(
        [
            'uv',
            'run',
            'python',
            '-m',
            'axi4lite_reg_generator',
            os.path.join(REPO_ROOT, 'example', 'inputs', 'example.json'),
            '--output',
            os.path.join(VERIFICATION_DIR, 'example'),
        ],
        check=True,
        cwd=REPO_ROOT,
    )


HAS_VERILATOR = shutil.which('verilator') is not None
HAS_GHDL = shutil.which('ghdl') is not None


@pytest.fixture(scope='session')
def example_outputs():
    generate_dut()


@pytest.mark.parametrize('language', ['sv', 'v'])
@pytest.mark.parametrize('register_inputs', [0, 1])
def test_verilator(language, register_inputs, example_outputs):
    if not HAS_VERILATOR:
        pytest.skip('verilator not found')
    hdl_src = os.path.join(VERIFICATION_DIR, f'example.{language}')
    build_dir = f'sim_build/verilator_{language}_ri{register_inputs}'

    sim = get_runner('verilator')
    sim.build(
        sources=[Verilog(hdl_src)],
        hdl_toplevel='example',
        parameters={'REGISTER_INPUTS': register_inputs},
        build_dir=build_dir,
        always=True,
        timescale=('1ns', '1ns'),
    )
    sim.test(
        test_module='tb_reg',
        hdl_toplevel='example',
        build_dir=build_dir,
    )


@pytest.mark.parametrize('register_inputs', [0, 1])
def test_ghdl(register_inputs, example_outputs):
    if not HAS_GHDL:
        pytest.skip('ghdl not found')
    hdl_src = os.path.join(VERIFICATION_DIR, 'example.vhd')
    build_dir = f'sim_build/ghdl_vhd_ri{register_inputs}'

    sim = get_runner('ghdl')
    sim.build(
        sources=[VHDL(hdl_src)],
        hdl_toplevel='example',
        parameters={'REGISTER_INPUTS': 'true' if register_inputs else 'false'},
        build_dir=build_dir,
        always=True,
    )
    sim.test(
        test_module='tb_reg',
        hdl_toplevel='example',
        build_dir=build_dir,
    )
