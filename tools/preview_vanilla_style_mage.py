# -*- coding: utf-8 -*-
"""精钢法师套：**原版风格**版本（只做对比预览，不写进模组）。

和 `gen_armor_pixel_equip.py` 的区别 —— 也就是玩家想看的那个"区别"
--------------------------------------------------------------------
现在身上那套（批次 35/37）是**写实向**画法：
  * 部件轮廓故意画得比身体窄一点，靠"深描边 + 亮高光 + 底边阴影"做出体积；
  * 中间调 + 高光 + 阴影一共 5~6 个色阶，还有腰带、扣带、发光缝这些细节。

原版盔甲（铂金 / 木制那一类）是**符号化**画法：
  * 一整块主体色，左上受光一条、右下压暗一条，**没有内部细节**；
  * 描边不是纯黑，而是"主体色压暗一档再偏冷"；
  * 部件要**盖住**身体对应部位（宁可略大），而不是"贴着身体画"；
  * 颜色是**单一色相**（铂金全是灰蓝、木制全是棕），不堆杂色。

所以这个脚本按原版口径重画同一个法师套（同尺寸 40×1120 = 20 帧 × 56），
用来和现在那版并排比。**它只输出到 .tmp-3d/preview/，不碰 Content/。**
"""
import os

from PIL import Image

OUT_DIR = r"E:\开发\.tmp-3d\preview\vanilla_style"
FRAME_W, FRAME_H, FRAMES = 40, 56, 20

# --- 原版口径的三个分区（与穿身图生成器同一组量测值，但这里按"盖住身体"取整）---
HEAD_TOP, HEAD_H = 9, 14          # 头 y9..22
BODY_TOP, BODY_H = 19, 19         # 胸 y19..37（盖到腰）
LEG_TOP, LEG_H = 30, 22           # 腿 y30..51（塞进胸甲下面）

# 铂金那类"单色相 + 明暗两档"的调色板（法师套用紫，对齐现有套装的色系）
OUT_L = (92, 78, 150)             # 描边（主体色压暗一档，偏冷）
BASE = (140, 122, 208)            # 主体
LIGHT = (176, 160, 232)           # 左上受光
SHADE = (108, 92, 170)            # 右下压暗
ACCENT = (216, 194, 120)          # 金扣（原版法师套也常有一条金饰）


def put(c, x, y, col):
    if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
        c.putpixel((x, y), col + (255,))


def rect(c, x0, y0, x1, y1, col):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(c, x, y, col)


def shade_rect(c, x0, y0, x1, y1, fill, light, shade, outline):
    """原版那种"一块主体 + 左上亮 / 右下暗 + 冷描边"的填法。"""
    rect(c, x0, y0, x1, y1, fill)
    for x in range(x0, x1 + 1):                       # 顶边一条亮
        put(c, x, y0, light)
    for y in range(y0, y1 + 1):                       # 左边一条亮
        put(c, x0, y, light)
    for x in range(x0, x1 + 1):                       # 底边压暗
        put(c, x, y1, shade)
    for y in range(y0, y1 + 1):                       # 右边压暗
        put(c, x1, y, shade)
    for x in range(x0, x1 + 1):                       # 描边（压在亮/暗上）
        put(c, x, y0, outline)
        put(c, x, y1, outline)
    for y in range(y0, y1 + 1):
        put(c, x0, y, outline)
        put(c, x1, y, outline)


def draw_head(c, dy):
    """尖顶兜帽：一个三角形 + 下面一块方肩。原版头部通常就是"一个形状"。"""
    top = HEAD_TOP + dy
    # 三角尖顶
    for i in range(5):
        half = 1 + i
        x0, x1 = 14 - half, 15 + half
        rect(c, x0, top + i, x1, top + i, BASE)
        put(c, x0, top + i, OUT_L)
        put(c, x1, top + i, OUT_L)
        put(c, 14, top + i, LIGHT)
    # 帽檐（横条）
    shade_rect(c, 10, top + 5, 19, top + 9, BASE, LIGHT, SHADE, OUT_L)
    # 面部开口：原版不会挖洞，直接一整块压暗
    rect(c, 12, top + 6, 17, top + 9, SHADE)
    put(c, 12, top + 6, OUT_L)
    put(c, 17, top + 6, OUT_L)
    # 下巴/颈部一块，接胸甲
    shade_rect(c, 11, top + 10, 18, top + 13, BASE, LIGHT, SHADE, OUT_L)
    # 金扣
    rect(c, 14, top + 11, 15, top + 11, ACCENT)


def draw_body(c, dy):
    """长袍：一整块梯形，只在腰间收一下，底部一条金边。原版没有内部细节。"""
    top = BODY_TOP + dy
    for row in range(BODY_H):
        y = top + row
        # 肩部 13 宽，向下收窄到 11，到裙摆再放到 14
        if row < 3:
            half = 6
        elif row < 12:
            half = 5
        else:
            half = 6
        x0, x1 = 14 - half, 15 + half
        rect(c, x0, y, x1, y, BASE)
        put(c, x0, y, OUT_L)
        put(c, x1, y, OUT_L)
        put(c, x0 + 1, y, LIGHT)
        put(c, x1 - 1, y, SHADE)
    # 腰带（金）与底边压暗
    belt = top + 11
    for x in range(14 - 5, 16 + 5):
        put(c, x, belt, ACCENT)
        put(c, x, belt + 1, SHADE)
    for x in range(14 - 6, 16 + 6):
        put(c, x, top + BODY_H - 1, OUT_L)


def draw_legs(c, swing):
    """两条直筒 + 靴子。原版腿部就是两根柱子，靠整体明暗区分，不做膝盖花纹。"""
    for index, sign in enumerate((1, -1)):
        x0 = 10 + index * 8
        y0 = LEG_TOP + swing * sign
        for row in range(LEG_H):
            y = y0 + row
            rect(c, x0, y, x0 + 5, y, BASE)
            put(c, x0, y, OUT_L)
            put(c, x0 + 5, y, OUT_L)
            put(c, x0 + 1, y, LIGHT)
            put(c, x0 + 4, y, SHADE)
        # 靴口压暗 + 靴底
        for x in range(x0, x0 + 6):
            put(c, x, y0 + 14, SHADE)
            put(c, x, y0 + LEG_H - 1, OUT_L)


SWING = [0, 0, 0, 0, 0, 1, 0, -1, 0, 1, 0, -1, 0, -1, 0, 1, 0, 1, 0, -1]


def sheet(part):
    out = Image.new("RGBA", (FRAME_W, FRAME_H * FRAMES), (0, 0, 0, 0))
    for f in range(FRAMES):
        c = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        dy = 1 if f >= 12 else 0
        if part == "Head":
            draw_head(c, dy)
        elif part == "Body":
            draw_body(c, dy)
        else:
            draw_legs(c, SWING[f] + dy)
        out.alpha_composite(c, (0, f * FRAME_H))
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for part in ("Head", "Body", "Legs"):
        s = sheet(part)
        p = os.path.join(OUT_DIR, "VanillaStyleMageHood_%s.png" % part)
        s.save(p)
        print("写出 %s  %dx%d" % (p, s.width, s.height))

    # 并排对比：左 = 现在的写实向，右 = 原版口径
    cur_dir = r"E:\开发\WastelandSoul\Content\Items\Armor"
    cur = ("SalvagedSteelMageHood", "SalvagedSteelMageRobe", "SalvagedSteelMageLeggings")
    new = tuple(os.path.join(OUT_DIR, "VanillaStyleMageHood_%s.png" % p)
                for p in ("Head", "Body", "Legs"))
    sc, frames = 8, [0, 5, 6, 7]
    tw, th = FRAME_W * sc, FRAME_H * sc
    img = Image.new("RGBA", ((tw + 10) * len(frames) * 2 + 30, (th + 8) * 2),
                    (26, 28, 34, 255))

    # 人物底色（皮肤色），用来看两版各自**盖住了多少身体**
    body = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    for x0, y0, x1, y1 in ((13, 9, 24, 23), (10, 23, 25, 38), (12, 38, 24, 53)):
        rect(body, x0, y0, x1, y1, (222, 201, 156))

    for side, (folder, names) in enumerate(((cur_dir, cur), (OUT_DIR, new))):
        for i, fr in enumerate(frames):
            tile = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
            for part, nm in zip(("Head", "Body", "Legs"), names):
                path = nm if nm.endswith(".png") else os.path.join(folder, "%s_%s.png" % (nm, part))
                tile.alpha_composite(Image.open(path).convert("RGBA")
                                     .crop((0, fr * FRAME_H, FRAME_W, (fr + 1) * FRAME_H)))
            x = side * ((tw + 10) * len(frames) + 30) + i * (tw + 10)
            # 上排 = 裸人物 + 盔甲，下排 = 只有盔甲（看轮廓）
            bare = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
            bare.alpha_composite(body)
            bare.alpha_composite(tile)
            img.alpha_composite(bare.resize((tw, th), Image.NEAREST), (x, 0))
            img.alpha_composite(tile.resize((tw, th), Image.NEAREST), (x, th + 8))

    out = r"E:\开发\.tmp-3d\preview\mage_vanilla_vs_current.png"
    img.save(out)
    print("对比预览 %s" % out)
    print("  上排 = 人物底色 + 盔甲（看盖没盖住 / 露不露身色）")
    print("  下排 = 只有盔甲（看轮廓）")
    print("  左 4 帧 = 现在这版（批次 37）　右 4 帧 = 原版口径的版本")


if __name__ == "__main__":
    main()
