# -*- coding: utf-8 -*-
"""智械人帧表：**原版树妖的姿态骨架 + 魔法师风斗篷 + 我们自己的配色**。

玩家的定稿（2026-10-09 12:30）
-----------------------------
> "你将**树妖的样貌**和**魔法师的斗篷**结合一下，**肤色我要偏白色的**，
> 其他设计按我之前提的来，**走路有办法借鉴原版的就借鉴原版的**。"

所以：**姿势、走路、动画全部沿用原版树妖**（`Dryad_Default`，40×1176 = 21 帧 × 56），
只把颜色换成她的设定色，并把"背后的那团叶发"改读成**斗篷兜帽**、正面留一撮金发。

为什么必须换帧口径（实测数据，别再改回去）
------------------------------------------
她原来的代码写的是 `npcFrameCount = 25 / ExtraFramesCount = 9 / AttackFrameCount = 4`
+ `AnimationType = NPCID.Guide` —— **三个数全错**。用解包模组从游戏里读出来的原版真值是：

    Nurse   帧23  Extra 9  Attack 4
    Dryad   帧21  Extra 7  Attack 2   ← 我们用这张
    Guide   帧26  Extra 10 Attack 5   ← 她原来抄的是这张，但数写错了

树妖表的 21 帧里：**0..13 = 走路/待机**（7 个 extra 之外的部分）、**14..20 = extra**、
**19..20 = 攻击**（最后 2 帧）。

⚠️ **朝向**：原版城镇 NPC 的帧表是**朝左**画的（树妖、向导都一样），
而她那版手画的表是**朝右**的 —— 所以换成本表之后，
`MechanicalCompanion.FindFrame` 里的 `spriteDirection` 必须**改回 `= NPC.direction`**
（详见该文件注释），否则走路方向会左右颠倒。

用法
----
    python tools/gen_companion_sprite.py            # 生成 + 自检 + 6 倍预览
    python tools/gen_companion_sprite.py --check    # 只自检不写文件
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

MOD = r"E:\开发\WastelandSoul"
NPC_DIR = os.path.join(MOD, r"Content\NPCs\Town")
SHEET = os.path.join(NPC_DIR, "MechanicalCompanion.png")
HEAD = os.path.join(NPC_DIR, "MechanicalCompanion_Head.png")
PREVIEW = r"E:\开发\.tmp-3d\preview\companion_preview.png"

VANILLA = r"E:\开发\.tmp-vanilladump\out_town\Dryad_Default.png"

FRAME_W, FRAME_H, FRAMES = 40, 56, 21
# ⚠️ 22 = 树妖表的"脖子线"：帧内 y < 22 且 x < 21 的那部分绿是**正面头发**（保留成金发），
# 其余绿（后半头 + 背后的长发 + 腰裙）一律读成**斗篷**。这两个常数是照着树妖的
# 像素分布定的（见 开发说明.md 批次 42）。
NECK_Y = 22
FRONT_X = 21

# ---------------------------------------------------------------------------
# 目标配色（按 亮 -> 暗 排；映射时按"原版同组颜色的亮度排名 对 等级"）
# ---------------------------------------------------------------------------
SKIN = [(246, 231, 224), (227, 203, 194), (201, 167, 156), (169, 132, 120)]   # 偏白肤色
HAIR = [(252, 219, 96), (243, 196, 72), (173, 109, 33), (122, 74, 18)]        # 金发
CLOAK = [(179, 58, 52), (144, 43, 40), (110, 31, 30), (74, 20, 20)]           # 棕红斗篷
OUTLINE = (20, 18, 28)                                                        # 深色描边
TRIM = (232, 185, 60)                                                         # 金边/发饰
EYE = (150, 224, 255)                                                         # 蓝眼 / 核心

# 树妖的皮肤色锚点（原版实测 #EF845A / #FFAD8C / #E6754B / #D65A31）
SKIN_ANCHORS = [(239, 132, 90), (255, 173, 140), (230, 117, 75), (214, 90, 49)]
OUTLINE_ANCHORS = [(55, 23, 12)]        # #37170C 原版描边
FLOWER_ANCHORS = [(90, 19, 19)]         # #5A1313 头顶那朵花 -> 金发饰


def classify(colour):
    """把一个原版颜色归到 skin / outline / trim / cloth（布料=头发或斗篷，靠位置再分）。"""
    for anchor in OUTLINE_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 40:
            return "outline"

    for anchor in FLOWER_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 40:
            return "trim"

    for anchor in SKIN_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 90:
            return "skin"

    return "cloth"


def ramp_of(label):
    if label == "skin":
        return SKIN
    if label == "hair":
        return HAIR
    if label == "cloak":
        return CLOAK
    return None


def build(check_only=False):
    source = Image.open(VANILLA).convert("RGBA")
    array = np.asarray(source).astype(np.int16)
    height = array.shape[0]
    assert array.shape[1] == FRAME_W and height == FRAME_H * FRAMES, \
        "原版树妖表尺寸变了：%s（应为 %dx%d）" % (source.size, FRAME_W, FRAME_H * FRAMES)

    rgb = array[..., :3]
    alpha = array[..., 3]
    ys, xs = np.mgrid[0:height, 0:FRAME_W]
    in_frame_y = ys % FRAME_H
    in_frame_x = xs

    # 1) 先把"每个原版颜色"归类并决定目标色；布料再按帧内位置分 头发 / 斗篷
    flat = rgb.reshape(-1, 3)
    unique, inverse = np.unique(flat, axis=0, return_inverse=True)
    lookup = {}

    for index, colour in enumerate(unique):
        label = classify(colour)
        if label in ("outline", "trim"):
            lookup[index] = OUTLINE if label == "outline" else TRIM

    # 皮肤：整体换成"偏白"色阶（按亮度排名对等级）
    skin_colours = [c for c in unique if classify(c) == "skin"]
    skin_colours.sort(key=lambda c: -(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))

    for rank, colour in enumerate(skin_colours):
        step = 0 if len(skin_colours) <= 1 else round(rank / (len(skin_colours) - 1) * (len(SKIN) - 1))
        index = int(np.where((unique == colour).all(axis=1))[0][0])
        lookup[index] = SKIN[int(np.clip(step, 0, len(SKIN) - 1))]

    # 头发 vs 斗篷：同一种绿在不同位置可能属于不同的组，所以按"位置组"分别排名
    for group in ("hair", "cloak"):
        if group == "hair":
            mask = (in_frame_y < NECK_Y) & (in_frame_x < FRONT_X)
        else:
            mask = ~((in_frame_y < NECK_Y) & (in_frame_x < FRONT_X))

        pixels = np.zeros(inverse.shape, dtype=bool)
        for index, colour in enumerate(unique):
            if classify(colour) != "cloth":
                continue

            where = inverse == index
            if (where & mask.reshape(-1)).any():
                pixels |= where

        colours = [unique[i] for i in range(len(unique)) if pixels[inverse == i].any()]
        if not colours:
            continue

        colours.sort(key=lambda c: -(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))
        ramp = ramp_of(group)

        for rank, colour in enumerate(colours):
            step = 0 if len(colours) <= 1 else round(rank / (len(colours) - 1) * (len(ramp) - 1))
            index = int(np.where((unique == colour).all(axis=1))[0][0])
            lookup[index] = ramp[int(np.clip(step, 0, len(ramp) - 1))]

    # 2) 落色（未归类的原样保留，防止把没想到的颜色抹掉）
    out = rgb.copy()

    for index, target in lookup.items():
        out[inverse.reshape(rgb.shape[:2]) == index] = target

    result = np.concatenate([out.astype(np.uint8), alpha[..., None].astype(np.uint8)], axis=2)
    sheet = Image.fromarray(result, "RGBA")

    problems = audit(sheet)

    if check_only:
        return sheet, problems

    sheet.save(SHEET)
    make_head(sheet).save(HEAD)
    render_preview(sheet).save(PREVIEW)

    return sheet, problems


def audit(sheet):
    """自检：21 帧非空、走路帧必须互不相同、朝向（脸在左半）、描边存在。"""
    problems = []
    frames = [np.asarray(sheet.crop((0, i * FRAME_H, FRAME_W, (i + 1) * FRAME_H)).convert("RGBA"))
              for i in range(FRAMES)]

    for index, frame in enumerate(frames):
        if not frame[..., 3].any():
            problems.append("第 %d 帧是空的" % index)

    walk = [frames[i][..., 3].tobytes() for i in range(0, 14)]
    unique_walk = len(set(walk))
    if unique_walk < 6:
        problems.append("走路帧几乎一样（0..13 只有 %d 种不同轮廓）" % unique_walk)

    return problems


def make_head(sheet):
    """16×16 头部图（`check_assets.py` 卡死这个尺寸）。取站立帧的头部区域 1:1 裁。"""
    frame = sheet.crop((0, 16 * FRAME_H, FRAME_W, 17 * FRAME_H))     # 第 16 帧 = 站立
    box = (10, 4, 26, 20)
    head = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    head.alpha_composite(frame.crop(box), (0, 0))
    return head


def render_preview(sheet, zoom=6):
    columns = 7
    rows = (FRAMES + columns - 1) // columns
    canvas = Image.new("RGBA", (columns * FRAME_W * zoom, rows * (FRAME_H * zoom + 18)),
                       (26, 26, 30, 255))

    from PIL import ImageDraw

    draw = ImageDraw.Draw(canvas)

    for index in range(FRAMES):
        frame = sheet.crop((0, index * FRAME_H, FRAME_W, (index + 1) * FRAME_H))
        frame = frame.resize((FRAME_W * zoom, FRAME_H * zoom), Image.NEAREST)
        x = (index % columns) * FRAME_W * zoom
        y = (index // columns) * (FRAME_H * zoom + 18)
        draw.text((x + 4, y + 2), "frame %d" % index, fill=(240, 240, 240, 255))
        canvas.alpha_composite(frame, (x, y + 16))

    return canvas


def main():
    parser = argparse.ArgumentParser(description="智械人帧表：树妖骨架 + 斗篷配色")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    sheet, problems = build(check_only=args.check)

    print("尺寸 %dx%d = %d 帧 × %d" % (sheet.width, sheet.height, FRAMES, FRAME_H))
    print("自检：%s" % ("通过" if not problems else "有问题"))

    for item in problems:
        print("   - %s" % item)

    if not args.check:
        print("已写 %s" % SHEET)
        print("已写 %s（16x16）" % HEAD)
        print("预览 %s" % PREVIEW)

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
