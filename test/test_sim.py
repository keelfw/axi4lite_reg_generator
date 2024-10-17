import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, ClockCycles, with_timeout
from cocotb_bus.drivers.amba import AXI4LiteMaster, AXIProtocolError, AXIxRESP

CLK_PERIOD_NS = 10

MODULE_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'hdl')
MODULE_PATH = os.path.abspath(MODULE_PATH)

TIMEOUT = (10 * CLK_PERIOD_NS, 'ns')


def setup_dut(dut):
    cocotb.start_soon(Clock(dut.REGS_ACLK, CLK_PERIOD_NS, units='ns').start())


async def reset(rst, time, units, active_high=False):
    if active_high:
        rst.value = 1
    else:
        rst.value = 0

    await Timer(time, units)

    if active_high:
        rst.value = 0
    else:
        rst.value = 1


@cocotb.test()
async def basic_readwrite(dut):
    """Write to the register at address 0, verify the value has changed.

    Test ID: 0

    Expected Results:
        The value read directly from the register is the same as the
        value written.
    """

    # Reset
    axim = AXI4LiteMaster(dut, 'REGS', dut.REGS_ACLK)
    setup_dut(dut)
    dut.R_Test_Register_I.setimmediatevalue(0xFEEDBACE)
    dut.R_Register_with_Fields_I.setimmediatevalue(int(2**12 - 1))
    cocotb.start_soon(reset(dut.REGS_ARESETN, 5 * CLK_PERIOD_NS, units='ns'))
    await Timer(3 * CLK_PERIOD_NS, units='ns')
    dut._log.info('Checking Reset State')
    assert dut.REGS_AWREADY.value == 0
    assert dut.REGS_WREADY.value == 0
    assert dut.REGS_BVALID.value == 0
    assert dut.REGS_ARREADY.value == 0
    assert dut.REGS_RVALID.value == 0
    assert dut.REGS_ARESETN.value == 0

    await RisingEdge(dut.REGS_ARESETN)
    dut._log.info('Reset Deasserted')
    await ClockCycles(dut.REGS_ACLK, 5)

    # Read Defaults
    dut._log.info('Checking default values')
    assert await with_timeout(axim.read(0x0000), *TIMEOUT) == 0xFEEDBACE
    assert await with_timeout(axim.read(0x0004), *TIMEOUT) == 0x0
    assert await with_timeout(axim.read(64), *TIMEOUT) == 2**12 - 1

    # Write Values
    dut._log.info('Writing new values')
    await with_timeout(axim.write(4, 0x1234567A), *TIMEOUT)
    await with_timeout(axim.write(64, 0xCCAABB11), *TIMEOUT)

    await ClockCycles(dut.REGS_ACLK, 5)

    assert dut.R_Scratch_Register_O.value == 0x1234567A
    assert dut.R_Register_with_Fields_O.value == 0x00000B11

    # Read new values back
    dut._log.info('Reading new values back')
    assert await with_timeout(axim.read(0x0000), *TIMEOUT) == 0xFEEDBACE
    assert await with_timeout(axim.read(0x0004), *TIMEOUT) == 0x1234567A
    assert await with_timeout(axim.read(64), *TIMEOUT) == 2**12 - 1

    dut._log.info('Test complete')


@cocotb.test()
async def read_invalid(dut):
    """Write to the register at address 0, verify the value has changed.

    Test ID: 0

    Expected Results:
        The value read directly from the register is the same as the
        value written.
    """

    # Reset
    axim = AXI4LiteMaster(dut, 'REGS', dut.REGS_ACLK)
    setup_dut(dut)
    dut._log.info('DUT Setup Complete')

    await reset(dut.REGS_ARESETN, 5 * CLK_PERIOD_NS, units='ns')

    await RisingEdge(dut.REGS_ARESETN)
    await ClockCycles(dut.REGS_ACLK, 5)

    try:
        await with_timeout(axim.read(0x0008), *TIMEOUT)
    except AXIProtocolError as e:
        assert e.xresp == AXIxRESP.SLVERR
    else:
        assert False


@cocotb.test()
async def write_invalid(dut):
    """Write to the register at address 0, verify the value has changed.

    Test ID: 0

    Expected Results:
        The value read directly from the register is the same as the
        value written.
    """

    # Reset
    axim = AXI4LiteMaster(dut, 'REGS', dut.REGS_ACLK)
    setup_dut(dut)
    dut._log.info('DUT Setup Complete')

    await reset(dut.REGS_ARESETN, 5 * CLK_PERIOD_NS, units='ns')

    await RisingEdge(dut.REGS_ARESETN)
    await ClockCycles(dut.REGS_ACLK, 5)

    try:
        await with_timeout(axim.write(0x0008, 0), *TIMEOUT)
    except AXIProtocolError as e:
        assert e.xresp == AXIxRESP.SLVERR
    else:
        assert False


@cocotb.test()
async def write_enables(dut):
    """Write to the register at address 0, verify the value has changed.

    Test ID: 0

    Expected Results:
        The value read directly from the register is the same as the
        value written.
    """

    def calc_value(byte_enable):
        val = 0
        if byte_enable & 1:
            val |= 0x000000FF
        if byte_enable & 2:
            val |= 0x0000FF00
        if byte_enable & 4:
            val |= 0x00FF0000
        if byte_enable & 8:
            val |= 0xFF000000
        return val

    # Reset
    axim = AXI4LiteMaster(dut, 'REGS', dut.REGS_ACLK)
    setup_dut(dut)
    dut._log.info('DUT Setup Complete')

    await reset(dut.REGS_ARESETN, 5 * CLK_PERIOD_NS, units='ns')

    await RisingEdge(dut.REGS_ARESETN)
    await ClockCycles(dut.REGS_ACLK, 5)

    for byte_enable in range(16):
        await with_timeout(axim.write(0x0004, 0), *TIMEOUT)
        assert await with_timeout(axim.read(0x0004), *TIMEOUT) == 0

        await with_timeout(axim.write(0x0004, 2**32 - 1, byte_enable), *TIMEOUT)
        assert await with_timeout(axim.read(0x0004), *TIMEOUT) == calc_value(
            byte_enable
        )

@cocotb.test()
async def upd_pulse(dut):
    """Verify update pulses are set when registers are updated.

    Expected Results:
        All _upd signals are '1' when registers are updated, else '0'
    """

    # Reset
    axim = AXI4LiteMaster(dut, 'REGS', dut.REGS_ACLK)
    setup_dut(dut)
    dut.R_Test_Register_I.setimmediatevalue(0xFEEDBACE)
    dut.R_Register_with_Fields_I.setimmediatevalue(int(2**12 - 1))
    cocotb.start_soon(reset(dut.REGS_ARESETN, 5 * CLK_PERIOD_NS, units='ns'))
    await Timer(3 * CLK_PERIOD_NS, units='ns')
    dut._log.info('Checking Reset State')
    assert dut.R_Scratch_Register_O_upd == 0
    assert dut.R_Register_with_Fields_O_upd == 0

    await RisingEdge(dut.REGS_ARESETN)
    dut._log.info('Reset Deasserted')
    await ClockCycles(dut.REGS_ACLK, 5)

    # Read Defaults
    dut._log.info('Checking default values')
    assert dut.R_Scratch_Register_O_upd == 0
    assert dut.R_Register_with_Fields_O_upd == 0

    # Write first register
    dut._log.info('Writing first register')

    write_co = cocotb.start_soon(with_timeout(axim.write(4,0), *TIMEOUT))
    await RisingEdge(dut.REGS_ACLK)
    while not (dut.REGS_WVALID == 1 and dut.REGS_WREADY == 1):
        assert dut.R_Scratch_Register_O_upd == 0
        assert dut.R_Register_with_Fields_O_upd == 0
        await RisingEdge(dut.REGS_ACLK)
    
    assert dut.R_Scratch_Register_O_upd == 0
    assert dut.R_Register_with_Fields_O_upd == 0
    await RisingEdge(dut.REGS_ACLK)

    assert dut.R_Scratch_Register_O_upd == 1
    assert dut.R_Register_with_Fields_O_upd == 0
    await RisingEdge(dut.REGS_ACLK)

    await write_co

    # Write second register
    dut._log.info('Writing second register')
    write_co = cocotb.start_soon(with_timeout(axim.write(64,0), *TIMEOUT))
    await RisingEdge(dut.REGS_ACLK)
    while not (dut.REGS_WVALID == 1 and dut.REGS_WREADY == 1):
        assert dut.R_Scratch_Register_O_upd == 0
        assert dut.R_Register_with_Fields_O_upd == 0
        await RisingEdge(dut.REGS_ACLK)
    
    assert dut.R_Scratch_Register_O_upd == 0
    assert dut.R_Register_with_Fields_O_upd == 0
    await RisingEdge(dut.REGS_ACLK)

    assert dut.R_Scratch_Register_O_upd == 0
    assert dut.R_Register_with_Fields_O_upd == 1
    await RisingEdge(dut.REGS_ACLK)

    await write_co

    dut._log.info('Test complete')