"""Home-screen icons, in the same house style as the other apps.

Dark tile, a small mark up top, the name in a serif wordmark in the page's own
accent colour, a hairline rule, then what the thing does in spaced-out sans.
Run once and commit the PNGs; CI copies them rather than rebuilding them.

    python3 make_icons.py
"""

import math

from PIL import Image, ImageDraw, ImageFont

BG = "#131519"        # the page's dark background
ACCENT = "#4FB5B0"    # the page's dark-mode accent
RULE = "#3A3A42"
SUB = "#8E9AAB"

SERIF = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
SANS = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def rounded_tile(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.225), fill=BG)
    return img, d


def centred(d, y, text, font, fill, tracking=0):
    if not tracking:
        w = d.textlength(text, font=font)
        d.text(((d.im.size[0] - w) / 2, y), text, font=font, fill=fill)
        return
    widths = [d.textlength(c, font=font) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (d.im.size[0] - total) / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=font, fill=fill)
        x += w + tracking


def countdown(d, size):
    """A dial with a hand at twelve — a dated event, in the accent colour."""
    cx, cy = size / 2, size * 0.30
    r = size * 0.085
    lw = max(2, int(size * 0.016))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ACCENT, width=lw)
    d.line([cx, cy, cx, cy - r * 0.72], fill=ACCENT, width=lw)
    d.line([cx, cy, cx + r * 0.5, cy + r * 0.3], fill=ACCENT, width=lw)
    for k in range(12):
        a = math.radians(k * 30)
        inner = r * (0.8 if k % 3 else 0.7)
        d.line([cx + math.sin(a) * inner, cy - math.cos(a) * inner,
                cx + math.sin(a) * r * 0.92, cy - math.cos(a) * r * 0.92], fill=ACCENT, width=max(1, lw // 2))


def build(size):
    img, d = rounded_tile(size)
    countdown(d, size)
    wordmark = ImageFont.truetype(SERIF, int(size * 0.165))
    subtitle = ImageFont.truetype(SANS, int(size * 0.058))
    centred(d, size * 0.42, "EVENT", wordmark, ACCENT)
    ry = size * 0.635
    d.line([size * 0.34, ry, size * 0.66, ry], fill=RULE, width=max(1, int(size * 0.006)))
    centred(d, size * 0.685, "SCREEN", subtitle, SUB, tracking=size * 0.028)
    return img


if __name__ == "__main__":
    for size, name in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")]:
        build(size).save(name)
        print(f"wrote {name} ({size}x{size})")
