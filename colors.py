RGB = tuple  # tuple[int, int, int]
Bitmap = list  # list[list[RGB]]
BLACK = (0, 0, 0)


def hex_to_rgb(hex_color: str) -> RGB:
    """Convert '#RRGGBB' to (r, g, b) tuple."""
    h = hex_color.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


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
