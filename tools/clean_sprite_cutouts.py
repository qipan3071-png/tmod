# -*- coding: utf-8 -*-
"""清理物品贴图的抠图残留（半透明白边 / 品红溢色）。

背景
----
玩家实测：污染炮、清道夫大刀、精钢法袍、精钢弓、归档者魔法杖的图标"抠图不干净有残留"。
排查确认是真的（透明/半透明像素里仍留着接近纯白的 RGB，
另有 50~170 个半透明白像素），典型成因是只压了 alpha、没清颜色，
以及缩放插值把背景色带进了边缘。

修法（与项目既有 `art_common` 流程一致，不引入新风格）
------------------------------------------------------
1. `threshold_alpha(low=8)`：把极低 alpha 彻底归零；
2. `bleed_fix(rounds=2)`：半透明像素的 RGB 换成邻近不透明像素的颜色
   —— 这一步专治"白边/紫边"，因为它把边缘颜色替换成主体色而不是背景色。

不调用 `key_magenta`：这些图早已去过背景，再跑一次会误伤浅色主体（骨白/冷蓝）。

用法:
    python tools/clean_sprite_cutouts.py                # 扫描并报告
    python tools/clean_sprite_cutouts.py --fix          # 就地清理（先备份到 .backup/sprite-cutouts/）
    python tools/clean_sprite_cutouts.py --fix --paths <单个文件...>
"""
import argparse
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from art_common import bleed_fix, threshold_alpha  # noqa: E402

MOD_ROOT = r"E:\开发\WastelandSoul"
BACKUP_ROOT = r"E:\开发\.backup\sprite-cutouts"

# 判定阈值：RGB 三通道都 > 235 且 alpha 在 (0, 250) 之间 = 半透明白边
WHITE_LEVEL = 235
PARTIAL_ALPHA_MAX = 250


def measure(path):
    """返回 (半透明白边像素数, 极低 alpha 像素数, 半透明像素总数)。"""
    image = Image.open(path).convert("RGBA")
    array = np.asarray(image).astype(np.int16)
    r, g, b, a = array[..., 0], array[..., 1], array[..., 2], array[..., 3]

    white_edge = int(np.count_nonzero((a > 0) & (a < PARTIAL_ALPHA_MAX)
                                      & (r > WHITE_LEVEL) & (g > WHITE_LEVEL) & (b > WHITE_LEVEL)))
    low_alpha = int(np.count_nonzero((a > 0) & (a < 8)))
    partial = int(np.count_nonzero((a > 0) & (a < PARTIAL_ALPHA_MAX)))
    return white_edge, low_alpha, partial


def clean(path):
    """物品图标的清理：半透明像素一律变成**全透明或全不透明**。

    ⚠️ 为什么不是只做 `bleed_fix`：实测残留是"**半透明白像素**"
    （例如 `SteelBow.png` 有 171 个 alpha∈(0,250) 且 RGB≈255 的点）。
    tModLoader 把 PNG 打包成 `.rawimg` 后按 alpha 混合，这些点就成了雾状白边 ——
    `bleed_fix` 只改 RGB、不改 alpha，治不了。
    物品图标本来就该是硬边像素画，所以这里直接二值化 alpha 到 0/255，
    再 `bleed_fix` 把边缘 RGB 换成主体色（防止缩放时再渗背景色）。
    """
    image = Image.open(path).convert("RGBA")
    array = np.asarray(image).astype(np.int16)
    alpha = array[..., 3]

    array[..., 3] = np.where(alpha >= 128, 255, 0)

    return bleed_fix(Image.fromarray(array.astype(np.uint8), "RGBA"), rounds=2)


# 只清理"物品/护甲图标"：Backgrounds 与 Projectiles 下的半透明是**故意**的
# （星空渐变、发光弹幕、EX 叠层），动了就会毁掉美术效果。
def is_icon(path):
    relative = os.path.relpath(path, MOD_ROOT).replace("\\", "/")

    if not relative.startswith("Content/Items/"):
        return False

    # 弹幕/特效不在此列
    return "/Projectiles/" not in relative


def iter_sprites(paths):
    if paths:
        for path in paths:
            yield path
        return

    for dirpath, dirs, files in os.walk(MOD_ROOT):
        dirs[:] = [d for d in dirs if d not in ("obj", "bin", ".vs")]

        for name in sorted(files):
            if name.endswith(".png"):
                yield os.path.join(dirpath, name)


def main():
    parser = argparse.ArgumentParser(description="清理贴图抠图残留")
    parser.add_argument("--fix", action="store_true", help="就地清理（会先备份）")
    parser.add_argument("--paths", nargs="*", default=None, help="只处理指定文件")
    parser.add_argument("--threshold", type=int, default=8, help="报告门限：白边像素数 >= 该值才处理")
    args = parser.parse_args()

    targets = []
    scanned = 0

    for path in iter_sprites(args.paths):
        scanned += 1

        if args.paths is None and not is_icon(path):
            continue

        white_edge, low_alpha, partial = measure(path)

        if white_edge >= args.threshold or low_alpha > 0:
            targets.append((path, white_edge, low_alpha, partial))

    print("扫描 %d 张（只统计物品图标；背景与弹幕的半透明是刻意设计），命中 %d 张需要清理"
          % (scanned, len(targets)))

    for path, white_edge, low_alpha, partial in targets:
        print("  %-58s 白边=%4d 极低alpha=%3d 半透明=%4d"
              % (os.path.relpath(path, MOD_ROOT), white_edge, low_alpha, partial))

    if not args.fix or not targets:
        return 0 if not args.fix else 0

    for path, _w, _l, _p in targets:
        relative = os.path.relpath(path, MOD_ROOT)
        backup = os.path.join(BACKUP_ROOT, relative)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(path, backup)
        clean(path).save(path)

    print("已清理 %d 张；备份在 %s" % (len(targets), BACKUP_ROOT))

    print("---- 清理后复测 ----")

    for path, _w, _l, _p in targets:
        white_edge, low_alpha, partial = measure(path)
        print("  %-58s 白边=%4d 极低alpha=%3d 半透明=%4d"
              % (os.path.relpath(path, MOD_ROOT), white_edge, low_alpha, partial))

    return 0


if __name__ == "__main__":
    sys.exit(main())
