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

led = rgbled(26, 25, 33)  # phy 7, 8, 9

page_start = """<html>
  <head>
    <title>ESP Web Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="data:," />
    <style>
      a.button {
        display: inline-block;
        padding: 0.3em 1.2em;
        margin: 0 0.1em 0.1em 0;
        border: 0.16em solid #000;
        border-radius: 2em;
        box-sizing: border-box;
        text-decoration: none;
        font-family: "Roboto", sans-serif;
        font-weight: 600;
        color: #000;
        /* text-shadow: 0 0.04em 0.04em rgba(0, 0, 0, 0.35); */
        text-align: center;
        transition: all 0.2s;
      }
      a.button:hover {
        border-color: rgba(0, 0, 0, 0.5);
        cursor: pointer;
      }
      @media all and (max-width: 30em) {
        a.button {
          display: block;
          margin: 0.2em auto;
        }
      }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/@jaames/iro@5"></script>
  </head>
  <body>
    <h1>ESP Web Server</h1>
    <div id="picker"></div>
    <div>
      <a class="button" style="background-color:rgb(255, 0, 0)">Red</a>
      <a class="button" style="background-color:rgb(0, 255, 0)">Green</a>
      <a class="button" style="background-color:rgb(0, 0, 255)">Blue</a><br />
      <a class="button" style="background-color:rgb(0, 0, 0)">Off</a>
      <a class="button" style="background-color:rgb(255, 255, 255)">White</a>
    </div>
    <script>
      function buttonClick(evt) {
        console.log(evt);
        var cs = evt.srcElement.style.backgroundColor;
        var color = cs
          .split("(")[1]
          .split(")")[0]
          .split(", ");
        colorPicker.color.set(cs);
        colorRequest(color[0], color[1], color[2], 1);
      }
      window.addEventListener("load", function() {
        var bns = document.getElementsByClassName("button");
        for (i = 0; i < bns.length; i++) {
          bns[i].addEventListener("click", buttonClick, false);
        }
      });
      var lock = false;
      function colorRequest(r, g, b, t = 1) {
        lock = true;
        const Http = new XMLHttpRequest();
        const url = "/?r=" + r + "&g=" + g + "&b=" + b + "&t=" + t;
        console.log(url);
        Http.open("GET", url, false);
        Http.send();
        lock = false;
      }
    </script>
    """

page_middle = "<script>initialColor = \"rgb({red},{green},{blue})\";</script>"

page_end = """    <script>
      var prevColor = 0;
      var colorPicker = new iro.ColorPicker("#picker", {
        color: initialColor,
      });
      colorPicker.on("input:start", function(color) {
        prevColor = color;
      });
      colorPicker.on("input:end", function(color) {
        if (lock) {
          colorPicker.color.set(prevColor.rgb);
          return;
        }
        color = color.rgb;
        colorRequest(color.r, color.g, color.b, 0);
      });
    </script>
  </body>
</html>
"""


def web_page():
    red = led.RED.state()
    green = led.GREEN.state()
    blue = led.BLUE.state()
    return page_middle.format(red=red, green=green, blue=blue)


try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
except OSError as e:
    machine.reset()

r = re.compile(r'GET\s\/\?r=(\d+)\&g\=(\d+)\&b\=(\d+)\&t\=(\d+)')
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
        big_send = False
        if m:
            print("interesting request")
            red = int(m.group(1))
            green = int(m.group(2))
            blue = int(m.group(3))
            time = int(m.group(4))
            led.changeto(red, green, blue, time)
            response = "OK"
        else:
            response = "{}\n{}\n{}".format(page_start, web_page(), page_end)
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
    except OSError as e:
        conn.close()
        print('Connection closed')
