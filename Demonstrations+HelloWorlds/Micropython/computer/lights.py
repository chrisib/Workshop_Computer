"""
Additional utilities for interacting with the LEDs.

This module contains additional functions that can be used by programs to simplify making
animated LED patterns.
"""

from .hardware import *
from random import choice as random_choice
import time

DEFAULT_PAUSE = 300

def all_leds_off():
    all_leds(False)


def timed_led_toggle(indices: int|list[int]):
    """
    Turn a set of LEDs on and then off.

    This function will block until the operation completes.

    :param indices: The indices of which LEDs we want to toggle
    """
    # leds can be either an integer or a list of integers
    if type(indices) == type(0):
        indices = (indices,)

    for i in indices:
        leds[i].on()

    time.sleep_ms(DEFAULT_PAUSE)

    for i in indices:
        leds[i].off()


def led_pattern(sequence, times=1):
    """
    Play an LED pattern.

    This function will block until the operation completes.

    :param sequence: An array of LED indices we want to turn on during each step
    :param times: The number of times the whole sequence should play
    """
    for _ in range(times):
        for s in sequence:
            timed_led_toggle(s)
    all_leds_off()


def led_spinner(times=1):
    """
    Show a simple spinning pattern.

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([0, 1, 3, 5, 4, 2], times)


def led_ping_pong(times=1):
    """
    Show a simple sideways ping-pong pattern.

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([(0, 4, 2), (1, 3, 5)], times)


def led_blink(index, times=1):
    """
    Blink a single LED

    This function will block until the operation completes.

    :param index: The index of the LED to blink
    :param times: The number of times the whole sequence should play
    """
    for _ in range(times):
        timed_led_toggle(index)
        time.sleep_ms(DEFAULT_PAUSE)
    all_leds_off()


def led_arrows(times=1):
    """
    Show left/right arrows with the LEDs.

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([(0, 3, 4), (1, 2, 5)], times)


def led_ladder_up(times=1):
    """
    Show ascending rows of LEDs.

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([(4, 5), (2, 3), (0, 1)], times)


def led_ladder_down(times=1):
    """
    Show descending rows of LEDs.

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([(0, 1), (2, 3), (4, 5)], times)


def led_snake(times=1):
    """
    Show a growing snake pattern

    This function will block until the operation completes.

    :param times: The number of times the whole sequence should play
    """
    led_pattern([
        (0),
        (0, 1),
        (0, 1, 3),
        (0, 1, 3, 2),
        (0, 1, 3, 2, 4),
        (0, 1, 3, 2, 4, 5)
    ], times)



def led_number(num: int):
    """
    Represent a 6-bit binary number with the LEDs.

    Since we only have 6 bits to work with, we can only meaningfully represent numbers
    from 0 to 63.

    :param num: The integer to display
    """
    n_bits = len(leds)
    for bit in range(n_bits):
        # reverse the order of bits so the most significant bit is the first LED
        if (num >> (n_bits - bit - 1)) & 0x01:
            leds[bit].on()
        else:
            leds[bit].off()
