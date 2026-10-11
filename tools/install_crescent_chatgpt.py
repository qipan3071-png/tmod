# -*- coding: utf-8 -*-
"""把 ChatGPT 出的巨新月刃装进模组：品红抠底 + 整数倍最近邻，不用 Lanczos。"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_common import bleed_fix, key_magenta, threshold_alpha  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "开发预览", "boss-art-chatgpt", "FireplaceGiantCrescent.png")
DST = os.path.join(ROOT, "WastelandSoul", "Content", "Projectiles", "Fireplace", "FireplaceGiantCrescent.png")
PREVIEW = os.path.join(ROOT, "开发预览", "boss-art-chatgpt", "FireplaceGiantCrescent_ingame.png")
PIXEL_DIV = 4
MAX_EDGE = 160


def main():
    image = Image.open(SRC).convert("RGBA")
    image = threshold_alpha(bleed_fix(key_magenta(image)))
    box = image.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("抠完是空的")

    image = image.crop(box)
    new_w = max(1, image.width // PIXEL_DIV)
    new_h = max(1, image.height // PIXEL_DIV)
    if max(new_w, new_h) > MAX_EDGE:
        extra = (max(new_w, new_h) + MAX_EDGE - 1) // MAX_EDGE
        new_w = max(1, new_w // extra)
        new_h = max(1, new_h // extra)

    body = image.resize((new_w, new_h), Image.NEAREST)
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    body.save(DST)
    body.resize((body.width * 4, body.height * 4), Image.NEAREST).save(PREVIEW)
    print("crescent %dx%d -> %s" % (body.width, body.height, DST))
    print("preview %s" % PREVIEW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
