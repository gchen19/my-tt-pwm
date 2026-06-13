/*
 * tt_um_tapewright_pwm — a small 8-bit PWM peripheral on the Tiny Tapeout
 * tile interface (spec §6 first target). Fully digital, deterministic, sized
 * for a single TT tile.
 *
 *   ui_in  : 8-bit duty-cycle setpoint (0..255)
 *   uo_out : {counter[7:1], pwm_out} — PWM on bit 0, counter high bits for scope
 *   uio_*  : unused (driven to 0, all inputs)
 *
 * PWM output is high while a free-running counter is below the duty setpoint,
 * so the high-time fraction over each 256-cycle period equals ui_in/256.
 */
`default_nettype none

module tt_um_tapewright_pwm (
    input  wire [7:0] ui_in,    // dedicated inputs: duty setpoint
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // bidirectional: input path (unused)
    output wire [7:0] uio_out,  // bidirectional: output path (unused)
    output wire [7:0] uio_oe,   // bidirectional: output-enable (all inputs)
    input  wire       ena,      // design selected (unused)
    input  wire       clk,      // clock
    input  wire       rst_n     // active-low reset
);

    reg [7:0] counter;

    always @(posedge clk) begin
        if (!rst_n)
            counter <= 8'd0;
        else
            counter <= counter + 8'd1;
    end

    wire pwm_out = (counter < ui_in);

    assign uo_out  = {counter[7:1], pwm_out};
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Tie off unused inputs so they are not flagged as unconnected.
    wire _unused = &{ena, uio_in, 1'b0};

endmodule

`default_nettype wire
