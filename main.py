# Complete project details at https://RandomNerdTutorials.com
import re
import gc

import wifimgr
import machine

from rgbled import rgbled

try:
    import usocket as socket
except:
    import socket

wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")

led = rgbled(14, 15, 4)


def web_page():
    red = led.RED.state()
    green = led.GREEN.state()
    blue = led.BLUE.state()

    html = """<html>
  <head>
    <title>ESP Web Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="data:," />
    <script src="https://cdn.jsdelivr.net/npm/@jaames/iro@5"></script>
  </head>
  <body>
    <h1>ESP Web Server</h1>
    <div id="picker"></div>
    <script>
      var lock = false;
      var colorPicker = new iro.ColorPicker("#picker", {{
        color: "rgb({red},{green},{blue})",
        // color: "rgb(0,0,0)",
      }});
      var prevColor = colorPicker.color;

      colorPicker.on("input:start", function(color) {{
        prevColor = color;
      }});
      colorPicker.on("input:end", function(color) {{
        if (lock) {{
          colorPicker.color.set(prevColor.rgb);
          console.log("here");
          return;
        }}
        console.log(color);
        lock = true;
        color = color.rgb;
        const Http = new XMLHttpRequest();
        const url = "/?r=" + color.r + "&g=" + color.g + "&b=" + color.b;
        console.log(url);
        Http.open("GET", url, false);
        Http.send();
        lock = false;
      }});
    </script>
  </body>
</html>
"""
    return html.format(red=red, green=green, blue=blue)


try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
except OSError as e:
    machine.reset()

r = re.compile(r'GET\s\/\?r=(\d+)\&g\=(\d+)\&b\=(\d+)')
while True:
    try:
        if gc.mem_free() < 102000:
            gc.collect()
        conn, addr = s.accept()
        conn.settimeout(3.0)
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        conn.settimeout(None)
        print(request)
        m = r.match(request)
        if m:
            machine.freq(160000000)
            print("interesting request")
            red = int(m.group(1))
            green = int(m.group(2))
            blue = int(m.group(3))
            led.changeto(red, green, blue, 1)
            response = "OK"
        else:
            response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
        machine.freq(80000000)
    except OSError as e:
        conn.close()
        print('Connection closed')
