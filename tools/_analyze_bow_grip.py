# -*- coding: utf-8 -*-
"""Measure item icon content bbox / center (for bow grip vs canvas center)."""
import os
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "WastelandSoul")


def analyze(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 10:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return {
        "path": path,
        "size": (w, h),
        "bbox": (min(xs), min(ys), max(xs), max(ys)),
        "center": (sum(xs) / len(xs), sum(ys) / len(ys)),
        "canvas": (w / 2, h / 2),
    }


def main():
    names = [
        "Content/Items/Weapons/Boss1Scavenger/ScavengerDrops/SteelBow.png",
        "Content/Items/Weapons/Rift/StarstringBow.png",
    ]
    for rel in names:
        path = os.path.normpath(os.path.join(ROOT, rel))
        info = analyze(path)
        if not info:
            print(rel, "MISSING or empty")
            continue
        b = info["bbox"]
        c = info["center"]
        cv = info["canvas"]
        print(
            os.path.basename(path),
            f"{info['size'][0]}x{info['size'][1]}",
            f"bbox={b}",
            f"content_center=({c[0]:.2f},{c[1]:.2f})",
            f"canvas_center=({cv[0]:.1f},{cv[1]:.1f})",
            f"delta_from_canvas=({c[0]-cv[0]:.2f},{c[1]-cv[1]:.2f})",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
