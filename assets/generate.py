#!/usr/bin/env python3
"""Regenerate Nexus page images from the source screenshot.

  assets/gallery-1920x1080.jpg  (16:9 downscale, gallery slot)
  assets/header-1300x372.jpg    (wide crop + title overlay, banner)

Usage: python3 assets/generate.py   (or: make assets)
Requires: Pillow (pip install Pillow). Typeface is vendored (see FONT).

SRC must be an in-game recharge screenshot at 2560x1440, showing the quick
menu or inventory with the recharge fuel order visible. Ship art that does
not match the mod is worse than shipping no art at all, so generate.py
refuses to run rather than guess.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src", "gallery-recharge-priority.jpg")
GAL = os.path.join(HERE, "gallery-1920x1080.jpg")
HDR = os.path.join(HERE, "header-1300x372.jpg")

# In-game heading typeface, vendored (SIL OFL 1.1):
# https://github.com/NMSCD/No-Mans-Sky-Universal-Font
FONT = os.path.join(HERE, "fonts", "GeosansLight-NMS.ttf")

TITLE = "RECHARGE PRIORITY"
SUBTITLE = "ION BATTERIES  \u2022  LIFE SUPPORT GEL"

# Vertical offset of the header crop band in source pixels. Kept at the top:
# the mission tracker overlaps the quick menu lower in the frame, so any
# band including the menu carries that text through the fuel cards. The
# gallery still below carries the proof; the header stays a clean vista.
HEADER_BAND_Y = 0

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

    img.resize((1920, 1080), Image.LANCZOS).save(GAL, quality=92)
    print(f"wrote {GAL}")

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
