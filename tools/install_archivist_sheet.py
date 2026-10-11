# -*- coding: utf-8 -*-
"""把 ChatGPT 定稿的归档者 7 帧拼成模组帧表（品红抠底 + 最近邻，不用 Lanczos）。"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_common import bleed_fix, key_magenta, threshold_alpha  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "开发预览", "boss-art-chatgpt")
DST_DIR = os.path.join(ROOT, "WastelandSoul", "Content", "NPCs", "Bosses", "Archivist")
FRAME = 292
HEAD_SIZE = (34, 34)
HEAD_BOX = (0.37, 0.00, 0.63, 0.34)


def fit_nearest(image, size, fill=0.92):
    target_w, target_h = size
    box = image.getchannel("A").getbbox()
    image = image.crop(box)
    ratio = min((target_w * fill) / image.width, (target_h * fill) / image.height)
    new_w = max(1, int(round(image.width * ratio)))
    new_h = max(1, int(round(image.height * ratio)))
    image = image.resize((new_w, new_h), Image.NEAREST)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def load_frame(name):
    path = os.path.join(SRC_DIR, name)
    image = threshold_alpha(bleed_fix(key_magenta(Image.open(path).convert("RGBA"))))
    box = image.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("%s 抠完是空的" % name)
    return fit_nearest(image.crop(box), (FRAME, FRAME))


def main():
    frames = [load_frame("Archivist_f%d.png" % i) for i in range(7)]
    sheet = Image.new("RGBA", (FRAME, FRAME * 7), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.alpha_composite(frame, (0, i * FRAME))

    os.makedirs(DST_DIR, exist_ok=True)
    body_path = os.path.join(DST_DIR, "Archivist.png")
    sheet.save(body_path)

    telegraph = frames[3]
    hw, hh = telegraph.size
    left, top, right, bottom = HEAD_BOX
    helm = telegraph.crop((int(hw * left), int(hh * top), int(hw * right), int(hh * bottom)))
    head = fit_nearest(helm, HEAD_SIZE, fill=0.96)
    head_path = os.path.join(DST_DIR, "Archivist_Head_Boss.png")
    head.save(head_path)

    preview = os.path.join(SRC_DIR, "Archivist_sheet_preview.png")
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(preview)
    head.resize((head.width * 6, head.height * 6), Image.NEAREST).save(os.path.join(SRC_DIR, "Archivist_Head_Boss.png"))
    print("Archivist sheet %dx%d  head %dx%d" % (sheet.width, sheet.height, head.size[0], head.size[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
