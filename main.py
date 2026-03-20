import machine
import neopixel
import network
import socket
import time
from font import render_text, CHAR_WIFI, CHAR_NO_WIFI

NUM_PIXELS = 320
PIN = 20  # GP20
COLS = 40
ROWS = 8
BRIGHTNESS = 32  # 255 // 8
SCROLL_DELAY_MS = 50

np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

hue_offset = 0
scroll_offset = 0

with open("index.html", "r") as f:
    HTML_PAGE = f.read()


def hsv_to_rgb(h):
    """Convert hue (0-359) to RGB tuple at full saturation/value."""
    region = h // 60
    remainder = h % 60
    t = (255 * remainder) // 60
    q = 255 - t
    if region == 0:
        return (255, t, 0)
    elif region == 1:
        return (q, 255, 0)
    elif region == 2:
        return (0, 255, t)
    elif region == 3:
        return (0, q, 255)
    elif region == 4:
        return (t, 0, 255)
    else:
        return (255, 0, q)


def dim(color):
    return tuple(c * BRIGHTNESS // 255 for c in color)


def xy_to_index(x, y):
    """Convert (x, y) to LED index. x=0 left, y=0 bottom.
    Even rows run right-to-left, odd rows run left-to-right."""
    if y % 2 == 0:
        return y * COLS + (COLS - 1 - x)
    else:
        return y * COLS + x


def clear():
    np.fill((0, 0, 0))
    np.write()


def draw_static(bitmap):
    """Draw bitmap centered on display (no scrolling)."""
    global hue_offset
    total_width = len(bitmap)
    x_start = 0
    np.fill((0, 0, 0))
    for bmp_x in range(total_width):
        screen_x = x_start + bmp_x
        if screen_x < 0 or screen_x >= COLS:
            continue
        col_data = bitmap[bmp_x]
        hue = ((screen_x * 360) // COLS + hue_offset) % 360
        color = dim(hsv_to_rgb(hue))
        for font_row in range(ROWS):
            if col_data[font_row]:
                y = ROWS - 1 - font_row
                np[xy_to_index(screen_x, y)] = color
    np.write()
    hue_offset = (hue_offset + 3) % 360


def draw_scroll(bitmap, offset):
    """Draw one frame of scrolling text at the given offset."""
    global hue_offset
    total_width = len(bitmap)
    np.fill((0, 0, 0))
    for screen_x in range(COLS):
        bmp_x = offset - (COLS - 1 - screen_x)
        if 0 <= bmp_x < total_width:
            col_data = bitmap[bmp_x]
            hue = ((screen_x * 360) // COLS + hue_offset) % 360
            color = dim(hsv_to_rgb(hue))
            for font_row in range(ROWS):
                if col_data[font_row]:
                    y = ROWS - 1 - font_row
                    np[xy_to_index(screen_x, y)] = color
    np.write()
    hue_offset = (hue_offset + 3) % 360


def show_text(text):
    """Display text statically (must fit on display)."""
    draw_static(render_text(text))


def url_decode(s):
    """Decode percent-encoded and plus-encoded string."""
    s = s.replace('+', ' ')
    parts = s.split('%')
    result = parts[0]
    for part in parts[1:]:
        if len(part) >= 2:
            try:
                result += chr(int(part[:2], 16)) + part[2:]
            except ValueError:
                result += '%' + part
        else:
            result += '%' + part
    return result


def parse_post_body(body):
    """Parse 'text=hello+world' form data, return the text value."""
    for pair in body.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            if key == 'text':
                return url_decode(value)
    return ""


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Noisebridge", "noisebridge")
    print("Connecting to WiFi...")
    dots = ["...", "..", ".", ".."]
    max_wait = 20
    while max_wait > 0:
        show_text(CHAR_WIFI + " " + dots[max_wait % len(dots)])
        status = wlan.status()
        if status == network.STAT_GOT_IP:
            break
        if status < 0:
            show_text(CHAR_NO_WIFI + " fail")
            raise RuntimeError("WiFi connection failed, status=" + str(status))
        max_wait -= 1
        time.sleep(1)
    if not wlan.isconnected():
        show_text(CHAR_NO_WIFI + " fail")
        raise RuntimeError("WiFi connection timed out")
    ip = wlan.ifconfig()[0]
    print("Connected! IP:", ip)
    show_text(CHAR_WIFI + " :D")
    time.sleep(2)
    return ip


def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.setblocking(False)
    print("HTTP server listening on port 80")
    return s


def handle_request(server_sock):
    """Check for and handle one HTTP request. Non-blocking. Returns new text or None."""
    try:
        cl, addr = server_sock.accept()
    except OSError:
        return None

    try:
        cl.settimeout(2)
        request = cl.recv(2048).decode("utf-8")
    except Exception:
        cl.close()
        return None

    new_text = None
    first_line = request.split("\r\n", 1)[0] if request else ""

    if first_line.startswith("POST /text"):
        body = ""
        if "\r\n\r\n" in request:
            body = request.split("\r\n\r\n", 1)[1]
        new_text = parse_post_body(body)[:32]
        cl.send("HTTP/1.0 303 See Other\r\nLocation: /\r\n\r\n")
    elif first_line.startswith("GET / ") or first_line.startswith("GET /index"):
        cl.send("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(HTML_PAGE)
    else:
        cl.send("HTTP/1.0 404 Not Found\r\n\r\n")

    cl.close()
    return new_text


def main():
    global scroll_offset

    clear()
    ip = connect_wifi()

    current_text = ip
    bitmap = render_text(current_text)
    total_width = len(bitmap)
    scrolling = total_width > COLS
    scroll_offset = 0

    server = start_server()
    last_frame = time.ticks_ms()

    while True:
        new_text = handle_request(server)
        if new_text is not None:
            current_text = new_text
            bitmap = render_text(current_text)
            total_width = len(bitmap)
            scrolling = True
            scroll_offset = 0
            print("New text:", current_text)

        now = time.ticks_ms()
        if time.ticks_diff(now, last_frame) >= SCROLL_DELAY_MS:
            last_frame = now
            if scrolling:
                draw_scroll(bitmap, scroll_offset)
                scroll_offset += 1
                if scroll_offset >= COLS + total_width:
                    scroll_offset = 0
            else:
                draw_static(bitmap)


try:
    main()
except Exception as e:
    print("Error:", e)
    err_text = "Error: " + str(e)
    err_bitmap = render_text(err_text)
    err_width = len(err_bitmap)
    err_offset = 0
    while True:
        draw_scroll(err_bitmap, err_offset)
        err_offset += 1
        if err_offset >= COLS + err_width:
            err_offset = 0
        time.sleep_ms(SCROLL_DELAY_MS)
