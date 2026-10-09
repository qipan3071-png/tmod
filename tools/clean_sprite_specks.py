# -*- coding: utf-8 -*-
"""删掉贴在物品**主体之外**的品红残点（`key_magenta_sprites.py` 的补丁）。

为什么还需要这一步
------------------
`key_magenta_sprites.py` 只删「与画布边缘连通」的品红，理由是怕误伤自带紫光的物品
（`StarstringBow`）。但 AI 出的图里还有大量**飘在透明背景里的孤立品红点**：
它们既不是整片粉底（不连通边缘），也不属于主体 —— 于是在游戏里就是散在物品周围的
粉色麻点（玩家原话"物品周围是粉紫色的"）。

实测（`SalvagedSteelMageRobe`）：整张 32x32 里 122 个不透明品红像素，
其中主体只占 ~60 个，剩下全是飘点。`SalvagedSteelWarriorHelm/Plate` 同理。

判定
----
1. 品红判定沿用 `R-G>60 且 B-G>60`（实测能区分"品红底"和"法师套自带的正紫"：
   `#BEAAFF` 的 R-G 只有 20）。
2. 只删**不与"最大不透明连通块"相连**的品红像素 —— 主体自带的紫光一定长在主体上。
3. 再对"紧贴透明、且颜色偏品红"的主体边缘做一次去溢色（用邻域非品红均值替代），
   否则缩放时那圈粉边会渗出来。

用法:
    python tools/clean_sprite_specks.py                 # 只扫描报告
    python tools/clean_sprite_specks.py --fix           # 就地清理（先备份到 .backup/sprite-specks）
    python tools/clean_sprite_specks.py --fix --paths <png> [...]
"""
import argparse
import os
import shutil
import sys
from collections import deque

import numpy as np
from PIL import Image

MOD_ROOT = r"E:\开发\WastelandSoul"
BACKUP_ROOT = r"E:\开发\.backup\sprite-specks"

MAGENTA_DELTA = 60
MIN_REPORT = 1
# 主体上品红连通块 <= 这个面积才算"细边溢色"；更大的当成物品自带的紫光，保留。
SPILL_LIMIT = 3


def magenta_mask(array):
    red, green, blue, alpha = array[..., 0], array[..., 1], array[..., 2], array[..., 3]
    return (red.astype(np.int16) - green > MAGENTA_DELTA) & \
           (blue.astype(np.int16) - green > MAGENTA_DELTA) & (alpha > 0)


def largest_component(mask):
    """4 连通的最大块（用 BFS；贴图都很小，够快）。"""
    height, width = mask.shape
    seen = np.zeros_like(mask)
    best = np.zeros_like(mask)
    best_size = 0

    for start_y in range(height):
        for start_x in range(width):
            if not mask[start_y, start_x] or seen[start_y, start_x]:
                continue

            queue = deque([(start_y, start_x)])
            seen[start_y, start_x] = True
            cells = []

            while queue:
                y, x = queue.popleft()
                cells.append((y, x))

                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx

                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))

            if len(cells) > best_size:
                best_size = len(cells)
                best = np.zeros_like(mask)

                for y, x in cells:
                    best[y, x] = True

    return best


def analyse(path):
    """返回 (漂浮品红掩码, 像素数, 主体边缘品红溢色掩码, 溢色数)。"""
    image = Image.open(path).convert("RGBA")
    array = np.asarray(image).astype(np.int16)

    opaque = array[..., 3] > 0
    magenta = magenta_mask(array)
    body = largest_component(opaque)

    # 与主体相连的品红 = 主体自带的紫/品红发光，保留
    floating = magenta & ~body

    # 溢色：紧贴透明、且在品红家族里的**主体**像素（会渗出粉边）
    height, width = opaque.shape
    near_transparent = np.zeros_like(opaque)

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            shifted = np.roll(np.roll(~opaque, dy, axis=0), dx, axis=1)
            near_transparent |= shifted

    spill = magenta & body & near_transparent

    return array, floating, int(floating.sum()), spill, int(spill.sum())


def small_magenta_on_body(array, spill, limit):
    """把主体上的品红溢色再按连通块分档：只留**细边**（<= limit 像素）的，保护大片紫光。

    `StarstringBow` 的紫色弓光是一整片连通区域，面积远大于细边；
    按颜色一刀切会把它一起洗掉（上一版工具踩过这个坑）。
    """
    height, width = spill.shape
    seen = np.zeros_like(spill)
    keep = np.zeros_like(spill)

    for start_y in range(height):
        for start_x in range(width):
            if not spill[start_y, start_x] or seen[start_y, start_x]:
                continue

            queue = deque([(start_y, start_x)])
            seen[start_y, start_x] = True
            cells = []

            while queue:
                y, x = queue.popleft()
                cells.append((y, x))

                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx

                        if 0 <= ny < height and 0 <= nx < width and spill[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))

            if len(cells) <= limit:
                for y, x in cells:
                    keep[y, x] = True

    return keep


def clean(path, despill=False, all_magenta=False):
    array, floating, _count, spill, _spill_count = analyse(path)

    # 1) 飘点直接变透明；`all_magenta` 用于**确认过本体没有品红家族颜色**的物品
    #    （例：精钢法袍是白+蓝，那团贴着主体的粉块也是背景）
    if all_magenta:
        array[..., 3] = np.where(magenta_mask(array), 0, array[..., 3])
    else:
        array[..., 3] = np.where(floating, 0, array[..., 3])

    if despill:
        spill = small_magenta_on_body(array, spill, SPILL_LIMIT)

    # 2) 溢色：用 8 邻域里"非品红的不透明像素"均值替换
    if spill.any():
        rgb = array[..., :3].astype(np.float32)
        replaced = rgb.copy()
        coords = np.argwhere(spill)

        for y, x in coords:
            neighbours = []

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx

                    if not (0 <= ny < array.shape[0] and 0 <= nx < array.shape[1]):
                        continue

                    if array[ny, nx, 3] == 0 or floating[ny, nx]:
                        continue

                    if magenta_mask(array[ny:ny + 1, nx:nx + 1])[0, 0]:
                        continue

                    neighbours.append(rgb[ny, nx])

            if neighbours:
                replaced[y, x] = np.mean(neighbours, axis=0)

        array[..., :3] = replaced

    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), "RGBA")


def iter_pngs():
    for dirpath, dirs, files in os.walk(MOD_ROOT):
        dirs[:] = [d for d in dirs if d not in ("obj", "bin", ".vs")]

        for name in sorted(files):
            if name.endswith(".png"):
                yield os.path.join(dirpath, name)


def main():
    parser = argparse.ArgumentParser(description="删掉物品主体之外的品红残点")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--despill", action="store_true",
                        help="顺带洗掉主体边缘的细品红溢色（默认关，因为它会碰主体像素）")
    parser.add_argument("--strip-magenta", action="store_true",
                        help="激进模式：把**所有**品红家族像素都抠掉。只在确认过该物品"
                             "本体没有紫/品红颜色时使用（例：精钢法袍）。")
    parser.add_argument("--min-specks", type=int, default=MIN_REPORT,
                        help="只处理飘点数 >= 这个值的贴图（默认全部）")
    parser.add_argument("--dirs", nargs="*", default=None,
                        help="只扫这些子目录（相对模组根，例如 Content/Items/Armor）")
    parser.add_argument("--paths", nargs="*", default=None)
    args = parser.parse_args()

    targets = []

    for path in (args.paths or iter_pngs()):
        if args.dirs:
            relative = os.path.relpath(path, MOD_ROOT).replace("\\", "/")

            if not any(relative.startswith(d.strip("/")) for d in args.dirs):
                continue

        _array, floating, count, _spill, spill_count = analyse(path)

        if count >= args.min_specks and count + spill_count >= MIN_REPORT:
            targets.append((path, count, spill_count))

    print("命中 %d 张有品红残点/溢色的贴图" % len(targets))

    for path, count, spill_count in sorted(targets, key=lambda item: -(item[1] + item[2])):
        print("  %-58s 飘点=%4d 溢色=%4d"
              % (os.path.relpath(path, MOD_ROOT), count, spill_count))

    if not args.fix or not targets:
        return 0

    for path, _count, _spill in targets:
        relative = os.path.relpath(path, MOD_ROOT)
        backup = os.path.join(BACKUP_ROOT, relative)
        os.makedirs(os.path.dirname(backup), exist_ok=True)

        if not os.path.exists(backup):
            shutil.copy2(path, backup)

        # 每次都从原始备份重做，避免反复抠上一次的结果
        clean(backup, despill=args.despill, all_magenta=args.strip_magenta).save(path)

    print("已清理 %d 张；原始备份在 %s" % (len(targets), BACKUP_ROOT))
    print("---- 复测 ----")

    worst = 0

    for path, _count, _spill in targets:
        _array, floating, count, _spill_mask, spill_count = analyse(path)
        worst = max(worst, count + spill_count)

    print("最大残留 = %d 像素" % worst)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
