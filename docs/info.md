# tt_um_tapewright_pwm

## How it works

An 8-bit PWM peripheral. A free-running 8-bit counter increments every clock; the
output `pwm_out` is high while `counter < ui_in`, so the duty cycle over each
256-cycle period equals `ui_in / 256`. The upper counter bits are exposed for
observation.

## How to test

Drive `ui_in` with a duty value (0–255). `uo_out[0]` is the PWM waveform; its
high-time fraction equals `ui_in/256`. `uo_out[7:1]` mirror `counter[7:1]`.
A cocotb testbench (`test/test_pwm.py`) checks the duty for several setpoints.

## External hardware

None required. Scope `uo_out[0]` to see the PWM, or low-pass filter it to an
analog level proportional to `ui_in`.

## Pinout

| Bus | Bit | Function |
|---|---|---|
| ui_in | [7:0] | duty-cycle setpoint |
| uo_out | 0 | pwm_out |
| uo_out | [7:1] | counter[7:1] |
| uio | — | unused |
