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

eventlist = []


def add_to_eventlist(source: str, event):
    global eventlist
    eventlist.append({"source": source, "event": event})


led = rgbled(26, 25, 33, add_to_eventlist)  # phy 7, 8, 9


def are_lights_on() -> bool:
    return any(c > 0 for c in led.colors())


on_off = TouchAction(15, 500, toggle=True, on_action=(led.changeto, (255, 255, 255, 0)),
                     off_action=(led.changeto, (0, 0, 0, 0)), toggle_state_on_func=are_lights_on)

loop = asyncio.get_event_loop()

app = picoweb.WebApp(__name__)
event_sinks = set()


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


def push_event(ev):
    global event_sinks
    to_del = set()

    for resp in event_sinks:
        try:
            await resp.awrite("data: %s\n\n" % json.dumps(ev))
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
            await push_event(event)
            eventlist.remove(event)
        await asyncio.sleep_ms(10)


loop.create_task(push_events())

logging.basicConfig(level=logging.INFO)
app.run(host='0.0.0.0', port=80, debug=True)
