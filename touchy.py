import uasyncio as asyncio
import machine
import esp32


class TouchAction():

    def __init__(self, pin: int, threshold: int, on_action=None, off_action=None, toggle_state_on_func=None, action=None, toggle=True):
        self.pin = pin
        self.THRESHOLD = threshold
        self.on_action = on_action
        self.off_action = off_action
        self.toggle_state_on_func = toggle_state_on_func
        self.action = action
        self.toggle = toggle
        self.loop = asyncio.get_event_loop()

        self.TOUCH = machine.TouchPad(machine.Pin(self.pin))

        self.listen_for_touch()

    async def do_toggle(self):
        if self.toggle_state_on_func():
            self.off_action[0](*self.off_action[1])
        else:
            self.on_action[0](*self.on_action[1])

    async def _listen_for_touch(self):
        while True:
            try:
                if self.TOUCH.read() <= self.THRESHOLD:
                    while self.TOUCH.read() <= self.THRESHOLD:
                        await asyncio.sleep(0.1)
                    await asyncio.sleep(0.1)
                    if self.toggle:
                        self.loop.create_task(self.do_toggle())
                await asyncio.sleep(0.1)
            except ValueError:
                pass

    def listen_for_touch(self):
        self.loop.create_task(self._listen_for_touch())


# class Touchy():

#     def __init__(self, toggle: int, cycle: int, threshold=500):
#         self.toggle_pin = toggle
#         self.cycle_pin = cycle
#         self.THRESHOLD = threshold

#         self.touchpads = []

#         self.setup()

#     def setup(self):
#         self.TOGGLE = machine.TouchPad(machine.Pin(self.toggle_pin))
#         self.CYCLE = machine.TouchPad(machine.Pin(self.cycle_pin))

#         self.TOGGLE.config(self.THRESHOLD)
#         self.CYCLE.config(self.THRESHOLD)

#         # Actions
#         self.off_action = (None, None)
#         self.on_action = (None, None)
#         self.off_check = (None, None)
