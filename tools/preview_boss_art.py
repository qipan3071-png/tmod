# -*- coding: utf-8 -*-
"""Boss 像素稿预览：只写到「开发预览」，不覆盖模组目录。

灰烬之心：四棱水晶 + 周围碎晶，略泛红。
壁炉守卫：落地机械骑士，约石巨人 1.3 倍（原版碰撞 140 → 182），双腿，盔内黑色单红眼。
归档者：机械法师坐在悬浮杖上，紫金翻开书，白兜帽，黑眼罩。

风格：有限色阶、1px 深色描边、硬边、不过度细节。朝左（原版 NPC 约定）。
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "开发预览", "boss-art-v1")

OUTLINE = (28, 22, 26, 255)


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, c):
    if 0 <= x < im.size[0] and 0 <= y < im.size[1] and len(c) == 4:
        im.putpixel((x, y), c)


def rect(im, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(im, x, y, c)


def diamond(im, cx, cy, rx, ry, fill, left=None, right=None):
    left = left or fill
    right = right or fill
    for y in range(-ry, ry + 1):
        t = 1.0 - abs(y) / float(max(ry, 1))
        w = int(round(rx * t))
        for x in range(-w, w + 1):
            put(im, cx + x, cy + y, left if x < 0 else right)


def outline_opaque(im, color=OUTLINE):
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


def copy_onto(dst, src, ox, oy):
    dst.alpha_composite(src, (ox, oy))


def trap(im, y0, y1, x0t, x1t, x0b, x1b, c):
    """上下底不同的梯形，用来做盔沿、披风、腿。"""
    for y in range(y0, y1 + 1):
        t = 0 if y1 == y0 else (y - y0) / float(y1 - y0)
        xa = int(round(x0t + (x0b - x0t) * t))
        xb = int(round(x1t + (x1b - x1t) * t))
        if xa > xb:
            xa, xb = xb, xa
        for x in range(xa, xb + 1):
            put(im, x, y, c)


def dots(im, pairs, c):
    for x, y in pairs:
        put(im, x, y, c)


# ---------------------------------------------------------------------------
# 灰烬之心
# ---------------------------------------------------------------------------
AH_CORE = (255, 118, 86, 255)
AH_MID = (196, 52, 44, 255)
AH_DARK = (118, 28, 32, 255)
AH_DEEP = (72, 16, 22, 255)
AH_GLOW = (255, 168, 120, 255)
AH_SPARK = (255, 210, 170, 255)

AH_W, AH_H, AH_FRAMES = 96, 110, 4


def ash_frame(index):
    im = new(AH_W, AH_H)
    cx, cy = 48, 56
    pulse = (0, 1, 2, 1)[index]
    diamond(im, cx, cy, 20 + pulse, 32 + pulse, AH_MID, AH_DARK, AH_CORE)
    diamond(im, cx - 1, cy - 2, 8 + pulse, 14, AH_CORE, AH_MID, AH_GLOW)
    # 四棱：中脊 + 一条略偏的横棱，不要画成十字准星
    for y in range(cy - 30, cy + 31):
        put(im, cx, y, AH_DEEP)
    for x in range(cx - 14, cx + 15):
        put(im, x, cy + 1, AH_DEEP)
    # 一处裂痕
    for i in range(6):
        put(im, cx + 4 + i // 2, cy - 10 + i, AH_DEEP)

    shards = [
        (-30, -16, 4, 7),
        (28, -20, 5, 8),
        (-26, 22, 4, 6),
        (26, 18, 4, 5),
        (-6, -38, 3, 4),
        (12, 38, 3, 5),
        (-36, 4, 3, 4),
        (34, -2, 3, 4),
        (20, 30, 2, 3),
    ]
    for i, (dx, dy, rx, ry) in enumerate(shards):
        ox = dx + ((i + index) % 3 - 1)
        oy = dy + ((i + index // 2) % 2)
        diamond(im, cx + ox, cy + oy, rx, ry, AH_MID, AH_DEEP, AH_CORE)

    if index % 2 == 0:
        dots(im, [(cx - 5, cy - 18), (cx + 9, cy + 10), (cx - 14, cy + 2)], AH_SPARK)
    outline_opaque(im, (48, 10, 14, 255))
    return im


def ash_sheet():
    sheet = new(AH_W, AH_H * AH_FRAMES)
    for i in range(AH_FRAMES):
        copy_onto(sheet, ash_frame(i), 0, i * AH_H)
    return sheet


# ---------------------------------------------------------------------------
# 壁炉守卫（落地骑士）
# 石巨人碰撞约 140；1.3 倍 ≈ 182。帧 184×240，双腿着地。
# ---------------------------------------------------------------------------
ST_L = (186, 188, 192, 255)
ST = (128, 132, 138, 255)
ST_D = (78, 80, 86, 255)
ST_K = (48, 50, 56, 255)
SOOT = (28, 26, 30, 255)
EYE = (220, 42, 38, 255)
EYE_D = (120, 18, 20, 255)
EMBER = (168, 64, 36, 255)
BRASS = (168, 124, 52, 255)

FG_W, FG_H, FG_FRAMES = 184, 240, 6


def plate(im, x0, y0, x1, y1, light=ST_L, mid=ST, dark=ST_D):
    rect(im, x0, y0, x1, y1, mid)
    rect(im, x0, y0, x0 + 1, y1, light)
    rect(im, x0, y0, x1, y0 + 1, light)
    rect(im, x1 - 1, y0, x1, y1, dark)
    rect(im, x0, y1 - 1, x1, y1, dark)


def fireplace_frame(index):
    im = new(FG_W, FG_H)
    walk = index % 4
    lk = (0, 8, 0, -8)[walk]
    rk = (0, -8, 0, 8)[walk]
    bob = (0, -1, 0, 1, 0, -1)[index]
    punch = 10 if index == 5 else 0

    fy = 220 + bob
    # 脚
    trap(im, fy, fy + 12, 58 + lk, 82 + lk, 52 + lk, 88 + lk, ST_D)
    trap(im, fy, fy + 12, 108 + rk, 132 + rk, 102 + rk, 138 + rk, ST_K)
    rect(im, 54 + lk, fy + 10, 86 + lk, fy + 14, ST_K)
    rect(im, 104 + rk, fy + 10, 136 + rk, fy + 14, SOOT)

    # 小腿
    trap(im, 184 + bob, fy, 66 + lk, 82 + lk, 62 + lk, 84 + lk, ST)
    trap(im, 184 + bob, fy, 114 + rk, 130 + rk, 110 + rk, 132 + rk, ST_D)
    rect(im, 64 + lk, 178 + bob, 84 + lk, 186 + bob, ST_L)
    rect(im, 112 + rk, 178 + bob, 132 + rk, 186 + bob, ST)

    # 大腿
    trap(im, 142 + bob, 180 + bob, 74 + lk // 2, 94 + lk // 2, 66 + lk, 86 + lk, ST)
    trap(im, 142 + bob, 180 + bob, 100 + rk // 2, 120 + rk // 2, 110 + rk, 130 + rk, ST_D)

    # 腰
    trap(im, 128 + bob, 146 + bob, 70, 122, 66, 126, ST)
    rect(im, 86, 132 + bob, 104, 142 + bob, BRASS)

    # 胸甲 + 小炉口
    trap(im, 78 + bob, 130 + bob, 62, 130, 70, 122, ST)
    trap(im, 82 + bob, 124 + bob, 66, 126, 74, 118, ST_L)
    rect(im, 88, 98 + bob, 104, 114 + bob, SOOT)
    rect(im, 92, 102 + bob, 100, 110 + bob, EMBER)
    put(im, 95, 105 + bob, EYE)
    put(im, 96, 105 + bob, EYE)

    # 肩
    trap(im, 70 + bob, 96 + bob, 44, 72, 40, 70, ST_L)
    trap(im, 70 + bob, 96 + bob, 120, 148, 122, 152, ST_D)

    # 左臂朝左
    trap(im, 94 + bob, 148 + bob, 42 - punch, 62 - punch, 36 - punch, 58 - punch, ST)
    trap(im, 146 + bob, 170 + bob, 34 - punch, 56 - punch, 30 - punch, 54 - punch, ST_D)
    # 右臂
    trap(im, 94 + bob, 148 + bob, 128, 150, 132, 154, ST_D)
    trap(im, 146 + bob, 170 + bob, 134, 154, 138, 156, ST_K)

    # 桶盔：面甲是一条黑缝，里面一颗小红眼
    trap(im, 24 + bob, 76 + bob, 80, 116, 74, 122, ST)
    trap(im, 18 + bob, 30 + bob, 88, 108, 80, 116, ST_L)
    rect(im, 78, 48 + bob, 116, 60 + bob, SOOT)
    rect(im, 80, 50 + bob, 114, 58 + bob, (8, 6, 8, 255))
    rect(im, 86, 52 + bob, 92, 57 + bob, EYE_D)
    rect(im, 87, 53 + bob, 90, 56 + bob, EYE)
    put(im, 89, 54 + bob, (255, 190, 170, 255))
    dots(im, [(70, 100 + bob), (118, 108 + bob), (76, 150 + bob), (110, 168 + bob)], ST_K)

    outline_opaque(im, SOOT)
    return im


def fireplace_sheet():
    sheet = new(FG_W, FG_H * FG_FRAMES)
    for i in range(FG_FRAMES):
        copy_onto(sheet, fireplace_frame(i), 0, i * FG_H)
    return sheet


# ---------------------------------------------------------------------------
# 归档者
# ---------------------------------------------------------------------------
HOOD = (236, 236, 230, 255)
HOOD_M = (196, 196, 190, 255)
HOOD_D = (148, 148, 142, 255)
MECH = (118, 114, 126, 255)
MECH_D = (70, 66, 78, 255)
MECH_K = (44, 42, 52, 255)
PATCH = (22, 20, 24, 255)
BOOK_P = (96, 46, 122, 255)
BOOK_P2 = (72, 32, 96, 255)
BOOK_G = (204, 164, 58, 255)
BOOK_PAGE = (232, 220, 196, 255)
STAFF = (92, 86, 102, 255)
STAFF_L = (140, 132, 148, 255)
GEM = (160, 72, 196, 255)

AR_W, AR_H, AR_FRAMES = 112, 148, 4


def archivist_frame(index):
    im = new(AR_W, AR_H)
    bob = (0, -2, 0, 2)[index]
    page = 2 if index == 2 else 0
    sy = 124 + bob

    # 1. 横杖（先画，人坐上面）
    rect(im, 8, sy, 102, sy + 4, STAFF)
    rect(im, 8, sy, 102, sy + 1, STAFF_L)
    trap(im, sy - 10, sy + 12, 90, 104, 88, 106, MECH)
    rect(im, 92, sy - 6, 102, sy + 8, GEM)
    put(im, 96, sy, (220, 160, 240, 255))
    rect(im, 6, sy - 2, 14, sy + 7, MECH_D)

    # 2. 机械腿盘坐在杖上
    trap(im, 98 + bob, sy - 2, 34, 50, 26, 48, MECH_D)
    trap(im, 98 + bob, sy - 2, 56, 76, 60, 84, MECH)
    rect(im, 26, sy - 4, 44, sy - 1, MECH_K)
    rect(im, 64, sy - 4, 84, sy - 1, MECH_D)

    # 3. 机械躯干（披风只盖肩，不盖全身）
    trap(im, 62 + bob, 102 + bob, 44, 72, 40, 76, MECH)
    trap(im, 66 + bob, 96 + bob, 48, 68, 46, 70, MECH_D)
    rect(im, 52, 76 + bob, 64, 84 + bob, MECH_K)
    dots(im, [(48, 88 + bob), (66, 92 + bob)], MECH_K)

    # 4. 白兜帽：巫师尖顶 + 短披肩，脸要露出来
    trap(im, 8 + bob, 36 + bob, 52, 62, 42, 72, HOOD)
    trap(im, 34 + bob, 44 + bob, 40, 74, 38, 76, HOOD)
    trap(im, 42 + bob, 58 + bob, 38, 76, 36, 78, HOOD_M)
    # 披肩只到肩
    trap(im, 56 + bob, 72 + bob, 36, 78, 40, 74, HOOD_D)

    # 5. 面部：无眼，一条黑眼罩
    rect(im, 46, 40 + bob, 68, 56 + bob, MECH_K)
    rect(im, 44, 46 + bob, 70, 54 + bob, PATCH)
    rect(im, 46, 48 + bob, 68, 52 + bob, (8, 6, 10, 255))

    # 6. 翻开的紫金书画在最前，盖在怀里
    bx, by = 36, 70 + bob
    rect(im, bx, by, bx + 18, by + 18, BOOK_P2)
    rect(im, bx + 18, by, bx + 36 + page, by + 18, BOOK_P)
    rect(im, bx, by, bx + 36 + page, by + 2, BOOK_G)
    rect(im, bx, by + 16, bx + 36 + page, by + 18, BOOK_G)
    rect(im, bx + 17, by, bx + 19, by + 18, BOOK_G)
    rect(im, bx + 3, by + 4, bx + 16, by + 15, BOOK_PAGE)
    rect(im, bx + 20, by + 4, bx + 33 + page, by + 15, BOOK_PAGE)
    # 手按书边
    rect(im, bx - 5, by + 10, bx, by + 16, MECH)
    rect(im, bx + 36 + page, by + 10, bx + 41 + page, by + 16, MECH)

    outline_opaque(im, (30, 26, 34, 255))
    return im


def archivist_sheet():
    sheet = new(AR_W, AR_H * AR_FRAMES)
    for i in range(AR_FRAMES):
        copy_onto(sheet, archivist_frame(i), 0, i * AR_H)
    return sheet


def zoom(im, z=4, bg=(32, 32, 36, 255)):
    big = im.resize((im.size[0] * z, im.size[1] * z), Image.NEAREST)
    canvas = Image.new("RGBA", (big.size[0] + 16, big.size[1] + 16), bg)
    canvas.paste(big, (8, 8), big)
    return canvas


def framestrip(frames, z=2, bg=(32, 32, 36, 255)):
    zoomed = [fr.resize((fr.size[0] * z, fr.size[1] * z), Image.NEAREST) for fr in frames]
    gap = 8
    w = sum(im.size[0] for im in zoomed) + gap * (len(zoomed) + 1)
    h = max(im.size[1] for im in zoomed) + 16
    canvas = Image.new("RGBA", (w, h), bg)
    x = gap
    for im in zoomed:
        canvas.paste(im, (x, 8), im)
        x += im.size[0] + gap
    return canvas


def label_font(size=16):
    for path in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def contact_sheet():
    a = zoom(ash_frame(0), 3)
    k = zoom(fireplace_frame(0), 2)
    r = zoom(archivist_frame(0), 3)
    w = a.size[0] + k.size[0] + r.size[0] + 48
    h = max(a.size[1], k.size[1], r.size[1]) + 40
    canvas = Image.new("RGBA", (w, h), (24, 24, 28, 255))
    draw = ImageDraw.Draw(canvas)
    font = label_font(16)
    x = 12
    for img, name in ((a, "灰烬之心"), (k, "壁炉守卫"), (r, "归档者")):
        draw.text((x, 6), name, fill=(230, 230, 230, 255), font=font)
        canvas.paste(img, (x, 28), img)
        x += img.size[0] + 12
    return canvas


def head_icon(frame, box):
    crop = frame.crop(box)
    return crop.resize((40, 40), Image.NEAREST)


def write(img, rel):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", rel, img.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    ash = ash_sheet()
    knight = fireplace_sheet()
    mage = archivist_sheet()
    write(ash, "AshHeart/AshHeart.png")
    write(zoom(ash_frame(0)), "AshHeart/AshHeart_preview.png")
    write(framestrip([ash_frame(i) for i in range(AH_FRAMES)], 3), "AshHeart/AshHeart_frames.png")
    write(head_icon(ash_frame(0), (24, 20, 72, 80)), "AshHeart/AshHeart_Head_Boss.png")
    write(knight, "FireplaceGuardian/FireplaceGuardian.png")
    write(zoom(fireplace_frame(0), 2), "FireplaceGuardian/FireplaceGuardian_preview.png")
    write(framestrip([fireplace_frame(i) for i in range(FG_FRAMES)], 1), "FireplaceGuardian/FireplaceGuardian_frames.png")
    write(head_icon(fireplace_frame(0), (70, 18, 124, 80)), "FireplaceGuardian/FireplaceGuardian_Head_Boss.png")
    write(mage, "Archivist/Archivist.png")
    write(zoom(archivist_frame(0), 3), "Archivist/Archivist_preview.png")
    write(framestrip([archivist_frame(i) for i in range(AR_FRAMES)], 2), "Archivist/Archivist_frames.png")
    write(head_icon(archivist_frame(0), (36, 10, 78, 64)), "Archivist/Archivist_Head_Boss.png")
    write(contact_sheet(), "contact_sheet.png")

    readme = os.path.join(OUT, "README.md")
    with open(readme, "w", encoding="utf-8") as handle:
        handle.write(
            "# Boss 像素稿 v1（预览，未装进游戏）\n\n"
            "这一版**只放在本文件夹**。觉得哪张能用，再说换进模组。\n\n"
            "## 灰烬之心\n"
            "- 四棱水晶（菱形 + 中脊/横棱），周围一圈碎晶\n"
            "- 略泛红，只有碎光点，没有光柱\n"
            "- 帧表 96×110 × 4（脉冲）\n\n"
            "## 壁炉守卫\n"
            "- 机械骑士，**双腿着地，不悬浮**\n"
            "- 体量按石巨人 140 的 1.3 倍：帧 184×240（约 182 宽）\n"
            "- 盔内黑色，一颗红眼；胸甲一块炉心，细节压着\n"
            "- 6 帧：走 4 步 + 待机/抬手\n"
            "- 若采用：代码里要关 `noGravity` 悬停，改成落地走\n\n"
            "## 归档者\n"
            "- 机械法师坐在**会悬浮的杖**上\n"
            "- 白兜帽、机械身、黑眼罩（没有眼睛）\n"
            "- 手里一本翻开的紫金皮书\n"
            "- 帧表 112×148 × 4（上下漂 + 翻页）\n\n"
            "每张有 `_preview`（放大静帧）和 `_frames`（分帧横条）。\n"
            "武器贴图另开 `开发预览/weapon-art-v1`。\n"
        )
    print("preview dir", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
