# -*- coding: utf-8 -*-
"""智械人**试用稿**：新配色（黄绿发 / 青蓝瞳 / 橙肤）+ 穿**法师的紫袍**。

玩家口径（2026-10-09）
--------------------
| 用途 | 值 |
| --- | --- |
| 头发 | `#F9FF56`（黄绿，取色器截图） |
| 瞳孔 | `#24E1FF`（青蓝） |
| 肤色 | `#FF914E`（橙） |
| 衣服 | "**先扒 NPC 法师的**" + "**尖帽不用扒**" ⇒ 只要那件紫袍，不要尖帽 |

骨架不变（还是 `Dryad_Default` 的 21 帧 × 56 走路/待机/攻击帧）⇒
**帧表尺寸、帧口径、`AnimationType = NPCID.Dryad` 全都不用动。**

⚠️ 两个查出来的实情（决定了这版怎么做）
------------------------------------
1. **NPC 巫师那张表里，袍子被他的大胡子挡掉了一大半**：实测 `Wizard_Default.png` 里
   紫像素只在 `y 20..25`（领口/肩）和 `y 32..55`（袍摆），中间全是胡子/脸/手。
   所以"把他的袍子整件抠下来贴上去"这条路走不通（第一版硬贴，预览里就是一堆紫补丁）。
2. 所以这版改成**用他的袍子色阶去染她的衣服**：把巫师身上那件紫袍的**6 档紫**抽出来
   （`#C785F4 → #310D4B`，见 `WIZARD_ROBE_RAMP`），
   然后**只染她身上"本来是衣服"的像素**（躯干/腰/裙 + 腿上的叶饰），**露出来的皮肤保持橙色**。
   ⇒ 视觉上就是"她穿上了这件紫袍"，而且不存在"袍子被胡子挖了洞"的问题。

怎么区分"衣服"和"皮肤"
--------------------
树妖的藤衣是**绿 + 肤色混着**的（露脐装），腿上有绿叶。所以判据是：
`帧内 y ≥ ROBE_Y0`（脖子以下）**且** 原像素**不是皮肤色** ⇒ 这些才是衣服/叶饰，染紫。
皮肤（脸、胳膊、腿）一个像素都不动，免得把腿染成紫的。

用法
----
    python tools/gen_companion_wizard_demo.py           # 生成试用稿 + 6 倍预览
    python tools/gen_companion_wizard_demo.py --install # 顺便写进模组目录（想实机看再开）
    python tools/gen_companion_wizard_demo.py --check   # 只看自检，不写文件

⚠️ 改这个文件**别用 PowerShell 的 Get-Content/Set-Content**：PS 5.1 会按 GBK 读 UTF-8，
   中文注释会变乱码并直接语法报错（这一轮踩过）。用 write/edit 工具，或用 Python 读写。
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

MOD = r"E:\开发\WastelandSoul"
NPC_DIR = os.path.join(MOD, r"Content\NPCs\Town")
REPO_SHEET = r"E:\开发\art-inbox\companion_wizard_demo.png"
REPO_HEAD = r"E:\开发\art-inbox\companion_wizard_demo_Head.png"
PREVIEW = r"E:\开发\.tmp-3d\preview\companion_wizard_demo.png"

DRYAD = r"E:\开发\.tmp-vanilladump\out_town\Dryad_Default.png"
WIZARD = r"E:\开发\.tmp-vanilladump\out_town\Wizard_Default.png"
# 巫师袍的**完整版**（`Wizard robe` 的装备图）。NPC 身上那件被他的胡子挡掉一大半，
# 抠不出一件整袍 —— 所以袍身用这张表里的一格当版型。
ROBE_SHEET = r"E:\开发\.tmp-vanilladump\out\Armor_Body_15.png"

FRAME_W, FRAME_H, FRAMES = 40, 56, 21

# 玩家给的色号
HAIR_BASE = (0xF9, 0xFF, 0x56)
SKIN_BASE = (0xFF, 0x91, 0x4E)
PUPIL = (0x24, 0xE1, 0xFF)
SCLERA = (240, 252, 255)

# 色阶（亮 -> 暗）：基色放在中间偏亮那一档，其余按基色明暗推
SKIN = [(255, 190, 150), SKIN_BASE, (214, 106, 52), (168, 74, 34)]
HAIR = [(255, 255, 150), HAIR_BASE, (196, 219, 42), (140, 162, 20)]

# **巫师那件紫袍自己的 6 档紫**（从 Wizard_Default.png 里量出来的，按亮度排）。
# ⚠️ 这是 2026-10-09 第一版的袍色；玩家当天改成"**白色 + 亮黄边**"，见下面的 ROBE_PALETTE。
WIZARD_ROBE_RAMP = [
    (199, 133, 244),   # #C785F4
    (173, 96, 226),    # #AD60E2
    (149, 48, 217),    # #9530D9
    (130, 36, 194),    # #8224C2
    (110, 30, 164),    # #6E1EA4
    (72, 20, 108),     # #48146C
    (49, 13, 75),      # #310D4B
]

# 玩家 2026-10-09（看着上面的紫袍预览说）："**把袍子改成白色＋亮黄边**"
# ⚠️ 试过"按亮度把版型的深蓝摊到白色阶"：那件蓝袍亮度范围太窄（lum 22..110），
#    摊出来是一件**灰袍**。所以最终改成**直接上色**：袍身纯白、轮廓一圈亮黄。
ROBE_BODY = (255, 255, 255)     # 白袍身
ROBE_TRIM = (253, 209, 77)      # 亮黄边 #FDD14D（取自巫师帽子上的星）
# 上面这套色阶保留给"以后想按亮度做明暗"时用；当前实现只取 ROBE_BODY / ROBE_TRIM。
ROBE_PALETTE = [
    (253, 209, 77),    # #FDD14D 亮黄
    (255, 246, 214),   # #FFF6D6 暖白高光
    (255, 255, 255),   # #FFFFFF 白
    (238, 234, 226),   # #EEEAE2
    (214, 208, 198),   # #D6D0C6
    (178, 171, 160),   # #B2ABA0
    (124, 118, 110),   # #7C766E
]

OUTLINE = (28, 24, 26)

# 原版锚点（实测）
SKIN_ANCHORS = [(239, 132, 90), (255, 173, 140), (230, 117, 75), (214, 90, 49)]
OUTLINE_ANCHORS = [(55, 23, 12)]
FLOWER_ANCHORS = [(242, 67, 67), (246, 131, 131), (244, 99, 99)]
EYE_ANCHORS = [(75, 8, 132)]
SCLERA_ANCHORS = [(247, 247, 247)]

HEAD_Y = 23          # 帧内 y ≤ 23 = 头（头发区）
BACK_X = 28          # 帧内 x ≥ 28 = 背后那一片长发
ROBE_Y0 = 30         # 帧内 y ≥ 30 才可能是"衣服"（脖子以下）
ROBE_SHADE_Y = 44    # 帧内 y ≥ 44 的衣服压深一档（当裙摆阴影）
ROBE_MAIN = (110, 30, 164)      # 巫师袍主色 #6E1EA4
ROBE_SHADE = (72, 20, 108)      # 巫师袍暗档 #48146C
ROBE_CELL = (0, 0)              # 袍子版型取哪一格
ROBE_DROP = 4                   # 袍子版型整体平移的行数（正数=往下）
ROBE_XOFF = 0                   # 左右平移的列数
ROBE_WIDE = 2                   # 袍子向左右各**加宽**几列（盖住她垂在身侧的手；
                                # 玩家 2026-10-09："袍子遮住手很正常"）

# 哪些原版颜色算"她的皮肤"（要从法师袍底下露出来的部分）
SKIN_CLASSES = ("skin",)



def classify(colour):
    for anchor in OUTLINE_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 40:
            return "outline"
    for anchor in EYE_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 40:
            return "eye"
    for anchor in FLOWER_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 30:
            return "flower"
    for anchor in SCLERA_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 20:
            return "sclera"
    for anchor in SKIN_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 90:
            return "skin"
    return "cloth"


def ramp_map(ramp, colours):
    """把原版的一组颜色按亮度排名，摊到目标色阶上（亮 -> 暗）。"""
    ordered = sorted(colours, key=lambda c: -(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))
    out = {}
    for rank, colour in enumerate(ordered):
        step = 0 if len(ordered) == 1 else round(rank / (len(ordered) - 1) * (len(ramp) - 1))
        out[tuple(int(v) for v in colour)] = ramp[int(np.clip(step, 0, len(ramp) - 1))]
    return out


def purple_pixels(frame):
    """紫 = 蓝比绿高不少、红也比绿高。

    巫师袍的紫有好几档，**最暗那档 `#310D4B` 的 `b - r` 只有 26** ——
    所以不能只用 `b > r + 30` 那种判据（第一版就是这么把袍子最暗的边判没的）。
    """
    r = frame[..., 0].astype(int)
    g = frame[..., 1].astype(int)
    b = frame[..., 2].astype(int)
    return (frame[..., 3] > 0) & (b - g >= 20) & (r - g >= 5)


def measured_robe_ramp():
    """从巫师表里**实测**那件紫袍用到的颜色（按亮度排、按数量配权），核对常量没写错。"""
    wizard = np.asarray(Image.open(WIZARD).convert("RGBA")).astype(np.uint8)
    mask = purple_pixels(wizard)
    if not mask.any():
        return []

    cols, counts = np.unique(wizard[mask][:, :3].reshape(-1, 3), axis=0, return_counts=True)
    pairs = sorted(zip(cols.tolist(), counts.tolist()),
                   key=lambda p: -(0.299 * p[0][0] + 0.587 * p[0][1] + 0.114 * p[0][2]))
    return [(tuple(c), n) for c, n in pairs]


def build(check_only=False, install=False):
    dryad = np.asarray(Image.open(DRYAD).convert("RGBA")).astype(np.int16)
    assert dryad.shape[0] == FRAME_H * FRAMES, "树妖表尺寸变了：%s" % (dryad.shape,)

    out = dryad.copy()
    rgb = dryad[..., :3]
    ys, xs = np.mgrid[0:dryad.shape[0], 0:FRAME_W]
    in_frame_y = ys % FRAME_H

    flat = rgb.reshape(-1, 3)
    unique, inverse = np.unique(flat, axis=0, return_inverse=True)
    inverse2d = inverse.reshape(rgb.shape[:2])
    colour_index = {tuple(int(v) for v in c): i for i, c in enumerate(unique)}
    lookup = {}

    labels = {}
    for colour in unique:
        labels[tuple(int(v) for v in colour)] = classify(colour)

    for colour in unique:
        key = tuple(int(v) for v in colour)
        label = labels[key]
        if label == "outline":
            lookup[key] = OUTLINE
        elif label == "eye":
            lookup[key] = PUPIL
        elif label == "sclera":
            lookup[key] = SCLERA
        elif label == "flower":
            lookup[key] = HAIR[0]          # 头顶那朵花 -> 亮发色（当发饰）

    # 肤色：整体换成玩家给的橙
    skin_colours = [c for c in unique if labels[tuple(int(v) for v in c)] == "skin"]
    for key, target in ramp_map(SKIN, skin_colours).items():
        lookup[key] = target

    # 头发：头 + 背后那片
    hair_zone = (in_frame_y <= HEAD_Y) | (xs >= BACK_X)
    hair_colours = []
    for i, colour in enumerate(unique):
        if labels[tuple(int(v) for v in colour)] != "cloth":
            continue
        if (inverse2d == i)[hair_zone].any():
            hair_colours.append(colour)

    for key, target in ramp_map(HAIR, hair_colours).items():
        lookup[key] = target

    # 衣服的最终效果由第 5 步"整件白袍盖上去"决定 —— 这里**不再给藤衣单独上紫/上白**，
    # 免得袍子版型盖不到的地方残留一块别的颜色的碎片（第一版紫袍的碎花就是这么来的）。

    # ---- 4) 落色（换肤色 / 发色 / 瞳色 / 描边 / 花） ----
    for key, target in lookup.items():
        out[..., :3][inverse2d == colour_index[key]] = np.array(target, dtype=np.int16)

    # ---- 5) 穿白袍（亮黄边）：直接拿游戏里那件袍子的**版型**盖上去 ----
    # 版型来自 `Armor_Body_15`（巫师袍的装备图，一格 40×56）。玩家口径：
    #   "先扒 NPC 法师的" + "尖帽不用扒" + "**不需要改用，袍子遮住手很正常**"
    #   + "**把袍子改成白色＋亮黄边**"
    #   ⇒ 袍子**整件**盖上去、不做裁剪（袖子盖住手是玩家认过的）；
    #     颜色不走原图的蓝，也不走巫师身上那件紫，而是按亮度映到 **ROBE_PALETTE**
    #     （暖灰白 + 最亮一档亮黄 = 金边）。
    # 那格图是"逻辑 20×28、每个逻辑像素占 2×2"，和树妖表同一个规格，所以直接按帧对齐。
    pattern = np.asarray(Image.open(ROBE_SHEET).convert("RGBA")).astype(np.int16)[0:FRAME_H, 0:FRAME_W]
    pmask = pattern[..., 3] > 0

    if ROBE_WIDE > 0:
        # 袍子向左右各加宽几列：把手也盖进去（用同行最外侧那两列的像素复制出去）。
        # 落点仍然受"她自己的不透明像素"限制，所以不会戳出人形。
        for _ in range(ROBE_WIDE):
            wide_pattern = pattern.copy()
            wide_mask = pmask.copy()
            for y in range(FRAME_H):
                cols = np.nonzero(pmask[y])[0]
                if len(cols) == 0:
                    continue
                lo, hi = int(cols.min()), int(cols.max())
                if lo - 1 >= 0 and not pmask[y, lo - 1]:
                    wide_pattern[y, lo - 1] = pattern[y, lo]
                    wide_mask[y, lo - 1] = True
                if hi + 1 < FRAME_W and not pmask[y, hi + 1]:
                    wide_pattern[y, hi + 1] = pattern[y, hi]
                    wide_mask[y, hi + 1] = True
            pattern, pmask = wide_pattern, wide_mask

    # 袍子版型是**蓝色**的（游戏里那件蓝袍）。这里只借它的**轮廓**，
    # 颜色直接上"白袍 + 亮黄边"（见下面的上色循环），不按亮度摊色阶。

    recoloured_hair = np.zeros(out.shape[:2], dtype=bool)
    for shade in HAIR:
        recoloured_hair |= (out[..., :3] == np.array(shade, dtype=np.int16)).all(axis=2)

    for f in range(FRAMES):
        base_y = f * FRAME_H
        block = out[base_y:base_y + FRAME_H]
        local_hair = recoloured_hair[base_y:base_y + FRAME_H] & hair_zone[base_y:base_y + FRAME_H]
        canvas = dryad[base_y:base_y + FRAME_H, :, 3] > 0

        for y in range(FRAME_H):
            target = y + ROBE_DROP
            if target < 0 or target >= FRAME_H:
                continue
            row = pmask[y]
            if not row.any():
                continue

            for x in range(FRAME_W):
                if not row[x]:
                    continue
                tx = x + ROBE_XOFF
                if tx < 0 or tx >= FRAME_W:
                    continue
                if not canvas[target, tx]:
                    continue

                block[target, tx, :3] = np.array(ROBE_BODY, dtype=np.int16)
                block[target, tx, 3] = 255

        # 长发最后盖回上层（袍肩被头发压住）
        block[local_hair] = out[base_y:base_y + FRAME_H][local_hair]

        # ---- 亮黄边：在**成品**上算一遍 ----
        # 必须放在"头发盖回来之后"：袍子外轮廓那一圈正好被长发压着，
        # 先描边再盖头发的话黄边会被吃掉（第一版就是这样，整件袍子只剩白）。
        robe_px = (block[..., :3] == np.array(ROBE_BODY, dtype=np.int16)).all(axis=2)
        outside = ~robe_px
        touches_outside = np.zeros_like(robe_px)
        touches_outside[1:, :] |= outside[:-1, :]
        touches_outside[:-1, :] |= outside[1:, :]
        touches_outside[:, 1:] |= outside[:, :-1]
        touches_outside[:, :-1] |= outside[:, 1:]
        trim = robe_px & touches_outside
        block[trim, :3] = np.array(ROBE_TRIM, dtype=np.int16)

    sheet = Image.fromarray(out.astype(np.uint8), "RGBA")
    problems = audit(sheet)

    if check_only:
        return sheet, problems

    os.makedirs(os.path.dirname(REPO_SHEET), exist_ok=True)
    sheet.save(REPO_SHEET)
    make_head(sheet).save(REPO_HEAD)
    render_preview(sheet).save(PREVIEW)

    if install:
        sheet.save(os.path.join(NPC_DIR, "MechanicalCompanion.png"))
        make_head(sheet).save(os.path.join(NPC_DIR, "MechanicalCompanion_Head.png"))

    return sheet, problems


def audit(sheet):
    problems = []
    frames = [np.asarray(sheet.crop((0, i * FRAME_H, FRAME_W, (i + 1) * FRAME_H)).convert("RGBA"))
              for i in range(FRAMES)]

    for index, frame in enumerate(frames):
        if not frame[..., 3].any():
            problems.append("第 %d 帧是空的" % index)

    walk = [frames[i][..., 3].tobytes() for i in range(0, 14)]
    if len(set(walk)) < 6:
        problems.append("走路帧几乎一样（0..13 只有 %d 种不同轮廓）" % len(set(walk)))

    # 三个新色号必须真的用上了
    for tag, colour in (("发色", HAIR_BASE), ("瞳色", PUPIL), ("肤色", SKIN_BASE)):
        hit = any(bool((f[..., :3] == np.array(colour, dtype=np.uint8)).all(axis=2).any())
                  for f in frames)
        if not hit:
            problems.append("%s #%02X%02X%02X 在表里一个像素都没有" % ((tag,) + colour))

    # 袍子必须真的穿上了：统计"白袍 + 黄边"这两色的像素（不是把整个人染白）
    palette = np.array([ROBE_BODY, ROBE_TRIM], dtype=np.int16)
    for index, frame in enumerate(frames):
        rgb = frame[..., :3].astype(np.int16)
        robe = np.zeros(frame.shape[:2], dtype=bool)
        for colour in palette:
            robe |= (np.abs(rgb - colour).sum(axis=2) <= 6)
        robe &= frame[..., 3] > 0

        if robe.sum() < 100:
            problems.append("第 %d 帧的白袍太少（袍色像素 %d）" % (index, int(robe.sum())))

        if robe.sum() > 0.6 * (frame[..., 3] > 0).sum():
            problems.append("第 %d 帧白得太多，像整只人都染白了" % index)

    # 亮黄边必须真的落在袍子上
    trim = np.array(ROBE_TRIM, dtype=np.uint8)
    if not any(bool((f[..., :3] == trim).all(axis=2).any()) for f in frames):
        problems.append("亮黄边 #%02X%02X%02X 一个像素都没有" % tuple(trim))

    return problems


def make_head(sheet):
    """16×16 头像（`check_assets.py` 卡死这个尺寸）。没帽子，窗口含脸 + 头发。"""
    frame = sheet.crop((0, 16 * FRAME_H, FRAME_W, 17 * FRAME_H))
    box = (10, 6, 26, 22)
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
    parser = argparse.ArgumentParser(description="智械人试用稿：法师紫袍 + 新配色")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--install", action="store_true",
                        help="顺便写进模组目录（想在游戏里看再开；之后要重新跑流水线装机）")
    parser.add_argument("--dump-robe", action="store_true", help="打印实测的巫师袍色阶")
    args = parser.parse_args()

    if args.dump_robe:
        for colour, count in measured_robe_ramp():
            print("#%02X%02X%02X  n=%d" % (colour + (count,)))
        return 0

    sheet, problems = build(check_only=args.check, install=args.install)

    print("尺寸 %dx%d = %d 帧 × %d" % (sheet.width, sheet.height, FRAMES, FRAME_H))
    print("自检：%s" % ("通过" if not problems else "有问题"))

    for item in problems:
        print("   - %s" % item)

    if not args.check:
        print("已写 %s" % REPO_SHEET)
        print("预览 %s" % PREVIEW)
        if args.install:
            print("已写模组目录的 MechanicalCompanion.png（要重新构建 + 装机才看得到）")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
