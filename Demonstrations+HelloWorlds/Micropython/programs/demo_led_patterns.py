# Copyright 2025 Music Thing Modular
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
