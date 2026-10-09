# -*- coding: utf-8 -*-
"""把 ChatGPT 出的 2x2 武器接触表切成 4 张物品图标：
品红抠底 -> 投影切格 -> 裁掉空白 -> 缩到 48x48 -> 输出 + 拼预览。
（这一版细节偏多，缩下来会糊，先当占位；同时会再向 ChatGPT 要一版"更少细节"的。）
"""
import io
import os
import sys

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\p老师\.dsh\attachments\v1\objects\c1\c1359705c00afa9c258f1532e712b60c7e7e0f846a128a9f6631dfa588329e9a"
OUT = r"E:\开发\art-inbox\weapons4"
NAMES = ["ScavengerGreatblade", "SteelDischarger", "PollutionCannon", "SteelBow"]

os.makedirs(OUT, exist_ok=True)

img = Image.open(SRC).convert("RGBA")
arr = np.asarray(img).astype(np.int16)

# 品红抠底：min(R,B) - G 越大越像背景
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
magenta = np.minimum(r, b) - g
alpha = np.clip(255 - magenta * 2, 0, 255).astype(np.uint8)
arr[..., 3] = alpha
cut = Image.fromarray(arr.astype(np.uint8), "RGBA")

# 2x2 切格（图上有明显间隙，直接按象限切）
w, h = cut.size
cells = [
    cut.crop((0, 0, w // 2, h // 2)),
    cut.crop((w // 2, 0, w, h // 2)),
    cut.crop((0, h // 2, w // 2, h)),
    cut.crop((w // 2, h // 2, w, h)),
]

sheet = Image.new("RGBA", (48 * 4 + 5 * 5, 58), (24, 26, 30, 255))

for index, (cell, name) in enumerate(zip(cells, NAMES)):
    bbox = cell.getbbox()

    if bbox is None:
        print("  %s 空" % name)
        continue

    icon = cell.crop(bbox)
    side = max(icon.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(icon, ((side - icon.width) // 2, (side - icon.height) // 2))

    small = square.resize((48, 48), Image.LANCZOS)
    small.save(os.path.join(OUT, name + ".png"))

    print("  %-22s %s -> 48x48" % (name, icon.size))

    sheet.paste(small, (5 + index * 53, 5), small)

sheet.save(r"E:\开发\art-inbox\preview_weapons4.png")
print("预览：E:\\开发\\art-inbox\\preview_weapons4.png")
