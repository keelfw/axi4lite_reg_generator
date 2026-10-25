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


def generate_cdc_dut():
    out_dir = os.path.join(VERIFICATION_DIR, 'cdc_dut')
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(
        [
            'uv',
            'run',
            'python',
            '-m',
            'axi4lite_reg_generator',
            os.path.join(REPO_ROOT, 'example', 'inputs', 'example_cdc.json'),
            '--output',
            os.path.join(out_dir, 'cdc_example'),
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
        log_file=os.path.join(build_dir, 'sim.log'),
        verbose=True,
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
        log_file=os.path.join(build_dir, 'sim.log'),
        verbose=True,
    )


@pytest.mark.parametrize('language', ['sv', 'v'])
def test_verilator_cdc(language):
    """Test the CDC wrapper with Verilator.

    Tests:
        1. Generates the CDC example register file and wrapper
        2. Builds the wrapper with the required CDC primitives
        3. Runs the CDC testbench
    """
    if not HAS_VERILATOR:
        pytest.skip('verilator not found')
    generate_cdc_dut()
    d = os.path.join(VERIFICATION_DIR, 'cdc_dut')
    sources = [
        Verilog(os.path.join(d, f'cdc_example.{language}')),
        Verilog(os.path.join(d, f'cdc_example_cdc.{language}')),
    ] + [
        Verilog(os.path.join(d, f'{m}.{language}'))
        for m in ('cdc_ff', 'cdc_vec', 'cdc_vecp')
    ]
    build_dir = f'sim_build/cdc_verilator_{language}'

    sim = get_runner('verilator')
    sim.build(
        sources=sources,
        hdl_toplevel='cdc_example_cdc',
        parameters={'REGISTER_INPUTS': 0},
        build_dir=build_dir,
        always=True,
        timescale=('1ns', '1ns'),
    )
    sim.test(
        test_module='tb_cdc',
        hdl_toplevel='cdc_example_cdc',
        build_dir=build_dir,
        log_file=os.path.join(build_dir, 'sim.log'),
        verbose=True,
    )


def test_ghdl_cdc():
    """Test CDC wrapper compilation and elaboration with GHDL.

    Tests:
        1. Generates the CDC example register file and wrapper
        2. Analyzes all VHDL sources with GHDL
        3. Elaborates the CDC wrapper
    """
    if not HAS_GHDL:
        pytest.skip('ghdl not found')
    generate_cdc_dut()
    d = os.path.join(VERIFICATION_DIR, 'cdc_dut')
    vhd = [
        'cdc_ff.vhd',
        'cdc_vec.vhd',
        'cdc_vecp.vhd',
        'cdc_example.vhd',
        'cdc_example_cdc.vhd',
    ]

    r = subprocess.run(['ghdl', '-a', '--std=08', *vhd], cwd=d)
    assert r.returncode == 0
    r = subprocess.run(['ghdl', '-e', '--std=08', 'cdc_example_cdc'], cwd=d)
    assert r.returncode == 0

    # Remove the work library artifacts created by GHDL
    for f in os.listdir(d):
        if f.endswith('.cf') or f.endswith('.o'):
            os.remove(os.path.join(d, f))
