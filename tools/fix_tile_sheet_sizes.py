# -*- coding: utf-8 -*-
"""按 tModLoader 的贴图尺寸规范修正两处（纯客观几何，不改美术内容）：

1) 奖杯：`TileObjectData.Style3x3` + `CoordinateHeights = {16,16,16}` + padding 2
   → 贴图必须是 **54×54**，三行分别落在 y=0 / 18 / 36。
   现状 54×48（三行紧贴、无 padding）⇒ 第三行落进 padding 区，下排会画成透明/错位。
2) 旗帜：`Style1x2Top` + `CoordinateHeights = {16,16}` + padding 2
   → 贴图必须是 **18×36**，两行在 y=0 / 18。现状 18×34 缺底部 2px padding。
"""
import glob
import os

from PIL import Image

TILES = r"E:\开发\WastelandSoul\Content\Tiles"

fixed_trophies = []
for path in sorted(glob.glob(os.path.join(TILES, "*Trophy*.png"))):
    image = Image.open(path).convert("RGBA")

    if image.size == (54, 54):
        continue

    source = image.crop((0, 0, 54, 48))
    rows = [source.crop((0, i * 16, 54, i * 16 + 16)) for i in range(3)]

    out = Image.new("RGBA", (54, 54), (0, 0, 0, 0))
    for index, row in enumerate(rows):
        out.paste(row, (0, index * 18))

    out.save(path)
    fixed_trophies.append((os.path.basename(path), image.size, out.size))

fixed_banners = []
for path in sorted(glob.glob(os.path.join(TILES, "*Banner*.png"))):
    image = Image.open(path).convert("RGBA")

    if image.size == (18, 36):
        continue

    out = Image.new("RGBA", (18, 36), (0, 0, 0, 0))
    out.paste(image.crop((0, 0, 18, 34)), (0, 0))
    out.save(path)
    fixed_banners.append((os.path.basename(path), image.size, out.size))

print("奖杯修正 %d 张：" % len(fixed_trophies))
for name, before, after in fixed_trophies:
    print("   %-38s %s -> %s" % (name, before, after))

print("旗帜修正 %d 张：" % len(fixed_banners))
for name, before, after in fixed_banners:
    print("   %-38s %s -> %s" % (name, before, after))
