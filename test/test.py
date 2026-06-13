# SPDX-FileCopyrightText: © 2026 The TapeWright Authors
# SPDX-License-Identifier: Apache-2.0
#
# Gate-level-capable cocotb test for tt_um_tapewright_pwm.
#
# Over any window of exactly 256 cycles the PWM output is high exactly `duty`
# times (it is high while a free-running 8-bit counter is below the setpoint),
# so the check is exact and phase-independent. The test attaches to the `tb`
# wrapper, so it passes for both RTL (`make`) and gate-level (`make GATES=yes`,
# which tt-gds-action's gl_test job runs against the hardened netlist on Icarus).

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # 10 ns clock (100 MHz). The functional check is phase-independent, so the
    # exact period is arbitrary here.
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    dut._log.info("Test PWM duty cycle")
    for duty in (0, 1, 64, 128, 200, 255):
        dut.ui_in.value = duty
        await RisingEdge(dut.clk)  # let the new setpoint take effect
        high = 0
        for _ in range(256):
            await RisingEdge(dut.clk)
            high += int(dut.uo_out.value) & 1  # uo_out[0] = pwm_out
        assert high == duty, f"duty={duty}: expected {duty} high cycles, got {high}"
        dut._log.info(f"duty={duty}: {high} high cycles over 256 — OK")
