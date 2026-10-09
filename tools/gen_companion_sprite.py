# -*- coding: utf-8 -*-
"""智械人帧表：**原版树妖的姿态骨架 + 棕色金边长袍 + 偏白肤色 + 亮蓝眼睛**。

玩家的定稿（2026-10-09）
-----------------------
> 12:30："你将**树妖的样貌**和**魔法师的斗篷**结合一下，**肤色我要偏白色的**，
>        其他设计按我之前提的来，**走路有办法借鉴原版的就借鉴原版的**。"
> 装机后："**她穿的不应该是长袍吗，还有把衣服改成棕色金边吧，眼睛要亮蓝色**"

所以：**姿势、走路、动画全部沿用原版树妖**（`Dryad_Default`，40×1176 = 21 帧 × 56），
只做换色 + 语义重读：

| 原版元素 | 这里读成 | 位置分区 |
| --- | --- | --- |
| 皮肤（`#EF845A` 等 4 色） | 偏白肤色（4 级色阶） | 全部皮肤像素 |
| 紫瞳 `#4B0884` / 眼白 `#F7F7F7` | **亮蓝瞳** `#6EE7FF` / 冷白 `#F3FAFF` | 按颜色锚点（并整体上移 2px） |
| 头部绿（帧内 y ≤ 23） | 金发 | `HEAD_Y` |
| 背后那一片绿（`x ≥ 28`，一路到腿根） | **散披在后面的长发**（金发） | `BACK_X` |
| **其余绿**（藤衣 + 腰裙 + 腿上绿叶） | **棕色长袍** | ~`hair_zone` |
| 长袍区域**最外侧一圈** | **金边**（`#E8B93C`） | 邻域运算，见 build() 第 4 步 |
| 露出来的躯干皮肤（露脐装） | 长袍色 | 帧内 y 29..47 且 x 13..29 |
| 头顶那朵花的花瓣 | 金色发饰 | 颜色锚点 |
| 描边 `#37170C` | 深色描边 `#14121C` | 颜色锚点 |

⚠️ 三条容易踩的坑（都实测过）
---------------------------
1. **长袍别做短了**：树妖的"露脐藤衣"是**绿色 + 皮肤色混着**的 —— 只换绿的部分会让她半裸，
   所以必须**再补一步**把身体区域里的皮肤像素也改成长袍色（build() 第 3 步）。
2. **背后那片头发是"散披的长发"**（玩家：不用马尾、散着披在后面就行）—— 它不能被归成衣服，
   也不能剪掉；只按 `y ≤ HEAD_Y` 判头发会把它整片染成棕色，只按位置裁又会把剪影切掉。
3. **帧口径必须和原版对齐**：她原来写的 `25 / 9 / 4 + AnimationType = Guide` 三个数全错，
   真值用解包模组读出来是（树妖 `21 / 7 / 2`、向导 `26 / 10 / 5`）。
   帧表换了，`MechanicalCompanion.cs` 里的三个数 + `AnimationType` 必须跟着换。

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
# 帧内分区的两个常数（照原版树妖的像素分布定的，见 开发说明.md 批次 42/44）：
#   · 头 = 帧内 y ≤ HEAD_Y（脸的最上一行是 y=22，所以 0..23 都算头）；
#   · 背后那片长发 = **x ≥ BACK_X**（从肩后一直垂到腿根）。
# 玩家 2026-10-09："**不用马尾**" → "**散着披在后面就行**"：
# 所以背后那片既不能当马尾剪掉，也不能归成长袍（否则头发只剩一个头），
# 它是**散披在后面的长发** —— 剪影照原版，颜色走金发。
HEAD_Y = 23
BACK_X = 28
# "穿衣服"的身体区域：帧内 y 29..47（**脸和脖子 y≤28 留在外面当皮肤**，
# 脚 y≥48 也留在外面 —— 树妖是赤脚的，要不要换靴子等玩家定），x 13..29
BODY_Y0, BODY_Y1, BODY_X0, BODY_X1 = 29, 47, 13, 29
# 原版树妖的眼睛 = 紫瞳 #4B0884（2×4）+ 眼白 #F7F7F7。玩家要"亮蓝色眼睛"。
EYE_HIGHLIGHT = 40    # 与 EYE_ANCHORS 的曼哈顿距离容差

# ---------------------------------------------------------------------------
# 目标配色（按 亮 -> 暗 排；映射时按"原版同组颜色的亮度排名 对 等级"）
# ---------------------------------------------------------------------------
SKIN = [(246, 231, 224), (227, 203, 194), (201, 167, 156), (169, 132, 120)]   # 偏白肤色
# ⚠️ 金发的**暗档必须比长袍的亮档更深**：原版树妖的绿是"暗绿"占多数，亮度排名一拉开，
#   头发和长袍会在中段撞色（第一版 #CF9224 vs #96663E 就糊成一片）。见 开发说明.md 批次 44。
HAIR = [(255, 216, 92), (247, 193, 62), (186, 126, 26), (104, 61, 10)]         # 金发（亮黄 -> 深栗）
ROBE = [(163, 112, 64), (133, 88, 50), (100, 63, 34), (62, 38, 20)]            # 棕色长袍（浅棕 -> 深褐）
OUTLINE = (20, 18, 28)                                                        # 深色描边
TRIM = (232, 185, 60)                                                         # 金边 / 发饰
EYE = (110, 231, 255)                                                         # 亮蓝瞳
SCLERA = (243, 250, 255)                                                      # 眼白（带一点冷色）

# 树妖的皮肤色锚点（原版实测 #EF845A / #FFAD8C / #E6754B / #D65A31）
SKIN_ANCHORS = [(239, 132, 90), (255, 173, 140), (230, 117, 75), (214, 90, 49)]
OUTLINE_ANCHORS = [(55, 23, 12)]        # #37170C 原版描边
# 头顶那朵花：**只把偏粉/亮红的花瓣**判成金发饰。花的暗红外圈（#5A1313 / #A62B2B）故意不认，
# 让它按普通"布料"走亮度色阶 —— 那两色同时也是树妖的**红发丝**，认了会把发丝一起染金。
FLOWER_ANCHORS = [(242, 67, 67), (246, 131, 131), (244, 99, 99)]
EYE_ANCHORS = [(75, 8, 132)]            # #4B0884 紫瞳
SCLERA_ANCHORS = [(247, 247, 247)]      # #F7F7F7 眼白



def classify(colour):
    """把一个原版颜色归到 skin / outline / trim / eye / cloth（布料=头发或长袍，靠位置再分）。"""
    for anchor in OUTLINE_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 40:
            return "outline"

    for anchor in EYE_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= EYE_HIGHLIGHT:
            return "eye"

    for anchor in FLOWER_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 30:
            return "trim"

    for anchor in SCLERA_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 20:
            return "sclera"

    for anchor in SKIN_ANCHORS:
        if sum(abs(int(colour[i]) - anchor[i]) for i in range(3)) <= 90:
            return "skin"

    return "cloth"


def ramp_of(label):
    if label == "skin":
        return SKIN
    if label == "hair":
        return HAIR
    if label == "robe":
        return ROBE
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

    # 1) 先把"每个原版颜色"归类并决定目标色；布料再按帧内位置分 头发 / 长袍
    flat = rgb.reshape(-1, 3)
    unique, inverse = np.unique(flat, axis=0, return_inverse=True)
    inverse2d = inverse.reshape(rgb.shape[:2])
    lookup = {}

    for index, colour in enumerate(unique):
        label = classify(colour)
        if label == "outline":
            lookup[index] = OUTLINE
        elif label == "trim":
            lookup[index] = TRIM
        elif label == "eye":
            # 原版紫瞳 -> 玩家要的**亮蓝色**
            lookup[index] = EYE
        elif label == "sclera":
            lookup[index] = SCLERA

    # 皮肤：整体换成"偏白"色阶（按亮度排名对等级）
    skin_colours = [c for c in unique if classify(c) == "skin"]
    skin_colours.sort(key=lambda c: -(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))

    for rank, colour in enumerate(skin_colours):
        step = 0 if len(skin_colours) <= 1 else round(rank / (len(skin_colours) - 1) * (len(SKIN) - 1))
        index = int(np.where((unique == colour).all(axis=1))[0][0])
        lookup[index] = SKIN[int(np.clip(step, 0, len(SKIN) - 1))]

    # 头发 vs 长袍（绿的部分）：
    #   · **头发** = 头（帧内 y ≤ HEAD_Y）＋ **背后垂下来那一整片**（x ≥ BACK_X，一路到腿根）→ 金发
    #   · 其余绿（藤衣 + 腰裙 + 腿上绿叶）→ **棕色长袍**
    # 玩家口径（2026-10-09，三轮）："头发改成散发，不要束发" → "不用马尾" → "**散着披在后面就行**"。
    # ⇒ 背后那片既不能剪掉（马尾）、也不能归成衣服（否则头发只剩一个头），
    #   要**当成散披的长发**：保持剪影，颜色走金发。
    hair_zone = (in_frame_y <= HEAD_Y) | (in_frame_x >= BACK_X)

    for group in ("hair", "robe"):
        mask = hair_zone if group == "hair" else ~hair_zone

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
        out[inverse2d == index] = target

    # 3) 穿衣服：身体区域里露出来的皮肤（树妖的露脐装）改用长袍色阶 ——
    #    脸（y≤26）、手（x 在 13..27 之外）、脚（y≥48）都自动保留成肤色。
    body_zone = ((ys % FRAME_H) >= BODY_Y0) & ((ys % FRAME_H) <= BODY_Y1) \
        & (xs >= BODY_X0) & (xs <= BODY_X1)

    for rank, colour in enumerate(skin_colours):
        index = int(np.where((unique == colour).all(axis=1))[0][0])
        where = (inverse2d == index) & body_zone
        if where.any():
            out[where] = ROBE[min(rank, len(ROBE) - 1)]

    # 4) 金边：长袍区域**最外侧那一圈**换成金色 —— 描边（深色）本身不换，
    #    所以看到的是"深色轮廓里镶一道金边"，与原版城镇 NPC 的衣饰同一个路子。
    #    只在长袍轮廓上换，不会碰到脸 / 手 / 马尾。
    robe_mask = np.zeros(out.shape[:2], dtype=bool)

    for shade in ROBE:
        robe_mask |= (out == np.array(shade, dtype=out.dtype)).all(axis=2)

    shifted = np.zeros_like(robe_mask)
    shifted[1:, :] |= robe_mask[:-1, :]
    shifted[:-1, :] |= robe_mask[1:, :]
    shifted[:, 1:] |= robe_mask[:, :-1]
    shifted[:, :-1] |= robe_mask[:, 1:]
    trim_mask = robe_mask & ~shifted & (alpha > 0)
    out[trim_mask] = TRIM

    # 5) 眼睛上移 2px：原版把紫瞳 + 眼白摆在**眼线下面**（帧内 y 22..23，眼线在 y 20..21）。
    #    上移之后瞳落到脸的上半、眼线正好变成眉线，而且 **16×16 的对话头像才装得下眼睛**
    #    （站在原位时头像窗口只能切到额头 —— 裁窗口只有 16 高，挪窗口就会把下巴切掉）。
    #    负向 roll 在表头会绕到表尾，所以这两行必须显式清零。
    iris = (out == np.array(EYE, dtype=out.dtype)).all(axis=2)
    sclera = (out == np.array(SCLERA, dtype=out.dtype)).all(axis=2)
    eye_rows = iris | sclera

    moved_iris = np.roll(iris, -2, axis=0)
    moved_sclera = np.roll(sclera, -2, axis=0)
    moved_iris[-2:, :] = False                           # 表尾保护（帧高 56，2px 不会跨帧）
    moved_sclera[-2:, :] = False

    out[eye_rows] = SKIN[0]                              # 原位置补肤色
    out[moved_iris] = EYE
    out[moved_sclera] = SCLERA

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
    """16×16 头部图（`check_assets.py` 卡死这个尺寸）。取站立帧的头部区域 1:1 裁。

    ⚠️ 裁窗口从 (10, 4, 26, 20) 挪到 **(9, 5, 25, 21)**：换色后脸的位置没动，
    但眼睛上移了 2px（见 build() 第 5 步），旧窗口会把眼睛切掉一半
    （对话框左边那一栏会明显不对）。窗口只有 16×16，**动眼睛就得跟着动窗口**。
    """
    frame = sheet.crop((0, 16 * FRAME_H, FRAME_W, 17 * FRAME_H))     # 第 16 帧 = 站立
    box = (10, 5, 26, 21)
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
