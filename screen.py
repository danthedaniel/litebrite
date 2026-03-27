import machine
import neopixel
import time
from font import render_text
from colors import Bitmap, RGB, BLACK

PIN = 20  # GP20
COLS = 40
ROWS = 8
NUM_PIXELS = COLS * ROWS
BRIGHTNESS = 32  # 255 // 8
SCROLL_DELAY_MS = 50


def dim(color: RGB) -> RGB:
    return tuple(c * BRIGHTNESS // 255 for c in color)


class Screen:
    def __init__(self) -> None:
        self.np: neopixel.NeoPixel = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)
        self._bitmap: Bitmap | None = None  # list[list[RGB]]
        self._scrolling: bool = False
        self.scroll_offset: int = 0
        self._shader: object = None  # Optional (x: int, y: int, t: int) -> RGB
        self._t: int = 0

    @property
    def bitmap(self) -> Bitmap | None:
        """Current display bitmap. list[list[RGB]]"""
        return self._bitmap

    @bitmap.setter
    def bitmap(self, value: Bitmap) -> None:
        self._bitmap = value
        self.scroll_offset = 0

    @property
    def scrolling(self) -> bool:
        """Whether text scrolls across the display. bool"""
        return self._scrolling

    @scrolling.setter
    def scrolling(self, value: bool) -> None:
        self._scrolling = value
        self.scroll_offset = 0

    @property
    def shader(self):
        """Per-pixel color function applied each frame. Optional[Callable[[int, int, int], RGB]]"""
        return self._shader

    @shader.setter
    def shader(self, value) -> None:
        self._shader = value

    @staticmethod
    def xy_to_index(x: int, y: int) -> int:
        """Convert (x, y) to LED index. x=0 left, y=0 bottom.
        Even rows run right-to-left, odd rows run left-to-right."""
        if y % 2 == 0:
            return y * COLS + (COLS - 1 - x)
        else:
            return y * COLS + x

    def shade(self, x: int, y: int) -> RGB:
        """Apply the shader to compute the color for pixel at (x, y)."""
        if not self._bitmap:
            raise ValueError("No bitmap set")

        if not callable(self._shader):
            return self._bitmap[x][y]

        return self._shader(x, y, self._t)  # pyright: ignore[reportReturnType]

    def clear(self) -> None:
        self.np.fill(BLACK)
        self.np.write()

    def _draw_bitmap(self, bitmap: Bitmap, offset: int) -> None:
        """Draw one frame of bitmap at the given scroll offset."""
        total_width = len(bitmap)
        self.np.fill(BLACK)
        self._t = time.ticks_ms()

        for screen_x in range(COLS):
            bmp_x = offset - (COLS - 1 - screen_x)
            if 0 <= bmp_x < total_width:
                col_data = bitmap[bmp_x]

                for font_row in range(ROWS):
                    pixel = col_data[font_row]
                    if pixel != BLACK:
                        if self._shader:
                            color = dim(self.shade(screen_x, font_row))
                        else:
                            color = dim(pixel)

                        y = ROWS - 1 - font_row
                        self.np[self.xy_to_index(screen_x, y)] = color

        self.np.write()

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
        self._draw_bitmap(render_text(text, "#FFFFFF"), COLS - 1)


screen = Screen()
