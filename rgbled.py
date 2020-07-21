import random
import time
import machine
import math
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
        self.GREEN = machine.PWM(machine.Pin(self.gpin), freq=self.freq)
        self.BLUE = machine.PWM(machine.Pin(self.bpin), freq=self.freq)
        self.frequency = freq
        self.redprev = 1
        self.greenprev = 1
        self.blueprev = 1

        self.PWMMAX = 1023

    async def killer(self, time):
        await asyncio.sleep(time)

    def changeto(self, redv, greenv, bluev, speed):
        r = self.rgb_to_duty(redv)
        g = self.rgb_to_duty(greenv)
        b = self.rgb_to_duty(bluev)
        if(r == self.redprev or r == 0):
            rx = self.redprev + 1
        else:
            rx = abs(r-self.redprev)
        if(g == self.greenprev or g == 0):
            gx = self.greenprev + 1
        else:
            gx = abs(g-self.greenprev)
        if(b == self.blueprev or b == 0):
            bx = self.blueprev + 1
        else:
            bx = abs(b-self.blueprev)
        rs = speed/rx
        gs = speed/gx
        bs = speed/bx
        loop = asyncio.get_event_loop()
        loop.create_task(self.changered(r, rs))
        loop.create_task(self.changegreen(g, gs))
        loop.create_task(self.changeblue(b, bs))
        loop.run_until_complete(self.killer(speed))

    async def changered(self, red, speed):
        if(red > self.redprev):
            for x in range(self.redprev, red):
                self.RED.duty(x)
                time.sleep(speed)
        else:
            down = self.redprev - red
            for x in range(0, down):
                self.RED.duty(self.redprev - x)
                time.sleep(speed)
        self.redprev = red

    async def changegreen(self, green, speed):
        if(green > self.greenprev):
            for x in range(self.greenprev, green):
                self.GREEN.duty(x)
                time.sleep(speed)
        else:
            down = self.greenprev - green
            for x in range(0, down):
                self.GREEN.duty(self.greenprev - x)
                time.sleep(speed)
        self.greenprev = green

    async def changeblue(self, blue, speed):
        if(blue > self.blueprev):
            for x in range(self.blueprev, blue):
                self.BLUE.duty(x)
                time.sleep(speed)
        else:
            down = self.blueprev - blue
            for x in range(0, down):
                self.BLUE.duty(self.blueprev - x)
                time.sleep(speed)
        self.blueprev = blue

    def on(self, r, g, b, speed):
        self.setup(self.rpin, self.gpin, self.bpin, self.freq)
        time.sleep(0.001)
        self.changeto(r, g, b, speed)

    def off(self, speed):
        self.changeto(1, 1, 1, speed)
        time.sleep(speed)

    def rgb_to_duty(self, val):
        new = int(abs((val * self.PWMMAX/255) - 1023))
        print(val, new)
        return new
