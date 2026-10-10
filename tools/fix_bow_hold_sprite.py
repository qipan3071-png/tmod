# -*- coding: utf-8 -*-
"""Re-center bow item sprites on the grip (holdout rotation origin = canvas center).

Handover 2026-10-09: SteelBow grip ~x16-17; game rotates around (width/2, height/2).
Default: flip X (player reported reversed facing) then shift so grip sits on center.

Usage:
  python tools/fix_bow_hold_sprite.py --preview
  python tools/fix_bow_hold_sprite.py --install
"""
import argparse
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "WastelandSoul"))
PREVIEW = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".tmp-3d", "preview"))

BOWS = [
    "Content/Items/Weapons/Boss1Scavenger/ScavengerDrops/SteelBow.png",
    "Content/Items/Weapons/Rift/StarstringBow.png",
]


def opaque_bbox(im):
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 10:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def estimate_grip(im):
    """Grip ≈ golden handle pixels on the left half of the bow."""
    px = im.load()
    w, h = im.size
    bbox = opaque_bbox(im)
    if not bbox:
        return w / 2, h / 2
    x0, y0, x1, y1 = bbox
    gold = []
    for y in range(y0, y1 + 1):
        for x in range(x0, min(x0 + (x1 - x0) // 2 + 8, w)):
            r, g, b, a = px[x, y]
            if a < 10:
                continue
            # warm metal / gold grip
            if r > 140 and g > 90 and b < 140 and r > g:
                gold.append((x, y))
    if gold:
        return sum(p[0] for p in gold) / len(gold), sum(p[1] for p in gold) / len(gold)
    return (x0 + x1) / 2, (y0 + y1) / 2


def transform(im, flip_x, grip_to_center):
    w, h = im.size
    out = im
    if flip_x:
        out = im.transpose(Image.FLIP_LEFT_RIGHT)
    if not grip_to_center:
        return out
    gx, gy = estimate_grip(out)
    cx, cy = w / 2, h / 2
    dx, dy = int(round(cx - gx)), int(round(cy - gy))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(out, (dx, dy), out)
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--no-flip", action="store_true", help="only re-center grip")
    parser.add_argument("--only", action="append", default=[], help="basename filter, e.g. StarstringBow.png")
    args = parser.parse_args()
    if not args.preview and not args.install:
        parser.error("use --preview or --install")

    os.makedirs(PREVIEW, exist_ok=True)
    flip = not args.no_flip
    only = {name.lower() for name in args.only}

    for rel in BOWS:
        name = os.path.basename(rel)
        if only and name.lower() not in only:
            continue
        path = os.path.join(ROOT, rel)
        name = os.path.basename(path)
        before = Image.open(path).convert("RGBA")
        after = transform(before, flip_x=flip, grip_to_center=True)

        if args.preview:
            w, h = before.size
            sheet = Image.new("RGBA", (w * 2 + 8, h + 24), (32, 32, 40, 255))
            sheet.paste(before, (0, 12))
            sheet.paste(after, (w + 8, 12))
            out = os.path.join(PREVIEW, name.replace(".png", "_hold_fix_preview.png"))
            sheet.save(out)
            g0 = estimate_grip(before)
            g1 = estimate_grip(after)
            print(name, "grip before", g0, "after", g1, "->", out)

        if args.install:
            after.save(path)
            print("wrote", path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
