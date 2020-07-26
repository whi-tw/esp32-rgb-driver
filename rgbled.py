import machine
import uasyncio as asyncio

import time as time_mod

from lib import colorlib


class CHANNEL:
    def __init__(self, color: int, pin: int, frequency: int, duty_converter):
        self.FREQUENCY = frequency
        self.COLOR = color
        self.PIN = pin
        self._state = 0
        self.duty_converter = duty_converter
        self.setup()

    def setup(self):
        self.PWM = machine.PWM(machine.Pin(self.PIN),
                               freq=self.FREQUENCY, duty=0)

    def state(self, new_state=None) -> int:
        if new_state is not None:
            self.PWM.duty(self.duty_converter(new_state))
            self._state = new_state
        return self._state


class rgbled:
    RED = 0
    GREEN = 1
    BLUE = 2

    def __init__(self, rpin, gpin, bpin):
        self.rpin = rpin
        self.gpin = gpin
        self.bpin = bpin
        self.FREQUENCY = 1000
        self.PWMMAX = 1023
        self.setup(self.rpin, self.gpin, self.bpin, self.FREQUENCY)

    def setup(self, rpin, gpin, bpin, frequency):
        duty_converter = colorlib.brightness_to_pwm_duty(self.PWMMAX)

        self.RED = CHANNEL(rgbled.RED, rpin, frequency, duty_converter)
        self.GREEN = CHANNEL(rgbled.GREEN, gpin, frequency, duty_converter)
        self.BLUE = CHANNEL(rgbled.BLUE, bpin, frequency, duty_converter)

        self.loop = asyncio.get_event_loop()

        self.current_action = (None, None, None)
        self.looping = False

    def colors(self) -> (int, int, int):
        return (self.RED.state(), self.GREEN.state(), self.BLUE.state())

    async def do_rainbow(self):
        self.looping = True
        h, _, _ = colorlib.rgb_to_hsl(*self.colors())
        while self.looping:
            self.changeto_hsl(h, 1, 0.5, loop_cmd=True)
            await asyncio.sleep_ms(100)
            h = (h + 1 if h < 360 else 1)
        self.looping = False

    def changeto_hsl(self, h: float, s: float, l: float, time=0, loop_cmd=False):
        r, g, b = colorlib.hsl_to_rgb(h, s, l)
        self.changeto(r, g, b, time, loop_cmd=loop_cmd)

    def changeto(self, r: int, g: int, b: int, time=0, loop_cmd=False):
        self.looping = loop_cmd
        for action in self.current_action:
            try:
                asyncio.cancel(action)
            except AttributeError as e:
                if "pend_throw" in e.args[0]:
                    continue
                else:
                    raise

        self.current_action = (
            self.transition(r, time, self.RED),
            self.transition(g, time, self.GREEN),
            self.transition(b, time, self.BLUE)
        )
        for action in self.current_action:
            self.loop.create_task(action)

    async def transition(self, value: int, time: int, led: CHANNEL):
        old = led.state()
        target = value
        steps = abs(target - old)
        if steps == 0:
            return
        step_time = time / steps
        if time == 0:
            led.state(value)
            return
        if(target > old):
            # Going up!
            for x in range(old, target+1):
                led.state(x)
                await asyncio.sleep(step_time)
        else:
            # going down
            for x in range(old, target-1, -1):
                led.state(x)
                await asyncio.sleep(step_time)
