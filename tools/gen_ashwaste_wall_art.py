# -*- coding: utf-8 -*-
"""生成「灰烬荒壁」（AshWasteWall）的贴图。

规格（从 tModLoader.dll 的 WallDrawing.DrawWalls 反查出来的硬约束）：
  * 每格墙的取样矩形是 `new Rectangle(WallFrameX, WallFrameY + Main.wallFrame[type] * 180, 32, 32)`；
  * `WallFrameX` / `WallFrameY` 走 **36 像素网格**（Framing.WallFrame 的查表值），
    `Main.wallFrame` 是 0~2 的墙体变体号。
  * 所以贴图必须覆盖 x = 0..36*9+31、y = 0..180*2+36*4+31。

做法：贴图 = **36×36 为一格**，每格里放同一张 32×32 的无缝图案 Q
（源列 c 取样 Q[(c % 36) % 32]，行列同构）。这样任何 frameX / frameY / 变体取到的
都是同一张 Q，相邻两格画出来严丝合缝（无接缝），也不需要为变体另画内容。

配色：暗底 + 与瑜钢合金（88,172,178）同一套青白点缀语言，但更暗更闷 —— 不是亮墙。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

TILE = 32                  # 一格的可见图案
CELL = 36                  # 墙的取样网格
SHEET_W = CELL * 10        # 360：覆盖 frameX 0..324
SHEET_H = CELL * 15        # 540：覆盖 frameY 0..144 + 180*2 的变体块
OUT = r"E:\开发\WastelandSoul\Content\Walls\AshWasteWall.png"

BASE = (29, 34, 38)        # 暗底（比瑜钢合金暗得多）
MORTAR = (20, 24, 27)      # 灰缝
SPECK_DIM = (58, 96, 104)  # 青白点缀（闷）
SPECK_LIT = (104, 140, 146)


def hash01(seed, x, y):
    """确定性哈希噪声（0..1），x/y 先按 32 取模 → 图案自身可无缝平铺。"""
    h = (seed * 374761393 + (x % TILE) * 668265263 + (y % TILE) * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0x7FFFFFFF) / float(0x7FFFFFFF)


def build_tile():
    image = Image.new("RGBA", (TILE, TILE))
    pixels = image.load()

    for y in range(TILE):
        for x in range(TILE):
            # 底：低频噪声（取整到 4 格，避免噪点太花）+ 细粒
            broad = hash01(11, x // 4 * 4, y // 4 * 4)
            fine = hash01(23, x, y)
            shade = (broad - 0.5) * 10.0 + (fine - 0.5) * 7.0

            r = BASE[0] + shade
            g = BASE[1] + shade
            b = BASE[2] + shade

            # 灰缝：每 16 行一条横缝；竖缝上下半砖错开（32 平铺下依然无缝）
            mortar = (y % 16 == 15)
            if y < 16:
                mortar = mortar or (x % 32 == 15)
            else:
                mortar = mortar or (x % 32 == 31)

            if mortar:
                r, g, b = MORTAR
                r += (fine - 0.5) * 6.0
                g += (fine - 0.5) * 6.0
                b += (fine - 0.5) * 6.0
            elif hash01(37, x, y) > 0.955:
                # 青白点缀：稀疏、暗；再撒极少数稍亮的一点（语言同瑜钢合金，亮度压下去）
                r, g, b = SPECK_LIT if hash01(53, x, y) > 0.7 else SPECK_DIM
                r += (fine - 0.5) * 8.0
                g += (fine - 0.5) * 8.0
                b += (fine - 0.5) * 8.0

            pixels[x, y] = (
                max(0, min(255, int(r))),
                max(0, min(255, int(g))),
                max(0, min(255, int(b))),
                255,
            )

    return image


def build_sheet(tile):
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H))
    src = tile.load()
    dst = sheet.load()

    for y in range(SHEET_H):
        qy = (y % CELL) % TILE
        for x in range(SHEET_W):
            dst[x, y] = src[(x % CELL) % TILE, qy]

    return sheet


def main():
    tile = build_tile()
    sheet = build_sheet(tile)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet.save(OUT)
    print("已写出 %s  %dx%d（36 像素网格：%d x %d 格）"
          % (OUT, sheet.size[0], sheet.size[1], SHEET_W // CELL, SHEET_H // CELL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
