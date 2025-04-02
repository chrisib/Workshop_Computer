"""
Low-level hardware definitions & interface instances.

This module is responsible for the Python <--> hardware implementation; everything
else builds on top of this foundation.
"""

from machine import (
    ADC,
    Pin,
    PWM,
    freq
)
import time

# overclock the CPU to get more oomph out of it
# default frequency is 125MHz, so double it
OVERCLOCK_FREQUENCY = 250_000_000
freq(OVERCLOCK_FREQUENCY)

# our ADCs are 16-bit, so this defines our resolution
UINT16_MAX_VALUE = 65535

# Voltage limits

MAX_INPUT_VOLTAGE = 6.0
MIN_INPUT_VOLTAGE = -6.0

MAX_OUTPUT_VOLTAGE = 6.0
MIN_OUTPUT_VOLTAGE = -6.0

# GPIO pins
# See /documentation/Computer_Rev 1 documentation.pdf

# Pulse I/O
PIN_PULSE_IN_1 = 2
PIN_PULSE_IN_2 = 3
PIN_PULSE_OUT_1 = 8
PIN_PULSE_OUT_2 = 9

# PWM outputs
PIN_CV_OUT_1 = 23
PIN_CV_OUT_2 = 22

# Multiplexer
PIN_LOGIC_MUX_A = 24
PIN_LOGIC_MUX_B = 25
PIN_MUX_IO_1 = 28
PIN_MUX_CV_IN = 29

# Audio in
PIN_AUDIO_IN_L = 26
PIN_AUDIO_IN_R = 27

# LEDs
PIN_LED_1 = 10
PIN_LED_2 = 11
PIN_LED_3 = 12
PIN_LED_4 = 13
PIN_LED_5 = 14
PIN_LED_6 = 15

# EEPROM
PIN_EEPROM_SDA = 16
PIN_EEPROM_SCL = 17

# DAC
PIN_DAC_SCK = 18
PIN_DAC_CS = 21
PIN_DAC_SDI = 19

# Normalization probe
# Toggle to identify sockets with plugs in them
PIN_NORM_PROBE = 4

# 3-bits for board revisions
PIN_REV_1 = 5
PIN_REV_2 = 6
PIN_REV_3 = 7

# helper functions

def convert(n: int, base: int=2) -> str:
    """
    Convert a number from one base to another.

    :param n: The integer to convert
    :param base: The base we're converting to
    :return: The string representation of the number in the given base
    """
    string = "0123456789ABCDEF"
    if n < base:
        return string[n]
    else:
        return convert(n // base, base) + string[n % base]


def zfl(s: str|int, width: int=8) -> str:
    """
    Zero-fill a string.

    The string is padded with leading zeros, such that it is at least width characters long.

    :param s: The string to pad
    :param width: The desired length of the string
    :return: The provided string, padded with zeros
    """
    return "{:0>{w}}".format(s, w=width)


def clamp(
    x: int|float,
    low: int|float,
    high: int|float,
):
    """
    Clamp a value to lie between inclusive endpoints.

    :param x: The value to clamp
    :param low: The inclusive lower-bound
    :param high: The inclusive upper-bound
    :return: x clamped to the specified range
    """
    if x < low:
        return low
    elif x > high:
        return high
    return x


def rescale(
    x: int|float,
    old_min: int|float,
    old_max: int|float,
    new_min: int|float,
    new_max: int|float,
    clamp: bool=True,
) -> float:
    """
    Linearly rescale a value in one range to another.

    :param x: The value to rescale
    :param old_min: The initial inclusive lower-bound of x
    :param old_max: The initial incluisive upper-bound of x
    :param new_min: The new inclusive lower-bound
    :param new_max: The new inclusive upper-bound
    :param clamp: If true, x is clamped to [old_min, old_max] before rescaling is applied.
        Otherwise we extrapolate the value outside the specified range
    :return: The rescaled value y, in the range [new_min, new_max]
    """
    if clamp and x < old_min:
        return new_min
    elif clamp and x > old_max:
        return new_max
    else:
        return (x - old_min) * (new_max - new_min) / (old_max - old_min) + new_min


def all_leds(on: bool=False):
    """
    Set all LEDs either on or off.

    :param on: Should the LEDs be on or off?
    """
    # We _could_ use 0/1 for the parameter, but it feels bad to conflate
    # integers with boolean logic in Python
    if on:
        value = 1
    else:
        value = 0
    for led in leds:
        led.value(value)


def turn_off_all_outputs():
    """
    Turn off all outputs (analogue & digital)
    """
    for pulse in pulse_outs:
        pulse.off()

    for cv in cv_outs:
        cv.off()


def reset():
    """
    Turn EVERYTHING off, including the LEDs
    """
    all_leds(False)
    turn_off_all_outputs()

# Hardware classes

class BoardRevision:
    """Specifies the board revision"""

    def __init__(self):
        self.pin_a = Pin(PIN_REV_1)
        self.pin_b = Pin(PIN_REV_2)
        self.pin_c = Pin(PIN_REV_3)

    @property
    def version(self):
        """
        Get the board version.

        :return: A string indicating the board revision
        """
        revisions = {
            "000": "Proto1.2",
            "100": "2.0.1"
        }

        bitstr = f"{self.pin_a.value()}{self.pin_b.value()}{self.pin_c.value()}"
        return revisions.get(bitstr, "unknown")



class Multiplexer:
    """
    Interface class for reading the multiplexed inputs.

    The multiplexer has 2 channels and 2 control bits. The following table shows what the
    control bits should be to reach each of the 6 multiplexed values:

    | Logic A | Logic B | ADC Channel 2 (GPIO 28) | ADC Channel 3 (GPIO 29) |
    |---------|---------|-------------------------|-------------------------|
    | 0       | 0       | Main Knob               | CV 1                    |
    | 0       | 1       | X Knob                  | CV 2                    |
    | 1       | 0       | Y Knob                  | CV 1                    |
    | 1       | 1       | Z switch                | CV 2                    |

    Generally users should never have to interact directly with this class; instead users should
    use the following variables defined later in this file:
    - knob_main, knob_x, knob_y -- the 3 knobs
    - switch_z -- the 3-position switch
    - cv_in1, cv_in2 -- the two analogue input jacks

    see: https://pdf1.alldatasheet.com/datasheet-pdf/view/454218/UTC/4052.html
    see: https://github.com/TomWhitwell/Hello_Computer/blob/main/Demonstrations%2BHelloWorlds/CircuitPython/mtm_computer.py#L36
    """

    MUX_MAIN_KNOB = "main"
    MUX_X_KNOB = "x"
    MUX_Y_KNOB = "y"
    MUX_Z_SWITCH = "switch"
    MUX_CV1 = "cv1"
    MUX_CV2 = "cv2"

    SWITCH_UP = 1
    SWITCH_MIDDLE = 0
    SWITCH_DOWN = -1


    def __init__(self):
        self.mux_logic_a = Pin(PIN_LOGIC_MUX_A, Pin.OUT)
        self.mux_logic_b = Pin(PIN_LOGIC_MUX_B, Pin.OUT)
        self.mux_io_1 = ADC(PIN_MUX_IO_1)
        self.cv_in = ADC(PIN_MUX_CV_IN)
        self.table = {
            self.MUX_MAIN_KNOB: (0, 0),
            self.MUX_X_KNOB: (0, 1),
            self.MUX_Y_KNOB: (1, 0),
            self.MUX_Z_SWITCH: (1, 1),
            self.MUX_CV1: (0, 0),
            self.MUX_CV2: (0, 1),
        }

    def read(self, component: str=MUX_MAIN_KNOB) -> float:
        """
        Read the value from a knob/switch.

        :param component: The component to read; should be one of
            the MUX_* constants at the top of the class

        :return: The value as a 0.0 to 1.0 float
        """
        a, b = self.table[component]

        self.mux_logic_a.value(a)
        self.mux_logic_b.value(b)

        if component in (self.MUX_CV1, self.MUX_CV2):
            value = self.cv_in.read_u16()
        else:
            value = self.mux_io_1.read_u16()
        return value / UINT16_MAX_VALUE


class Input:
    """Generic superclass for all inputs."""

    def read(self) -> float|int|bool:
        raise NotImplementedError(".read() must be implemented by child classes")


class CvInput(Input):
    """Generic superclass for all CV inputs"""

    def voltage(self) -> float:
        """
        Read the current value of the input and return it as a raw voltage.

        :return: The raw input voltage, in the range [MIN_INPUT_VOLTAGE, MAX_INPUT_VOLTAGE]
        """
        return rescale(self.read(), -1, 1, MIN_INPUT_VOLTAGE, MAX_INPUT_VOLTAGE)



class SwitchInput(Input):
    """
    Wrapper class for reading the 3-position switch.

    This reads the data from the multiplexer.
    """

    POSITION_DOWN = -1
    POSITION_MIDDLE = 0
    POSITION_UP = 1

    def read(self) -> int:
        """
        Read the switch position and return it.

        :return: POSITION_UP, POSITION_MIDDLE, or POSITION_DOWN, depending on the switch's
            physical position
        """
        value = computer_mux.read(computer_mux.MUX_Z_SWITCH)
        if value > 50:
            return self.POSITION_UP
        elif value < 10:
            return self.POSITION_DOWN
        else:
            return self.POSITION_MIDDLE


class MuxInput(Input):
    """
    Wrapper class for reading the CV inputs from the multiplexer.

    :param mux_key: The key we need to pass to the multiplexer to read the value
    """

    def __init__(self, mux_key: str):
        self.key = mux_key

    def read(self) -> float:
        """
        Read the input's current value.

        :return: A value in the range 0.0 to 1.0
        """
        return computer_mux.read(self.key)


class KnobInput(MuxInput):
    """
    Wrapper class for reading the 3 knobs.

    This reads the data from the multiplexer

    :param mux_key: The key we need to pass to the multiplexer to read the value
    """

    def __init__(self, mux_key: str):
        super().__init__(mux_key)

    def choice(self, arr: list):
        """
        Use the knob to choose an item from a list

        :param arr: The list of items we're choosing from
        """
        x = int(self.read() * len(arr))
        if x == len(arr):
            # .read() can return 1.0, so handle that case
            return arr[-1]
        else:
            return arr[x]


class MuxCvInput(MuxInput, CvInput):
    """
    Wrapper class for the multiplexed CV inputs.

    :param mux_key: The key we need to pass to the multiplexer to read the value
    """

    def __init__(self, mux_key):
        super().__init__(mux_key)

    def read(self) -> float:
        """
        Read the current value of the input and return it as a value in the range [-1, 1].

        :return: A value in the range -1 to +1 indicating the CV level
        """
        return super().read() * 2.0 - 1.0


class CvInput(CvInput):
    """
    Wrapper class for reading the analogue & audio inputs

    This reads the data directly from an adc pin

    :param pin: The pin we read from
    """

    def __init__(self, pin: int, samples: int=32):
        self.pin = Pin(pin, Pin.IN)
        self.adc = ADC(self.pin)
        self.samples = samples

    def _sample_adc(self, samples: int=None):
        value = 0
        for _ in range(samples or self.samples):
            value += self.adc.read_u16()
        return round(value / (samples or self.samples))

    def read(self) -> float:
        """
        Read the current value of the input and return it as a value in the range [-1, 1].

        :return: A value in the range -1 to +1 indicating the CV level
        """
        adc = self._sample_adc(self.samples)
        return rescale(adc, 0, UINT16_MAX_VALUE, MIN_INPUT_VOLTAGE, MAX_INPUT_VOLTAGE)


class PulseInput(Input):
    """
    Wrapper for the pulse (digital) inputs.

    These can be read normally, or can have interrupt handlers associated with their
    rising & falling edges to trigger immediate responses.

    :param pin: The GPIO pin the input reads from
    :param debounce_delay: The number of milliseconds we use for debouncing the input
    """

    def __init__(self, pin: int, debounce_delay: int=10):
        self.pin = Pin(pin, Pin.IN)
        self.debounce_delay = debounce_delay

        # Default handlers are noop callables.
        self._rising_handler = lambda: None
        self._falling_handler = lambda: None

        # Both high handler
        self._both_handler = lambda: None
        self._other = None

        # IRQ event timestamps
        self.last_rising_ms = 0
        self.last_falling_ms = 0

    def _bounce_wrapper(self, pin):
        """IRQ handler wrapper for falling and rising edge callback functions."""
        if self.value() == 1:
            if time.ticks_diff(time.ticks_ms(), self.last_rising_ms) < self.debounce_delay:
                return
            self.last_rising_ms = time.ticks_ms()
            return self._rising_handler()
        else:
            if time.ticks_diff(time.ticks_ms(), self.last_falling_ms) < self.debounce_delay:
                return
            self.last_falling_ms = time.ticks_ms()

            # Check if 'other' pin is set and if 'other' pins is high and if this pin has been high for long enough.
            if (
                self._other
                and self._other.value()
                and time.ticks_diff(self.last_falling_ms, self.last_rising_ms) > 500
            ):
                return self._both_handler()
            return self._falling_handler()

    def handler(self, func):
        """Define the callback function to call when rising edge detected."""
        if not callable(func):
            raise ValueError("Provided handler func is not callable")
        self._rising_handler = func
        self.pin.irq(handler=self._bounce_wrapper)

    def handler_falling(self, func):
        """Define the callback function to call when falling edge detected."""
        if not callable(func):
            raise ValueError("Provided handler func is not callable")
        self._falling_handler = func
        self.pin.irq(handler=self._bounce_wrapper)

    def reset_handler(self):
        self.pin.irq(handler=None)

    def _handler_both(self, other, func):
        """When this and other are high, execute the both func."""
        if not callable(func):
            raise ValueError("Provided handler func is not callable")
        self._other = other
        self._both_handler = func
        self.pin.irq(handler=self._bounce_wrapper)

    def read(self) -> bool:
        """
        Read this pin's current value and return it

        :return: True if this pin is high, otherwise False
        """
        if self.pin.value():
            return True
        else:
            return False


class Output:
    """
    Generic superclass for pulse & analogue outputs.

    :param pin: The GPIO pin the output is connected to
    """

    def __init__(self, pin: int):
        self.pin = Pin(pin, Pin.OUT)  #: the low-level Pin instance

    def write(self, _):
        raise NotImplemented(".write(x) must be implemented by subclasses")


class PulseOutput(Output):
    """
    Wrapper for the pulse (digital) outputs.

    These are binary outputs: either on or off. There's no voltage control.

    :param pin: The GPIO pin the output is connected to
    """

    def __init__(self, pin):
        super().__init__(pin)

    def on(self):
        """Turn the output on."""
        self.pin.value(1)

    def off(self):
        """Turn the output off."""
        self.pin.value(0)

    def write(self, value: bool):
        """
        Write the value for this output.

        :param value: The on/off state for this output
        """
        if value:
            self.pin.value(1)
        else:
            self.pin.value(0)

    def toggle(self):
        """
        Toggle this output's state.

        If we're off, turn on. If we're on, turn off.
        """
        if self.pin.value():
            self.pin.value(0)
        else:
            self.pin.value(1)


class LedOutput(PulseOutput):
    """
    Wrapper for LED outputs.

    These are fundamentally the same as the pulse outputs, but we use a different class
    just to make the distinction obvious to the programmer that these won't generate any
    voltage.

    :param pin: The GPIO pin the output is connected to
    """

    def __init__(self, pin: int):
        super().__init__(pin)


class AnalogueOutput(Output):
    """
    Wrapper for the analogue outputs.

    :param pin: The GPIO pin the output is connected to
    """

    def __init__(self, pin):
        PWM_FREQ = 60000
        DUTY_U16 = 32768

        super().__init__(pin)
        self.pwm = PWM(
            self.pin,
            freq=PWM_FREQ,
            duty_u16=DUTY_U16,
        )
        self._duty = DUTY_U16

    def write(self, value: float):
        """
        Set the value for this output.

        :param value: The desired level for this output, -1.0 to +1.0.
            -1 will output the minumum-possible voltage (-6V), +1 will output
            the maximum-possible voltage (+6V), 0 will output 0V.
        """
        self._duty = rescale(value, -1, 1, 0, UINT16_MAX_VALUE)
        self.pwm.duty_u16(self._duty)

    def voltage(self, volts: float=None) -> float:
        """
        Get/set the raw voltage for this output.

        :param volts: The raw voltage to send from the output. If None the current
            voltage is returned.
        """
        if volts is None:
            return rescale(self._duty, 0, UINT16_MAX_VALUE, MIN_OUTPUT_VOLTAGE, MAX_OUTPUT_VOLTAGE)
        else:
            value = rescale(volts, MIN_OUTPUT_VOLTAGE, MAX_OUTPUT_VOLTAGE, -1, 1)
            self.write(value)
            return volts

    def off(self):
        """Turn this output off."""
        self.write(0)

    def on(self):
        """Turn this output on to its highest level."""
        self.write(1)

# Hardware initialization

board_revision = BoardRevision()  #: Reader for the board revision

# Initialize multiplexed inputs
computer_mux = Multiplexer()
knob_main = KnobInput(computer_mux.MUX_MAIN_KNOB)  #: Main knob input
knob_x = KnobInput(computer_mux.MUX_X_KNOB)  #: X knob input
knob_y = KnobInput(computer_mux.MUX_Y_KNOB)  #: Y knob input
knobs = (
    knob_main,
    knob_x,
    knob_y,
)  #: Tuple of all knobs for convenience/iteration
switch_z = SwitchInput()  #: the 3-position Z switch
cv_in1 = MuxCvInput(computer_mux.MUX_CV1)  #: CV input 1
cv_in2 = MuxCvInput(computer_mux.MUX_CV2)  #: CV input 2
cv_audio_in_l = CvInput(PIN_AUDIO_IN_L)  #: CV/Audio L input
cv_audio_in_r = CvInput(PIN_AUDIO_IN_R)  #: CV/Audio R input
cv_ins = (
    cv_in1,
    cv_in2,
    cv_audio_in_l,
    cv_audio_in_r,
)  #: Tuple of all CV inputs for convenience/iteration
cv_audio_in = (
    cv_audio_in_l,
    cv_audio_in_r,
)  #: Tuple of all CV/audio inputs for convenience/iteration

# Initialize pulse/digital inputs
pulse_in1 = PulseInput(PIN_PULSE_IN_1)  #: Pulse/digital input 1
pulse_in2 = PulseInput(PIN_PULSE_IN_2)  #: Pulse/digital input 2
pulse_ins = (
    pulse_in1,
    pulse_in2,
)  #: Tuple of all pulse inputs for convenience/iteration

# Analogue outputs
cv_out1 = AnalogueOutput(PIN_CV_OUT_1)  #: CV output 1
cv_out2 = AnalogueOutput(PIN_CV_OUT_2)  #: CV output 2
#cv_audio_out_l = AnalogueOutput()  #: CV/Audio output L
#cv_audio_out_r = AnalogueOutput()  #: CV/Audio output R
cv_outs = (
    cv_out1,
    cv_out2,
#    cv_audio_out_l,
#    cv_audio_out_r,
)  #: Tuple of all CV outputs for convenience/iteration
#cv_audio_out = (
#    cv_audio_out_l,
#    cv_audio_out_r,
#)  #: Tuple of all cv/audio outputs for convenience/iteration

# Pulse outputs
pulse_out1 = PulseOutput(PIN_PULSE_OUT_1)  #: Pulse/digital output 1
pulse_out2 = PulseOutput(PIN_PULSE_OUT_2)  #: Pulse/digital output 2
pulse_outs = (
    pulse_out1,
    pulse_out2,
)  #: Tuple of all pulse outputs for convenience/iteration

# Initialize LEDs
led1 = LedOutput(PIN_LED_1)  #: LED 1 (top-left)
led2 = LedOutput(PIN_LED_2)  #: LED 2 (top-right)
led3 = LedOutput(PIN_LED_3)  #: LED 3 (center-left)
led4 = LedOutput(PIN_LED_4)  #: LED 4 (center-right)
led5 = LedOutput(PIN_LED_5)  #: LED 5 (bottom-left)
led6 = LedOutput(PIN_LED_6)  #: LED 6 (bottom-right)
leds = (
    led1,
    led2,
    led3,
    led4,
    led5,
    led6,
)  #: Tuple of all LEDs for convenience/iteration

# Ensure everything is off when this module gets imported
reset()
