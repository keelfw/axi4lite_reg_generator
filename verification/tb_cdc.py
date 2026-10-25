"""Functional testbench for the generated CDC wrapper (``<entity>_cdc``).

Drives the AXI4-Lite register file while a second, unrelated clock toggles the
non-default clock domain, and checks that register values make it across the
clock domain crossing in both directions.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer, with_timeout
from cocotb.utils import get_sim_time
from cocotb_bus.drivers.amba import AXI4LiteMaster

CLK_PERIOD_NS = 10
OTHER_PERIOD_NS = 18

TIMEOUT = (20 * CLK_PERIOD_NS, 'ns')

# Addresses from example/inputs/example_cdc.json
ADDR_VERSION = 0
ADDR_SCRATCH = 4
ADDR_CONTROL = 8
ADDR_STATUS = 12
ADDR_FLAG = 16
ADDR_EVENT = 20


def start_clocks(dut):
    cocotb.start_soon(Clock(dut.regs_aclk, CLK_PERIOD_NS, unit='ns').start())
    cocotb.start_soon(Clock(dut.CLK_OTHER, OTHER_PERIOD_NS, unit='ns').start())


async def reset_dut(dut):
    dut.regs_aresetn.value = 0
    await Timer(5 * CLK_PERIOD_NS, unit='ns')
    dut.regs_aresetn.value = 1
    await Timer(5 * CLK_PERIOD_NS, unit='ns')


class PulseCounter:
    """Count rising edges on a 1-bit signal, bounded by a timeout.

    The counting task finishes by itself once the target count is reached (or
    the timeout elapses), so it is never cancelled: cancelling a task that is
    awaiting a trigger trips a cocotb teardown bug.
    """

    def __init__(self, signal):
        self.signal = signal
        self.count = 0
        self._target = 0
        self._task = None

    async def _run(self, timeout_ns):
        while self.count < self._target:
            await with_timeout(RisingEdge(self.signal), timeout_ns, 'ns')
            self.count += 1

    def start(self, target, timeout_ns=20000):
        self._target = target
        self._task = cocotb.start_soon(self._run(timeout_ns))

    async def wait(self):
        await self._task


@cocotb.test()
async def cdc_write_and_read(dut):
    axim = AXI4LiteMaster(dut, 'regs', dut.regs_aclk)
    start_clocks(dut)

    scratch_upd = PulseCounter(dut.R_Scratch_O_upd)
    control_upd = PulseCounter(dut.OTHER_Control_O_upd)
    scratch_upd.start(target=1)
    control_upd.start(target=2)

    await reset_dut(dut)
    dut._log.info('Reset complete')

    # Read-only register in the AXI domain
    dut.R_Version_I.value = 0xFEEDBACE
    await ClockCycles(dut.regs_aclk, 3)
    assert await with_timeout(axim.read(ADDR_VERSION), *TIMEOUT) == 0xFEEDBACE

    # rw register in the AXI domain with an update pulse
    await with_timeout(axim.write(ADDR_SCRATCH, 0x1234567A), *TIMEOUT)
    await ClockCycles(dut.regs_aclk, 3)
    assert int(dut.R_Scratch_O.value) == 0x1234567A

    # Write-side VECP into the OTHER domain
    await with_timeout(axim.write(ADDR_CONTROL, 0xDEADBEEF), *TIMEOUT)
    await Timer(500, unit='ns')
    assert int(dut.OTHER_Control_O.value) == 0xDEADBEEF

    # 1-bit FF write into the OTHER domain
    await with_timeout(axim.write(ADDR_FLAG, 1), *TIMEOUT)
    await Timer(300, unit='ns')
    assert int(dut.OTHER_Flag_O.value) == 1

    # Read-side VEC from the OTHER domain (quasi-static value)
    dut.OTHER_Status_I.value = 0x1A2B
    await Timer(300, unit='ns')
    assert await with_timeout(axim.read(ADDR_STATUS), *TIMEOUT) == 0x1A2B

    # Read-side VECP from the OTHER domain: drive data + a single pulse
    dut.OTHER_Event_I.value = 0x5A
    await RisingEdge(dut.CLK_OTHER)
    dut.OTHER_Event_I_upd.value = 1
    await RisingEdge(dut.CLK_OTHER)
    dut.OTHER_Event_I_upd.value = 0
    await Timer(500, unit='ns')

    deadline = get_sim_time('ns') + 5000
    while True:
        val = await with_timeout(axim.read(ADDR_EVENT), *TIMEOUT)
        if val == 0x5A:
            break
        assert get_sim_time('ns') < deadline, f'Event never captured: {val:#x}'

    # A later write to the same VECP register must land as well
    await with_timeout(axim.write(ADDR_CONTROL, 0x1234), *TIMEOUT)
    await Timer(500, unit='ns')
    assert int(dut.OTHER_Control_O.value) == 0x1234

    # Both update pulses must have been seen (Scratch: 1 write, Control: 2 writes)
    await scratch_upd.wait()
    await control_upd.wait()
    assert scratch_upd.count == 1
    assert control_upd.count == 2

    # Finish on a clock-edge (ReadWrite phase) trigger rather than a bare
    # time-based Timer: ending a Verilator run on a pending Timer callback
    # trips a cocotb/Verilator $finish teardown use-after-free (segfault).
    await ClockCycles(dut.regs_aclk, 2)

    dut._log.info('CDC test complete')
