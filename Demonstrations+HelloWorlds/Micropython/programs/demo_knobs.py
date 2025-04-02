from computer.hardware import *
from computer.lights import *


def led_vu(leds, value):
    """
    Use a series of LEDs as a vertical VU meter

    :param leds: The list of LEDs to use, from top to bottom
    :param value: The value to represent in the range [0, 1]
    """
    for led in leds:
        led.off()
    if value >= 0.33:
        leds[-1].on()
    if value >= 0.5:
        leds[1].on()
    if value >= 0.66:
        leds[0].on()


def main():
    while True:
        lvl1 = knob_x.read()
        lvl2 = knob_y.read()

        cv_out1.write(lvl1 * 2 - 1)  # convert to -1 to + 1
        cv_out2.write(lvl2 * 2 - 1)  # convert to -1 to + 1

        # use the left & right LED columns as low-resolution VU meters
        led_vu((led1, led3, led5), lvl1)
        led_vu((led2, led4, led6), lvl2)


if __name__ == "__main__":
    main()
