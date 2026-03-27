import uasyncio
import network
import time
from font import render_text, CHAR_WIFI, CHAR_NO_WIFI
from microdot import Microdot, Request, urlencode
from screen import screen, COLS, ROWS, SCROLL_DELAY_MS
from colors import hsv_to_rgb, RGB


def rainbow_shader(x: int, _y: int, t: int) -> RGB:
    """Cycle hues across the x-axis, animated over time."""
    hue = ((x * 360) // COLS + t * 3 // 50) % 360
    return hsv_to_rgb(hue)


app = Microdot()

with open("index.html", "r") as f:
    HTML_PAGE = f.read()


@app.get('/')
async def index(_req: Request):
    return HTML_PAGE, 200, {'Content-Type': 'text/html'}


def is_hex_color(s: str) -> bool:
    return len(s) == 7 and s[0] == '#' and all(c in '0123456789abcdef' for c in s[1:])


def parse_text_payload(data: dict) -> tuple[str, bool, str]:
    text = str(data.get('text', ''))[:32]

    raw_scrolling = data.get('scrolling', False)
    if isinstance(raw_scrolling, bool):
        scrolling = raw_scrolling
    elif isinstance(raw_scrolling, str):
        scrolling = raw_scrolling.lower() == 'true'
    else:
        raise ValueError('scrolling must be a boolean or string')

    color = str(data.get('color', 'rainbow')).lower()
    if color != 'rainbow' and not is_hex_color(color):
        raise ValueError('color must be "rainbow" or a hex code like #FF0000')

    return text, scrolling, color


@app.post('/text')
async def set_text(req: Request):
    is_json = bool(req.content_type and 'application/json' in req.content_type)
    if is_json:
        data = req.json or {}
    else:
        data = req.form or {}

    try:
        text, scrolling, color = parse_text_payload(data)
    except ValueError as e:
        if is_json:
            return {'ok': False, 'error': str(e)}, 400
        else:
            return '', 303, {'Location': '/?error=' + urlencode(str(e))}

    screen.bitmap = render_text(text, "#FFFFFF" if color == "rainbow" else color)
    screen.scrolling = scrolling
    screen.shader = rainbow_shader if color == 'rainbow' else None

    if is_json:
        return {'ok': True}
    else:
        return '', 303, {'Location': '/'}


def parse_bitmap_payload(data: dict) -> list:
    raw_bitmap = data.get("bitmap")
    if not isinstance(raw_bitmap, list):
        raise ValueError('expected a list of columns')

    if len(raw_bitmap) != COLS:
        raise ValueError('bitmap must have ' + str(COLS) + ' columns')

    bitmap = []

    for x, col in enumerate(raw_bitmap):
        if not isinstance(col, list) or len(col) != ROWS:
            raise ValueError('column ' + str(x) + ' must have ' + str(ROWS) + ' pixels')

        bitmap_col = []

        for y, pixel in enumerate(col):
            if not isinstance(pixel, list) or len(pixel) != 3:
                raise ValueError('pixel at (' + str(x) + ',' + str(y) + ') must be [r, g, b]')

            for color in pixel:
                if not isinstance(color, int):
                    raise ValueError('RGB values must be integers at (' + str(x) + ',' + str(y) + ')')
                if not 0 <= color <= 255:
                    raise ValueError('RGB values must be 0-255 at (' + str(x) + ',' + str(y) + ')')

            bitmap_col.append(tuple(pixel))

        bitmap.append(bitmap_col)

    return bitmap


@app.post('/bitmap')
async def set_bitmap(req: Request):
    data = req.json or {}

    try:
        bitmap = parse_bitmap_payload(data)
    except ValueError as e:
        return {'ok': False, 'error': str(e)}, 400

    screen.bitmap = bitmap
    screen.scrolling = False
    screen.shader = None

    return {'ok': True}


async def display_loop() -> None:
    while True:
        screen.update()
        await uasyncio.sleep_ms(SCROLL_DELAY_MS)


def connect_wifi() -> str:
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

    ip = str(wlan.ifconfig()[0])
    screen.show_text(CHAR_WIFI + " :D")
    time.sleep(2)

    return ip


def main() -> None:
    screen.clear()
    ip = connect_wifi()

    bitmap = render_text(ip, "#FFFFFF")
    screen.bitmap = bitmap
    screen.scrolling = len(bitmap) > COLS

    uasyncio.create_task(display_loop())
    app.run(port=80)


def show_error(e: Exception) -> None:
    screen.bitmap = render_text("Error: " + str(e)[0:64], "#FF0000")
    screen.scrolling = True

    while True:
        screen.update()
        time.sleep_ms(SCROLL_DELAY_MS)


try:
    main()
except Exception as e:
    show_error(e)
