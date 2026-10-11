# -*- coding: utf-8 -*-
"""把已点头的 ChatGPT 壁炉守卫原图装进模组。

不走 apply_art 的 Lanczos/BOX 缩小（会糊成贴纸）。
品红抠底后按整数倍最近邻缩小，碰撞箱按石巨人 140 的 1.3 倍另写。
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art_common import bleed_fix, key_magenta, threshold_alpha  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "开发预览", "boss-art-chatgpt", "FireplaceGuardian_f0.png")
DST_DIR = os.path.join(ROOT, "WastelandSoul", "Content", "NPCs", "Bosses", "FireplaceGuardian")
PREVIEW = os.path.join(ROOT, "开发预览", "boss-art-chatgpt", "FireplaceGuardian_ingame.png")
HEAD_PREVIEW = os.path.join(ROOT, "开发预览", "boss-art-chatgpt", "FireplaceGuardian_Head_Boss.png")

# 1026x1229 裁切 / 4 = 256x307，整图约 1.8 倍石巨人，主体接近 1.3 倍
PIXEL_DIV = 4
HEAD_SIZE = (34, 34)


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


def main():
    image = Image.open(SRC).convert("RGBA")
    image = threshold_alpha(bleed_fix(key_magenta(image)))
    box = image.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("抠完是空的")

    image = image.crop(box)
    new_w = max(1, image.width // PIXEL_DIV)
    new_h = max(1, image.height // PIXEL_DIV)
    body = image.resize((new_w, new_h), Image.NEAREST)

    os.makedirs(DST_DIR, exist_ok=True)
    body_path = os.path.join(DST_DIR, "FireplaceGuardian.png")
    body.save(body_path)

    # 头盔在上沿中部
    hw, hh = body.size
    helm = body.crop((int(hw * 0.28), 0, int(hw * 0.72), int(hh * 0.28)))
    head = fit_nearest(helm, HEAD_SIZE)
    head_path = os.path.join(DST_DIR, "FireplaceGuardian_Head_Boss.png")
    head.save(head_path)

    zoom = body.resize((body.width * 3, body.height * 3), Image.NEAREST)
    zoom.save(PREVIEW)
    head.resize((head.width * 6, head.height * 6), Image.NEAREST).save(HEAD_PREVIEW)

    print("body %dx%d -> %s" % (body.width, body.height, body_path))
    print("head %dx%d -> %s" % (head.size[0], head.size[1], head_path))
    print("preview %s" % PREVIEW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
