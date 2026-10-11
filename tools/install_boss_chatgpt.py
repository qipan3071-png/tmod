# -*- coding: utf-8 -*-
"""把已点头的 ChatGPT Boss 原图装进模组（品红抠底 + 整数倍最近邻，不用 Lanczos）。"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_common import bleed_fix, key_magenta, threshold_alpha  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "开发预览", "boss-art-chatgpt")
HEAD_SIZE = (34, 34)

JOBS = (
    {
        "src": "AshHeart_f0.png",
        "dst": os.path.join("WastelandSoul", "Content", "NPCs", "Bosses", "AshHeart"),
        "name": "AshHeart",
        "div": 4,
        "head": (0.18, 0.08, 0.82, 0.72),
    },
    {
        "src": "Archivist_f0.png",
        "dst": os.path.join("WastelandSoul", "Content", "NPCs", "Bosses", "Archivist"),
        "name": "Archivist",
        "div": 4,
        "head": (0.34, 0.00, 0.66, 0.36),
    },
)


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


def install(job):
    src = os.path.join(SRC_DIR, job["src"])
    dst_dir = os.path.join(ROOT, job["dst"])
    image = threshold_alpha(bleed_fix(key_magenta(Image.open(src).convert("RGBA"))))
    box = image.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("%s 抠完是空的" % job["src"])

    image = image.crop(box)
    body = image.resize((max(1, image.width // job["div"]), max(1, image.height // job["div"])), Image.NEAREST)
    os.makedirs(dst_dir, exist_ok=True)
    body_path = os.path.join(dst_dir, job["name"] + ".png")
    body.save(body_path)

    hw, hh = body.size
    left, top, right, bottom = job["head"]
    helm = body.crop((int(hw * left), int(hh * top), int(hw * right), int(hh * bottom)))
    head = fit_nearest(helm, HEAD_SIZE)
    head_path = os.path.join(dst_dir, job["name"] + "_Head_Boss.png")
    head.save(head_path)

    preview_body = os.path.join(SRC_DIR, job["name"] + "_ingame.png")
    preview_head = os.path.join(SRC_DIR, job["name"] + "_Head_Boss.png")
    body.resize((body.width * 3, body.height * 3), Image.NEAREST).save(preview_body)
    head.resize((head.width * 6, head.height * 6), Image.NEAREST).save(preview_head)

    print("%s body %dx%d  head %dx%d" % (job["name"], body.width, body.height, head.size[0], head.size[1]))


def main():
    for job in JOBS:
        install(job)
    return 0


if __name__ == "__main__":
    sys.exit(main())
