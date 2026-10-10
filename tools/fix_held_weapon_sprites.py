# -*- coding: utf-8 -*-
"""Re-orient weapon item sprites so in-hand draw matches vanilla / Calamity.

Inventory and held-use share the same PNG. Square icon art floats off the hand
because vanilla draw origins assume:

  gun    grip on the LEFT, barrel RIGHT, origin ~ (10, height/2)
  staff  handle BOTTOM-LEFT, gem TOP-RIGHT, then Item.staff rotates +45 deg
  sword  handle BOTTOM-LEFT, tip TOP-RIGHT (swing)

Pixel-art: rotate with NEAREST. Idempotent-ish: already-aligned sprites stay put.

Usage:
  python tools/fix_held_weapon_sprites.py --list
  python tools/fix_held_weapon_sprites.py --preview
  python tools/fix_held_weapon_sprites.py --install
"""
from __future__ import annotations

import argparse
import math
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "WastelandSoul"))
WEAPONS = os.path.join(ROOT, "Content", "Items", "Weapons")
PREVIEW = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".tmp-3d", "preview", "held"))

SKIP_DIR = {"Whips"}
ALPHA = 20
PAD = 2


def contains(name, *needles):
    lower = name.lower()
    return any(n.lower() in lower for n in needles)


# Already baked into the PNG. Re-applying rotate/flip on --install is not idempotent.
# Names listed here skip PCA auto-orient (transform_diagonal). Do not --install to "fix" them.
FORCE_ROTATE = {
    "ScavengerMageWeapon.png": 180,
    "ScavengerMageWeaponEX.png": 180,
    "ScavengerCMage.png": 180,
}
FORCE_FLIP_X = {
    "ScavengerGreatblade.png",
    "ArchivistWarriorWeapon.png",
    "ArchivistWarriorWeaponEX.png",
    "ArchivistCWarrior.png",
    "FireplaceWarriorWeapon.png",
    "FireplaceWarriorWeaponEx.png",
    "FireplaceCWarrior.png",
    "RustCleaver.png",
    "RustCleaverEX.png",
    "ScavengerWarriorWeapon.png",
    "ScavengerWarriorWeaponEX.png",
    "ScavengerCWarrior.png",
}


def classify(rel, name):
    n = name.lower()
    if contains(n, "whip", "lash", "bow", "yoyo", "chakram", "whistle"):
        return "skip"
    if contains(n, "discharger"):
        return "gauntlet"
    if contains(n, "tome", "codex", "book") or (contains(n, "archivist") and contains(n, "mage")):
        return "tome"
    if contains(n, "ranger", "shotgun", "nailgun", "railgun", "cannon", "scatter", "flechette"):
        return "gun"
    if contains(n, "summoner", "dronestaff", "wardenstaff", "wispstaff", "spitterstaff"):
        return "crop"
    if contains(n, "warrior", "cleaver", "saber", "greatblade", "greatsword"):
        return "sword"
    if contains(n, "scepter"):
        return "staff"
    if contains(n, "blade") and not contains(n, "mage"):
        return "sword"
    if contains(n, "mage", "wand", "staff", "rod"):
        return "staff"
    return "crop"


def opaque_points(im):
    px = im.load()
    w, h = im.size
    pts = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > ALPHA:
                pts.append((x, y, px[x, y]))
    return pts


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def pca_angle(pts):
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    cxx = sum((p[0] - cx) ** 2 for p in pts) / n
    cyy = sum((p[1] - cy) ** 2 for p in pts) / n
    cxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    return math.degrees(0.5 * math.atan2(2 * cxy, cxx - cyy)), cx, cy


def pca_ends(pts):
    ang, cx, cy = pca_angle(pts)
    rad = math.radians(ang)
    dx, dy = math.cos(rad), math.sin(rad)
    best_lo = best_hi = None
    lo = hi = None
    for p in pts:
        proj = (p[0] - cx) * dx + (p[1] - cy) * dy
        if lo is None or proj < lo:
            lo, best_lo = proj, p
        if hi is None or proj > hi:
            hi, best_hi = proj, p
    return best_lo, best_hi


def neighborhood_brightness(pts, x, y, radius=5):
    r2 = radius * radius
    total = count = 0
    for p in pts:
        if (p[0] - x) ** 2 + (p[1] - y) ** 2 <= r2:
            total += p[2][0] + p[2][1] + p[2][2]
            count += 1
    return total / count if count else 0


def crop_pad(im, pad=PAD):
    pts = opaque_points(im)
    if not pts:
        return im
    x0, y0, x1, y1 = bbox_of(pts)
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(im.size[0] - 1, x1 + pad)
    y1 = min(im.size[1] - 1, y1 + pad)
    return im.crop((x0, y0, x1 + 1, y1 + 1))


def rotate_nearest(im, degrees):
    if abs(degrees) < 1.5:
        return im
    return im.rotate(degrees, resample=Image.NEAREST, expand=True, fillcolor=(0, 0, 0, 0))


def column_mass(pts, x0, x1):
    return sum(1 for p in pts if x0 <= p[0] <= x1)


def bright_centroid(pts, brightest=True):
    scored = [(p[2][0] + p[2][1] + p[2][2], p[0], p[1]) for p in pts]
    scored.sort()
    k = max(1, len(scored) // 8)
    chunk = scored[-k:] if brightest else scored[:k]
    return sum(p[1] for p in chunk) / k, sum(p[2] for p in chunk) / k


def transform_gun(im):
    """Keep side-view guns horizontal; grip left, barrel right. No PCA rotate."""
    out = crop_pad(im)
    pts = opaque_points(out)
    if len(pts) < 8:
        return out
    x0, y0, x1, y1 = bbox_of(pts)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    if h > w * 1.25:
        # Rare vertical cannon: lay it on its side, barrel to the right of the thicker end.
        out = rotate_nearest(out, -90)
        out = crop_pad(out)
        pts = opaque_points(out)
        if not pts:
            return out
        x0, y0, x1, y1 = bbox_of(pts)
    mid = (x0 + x1) / 2
    left = column_mass(pts, x0, mid)
    right = column_mass(pts, mid, x1)
    if left < right * 0.85:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
        out = crop_pad(out)
    return out


def neighborhood_sat(pts, x, y, radius=5):
    r2 = radius * radius
    total = count = 0
    for p in pts:
        if (p[0] - x) ** 2 + (p[1] - y) ** 2 <= r2:
            r, g, b = p[2][0], p[2][1], p[2][2]
            mx, mn = max(r, g, b), min(r, g, b)
            total += ((mx - mn) / mx) if mx else 0
            count += 1
    return total / count if count else 0


def transform_diagonal(im, debug_name=None):
    """Staff / sword: high-sat tip top-right, duller handle bottom-left (vanilla 朝右上)."""
    out = crop_pad(im)
    pts = opaque_points(out)
    if len(pts) < 8:
        return out
    a, b = pca_ends(pts)
    sa = neighborhood_sat(pts, a[0], a[1])
    sb = neighborhood_sat(pts, b[0], b[1])
    if sa >= sb:
        tip, handle = a, b
    else:
        tip, handle = b, a
    vx = tip[0] - handle[0]
    vy = tip[1] - handle[1]
    if vx == 0 and vy == 0:
        return out
    current = math.atan2(vy, vx)
    target = math.atan2(-1.0, 1.0)
    phi = math.degrees(current - target)
    if debug_name:
        print(f"  debug {debug_name} handle=({handle[0]:.0f},{handle[1]:.0f}) tip=({tip[0]:.0f},{tip[1]:.0f}) "
              f"sat h={min(sa, sb):.2f} t={max(sa, sb):.2f} phi={phi:.1f}")
    out = rotate_nearest(out, phi)
    return crop_pad(out)


def transform_crop(im):
    return crop_pad(im)


def apply_force(im, fname):
    # Corrections are already in the files. Listing a name only skips PCA re-orient.
    return im


def transform(im, kind, fname=""):
    im = apply_force(im, fname)
    if kind == "gun":
        return transform_gun(im)
    if kind in ("staff", "sword") and fname not in FORCE_ROTATE and fname not in FORCE_FLIP_X:
        return transform_diagonal(im)
    if kind in ("staff", "sword"):
        return crop_pad(im)
    if kind in ("tome", "gauntlet", "crop"):
        return transform_crop(im)
    return im


def iter_weapon_pngs():
    for dirpath, dirs, files in os.walk(WEAPONS):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR]
        for fname in sorted(files):
            if not fname.lower().endswith(".png"):
                continue
            path = os.path.join(dirpath, fname)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            yield path, rel, fname, classify(rel, fname)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--only", action="append", default=[], help="basename filter")
    args = parser.parse_args()
    if not (args.list or args.preview or args.install):
        parser.error("use --list, --preview, or --install")

    os.makedirs(PREVIEW, exist_ok=True)
    only = {n.lower() for n in args.only}
    counts = {}
    changed = 0

    for path, rel, fname, kind in iter_weapon_pngs():
        if only and fname.lower() not in only:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        before = Image.open(path).convert("RGBA")
        if args.list:
            pts = opaque_points(before)
            box = bbox_of(pts) if pts else (0, 0, 0, 0)
            print(f"{kind:8} {before.size[0]:3}x{before.size[1]:<3} bbox {box}  {rel}")
            continue

        after = transform(before, kind, fname)
        if kind == "skip":
            continue

        if args.preview:
            w = before.size[0] + after.size[0] + 12
            h = max(before.size[1], after.size[1]) + 20
            sheet = Image.new("RGBA", (w, h), (28, 28, 36, 255))
            sheet.paste(before, (4, 16), before)
            sheet.paste(after, (before.size[0] + 8, 16), after)
            out = os.path.join(PREVIEW, fname.replace(".png", f"_{kind}.png"))
            sheet.save(out)
            print(f"{kind:8} {before.size} -> {after.size}  {fname}")

        if args.install:
            if after.size != before.size or list(after.getdata()) != list(before.getdata()):
                after.save(path)
                changed += 1
                print(f"wrote {rel}  {before.size} -> {after.size}")
            else:
                print(f"keep  {rel}")

    print("counts", counts, "changed", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
