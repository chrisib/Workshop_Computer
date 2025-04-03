"""
A two-channel quantizer for Workshop

Each channel uses the following inputs & outputs:
- pulse_in_N -- trigger input for the sample
- cv_in_N -- the signal to be quantized
- cv_out_N -- the quantized signal

Controls:
- main knob: select the scale to quantize (LEDs show the scale as a binary integer)
- x knob: channel a transpose
- y knob: channel b transpose


Scales in order:
    0- Chromatic
    1- Nat Major
    2- Har Major
    3- Maj 135
    4- Maj 1356
    5- Maj 1357
    6- Nat Minor
    7- Har Minor
    8- Min 135
    9- Min 1356
    10- Min 1357
    11- Maj Blues
    12- Min Blues
    13- Whole
    14- Penta
    15- Dom7
"""

from computer.hardware import *
from computer.lights import led_number
from computer.quantizer import *

scales = [
    CommonScales.Chromatic,
    CommonScales.NatMajor,
    CommonScales.HarMajor,
    CommonScales.Major135,
    CommonScales.Major1356,
    CommonScales.Major1357,

    CommonScales.NatMinor,
    CommonScales.HarMinor,
    CommonScales.Minor135,
    CommonScales.Minor1356,
    CommonScales.Minor1357,

    CommonScales.MajorBlues,
    CommonScales.MinorBlues,

    CommonScales.WholeTone,
    CommonScales.Pentatonic,
    CommonScales.Dominant7,
]

class WorkshopQuantizer:
    """
    A two-channel quantizer executable for the Workshop computer
    """

    def __init__(self):
        self.channel_a_dirty = False
        self.channel_b_dirty = False

        self.current_scale_index = 0

        @pulse_in1.handler
        def on_channel_a():
            self.channel_a_dirty = True

        @pulse_in2.handler
        def on_channel_b():
            self.channel_b_dirty = True

    def main(self):
        while True:
            # read the current scale & offsets
            scale_index = knob_main.read() * len(scales)
            if scale_index == len(scales):
                scale_index -= 1

            if scale_index != self.current_scale_index:
                self.current_scale_index = scale_index
                led_number(self.current_scale_index)

                # if we change scales, re-quantize immediately
                self.channel_a_dirty = True
                self.channel_b_dirty = True

            if self.channel_a_dirty:
                self.channel_a_dirty = False
                channel_a_in = cv_in1.voltage()
                channel_a_transpose = int(knob_x.read() * SEMITONES_PER_OCTAVE)

                (volts, _) = scales[self.current_scale_index].quantize(channel_a_in, channel_a_transpose)
                cv_out1.voltage(volts)

            if self.channel_b_dirty:
                self.channel_b_dirty = False
                channel_b_in = cv_in2.voltage()
                channel_b_transpose = int(knob_y.read() * SEMITONES_PER_OCTAVE)

                (volts, _) = scales[self.current_scale_index].quantize(channel_b_in, channel_b_transpose)
                cv_out2.voltage(volts)


if __name__ == "__main__":
    WorkshopQuantizer().main()
