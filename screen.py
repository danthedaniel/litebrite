import machine
import neopixel
from font import render_text, Bitmap

NUM_PIXELS = 320
PIN = 20  # GP20
COLS = 40
ROWS = 8
BRIGHTNESS = 32  # 255 // 8
SCROLL_DELAY_MS = 50

RGB = tuple


class Screen:
    def __init__(self) -> None:
        self.np: neopixel.NeoPixel = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)
        self.hue_offset: int = 0
        self._bitmap: Bitmap | None = None
        self._scrolling: bool = False
        self.scroll_offset: int = 0
        self._color: str = 'rainbow'

    @property
    def bitmap(self) -> Bitmap | None:
        return self._bitmap

    @bitmap.setter
    def bitmap(self, value: Bitmap) -> None:
        self._bitmap = value
        self.scroll_offset = 0

    @property
    def scrolling(self) -> bool:
        return self._scrolling

    @scrolling.setter
    def scrolling(self, value: bool) -> None:
        self._scrolling = value
        self.scroll_offset = 0

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str) -> None:
        self._color = value

    @staticmethod
    def hex_to_rgb(hex_color: str) -> RGB:
        """Convert '#RRGGBB' to (r, g, b) tuple."""
        h = hex_color.lstrip('#')
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @staticmethod
    def hsv_to_rgb(h: int) -> RGB:
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
    def dim(color: RGB) -> RGB:
        return tuple(c * BRIGHTNESS // 255 for c in color)

    @staticmethod
    def xy_to_index(x: int, y: int) -> int:
        """Convert (x, y) to LED index. x=0 left, y=0 bottom.
        Even rows run right-to-left, odd rows run left-to-right."""
        if y % 2 == 0:
            return y * COLS + (COLS - 1 - x)
        else:
            return y * COLS + x

    def clear(self) -> None:
        self.np.fill((0, 0, 0))
        self.np.write()

    def _draw_bitmap(self, bitmap: Bitmap, offset: int) -> None:
        """Draw one frame of bitmap at the given scroll offset."""
        total_width = len(bitmap)
        self.np.fill((0, 0, 0))

        use_rainbow = self._color == 'rainbow'
        solid_color = (0, 0, 0) if use_rainbow else self.dim(self.hex_to_rgb(self._color))

        for screen_x in range(COLS):
            bmp_x = offset - (COLS - 1 - screen_x)
            if 0 <= bmp_x < total_width:
                col_data = bitmap[bmp_x]

                if use_rainbow:
                    hue = ((screen_x * 360) // COLS + self.hue_offset) % 360
                    color = self.dim(self.hsv_to_rgb(hue))
                else:
                    color = solid_color

                for font_row in range(ROWS):
                    if col_data[font_row]:
                        y = ROWS - 1 - font_row
                        self.np[self.xy_to_index(screen_x, y)] = color

        self.np.write()
        if use_rainbow:
            self.hue_offset = (self.hue_offset + 3) % 360

    def update(self) -> None:
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

    def show_text(self, text: str) -> None:
        """Display text statically (must fit on display)."""
        self._draw_bitmap(render_text(text), COLS - 1)


screen = Screen()
