import machine
import uasyncio as asyncio

import time as time_mod


def hue_to_rgb(p, q, t):
    if t < 0:
        t += 1
    elif t > 1:
        t -= 1

    if (t * 6) < 1:
        return p + (q - p) * 6 * t
    if (t * 2) < 1:
        return q
    if (t * 3) < 2:
        return p + (q - p) * (2/3 - t) * 6
    return p


def hsl_to_rgb(h, s, l):
    r = g = b = 0

    if s == 0:
        r = g = b = l
    else:
        if l < 0.5:
            q = l * (1 + s)  # temporary_1
        else:
            q = (l + s) - (l * s)  # temporary_1

        p = (2 * l) - q  # temporary_2

        h /= 360

        r = hue_to_rgb(p, q, h + (1/3))
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - (1/3))

    return round(r*255), round(g*255), round(b*255)


class CHANNEL:
    def __init__(self, color: int, pin: int, frequency: int, duty_map: {int: int}):
        self.FREQUENCY = frequency
        self.COLOR = color
        self.PIN = pin
        self._state = 0
        self.DUTY_MAP = duty_map
        self.setup()

    def setup(self):
        self.PWM = machine.PWM(machine.Pin(self.PIN),
                               freq=self.FREQUENCY, duty=0)

    def state(self, new_state=None) -> int:
        if new_state is not None:
            self.PWM.duty(self.DUTY_MAP[new_state])
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
        duty_map = {}
        for i in range(0, 256):
            duty_map[i] = self.rgb_to_duty(i)

        self.RED = CHANNEL(rgbled.RED, rpin, frequency, duty_map)
        self.GREEN = CHANNEL(rgbled.GREEN, gpin, frequency, duty_map)
        self.BLUE = CHANNEL(rgbled.BLUE, bpin, frequency, duty_map)

        self.loop = asyncio.get_event_loop()

        self.current_action = (None, None, None)
        self.looping = False

    def colors(self) -> (int, int, int):
        return (self.RED.state(), self.GREEN.state(), self.BLUE.state())

    async def do_loop(self):
        self.looping = True
        while self.looping:
            for i in range(0, 360):
                if not self.looping:
                    break
                self.changeto_hsl(i, 1, 0.5, loop_cmd=True)
                await asyncio.sleep_ms(100)
        self.looping = False

    def changeto_hsl(self, h: float, s: float, l: float, time=0, loop_cmd=False):
        r, g, b = hsl_to_rgb(h, s, l)
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

    def rgb_to_duty(self, val) -> int:
        new = int(abs((val * self.PWMMAX/255)))
        return new
