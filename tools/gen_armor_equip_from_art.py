# -*- coding: utf-8 -*-
"""Turn a ChatGPT-generated armour render into a vanilla-style equip sheet.

Output: `Content/Items/Armor/<Name>_{Head,Body,Legs}.png` = 40 wide x 20 frames x 56 high,
which is what vanilla's player drawing expects (see PlayerDrawLayers: head/body use
`bodyFrame`, legs use `legFrame`, and the frame rectangle is picked per pose).

WHY this replaces the old generator
-----------------------------------
The old `gen_armor_equip.py` painted "1px outline + one flat block + one highlight"
from four sampled colours and wrote **the same content into all 20 frames** (only
bobbing 1px). Vanilla armour is an animated 2D layer: every pose needs its own
silhouette, otherwise the armour reads as a static board pasted on the player
(the player's words: "很塑料"). So here every frame gets:

  * the source art scaled into the pose's body box,
  * a **per-frame leg split** (two trouser legs, gap between them) whose columns
    shift per walk frame, so the legs actually move,
  * 1px overlap between head/body/legs boxes so nothing shows through.

Vanilla body-frame layout (40x56 per frame, 4 columns x 6 rows):
  row 0 standing (col 0) | row 1 walking (col 0..3) | row 2 jumping (col 0..3)
  row 3 falling  (col 0..3) | row 4 crouching (col 0..3) | row 5 climbing (col 0..3)

The walk cycle leans left/right by one pixel; that is what the table below encodes.
"""
import argparse
import os

from PIL import Image

MAIN = r"E:\开发\WastelandSoul"
ARMOR_DIR = os.path.join(MAIN, r"Content\Items\Armor")
RAW_DIR = r"E:\开发\art-inbox\raw"

FRAME_W, FRAME_H, ROWS, COLS = 40, 56, 6, 4
# ⚠️ 帧表高度必须与原版一致：**40×1120 = 20 帧**（不是 6 行 × 4 列 = 24）。
# 项目原有的 `_Head/_Body/_Legs.png` 就全是 40x1120，改成 1344 是没必要的风险。
FRAME_COUNT = 20

# Where each piece is drawn inside a 40x56 frame. Boxes touch (1px overlap) so the
# worn pieces never leave a gap of bare skin between them.
BOXES = {
    "Head": (13, 8, 27, 20),
    "Body": (11, 20, 29, 36),
    "Legs": (13, 35, 27, 53),
}

# Per-frame horizontal shift of the leg pair, in pixels. Index = frame number
# (row * 4 + col); rows are standing/walk/jump/fall/crouch/climb.
LEG_SHIFT = [
    0, 0, 0, 0,          # standing
    0, -1, 0, 1,         # walking: legs swing left then right
    0, -1, 0, 1,         # jumping
    0, 1, 0, -1,         # falling
    0, 0, 0, 0,          # crouching
    0, -1, 0, 1,         # climbing
]

# Per-frame vertical offset for the torso (jump/fall/crouch compress a little).
BODY_DY = [0] * 4 + [0] * 4 + [-1] * 4 + [1] * 4 + [1] * 4 + [0] * 4


def load_source(path):
    """Load the render, drop the white background, return RGBA."""
    image = Image.open(path).convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]

            if r > 235 and g > 235 and b > 235:
                pixels[x, y] = (r, g, b, 0)

    box = image.getchannel("A").getbbox()

    if box is None:
        raise SystemExit("!! %s 抠完是空的（背景不是白色？）" % path)

    return image.crop(box)


def scale_into(source, size):
    """Scale to fit `size`, preserving aspect, and return the scaled image."""
    target_w, target_h = size
    scale = min(target_w / source.width, target_h / source.height)
    new_size = (max(1, int(round(source.width * scale))), max(1, int(round(source.height * scale))))
    return source.resize(new_size, Image.LANCZOS)


def draw_head(canvas, art, dy):
    left, top, right, bottom = BOXES["Head"]
    scaled = scale_into(art, (right - left, bottom - top - 1))
    x = left + ((right - left) - scaled.width) // 2
    canvas.alpha_composite(scaled, (x, top + dy))


def draw_body(canvas, art, dy):
    left, top, right, bottom = BOXES["Body"]
    scaled = scale_into(art, (right - left, bottom - top))
    x = left + ((right - left) - scaled.width) // 2
    canvas.alpha_composite(scaled, (x, top + dy))


def draw_legs(canvas, art, shift):
    """Split the leg art into two legs with a gap, then shift the pair sideways."""
    left, top, right, bottom = BOXES["Legs"]
    width = right - left
    height = bottom - top
    scaled = scale_into(art, (width, height))

    gap = 2
    leg_w = (width - gap) // 2
    mid = scaled.width // 2

    for index, x0 in enumerate((0, mid)):
        piece = scaled.crop((x0, 0, min(x0 + mid, scaled.width), scaled.height))
        piece = piece.resize((leg_w, height), Image.LANCZOS)
        x = left + index * (leg_w + gap) + shift
        canvas.alpha_composite(piece, (x, top))


def build_sheet(sources, part):
    """Compose the 40x1120 sheet for one piece."""
    sheet = Image.new("RGBA", (FRAME_W, FRAME_H * FRAME_COUNT), (0, 0, 0, 0))

    for frame in range(FRAME_COUNT):
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))

        if part == "Head":
            draw_head(canvas, sources["Head"], BODY_DY[frame])
        elif part == "Body":
            draw_body(canvas, sources["Body"], BODY_DY[frame])
            draw_legs(canvas, sources["Legs"], LEG_SHIFT[frame])
        else:
            draw_legs(canvas, sources["Legs"], LEG_SHIFT[frame])

        sheet.alpha_composite(canvas, (0, frame * FRAME_H))

    return sheet


PIECES = {
    "Warrior": {
        "Head": ("SalvagedSteelWarriorHelm", "steel_warrior_helm.png"),
        "Body": ("SalvagedSteelWarriorPlate", "steel_warrior_plate.png"),
        "Legs": ("SalvagedSteelWarriorGreaves", "steel_warrior_greaves.png"),
    },
}


def main():
    parser = argparse.ArgumentParser(description="ChatGPT 原图 -> 原版格式装备帧表")
    parser.add_argument("--set", default="Warrior")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    pieces = PIECES[args.set]
    sources = {}

    for part, (_name, file_name) in pieces.items():
        path = os.path.join(RAW_DIR, file_name)

        if not os.path.exists(path):
            raise SystemExit("缺少原图：%s" % path)

        sources[part] = load_source(path)
        print("原图 %-10s %s -> 抠底后 %dx%d"
              % (part, file_name, sources[part].width, sources[part].height))

    for part, (name, _file) in pieces.items():
        sheet = build_sheet(sources, part)
        out = os.path.join(ARMOR_DIR, "%s_%s.png" % (name, part))

        if args.check:
            print("  [check] %s  ->  %dx%d" % (os.path.basename(out), sheet.width, sheet.height))
            continue

        sheet.save(out)
        print("  写出 %-46s %dx%d" % (os.path.basename(out), sheet.width, sheet.height))

    print("完成（%s 套）" % args.set)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
