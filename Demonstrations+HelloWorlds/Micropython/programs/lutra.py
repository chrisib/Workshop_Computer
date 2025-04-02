"""
Workshop Computer re-implementation of EuroPi's Lutra.

Lutra is a re-imagining of Expert Sleepers' Otterley; multiple free-running LFOs
with speed & spread control.

Outputs:
- CV1: primary LFO
- CV2: secondary LFO
- CV/Audio L: tertiary LFO
- CV/Audio R: quaternary LFO

Inputs:
- Pulse1: reset/sync input (rising edge)
- Pulse2: hold-low input (sets all outputs to 0 when high, resets on rising edge)
- CV1: speed CV
- CV2: spread CV

Controls:
- Main knob: base speed
- X knob: spread control (anticlockwise: less spread, clockwise: more spread)
- Y knob: wave shape
- Z switch: center: bipolar -6 to +6 V output, up: unipolar 0 to +6 V, down: unipolar -6 to 0 V

Wave shape is one of:
- sine
- triangle
- ramp (rising)
- ramp (falling)
- square (50% duty cycle)
- stepped random

LEDs 1-6 show the active wave shape in the order specified above
"""
from computer.hardware import *
import math
from random import random


class WaveGenerator:
    """
    Generates the output wave forms and sets the voltage going to one of the output jacks

    The generated wave is bipolar, oscillating between -1 and + 1; this should be multiplied and/or
    offset as appropriate to generate the final output voltages.

    Several wave shapes are supported, with the cycle time expressed in "ticks." These ticks have no
    1:1 relationship with any real-world time unit, and are simply defined by each iteration through
    the script's main loop.
    """

    ## Supported wave shapes
    WAVE_SHAPE_SINE = 0
    WAVE_SHAPE_TRIANGLE = 1
    WAVE_SHAPE_SAW = 2
    WAVE_SHAPE_RAMP = 3
    WAVE_SHAPE_SQUARE = 4
    WAVE_SHAPE_STEP_RANDOM = 5
    NUM_WAVE_SHAPES = 6

    def __init__(self):
        self.shape = self.WAVE_SHAPE_SINE

        self.cycle_ticks = 1000

        self.current_tick = 0
        self.random_goal = random() * 2 - 1
        self.output_level = 0.0  #: the output level of the wave; updated every tick

    def reset(self):
        """Reset the wave to the beginning"""
        self.current_tick = 0
        self.random_goal = random() * 2 - 1
        self.output_level = 0.0

    def change_cycle_length(self, new_length):
        """
        Change the number of steps in the pattern

        We need to preserve our relative progress to avoid skipping when changing the cycle length
        """
        if new_length != self.cycle_ticks:
            progress = self.current_tick / self.cycle_ticks
            self.cycle_ticks = new_length
            self.current_tick = int(new_length * progress)

    def tick(self):
        """
        Calculate the appropriate voltage for the output, given the current clock time

        :return: The desired output level in the range -1 to +1
        """
        if self.shape == self.WAVE_SHAPE_SINE:
            # we want to start at -1 and go up, so we actually use a negative cos wave, but the shape is the same
            theta = (self.current_tick / self.cycle_ticks) * 2 * math.pi
            self.output_level = -math.cos(theta)
        elif self.shape == self.WAVE_SHAPE_SQUARE:
            if self.current_tick < (self.cycle_ticks >> 1):
                self.output_level = 1
            else:
                self.output_level = -1
        elif self.shape == self.WAVE_SHAPE_TRIANGLE:
            half_cycle_ticks = (self.cycle_ticks >> 1)
            if self.current_tick < half_cycle_ticks:
                self.output_level = self.current_tick / half_cycle_ticks * 2 - 1
            else:
                self.output_level = 1.0 - ((self.current_tick - half_cycle_ticks) / half_cycle_ticks * 2)
        elif self.shape == self.WAVE_SHAPE_SAW:
            self.output_level = 1.0 - self.current_tick / self.cycle_ticks * 2
        elif self.shape == self.WAVE_SHAPE_RAMP:
            self.output_level = -1.0 + self.current_tick / self.cycle_ticks * 2
        elif self.shape == self.WAVE_SHAPE_STEP_RANDOM:
            self.output_level = self.random_goal
        else:
            self.output_level = 0  # this should never happen, but just in case...

        self.current_tick = self.current_tick + 1
        if self.current_tick >= self.cycle_ticks:
            self.current_tick = 0
            self.random_goal = random() * 2 - 1

        return self.output_level


class Lutra:
    """The main class for this program"""

    # The maximum and minimum cycle time for the LFOs
    MIN_CYCLE_TICKS = 250
    MAX_CYCLE_TICKS = 10000

    # Maximum wave speed multipliers relative to cv1
    MAX_SPEED_MULTIPLIERS = [
        1/1,
        4/3,
        3/2,
        2/1,
    ]

    def __init__(self):
        self.waves = []
        for _ in cv_outs:
            self.waves.append(WaveGenerator())

        self.hold_low = False

        @pulse_in1.handler
        def on_reset_in():
            self.reset_all_waves()

        @pulse_in2.handler
        def on_hold_low_rise():
            self.hold_low = True

        @pulse_in2.handler_falling
        def on_hold_low_fall():
            self.reset_all_waves()
            self.hold_low = False

    def reset_all_waves(self):
        for w in self.waves:
            w.reset()

    def main(self):
        while True:
            # determine our wave shape
            wave_shape = int(knob_y.read() * WaveGenerator.NUM_WAVE_SHAPES)
            if wave_shape == WaveGenerator.NUM_WAVE_SHAPES:
                wave_shape -= 1  # make sure we're in the valid range, since .read() can return 1.0!
            for w in self.waves:
                w.shape = wave_shape
                all_leds(False)
                leds[wave_shape].on()

            # calculate the speed & spread of our waves
            speed = clamp(knob_main.read() + cv_in1.read(), 0, 1)
            spread = clamp(knob_x.read() + cv_in2.read(), 0, 1)
            base_ticks = int((1.0 - speed) * (self.MAX_CYCLE_TICKS - self.MIN_CYCLE_TICKS) + self.MIN_CYCLE_TICKS)
            for i in range(len(self.waves)):
                base_tick_multiplier = rescale(spread, 0, 1, 1, self.MAX_SPEED_MULTIPLIERS[i])
                spread_ticks = int(base_ticks / base_tick_multiplier)
                self.waves[i].change_cycle_length(spread_ticks)

            # determine the offset & multiplier to get the output waves in the right range
            range_switch = switch_z.read()
            if range_switch == switch_z.POSITION_MIDDLE:
                range_offset = 0.0
                range_multiplier = 1.0
            elif range_switch == switch_z.POSITION_UP:
                range_offset = 1.0
                range_multiplier = 0.5
            else:
                range_offset = -1.0
                range_multiplier = 0.5

            # advance the waves
            for i in range(len(self.waves)):
                if self.hold_low:
                    cv_outs[i].off()
                else:
                    output_level = (self.waves[i].tick() + range_offset) * range_multiplier
                    cv_outs[i].write(output_level)


if __name__ == "__main__":
    Lutra().main()
