# -*- coding: utf-8 -*-
"""把**原版的装备帧表**换成我们自己的配色，直接当穿身图用。

为什么走这条路（批次 38）
------------------------
批次 35/37 的穿身图是"逐像素手画的 ASCII 小方块"：宽 12px、只有一个躯干，
**不含手臂**。原版的 `Armor_Body_*` 帧表里躯干和**两条手臂**是画在一起的，
所以原版护甲穿上去不会有"肩膀/手臂露身色"的问题；手画的方块套上去必然露。

玩家的话："你的装备纹理做的太差了，不行就去参考数据，不要想着靠贴图，
想办法，让装备纹理到人物身上。"
→ 正确做法不是再画一版方块，而是**拿原版的帧表当形状数据**（姿势、手臂、
   每帧的轮廓都在里面），只把颜色换成本套装该有的颜色。

因此：`<原版贴图>` 的 alpha 通道**原样保留**，RGB 按亮度重映射到本套装的色阶。

色阶来源
--------
复用 `gen_armor_pixel_equip.py` 里那 9 套已经定稿的 `PAL_*`（本来就是从物品图标
采样 + 拉开对比得来的），所以"人物身上的颜色"和"背包里的图标"仍然是同一套色。

用法
----
    python tools/gen_armor_equip_recolor.py --list                # 看有哪些原版贴图可选
    python tools/gen_armor_equip_recolor.py --contact 1 2 3       # 出一张原版对照表
    python tools/gen_armor_equip_recolor.py --set Mage --preview  # 只做一套 + 预览
    python tools/gen_armor_equip_recolor.py                       # 全部 27 张写回模组
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gen_armor_pixel_equip as base  # noqa: E402

VANILLA_DIR = r"E:\开发\.tmp-vanilladump\out"
PREVIEW_DIR = r"E:\开发\.tmp-3d\preview"

# 每套：用哪张原版贴图当形状 + 用哪个色阶。
# `ref` 的三项是**原版贴图索引**（`Armor_Head_<n>` / `Armor_Body_<n>` / `Armor_Legs_<n>`），
# 由 `--contact` 看过之后填。None = 还没挑。
# `ref` = (原版头/身/腿索引)。索引来自 `.tmp-vanilladump/out/_index_armor.txt`：
#   IronHelmet=2  IronChainmail=2  IronGreaves=2
#   WizardHat=14  Robe=15         WoodGreaves=31
#   CactusHelmet=70 CactusBreastplate=46 CactusLeggings=42
#   JungleHat=8   JungleShirt=8   JunglePants=8
#   MoltenHelmet=9 MoltenBreastplate=9 MoltenGreaves=9
#   FrostHelmet=46 FrostBreastplate=27 FrostLeggings=26
#   MeteorHelmet=6 MeteorSuit=6   MeteorLeggings=6
#   ShadowHelmet=5 ShadowScalemail=5 ShadowGreaves=5
#   PlatinumHelmet=50 PlatinumChainmail=31 PlatinumGreaves=30
# 选型原则：**每套用不同形状**（9 套 9 个轮廓），且形状的"气质"要对得上那套的设定。
SPECS = {
    # 精钢战士：铁甲的板甲轮廓
    "Warrior":     {"pal": "PAL_WARRIOR",      "ref": (2, 2, 2)},
    # 精钢法师：原版法师帽 + 长袍（长袍本身盖到腿）
    "Mage":        {"pal": "PAL_MAGE",         "ref": (14, 15, 31)},
    # 精钢射手：仙人掌甲的轻甲轮廓（沙漠/废土气质）
    "Ranger":      {"pal": "PAL_RANGER",       "ref": (70, 46, 42)},
    # 精钢召唤：丛林套的部族布甲轮廓
    "Summoner":    {"pal": "PAL_SUMMONER",     "ref": (8, 8, 8)},
    # 灰烬之心：熔岩套（火）
    "AshHeart":    {"pal": "PAL_HEARTH",       "ref": (9, 9, 9)},
    # 炉卫：霜冻套（冷火）
    "HearthGuard": {"pal": "PAL_FROST",        "ref": (46, 27, 26)},
    # 信号甲：陨石套（科技感）
    "SignalRig":   {"pal": "PAL_SIGNAL",       "ref": (6, 6, 6)},
    # 升级树一档：暗影套（更凶的轮廓）
    "AshAlloy":    {"pal": "PAL_ASH_ALLOY",    "ref": (5, 5, 5)},
    # 升级树二档：铂金套（最亮的轮廓，作为最终档）
    "HearthAlloy": {"pal": "PAL_HEARTH_ALLOY", "ref": (50, 31, 30)},
}

# 我们的色阶里，哪几个字母是"中性明暗"（按暗 -> 亮），哪几个是点缀色。
RAMP_KEYS = ("k", "d", "D", "m", "L", "H")
ACCENT_KEYS = ("r", "g")

# 饱和度超过这个值的像素算"点缀色"（原版的金边/宝石/发光），走点缀色阶而不是中性色阶。
ACCENT_SATURATION = 0.45


def vanilla_path(part, index):
    return os.path.join(VANILLA_DIR, "Armor_%s_%d.png" % (part, index))


def load_ramp(set_name):
    palette = getattr(base, SPECS[set_name]["pal"])
    ramp = [palette[key] for key in RAMP_KEYS]
    accents = [palette[key] for key in ACCENT_KEYS]
    return ramp, accents


def luminance(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def recolor(image, ramp, accents):
    """保留 alpha（= 原版轮廓），把 RGB 换成我们的色阶。

    ⚠️ 不能按"像素亮度线性分档"直接映射：原版帧表的颜色是**带明暗层次的几十种近似色**，
    线性分档会让相邻两种颜色落到不同档位，平涂区块被打成一堆噪点（第一版实测就是这样，
    远看像撒了白点/橙点）。

    正确做法是**先看原版这套一共用了哪几种颜色**，把它们按亮度**排序分等级**，
    再把"第 k 档"整体换成我们色阶的第 k 档 —— 平涂区块因此保持平涂，
    原版自带的明暗关系也原样保留。
    """
    array = np.asarray(image.convert("RGBA"))
    rgb = array[..., :3].astype(np.int32)
    alpha = array[..., 3].copy()
    opaque = alpha > 0

    if not opaque.any():
        return Image.fromarray(array, "RGBA")

    flat = rgb[opaque].reshape(-1, 3)
    colors, inverse = np.unique(flat, axis=0, return_inverse=True)

    # 每个"原版颜色"的亮度与饱和度
    luminance_values = colors @ np.array([0.299, 0.587, 0.114], dtype=np.float64)
    biggest = colors.max(axis=1)
    smallest = colors.min(axis=1)
    saturation = np.where(biggest > 0, (biggest - smallest) / np.maximum(biggest, 1.0), 0.0)

    lookup = np.zeros_like(colors)

    # 全部按亮度等级映射到我们的中性色阶。
    #
    # ⚠️ 曾经试过"饱和度高 = 点缀色，单独映射到金/锈色"——错的：原版**长袍本体就是蓝色的**
    # （`Armor_Body_15` 的主色 #162350 / #3454BE），一判饱和度就整件袍子被当成金边，
    # 法师套直接变成金色。原版护甲的"主色"本来就可能是饱和色，
    # 所以**只按明暗等级换色**，套装的颜色身份完全由我们自己的色阶决定。
    neutral_order = np.argsort(luminance_values)
    neutral_total = len(neutral_order)

    for slot, color_index in enumerate(neutral_order):
        step = 0 if neutral_total <= 1 else round(slot / (neutral_total - 1) * (len(ramp) - 1))
        lookup[color_index] = ramp[int(np.clip(step, 0, len(ramp) - 1))]

    output = rgb.copy()
    output[opaque] = lookup[inverse]
    result = np.concatenate([output.astype(np.uint8), alpha[..., None].astype(np.uint8)], axis=2)
    return Image.fromarray(result, "RGBA")


def build(set_name, part, index, preview_only=False):
    source = vanilla_path(part, index)

    if not os.path.exists(source):
        raise SystemExit("缺少原版参考贴图：%s（先跑 .tmp-vanilladump 的取图流程）" % source)

    ramp, accents = load_ramp(set_name)
    sheet = recolor(Image.open(source), ramp, accents)

    for item_name, piece in base.pieces_for(set_name):
        if piece != part:
            continue

        target = os.path.join(base.out_dir(set_name), "%s_%s.png" % (item_name, part))

        if preview_only:
            print("  [预览] %-52s <- %s" % (os.path.basename(target), os.path.basename(source)))
        else:
            sheet.save(target)
            print("  写出 %-52s <- %s  %dx%d"
                  % (os.path.basename(target), os.path.basename(source),
                     sheet.width, sheet.height))

    return sheet


def contact_sheet(indices, part="Body", zoom=4):
    """把若干张原版贴图并排画出来，方便挑形状。"""
    tiles = []

    for index in indices:
        path = vanilla_path(part, index)

        if not os.path.exists(path):
            continue

        image = Image.open(path).convert("RGBA")
        frame = image.crop((0, 0, min(40, image.width), min(56, image.height)))
        tiles.append((index, frame.resize((frame.width * zoom, frame.height * zoom), Image.NEAREST)))

    if not tiles:
        raise SystemExit("没有可用的原版贴图（%s）" % VANILLA_DIR)

    cell_w = max(tile.width for _index, tile in tiles) + 8
    cell_h = max(tile.height for _index, tile in tiles) + 24
    columns = min(8, len(tiles))
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGBA", (cell_w * columns, cell_h * rows), (26, 26, 30, 255))

    from PIL import ImageDraw

    draw = ImageDraw.Draw(sheet)

    for position, (index, tile) in enumerate(tiles):
        column, row = position % columns, position // columns
        x, y = column * cell_w + 4, row * cell_h + 20
        sheet.alpha_composite(tile, (x, y))
        draw.text((x, y - 16), "%s %d" % (part, index), fill=(230, 230, 230, 255))

    return sheet


def main():
    parser = argparse.ArgumentParser(description="原版装备帧表 -> 我们的配色穿身图")
    parser.add_argument("--set", default=None, help="只做这一套")
    parser.add_argument("--preview", action="store_true", help="只打印，不写文件")
    parser.add_argument("--list", action="store_true", help="列出可用的原版贴图索引")
    parser.add_argument("--contact", nargs="*", type=int, default=None,
                        help="出一张对照表：--contact <索引...> [--part Body]")
    parser.add_argument("--part", default="Body", choices=["Head", "Body", "Legs"])
    args = parser.parse_args()

    if args.contact is not None:
        sheet = contact_sheet(args.contact, args.part)
        os.makedirs(PREVIEW_DIR, exist_ok=True)
        out = os.path.join(PREVIEW_DIR, "vanilla_contact_%s.png" % args.part)
        sheet.save(out)
        print("对照表 -> %s  %dx%d" % (out, sheet.width, sheet.height))
        return 0

    if args.list:
        for part in ("Head", "Body", "Legs"):
            found = []

            for name in os.listdir(VANILLA_DIR) if os.path.isdir(VANILLA_DIR) else []:
                prefix, suffix = "Armor_%s_" % part, ".png"

                if name.startswith(prefix) and name.endswith(suffix):
                    found.append(int(name[len(prefix):-len(suffix)]))

            print("%-5s 可用 %d 个：%s" % (part, len(found), sorted(found)[:40]))

        return 0

    sets = [args.set] if args.set else list(SPECS)
    missing = []

    for set_name in sets:
        for part, index in zip(("Head", "Body", "Legs"), SPECS[set_name]["ref"]):
            if index is None:
                missing.append(set_name)

    if missing:
        raise SystemExit("这些套还没挑原版参考贴图：%s（用 --contact 先看）"
                         % ", ".join(sorted(set(missing))))

    for set_name in sets:
        for part, index in zip(("Head", "Body", "Legs"), SPECS[set_name]["ref"]):
            build(set_name, part, index, preview_only=args.preview)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
