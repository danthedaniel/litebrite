import machine
import neopixel
import time
from font import render_text

NUM_PIXELS = 320
PIN = 20  # GP20
COLS = 40
ROWS = 8
BRIGHTNESS = 32  # 255 // 8

np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)


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


def scroll_text(text, delay_ms=50):
    bitmap = render_text(text)
    total_width = len(bitmap)
    hue_offset = 0
    # Scroll from off-screen right to off-screen left
    while True:
        for offset in range(COLS + total_width):
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
            time.sleep_ms(delay_ms)


clear()
scroll_text("Always be excellent")
