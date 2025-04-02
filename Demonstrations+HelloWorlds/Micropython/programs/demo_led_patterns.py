from computer.hardware import *
from computer.lights import *
import time

times = 4

# cycle through all of the stock LED patterns
while True:
    led_spinner(times)
    led_snake(times)
    led_arrows(times)
    led_ladder_up(times)
    led_ladder_down(times)
    led_ping_pong(times)

    for i in range(64):
        led_number(i)
        time.sleep(DEFAULT_PAUSE)
