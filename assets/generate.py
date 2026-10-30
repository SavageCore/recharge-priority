#!/usr/bin/env python3
"""Regenerate the Nexus page header from the source screenshot.

  assets/header-1300x372.jpg    (wide crop + title overlay, banner)

This mod ships no generated gallery still: the before/after comparison
stills in src/ upload to Nexus directly, and a downscale of either one
would only duplicate them. The header therefore stays a clean vista
band off the top of the after shot.

Usage: python3 assets/generate.py   (or: make assets)
Requires: Pillow (pip install Pillow). Typeface is vendored (see FONT).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src", "header-recharge-priority.jpg")
HDR = os.path.join(HERE, "header-1300x372.jpg")

# In-game heading typeface, vendored (SIL OFL 1.1):
# https://github.com/NMSCD/No-Mans-Sky-Universal-Font
FONT = os.path.join(HERE, "fonts", "GeosansLight-NMS.ttf")

TITLE = "RECHARGE PRIORITY"
SUBTITLE = "ION BATTERIES  \u2022  LIFE SUPPORT GEL  \u2022  SILICATE POWDER"

# Vertical offset of the header crop band in source pixels. The band frames
# the quick menu: the source is the after shot with no mission tracker
# overlapping the fuel cards, so the menu reads cleanly under the title.
HEADER_BAND_Y = 649

# Banner geometry. The Nexus banner slot is 1300x372.
BAND_W, BAND_H = 1300, 372

# Scrim opacity (0-255 of black). FLOOR darkens the whole banner; TEXT is the
# extra scrim held across the text block.
SCRIM_FLOOR = 145
SCRIM_TEXT = 75

# Text placement. TEXT_BOTTOM is the last row covered by the flat text scrim.
TEXT_X = 48
TITLE_Y = 48
SUBTITLE_Y = 118
TITLE_SIZE = 50
SUBTITLE_SIZE = 30
TEXT_BOTTOM = 165
TITLE_COLOR = (255, 255, 255)
SUBTITLE_COLOR = (255, 205, 130)


def main():
    if not os.path.exists(SRC):
        sys.exit(f"missing source screenshot: {SRC}\n"
                 f"Drop a 2560x1440 in-game recharge screenshot there.")

    img = Image.open(SRC).convert("RGB")
    assert img.size == (2560, 1440), f"unexpected source size {img.size}"

    w, h = img.size
    band_h = int(w * 372 / 1300)
    band = img.crop((0, HEADER_BAND_Y, w, HEADER_BAND_Y + band_h))
    band = band.resize((BAND_W, BAND_H), Image.LANCZOS)

    # Scrim, in two parts: a floor across the whole banner, then a flat text
    # scrim eased out below the text block with a smoothstep. Built on its own
    # layer and alpha composited; drawing rows straight onto the band would
    # paint every row twice because Pillow's rectangle() includes both
    # corners.
    scrim = Image.new("RGBA", (BAND_W, BAND_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(BAND_H):
        if y <= TEXT_BOTTOM:
            f = 1.0
        else:
            t = (y - TEXT_BOTTOM) / (BAND_H - TEXT_BOTTOM)
            u = 1.0 - t
            f = u * u * (3 - 2 * u)  # smoothstep, 1 -> 0
        sd.line([(0, y), (BAND_W, y)], fill=(0, 0, 0, min(255, SCRIM_FLOOR + int(SCRIM_TEXT * f))))
    band = Image.alpha_composite(band.convert("RGBA"), scrim).convert("RGB")

    d = ImageDraw.Draw(band)
    fb = ImageFont.truetype(FONT, TITLE_SIZE)
    fs = ImageFont.truetype(FONT, SUBTITLE_SIZE)
    d.text((TEXT_X, TITLE_Y), TITLE, font=fb, fill=TITLE_COLOR)
    d.text((TEXT_X + 2, SUBTITLE_Y), SUBTITLE, font=fs, fill=SUBTITLE_COLOR)
    band.save(HDR, quality=92)
    print(f"wrote {HDR}")


if __name__ == "__main__":
    main()
