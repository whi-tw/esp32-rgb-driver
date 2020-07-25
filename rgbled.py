import machine
import uasyncio as asyncio


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

        self.current_action = (None, None, None)

    def colors(self) -> (int, int, int):
        return (self.RED.state(), self.GREEN.state(), self.BLUE.state())

    def changeto(self, r: int, g: int, b: int, time=0):
        for action in self.current_action:
            try:
                asyncio.cancel(action)
                print("cancelled")
            except AttributeError as e:
                if "pend_throw" in e.args[0]:
                    continue
                else:
                    raise

        loop = asyncio.get_event_loop()
        self.current_action = (
            self.transition(r, time, self.RED),
            self.transition(g, time, self.GREEN),
            self.transition(b, time, self.BLUE)
        )
        print(self.current_action)
        for action in self.current_action:
            loop.create_task(action)

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
