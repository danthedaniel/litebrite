import machine
import neopixel
from font import render_text

NUM_PIXELS = 320
PIN = 20  # GP20
COLS = 40
ROWS = 8
BRIGHTNESS = 32  # 255 // 8
SCROLL_DELAY_MS = 50


class Screen:
    def __init__(self):
        self.np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)
        self.hue_offset = 0
        self._bitmap = None
        self._scrolling = False
        self.scroll_offset = 0

    @property
    def bitmap(self):
        return self._bitmap

    @bitmap.setter
    def bitmap(self, value):
        self._bitmap = value
        self.scroll_offset = 0

    @property
    def scrolling(self):
        return self._scrolling

    @scrolling.setter
    def scrolling(self, value):
        self._scrolling = value
        self.scroll_offset = 0

    @staticmethod
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

    @staticmethod
    def dim(color):
        return tuple(c * BRIGHTNESS // 255 for c in color)

    @staticmethod
    def xy_to_index(x, y):
        """Convert (x, y) to LED index. x=0 left, y=0 bottom.
        Even rows run right-to-left, odd rows run left-to-right."""
        if y % 2 == 0:
            return y * COLS + (COLS - 1 - x)
        else:
            return y * COLS + x

    def clear(self):
        self.np.fill((0, 0, 0))
        self.np.write()

    def _draw_bitmap(self, bitmap, offset):
        """Draw one frame of bitmap at the given scroll offset."""
        total_width = len(bitmap)
        self.np.fill((0, 0, 0))
        for screen_x in range(COLS):
            bmp_x = offset - (COLS - 1 - screen_x)
            if 0 <= bmp_x < total_width:
                col_data = bitmap[bmp_x]
                hue = ((screen_x * 360) // COLS + self.hue_offset) % 360
                color = self.dim(self.hsv_to_rgb(hue))
                for font_row in range(ROWS):
                    if col_data[font_row]:
                        y = ROWS - 1 - font_row
                        self.np[self.xy_to_index(screen_x, y)] = color
        self.np.write()
        self.hue_offset = (self.hue_offset + 3) % 360

    def update(self):
        """Draw one frame using the current bitmap and scroll state."""
        if self.bitmap is None:
            return

        if not self.scrolling:
            self._draw_bitmap(self.bitmap, COLS - 1)
            return

        self._draw_bitmap(self.bitmap, self.scroll_offset)
        self.scroll_offset += 1
        if self.scroll_offset >= COLS + len(self.bitmap):
            self.scroll_offset = 0

    def show_text(self, text):
        """Display text statically (must fit on display)."""
        self._draw_bitmap(render_text(text), COLS - 1)


screen = Screen()
