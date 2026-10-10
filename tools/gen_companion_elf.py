# -*- coding: utf-8 -*-
"""智械人帧表：原版树妖的 21 帧骨架 + 精灵外形（不是树妖换色）。

玩家 2026-10-10：
  「根据原版的帧表，和像素绘风来设计她，骨架参考树妖的，不是叫一样的，
   做的要和原版风格一样，走路方式什么的，自己看元的代码」

所以：
  · 表还是 Dryad_Default：40×1176 = 21 帧 × 56，朝左
  · AnimationType = Dryad，FindFrame / AI 一个字节都不自己写
  · 外形按概念图（金发、尖耳、亮蓝瞳、棕红金边长袍）重画，剪影不再是树妖那件藤衣

用法
----
    python tools/gen_companion_elf.py
    python tools/gen_companion_elf.py --check
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
MOD = os.path.join(ROOT, "WastelandSoul")
NPC_DIR = os.path.join(MOD, "Content", "NPCs", "Town")
SHEET = os.path.join(NPC_DIR, "MechanicalCompanion.png")
HEAD = os.path.join(NPC_DIR, "MechanicalCompanion_Head.png")
PREVIEW = os.path.join(ROOT, ".tmp-3d", "preview", "companion_elf_preview.png")
VANILLA = os.path.join(ROOT, ".tmp-vanilladump", "out_town", "Dryad_Default.png")
CONCEPT = os.path.join(os.path.dirname(__file__), "data", "companion_elf_concept.png")

FRAME_W, FRAME_H, FRAMES = 40, 56, 21
HEAD_Y = 23
BACK_X = 28
BODY_Y0, BODY_Y1, BODY_X0, BODY_X1 = 29, 47, 13, 29

# 概念图色阶（从玩家给的 5×5 表采样，再收成原版那种 3~5 档）
SKIN = [(244, 214, 196), (232, 186, 158), (214, 154, 122), (176, 112, 86)]
HAIR = [(255, 232, 140), (248, 208, 80), (232, 176, 56), (196, 132, 40), (140, 84, 24)]
ROBE = [(176, 56, 48), (144, 40, 40), (120, 32, 32), (88, 24, 28), (56, 16, 20)]
SHOE = [(120, 72, 40), (88, 48, 28), (56, 32, 20)]
OUTLINE = (36, 24, 28)
TRIM = (240, 196, 72)
EYE = (48, 168, 232)
SCLERA = (244, 248, 252)
SPARK = (80, 196, 255)

SKIN_ANCHORS = [(239, 132, 90), (255, 173, 140), (230, 117, 75), (214, 90, 49)]
OUTLINE_ANCHORS = [(55, 23, 12)]
FLOWER_ANCHORS = [(242, 67, 67), (246, 131, 131), (244, 99, 99)]
EYE_ANCHORS = [(75, 8, 132)]
SCLERA_ANCHORS = [(247, 247, 247)]


def dist(a, b):
    return abs(int(a[0]) - b[0]) + abs(int(a[1]) - b[1]) + abs(int(a[2]) - b[2])


def classify(colour):
    for anchor in OUTLINE_ANCHORS:
        if dist(colour, anchor) <= 40:
            return "outline"
    for anchor in EYE_ANCHORS:
        if dist(colour, anchor) <= 40:
            return "eye"
    for anchor in FLOWER_ANCHORS:
        if dist(colour, anchor) <= 30:
            return "hair"
    for anchor in SCLERA_ANCHORS:
        if dist(colour, anchor) <= 20:
            return "sclera"
    for anchor in SKIN_ANCHORS:
        if dist(colour, anchor) <= 90:
            return "skin"
    return "cloth"


def ramp_pick(ramp, lum, lo, hi):
    if hi <= lo:
        return ramp[len(ramp) // 2]
    t = (lum - lo) / (hi - lo)
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    index = int(round((1.0 - t) * (len(ramp) - 1)))
    return ramp[index]


def luminance(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def opaque_bbox(frame):
    alpha = frame[..., 3]
    ys, xs = np.where(alpha > 20)
    if len(xs) == 0:
        return 0, 0, FRAME_W, FRAME_H
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def extract_cell(sheet, col, row):
    cell_w, cell_h = sheet.size[0] // 5, sheet.size[1] // 5
    x0, y0 = col * cell_w, row * cell_h
    cell = np.asarray(sheet.crop((x0, y0, x0 + cell_w, y0 + cell_h)))
    alpha = cell[..., 3]
    rgb = cell[..., :3]
    mask = (alpha > 20) & ~((rgb[..., 0] < 45) & (rgb[..., 1] < 45) & (rgb[..., 2] < 45))
    ys, xs = np.where(mask)
    crop = Image.fromarray(cell[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1], "RGBA")
    return crop


def extract_concept_stand():
    sheet = Image.open(CONCEPT).convert("RGBA")
    crop = extract_cell(sheet, 0, 0)
    # 体量对齐树妖占位（约 26×46），最近邻，禁止平滑缩放
    return crop.resize((26, 48), Image.NEAREST)


def extract_concept_cast():
    """攻击帧用手持火花的那几格（第 5 行第 2~4 格）。"""
    sheet = Image.open(CONCEPT).convert("RGBA")
    poses = []
    for col in (1, 2, 3):
        crop = extract_cell(sheet, col, 4)
        h = 48
        w = max(26, int(round(crop.size[0] * h / crop.size[1])))
        w = min(w, FRAME_W)
        poses.append(crop.resize((w, h), Image.NEAREST))
    return poses


def paste(dst, src, ox, oy):
    sh, sw = src.shape[:2]
    dh, dw = dst.shape[:2]
    for y in range(sh):
        ty = oy + y
        if ty < 0 or ty >= dh:
            continue
        for x in range(sw):
            tx = ox + x
            if tx < 0 or tx >= dw:
                continue
            if src[y, x, 3] <= 20:
                continue
            dst[ty, tx] = src[y, x]


def fill_skirt(canvas, pose):
    """两腿之间填上袍色，走起来是裙摆在晃，不是两条裤子。"""
    alpha_pose = pose[..., 3]
    for y in range(32, 51):
        filled = [x for x in range(FRAME_W) if canvas[y, x, 3] > 20 or alpha_pose[y, x] > 20]
        if len(filled) < 2:
            continue
        left, right = min(filled), max(filled)
        for x in range(left, right + 1):
            if canvas[y, x, 3] > 20:
                continue
            canvas[y, x, :3] = ROBE[1] if y < 46 else ROBE[2]
            canvas[y, x, 3] = 255


def drop_specks(canvas):
    """去掉悬空的 1px 残渣（说话帧伸手时容易带出来）。"""
    alpha = canvas[..., 3]
    kill = []
    for y in range(FRAME_H):
        for x in range(FRAME_W):
            if alpha[y, x] <= 20:
                continue
            n = 0
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < FRAME_W and 0 <= ny < FRAME_H and canvas[ny, nx, 3] > 20:
                    n += 1
            if n < 2:
                kill.append((x, y))
    for x, y in kill:
        canvas[y, x] = 0


def fill_waist(canvas, pose):
    """32 这一行是切腿线，把树妖腰腹占位补回袍色，头和肩仍是概念图。"""
    rgb = pose[..., :3]
    alpha = pose[..., 3]
    for y in range(28, 36):
        for x in range(FRAME_W):
            if alpha[y, x] <= 20 or canvas[y, x, 3] > 20:
                continue
            if classify(rgb[y, x]) == "outline":
                canvas[y, x, :3] = OUTLINE
            else:
                canvas[y, x, :3] = ROBE[2]
            canvas[y, x, 3] = 255


def fill_pose_extra(canvas, pose):
    """走路抬腿、说话伸手：树妖骨架多出来的占位，用袍/靴补上。头发区不抄树妖。"""
    rgb = pose[..., :3]
    alpha = pose[..., 3]
    lums = [luminance(rgb[y, x]) for y in range(FRAME_H) for x in range(FRAME_W) if alpha[y, x] > 20]
    lo, hi = (min(lums), max(lums)) if lums else (0, 255)
    for y in range(FRAME_H):
        for x in range(FRAME_W):
            if alpha[y, x] <= 20 or canvas[y, x, 3] > 20:
                continue
            if y <= HEAD_Y:
                continue
            lum = luminance(rgb[y, x])
            kind = classify(rgb[y, x])
            if y >= 50 or kind == "skin" and y >= 48:
                colour = ramp_pick(SHOE, lum, lo, hi)
            elif kind == "outline":
                colour = OUTLINE
            else:
                colour = ramp_pick(ROBE, lum, lo, hi)
            canvas[y, x, :3] = colour
            canvas[y, x, 3] = 255


def build(check_only=False):
    dryad = np.asarray(Image.open(VANILLA).convert("RGBA"))
    assert dryad.shape[0] == FRAME_H * FRAMES and dryad.shape[1] == FRAME_W

    stand = np.asarray(extract_concept_stand().convert("RGBA"))
    casts = [np.asarray(im.convert("RGBA")) for im in extract_concept_cast()]

    idle = dryad[0:FRAME_H]
    idle_box = opaque_bbox(idle)

    sheet = np.zeros((FRAME_H * FRAMES, FRAME_W, 4), dtype=np.uint8)

    for index in range(FRAMES):
        pose = dryad[index * FRAME_H:(index + 1) * FRAME_H]
        box = opaque_bbox(pose)
        canvas = np.zeros((FRAME_H, FRAME_W, 4), dtype=np.uint8)

        if index >= FRAMES - 2 and casts:
            sprite = casts[min(index - (FRAMES - 2), len(casts) - 1)]
        else:
            sprite = stand

        ox = box[0] + ((box[2] - box[0]) - sprite.shape[1]) // 2
        oy = box[3] - sprite.shape[0]
        paste(canvas, sprite, ox, oy)
        if 1 <= index <= 13:
            # 走路帧（原版树妖 2..13 是走循环，1 是起脚）：下摆跟骨架抬腿
            canvas[32:, :, :] = 0
            fill_pose_extra(canvas, pose)
            fill_waist(canvas, pose)
            fill_skirt(canvas, pose)
        elif index < FRAMES - 2:
            fill_pose_extra(canvas, pose)
        drop_specks(canvas)
        sheet[index * FRAME_H:(index + 1) * FRAME_H] = canvas

    image = Image.fromarray(sheet, "RGBA")
    problems = audit(image)

    if check_only:
        return image, problems

    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    image.save(SHEET)
    make_head(image).save(HEAD)
    render_preview(image).save(PREVIEW)
    return image, problems


def audit(sheet):
    problems = []
    frames = [np.asarray(sheet.crop((0, i * FRAME_H, FRAME_W, (i + 1) * FRAME_H))) for i in range(FRAMES)]
    for index, frame in enumerate(frames):
        if not frame[..., 3].any():
            problems.append("第 %d 帧是空的" % index)
    walk = [frames[i][..., 3].tobytes() for i in range(0, 14)]
    if len(set(walk)) < 6:
        problems.append("走路帧几乎一样（0..13 只有 %d 种不同轮廓）" % len(set(walk)))
    if sheet.size != (FRAME_W, FRAME_H * FRAMES):
        problems.append("表尺寸 %s 不是 %dx%d" % (sheet.size, FRAME_W, FRAME_H * FRAMES))
    return problems


def make_head(sheet):
    """16×16 头像：对准脸和尖耳（朝左，脸在左半），不要整片披发。"""
    frame = np.asarray(sheet.crop((0, 0, FRAME_W, FRAME_H)))
    rgb = frame[..., :3].astype(np.int16)
    iris = (frame[..., 3] > 20) & (rgb[..., 2] > rgb[..., 0] + 20) & (rgb[..., 2] > rgb[..., 1])
    ys, xs = np.where(iris)
    if len(xs) == 0:
        ys, xs = np.where((frame[:26, :, 3] > 20))
    cx = int(np.median(xs))
    cy = int(np.median(ys))
    x0 = max(0, min(FRAME_W - 16, cx - 9))
    y0 = max(0, min(FRAME_H - 16, cy - 6))
    return Image.fromarray(frame[y0:y0 + 16, x0:x0 + 16], "RGBA")


def render_preview(sheet, zoom=6):
    from PIL import ImageDraw

    columns = 7
    rows = (FRAMES + columns - 1) // columns
    canvas = Image.new("RGBA", (columns * FRAME_W * zoom, rows * (FRAME_H * zoom + 18)), (26, 26, 30, 255))
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
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sheet, problems = build(check_only=args.check)
    print("尺寸 %dx%d = %d 帧 x %d" % (sheet.width, sheet.height, FRAMES, FRAME_H))
    print("自检：%s" % ("通过" if not problems else "有问题"))
    for item in problems:
        print("   -", item)
    if not args.check:
        print("已写", SHEET)
        print("已写", HEAD)
        print("预览", PREVIEW)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
