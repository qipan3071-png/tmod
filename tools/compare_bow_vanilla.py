# -*- coding: utf-8 -*-
"""Side-by-side: vanilla bow PNG vs mod bow vs hold-fix preview."""
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PREVIEW = os.path.join(ROOT, ".tmp-3d", "preview")
VANILLA = os.path.join(ROOT, ".tmp-vanilladump", "out_bow")
MOD = os.path.join(ROOT, "WastelandSoul")

ROWS = [
    ("WoodenBow (Item_39)", "Item_39.png", "Content/Items/Weapons/Boss1Scavenger/ScavengerDrops/SteelBow.png", "SteelBow_hold_fix_preview.png"),
    ("DemonBow (Item_44)", "Item_44.png", None, None),
    ("IronBow (Item_99)", "Item_99.png", "Content/Items/Weapons/Rift/StarstringBow.png", "StarstringBow_hold_fix_preview.png"),
]


def load(path, label):
    if not path or not os.path.isfile(path):
        return None, label + " (missing)"
    return Image.open(path).convert("RGBA"), label


def pad(im, target_h):
    w, h = im.size
    if h >= target_h:
        return im
    canvas = Image.new("RGBA", (w, target_h), (0, 0, 0, 0))
    canvas.paste(im, (0, (target_h - h) // 2))
    return canvas


def main():
    os.makedirs(PREVIEW, exist_ok=True)
    gap = 8
    for title, van_name, mod_rel, prev_name in ROWS:
        panels = []
        van_path = os.path.join(VANILLA, van_name)
        im, lab = load(van_path, "vanilla")
        if im:
            panels.append((lab, im))
        if mod_rel:
            mod_path = os.path.join(MOD, mod_rel.replace("/", os.sep))
            im, lab = load(mod_path, "mod (current)")
            if im:
                panels.append((lab, im))
        if prev_name:
            prev_path = os.path.join(PREVIEW, prev_name)
            im, lab = load(prev_path, "preview fix")
            if im:
                # preview sheet is 2-up; take right half
                w, h = im.size
                im = im.crop((w // 2 + 4, 0, w, h))
                panels.append((lab, im))

        if not panels:
            print("skip", title, "- no images")
            continue

        max_h = max(p.size[1] for _, p in panels) + 20
        total_w = sum(p.size[0] for _, p in panels) + gap * (len(panels) - 1) + 16
        sheet = Image.new("RGBA", (total_w, max_h + 28), (32, 32, 40, 255))
        x = 8
        for lab, im in panels:
            im = pad(im, max_h - 20)
            sheet.paste(im, (x, 24))
            x += im.size[0] + gap
        out = os.path.join(PREVIEW, title.replace(" ", "_").replace("(", "").replace(")", "") + "_compare.png")
        sheet.save(out)
        print("wrote", out, "panels:", [l for l, _ in panels])

    return 0


if __name__ == "__main__":
    sys.exit(main())
