# Complete project details at https://RandomNerdTutorials.com
import re
import gc
import machine

try:
    import tinyweb
except:
    from lib import tinyweb
try:
    import wifimgr
except:
    from lib import wifimgr

from rgbled import rgbled
from touchy import TouchAction

wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")

led = rgbled(26, 25, 33)  # phy 7, 8, 9


def are_lights_on() -> bool:
    return any(c > 0 for c in led.colors())


on_off = TouchAction(15, 500, toggle=True, on_action=(led.changeto, (255, 255, 255, 0)),
                     off_action=(led.changeto, (0, 0, 0, 0)), toggle_state_on_func=are_lights_on)

app = tinyweb.webserver()

# Index page


@app.route('/')
async def index(request, response):
    # Start HTTP response with content-type text/html
    await response.start_html()
    # Send actual HTML page
    from templates import page_html
    for val in page_html.render():
        await response.send(val)


@app.resource('/api/get_colors', method='GET')
async def colors(data):
    yield '{'
    yield '"red": {},'.format(led.RED.state())
    yield '"green": {},'.format(led.GREEN.state())
    yield '"blue": {}'.format(led.BLUE.state())
    yield '}'


@app.resource('/api/set_colors', method='POST')
async def set_colors(data):
    led.changeto(int(data["red"]), int(data["green"]),
                 int(data["blue"]), int(data["time"]))
    yield '{'
    yield '"status": "OK"'
    yield '}'


app.run(host='0.0.0.0', port=80)
