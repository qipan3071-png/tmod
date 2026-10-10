# -*- coding: utf-8 -*-
"""武器像素稿预览：只写到「开发预览/weapon-art-v1」，不覆盖模组目录。

原版味：偶数尺寸、硬边、3~4 阶色、深色收边、剪影清楚。剑柄在左下、刃向右上。
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "开发预览", "weapon-art-v1")


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c):
    if 0 <= x < im.size[0] and 0 <= y < im.size[1]:
        im.putpixel((int(x), int(y)), c)


def rect(im, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            put(im, x, y, c)


def disk(im, cx, cy, r, c):
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r * r:
                put(im, cx + x, cy + y, c)


def thick(im, x0, y0, x1, y1, r, c):
    steps = int(max(abs(x1 - x0), abs(y1 - y0), 1) * 3)
    for i in range(steps + 1):
        t = i / float(steps)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        disk(im, round(x), round(y), r, c)


def outline_opaque(im, color):
    px = im.load()
    w, h = im.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] < 20:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h or px[nx, ny][3] < 20:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = color


def sword(w, h, handle, tip, blade_r, pal, guard=6, grip=10):
    """pal: light, mid, dark, outline, wood, brass"""
    light, mid, dark, out, wood, brass = pal
    im = new(w, h)
    hx, hy = handle
    tx, ty = tip
    dx, dy = tx - hx, ty - hy
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    # 刃：中亮、右下暗
    thick(im, hx + ux * grip, hy + uy * grip, tx, ty, blade_r, mid)
    thick(im, hx + ux * grip - uy, hy + uy * grip + ux, tx - uy, ty + ux, max(1, blade_r - 1), dark)
    thick(im, hx + ux * grip + uy, hy + uy * grip - ux, tx + uy, ty - ux, max(1, blade_r - 1), light)
    # 护手
    gx, gy = hx + ux * grip, hy + uy * grip
    thick(im, gx - uy * guard, gy + ux * guard, gx + uy * guard, gy - ux * guard, 1, brass)
    # 柄
    thick(im, hx, hy, gx, gy, 2, wood)
    disk(im, hx, hy, 2, brass)
    outline_opaque(im, out)
    return im


# 色板
STEEL = ((210, 214, 220, 255), (150, 154, 162, 255), (88, 90, 98, 255), (36, 34, 40, 255), (92, 64, 42, 255), (186, 142, 58, 255))
RUST = ((186, 122, 64, 255), (138, 72, 36, 255), (84, 40, 22, 255), (42, 22, 16, 255), (72, 48, 32, 255), (156, 96, 40, 255))
EMBER = ((255, 168, 96, 255), (196, 72, 40, 255), (110, 32, 24, 255), (48, 16, 18, 255), (70, 46, 32, 255), (204, 140, 48, 255))
BONE = ((232, 220, 196, 255), (186, 168, 140, 255), (120, 100, 78, 255), (48, 36, 28, 255), (92, 64, 42, 255), (196, 160, 64, 255))
SCRAP = ((168, 172, 164, 255), (112, 116, 108, 255), (64, 68, 62, 255), (28, 28, 26, 255), (80, 56, 36, 255), (148, 108, 48, 255))


def fireplace_greatsword():
    im = sword(56, 56, (10, 46), (46, 8), 3, STEEL, guard=7, grip=12)
    # 炉心：刃中一颗红芯
    put(im, 30, 22, (220, 56, 40, 255))
    put(im, 31, 22, (220, 56, 40, 255))
    put(im, 30, 23, (255, 140, 80, 255))
    return im


def hearth_blade():
    return sword(48, 48, (8, 40), (40, 8), 2, EMBER, guard=5, grip=9)


def scrap_spark():
    im = new(40, 40)
    # 短杖 + 电火花
    thick(im, 8, 32, 24, 16, 2, (92, 64, 42, 255))
    disk(im, 26, 14, 4, (80, 180, 220, 255))
    disk(im, 26, 14, 2, (200, 240, 255, 255))
    put(im, 32, 10, (200, 240, 255, 255))
    put(im, 20, 10, (200, 240, 255, 255))
    put(im, 30, 18, (80, 180, 220, 255))
    outline_opaque(im, (28, 30, 36, 255))
    return im


def rust_cleaver():
    im = sword(52, 52, (8, 44), (42, 10), 4, RUST, guard=6, grip=10)
    # 缺口
    put(im, 28, 18, (0, 0, 0, 0))
    put(im, 29, 18, (0, 0, 0, 0))
    return im


def scavenger_cleaver():
    return sword(52, 52, (8, 44), (44, 8), 3, SCRAP, guard=6, grip=11)


def scrap_cleaver():
    return sword(48, 48, (8, 40), (40, 8), 3, SCRAP, guard=5, grip=9)


def steel_discharger():
    im = new(48, 48)
    # 握把
    thick(im, 10, 38, 22, 26, 3, (92, 64, 42, 255))
    # 机身
    rect(im, 18, 14, 34, 30, (140, 148, 156, 255))
    rect(im, 20, 16, 32, 22, (88, 200, 210, 255))
    rect(im, 22, 18, 30, 20, (200, 240, 255, 255))
    # 枪口两根电极
    rect(im, 34, 16, 42, 18, (180, 184, 190, 255))
    rect(im, 34, 24, 42, 26, (180, 184, 190, 255))
    put(im, 43, 17, (200, 240, 255, 255))
    put(im, 43, 25, (200, 240, 255, 255))
    outline_opaque(im, (32, 34, 40, 255))
    return im


def starstring_bow():
    im = new(48, 48)
    wood = (120, 78, 46, 255)
    light = (186, 140, 78, 255)
    string = (210, 214, 220, 255)
    # C 形弓臂，开口朝右，构图跟精钢弓同一套
    thick(im, 16, 24, 14, 10, 1, wood)
    thick(im, 14, 10, 24, 6, 1, light)
    thick(im, 24, 6, 30, 12, 1, wood)
    thick(im, 16, 24, 14, 38, 1, wood)
    thick(im, 14, 38, 24, 42, 1, light)
    thick(im, 24, 42, 30, 36, 1, wood)
    thick(im, 30, 12, 36, 24, 0, string)
    thick(im, 30, 36, 36, 24, 0, string)
    rect(im, 12, 20, 20, 28, (92, 60, 36, 255))
    put(im, 36, 24, (255, 230, 140, 255))
    outline_opaque(im, (40, 26, 18, 255))
    return im


def ash_firegun():
    im = new(48, 48)
    rect(im, 8, 22, 36, 30, (118, 52, 40, 255))
    rect(im, 10, 20, 34, 24, (186, 72, 48, 255))
    rect(im, 28, 18, 40, 28, (88, 40, 32, 255))
    rect(im, 36, 20, 44, 26, (48, 24, 22, 255))
    # 枪管口一点红
    put(im, 44, 22, (255, 140, 80, 255))
    put(im, 44, 23, (255, 80, 40, 255))
    # 握把
    rect(im, 12, 30, 20, 40, (72, 40, 28, 255))
    outline_opaque(im, (40, 16, 16, 255))
    return im


def archivist_boneblade():
    im = sword(52, 52, (8, 44), (44, 8), 2, BONE, guard=5, grip=10)
    # 刃上两道骨节
    put(im, 24, 24, (120, 100, 78, 255))
    put(im, 32, 16, (120, 100, 78, 255))
    return im


WEAPONS = [
    ("FireplaceWarriorWeapon", "壁炉守卫大剑", fireplace_greatsword),
    ("FireplaceCWarrior", "炉心刃", hearth_blade),
    ("ScavengerCMage", "废料火花", scrap_spark),
    ("RustCleaver", "锈蚀砍刀", rust_cleaver),
    ("ScavengerWarriorWeapon", "清道夫废料砍刀", scavenger_cleaver),
    ("ScavengerCWarrior", "废料砍刀", scrap_cleaver),
    ("SteelDischarger", "精钢放电器", steel_discharger),
    ("StarstringBow", "星弦弓", starstring_bow),
    ("AshHeartRangerWeapon", "灰烬之心火铳", ash_firegun),
    ("ArchivistWarriorWeapon", "归档者骨刃", archivist_boneblade),
]


def zoom(im, z=4, bg=(32, 32, 36, 255)):
    big = im.resize((im.size[0] * z, im.size[1] * z), Image.NEAREST)
    canvas = Image.new("RGBA", (big.size[0] + 12, big.size[1] + 12), bg)
    canvas.paste(big, (6, 6), big)
    return canvas


def label_font(size=16):
    for path in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def contact():
    cells = [(name, zh, fn()) for name, zh, fn in WEAPONS]
    cell = 56 * 4 + 24
    cols = 5
    rows = (len(cells) + cols - 1) // cols
    canvas = Image.new("RGBA", (cols * cell, rows * (cell + 28)), (24, 24, 28, 255))
    draw = ImageDraw.Draw(canvas)
    font = label_font(16)
    for i, (name, zh, im) in enumerate(cells):
        c, r = i % cols, i // cols
        x, y = c * cell + 8, r * (cell + 28) + 8
        z = zoom(im, 4)
        canvas.paste(z, (x, y + 18), z)
        draw.text((x, y), zh, fill=(230, 230, 230, 255), font=font)
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, zh, fn in WEAPONS:
        im = fn()
        path = os.path.join(OUT, name + ".png")
        im.save(path)
        zoom(im).save(os.path.join(OUT, name + "_preview.png"))
        print("wrote", name, zh, im.size)
    contact().save(os.path.join(OUT, "contact_sheet.png"))
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as handle:
        handle.write(
            "# 武器像素稿 v1（预览，未装进游戏）\n\n"
            "先看 `contact_sheet.png`。这一版只换你点头的那几张。\n\n"
            "画法：偶数边、硬边、3~4 阶色、柄在左下刃向右上（阔剑/砍刀），"
            "弓朝右、和精钢弓同一套构图。\n"
        )
    print("preview dir", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
