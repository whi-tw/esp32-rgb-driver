import time

import machine
import uasyncio as asyncio


class rgbled:
    def __init__(self, rpin, gpin, bpin):
        self.rpin = rpin
        self.gpin = gpin
        self.bpin = bpin
        self.freq = 1000
        self.setup(self.rpin, self.gpin, self.bpin, self.freq)

    def setup(self, rpin, gpin, bpin, freq):
        self.RED = machine.PWM(machine.Pin(self.rpin), freq=self.freq)
        self.RED.deinit()
        self.GREEN = machine.PWM(machine.Pin(self.gpin), freq=self.freq)
        self.GREEN.deinit()
        self.BLUE = machine.PWM(machine.Pin(self.bpin), freq=self.freq)
        self.BLUE.deinit()
        self.frequency = freq

        self.PWMMAX = 1023

    async def killer(self, time):
        await asyncio.sleep(time)

    def changeto(self, r, g, b, t):
        loop = asyncio.get_event_loop()
        loop.create_task(self.transition(r, t, self.RED))
        loop.create_task(self.transition(g, t, self.GREEN))
        loop.create_task(self.transition(b, t, self.BLUE))
        loop.run_until_complete(self.killer(t))

    async def transition(self, value: int, t: int, led: machine.PWM):
        current_duty = led.duty()
        target_duty = self.rgb_to_duty(value)
        try:
            steps = abs(current_duty - target_duty)
            step_time = t / steps
        except ZeroDivisionError:
            steps = 0
            step_time = 0
        print(current_duty, target_duty, steps, step_time)
        if(target_duty > current_duty):
            for x in range(current_duty, target_duty+1):
                print(x)
                led.duty(x)
                asyncio.sleep(step_time)
        else:
            down = current_duty - target_duty
            for x in range(0, down):
                led.duty(current_duty - x)
                asyncio.sleep(step_time)

    def on(self, r, g, b, speed):
        self.setup(self.rpin, self.gpin, self.bpin, self.freq)
        time.sleep(0.001)
        self.changeto(r, g, b, speed)

    def off(self, speed):
        self.changeto(1, 1, 1, speed)
        time.sleep(speed)

    def rgb_to_duty(self, val):
        new = int(abs((val * self.PWMMAX/255) - 1023))
        # print(val, new)
        return new
