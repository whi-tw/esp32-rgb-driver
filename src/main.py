# Complete project details at https://RandomNerdTutorials.com
import ulogging as logging
import re
import gc
import json
import machine

import uasyncio as asyncio

from lib import wifimgr
from lib import picoweb

from rgbled import rgbled
from touchy import TouchAction

wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")


event_sinks = set()
eventlist = []


def add_to_eventlist(event, e_type=""):
    global eventlist
    if event_sinks:
        eventlist.append((event, e_type))


led = rgbled(26, 25, 33, add_to_eventlist)  # phy 7, 8, 9

loop = asyncio.get_event_loop()


def on_off_switch(pin):
    if any(c > 0 for c in led.colors()):
        led.changeto(0, 0, 0, 0)
    else:
        led.changeto(255, 255, 255, 0)


def toggle_rainbow():
    if led.looping:
        led.looping = False
    else:
        loop.create_task(led.do_rainbow())


machine.Pin(0, machine.Pin.IN).irq(
    trigger=machine.Pin.IRQ_RISING, handler=on_off_switch)  # set up internal interrupt for pin 0 to toggle white


toggle_colorloop = TouchAction(15, 500, action=toggle_rainbow, toggle=False)


app = picoweb.WebApp(__name__)


@ app.route('/')
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.render_template(resp, "page.html")
    gc.collect()


@ app.route("/api/colors")
def colors(req: picoweb.HTTPRequest, resp):
    if req.method == "POST":
        yield from req.read_form_data()
        led.changeto(int(req.form["red"]), int(req.form["green"]),
                     int(req.form["blue"]), int(req.form["time"]))

    yield from picoweb.jsonify(resp, {
        "red": led.RED.state(),
        "green": led.GREEN.state(),
        "blue": led.BLUE.state()
    })
    gc.collect()


@ app.route("/api/state")
def state(req: picoweb.HTTPRequest, resp):
    yield from picoweb.jsonify(resp, {
        "red": led.RED.state(),
        "green": led.GREEN.state(),
        "blue": led.BLUE.state(),
        "rainbow": led.looping
    })
    gc.collect()


@ app.route('/api/rainbow')
def rainbow_control(req: picoweb.HTTPRequest, resp):
    status = "bad"
    if req.method == "POST":
        loop.create_task(led.do_rainbow())
        status = "ok"
    yield from picoweb.jsonify(resp, {"status": status})

    gc.collect()


@ app.route('/events')
def events(req, resp):
    global event_sinks
    print("Event source %r connected" % resp)
    yield from resp.awrite("HTTP/1.0 200 OK\r\n")
    yield from resp.awrite("Content-Type: text/event-stream\r\n")
    yield from resp.awrite("\r\n")
    event_sinks.add(resp)
    return False


def push_event(ev, e_type=""):
    global event_sinks
    to_del = set()
    for resp in event_sinks:
        try:
            await resp.awrite("{}data: {}\n\n".format(
                ("event: {}\n".format(e_type) if e_type else ""),
                json.dumps(ev))
            )
        except OSError as e:
            print("Event source %r disconnected (%r)" % (resp, e))
            await resp.aclose()
            # Can't remove item from set while iterating, have to have
            # second pass for that (not very efficient).
            to_del.add(resp)

    for resp in to_del:
        event_sinks.remove(resp)


def push_events():
    global eventlist
    while True:
        for event in eventlist:
            await push_event(event[0], event[1])
            eventlist.remove(event)
        await asyncio.sleep_ms(10)


loop.create_task(push_events())

logging.basicConfig(level=logging.INFO)
app.run(host='0.0.0.0', port=80, debug=True)
