"""
Copy the pulse & cv inputs to their corresponding outputs
"""
from computer.hardware import *
from computer.lights import DEFAULT_PAUSE

# define rising & falling edge handlers for the pulse inputs
# each one sets an LED on/off and sets the pulse output high or low

@pulse_out1.handler
def pulse1_rise():
    led1.on()
    pulse_out1.on()


@pulse_out1.handler_falling
def pulse1_fall():
    led1.off()
    pulse_out1.off()


@pulse_out2.handler
def pulse2_rise():
    led2.on()
    pulse_out2.on()


@pulse_out2.handler_falling
def pulse2_fall():
    led2.off()
    pulse_out2.off()


def main():
    last_toggle_at = time.ticks_ms()

    while True:
        # copy the analogue inputs to their equivalent outputs
        cv_out1.write(cv_in1.read())
        cv_out2.write(cv_in2.read())

        # blink LED6 as a heartbeat indicator
        now = time.ticks_ms()
        if time.ticks_diff(now, last_toggle_at) >= DEFAULT_PAUSE:
            last_toggle_at = now
            led6.toggle()


if __name__ == "__main__":
    main()
