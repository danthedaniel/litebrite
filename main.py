import asyncio
import network
import time
from font import render_text, CHAR_WIFI, CHAR_NO_WIFI
from microdot import Microdot
from screen import screen, COLS, SCROLL_DELAY_MS
app = Microdot()

with open("index.html", "r") as f:
    HTML_PAGE = f.read()


@app.get('/')
async def index(_req):
    return HTML_PAGE, 200, {'Content-Type': 'text/html'}


@app.post('/text')
async def set_text(req):
    text = req.form.get('text', '')[:32]
    screen.bitmap = render_text(text)
    screen.scrolling = True
    return '', 303, {'Location': '/'}


async def display_loop():
    while True:
        screen.update()
        await asyncio.sleep_ms(SCROLL_DELAY_MS)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Noisebridge", "noisebridge")
    dots = ["...", "..", ".", ".."]

    max_wait = 20
    while max_wait > 0:
        screen.show_text(CHAR_WIFI + " " + dots[max_wait % len(dots)])

        status = wlan.status()
        if status == network.STAT_GOT_IP:
            break
        if status < 0:
            screen.show_text(CHAR_NO_WIFI + " fail")
            raise RuntimeError("WiFi connection failed, status=" + str(status))

        max_wait -= 1
        time.sleep(1)

    if not wlan.isconnected():
        screen.show_text(CHAR_NO_WIFI + " fail")
        raise RuntimeError("WiFi connection timed out")

    ip = wlan.ifconfig()[0]
    screen.show_text(CHAR_WIFI + " :D")
    time.sleep(2)
    return ip


def main():
    screen.clear()
    ip = connect_wifi()

    screen.bitmap = render_text(ip)
    screen.scrolling = len(screen.bitmap) > COLS

    asyncio.create_task(display_loop())
    app.run(port=80)


def show_error(e):
  screen.bitmap = render_text("Error: " + str(e)[0:64])
  screen.scrolling = True

  while True:
      screen.update()
      time.sleep_ms(SCROLL_DELAY_MS)


try:
    main()
except Exception as e:
    show_error(e)
