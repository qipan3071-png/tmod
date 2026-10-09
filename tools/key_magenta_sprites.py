# -*- coding: utf-8 -*-
"""把还留着品红背景的贴图补做抠图（品红 -> alpha）。

背景（玩家实测）
----------------
"抠图不干净的有包括物品周围是粉紫色的，应该是这个方形贴图除物品都是粉紫色"
—— 精确命中：有一批贴图**背景是整片不透明品红**，压根没跑过抠图流程。
扫描实测 10 张（不透明品红像素数）：

    ArchivistSummonerWeapon(.EX)  1387
    ArchivistCSummoner             1118
    SalvagedSteelWarriorHelm        418
    ScavengerGraceHood              228
    StarstringBow                   135
    SalvagedSteelMageRobe           122   （玩家点名的"精钢法袍"）
    RiftCleaver / OrbitScepter / SignalRigHelm   76 / 59 / 48

修法
----
**只删"与画布边缘连通"的品红背景**（从四边向内漫水填充），而不是按颜色整体淡出。
原因：有些物品**自带紫/品红发光**（例 `StarstringBow` 是紫黑弓臂 + 青弦 + 中心紫光），
按颜色抠会误伤主体（实测掉 54 个本体像素）；只有整片粉底那种才是背景。
清完再 `bleed_fix` 防止缩放把残留的粉色渗成紫边。

用法:
    python tools/key_magenta_sprites.py            # 扫描并报告
    python tools/key_magenta_sprites.py --fix      # 就地补抠图（先备份原始文件）
"""
import argparse
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from art_common import bleed_fix  # noqa: E402

MOD_ROOT = r"E:\开发\WastelandSoul"
BACKUP_ROOT = r"E:\开发\.backup\sprite-magenta"

# 判定为"品红背景残留"的门限：不透明且 R、B 都明显高于 G
MAGENTA_DELTA = 60
MAGENTA_MIN_PIXELS = 30


def border_connected_magenta(path, delta=MAGENTA_DELTA):
    """只挑出**与画布边缘相连**的品红像素（真正的背景），返回布尔掩码与像素数。

    ⚠️ 为什么不能直接用 `art_common.key_magenta`：它是**按颜色**把品红整体淡出，
    对"自带紫/品红发光"的物品会**误伤主体**。
    实测 `StarstringBow`（紫黑弓臂 + 青弦 + 中心紫光）用按颜色抠会掉 54 个本体像素，
    而 `ArchivistSummonerWeapon` 的背景才真的是整片亮粉方块。
    所以改成"从四边向内漫水填充"：只有与边框连通的品红才算背景。
    """
    array = np.asarray(Image.open(path).convert("RGBA")).astype(np.int16)
    red, green, blue, alpha = array[..., 0], array[..., 1], array[..., 2], array[..., 3]
    magenta = (red - green > delta) & (blue - green > delta) & (alpha > 0)

    height, width = magenta.shape
    seeds = []

    for x in range(width):
        for y in (0, height - 1):
            if magenta[y, x]:
                seeds.append((y, x))

    for y in range(height):
        for x in (0, width - 1):
            if magenta[y, x]:
                seeds.append((y, x))

    connected = np.zeros_like(magenta)
    stack = list(seeds)

    while stack:
        y, x = stack.pop()

        if y < 0 or x < 0 or y >= height or x >= width:
            continue

        if connected[y, x] or not magenta[y, x]:
            continue

        connected[y, x] = True
        stack.append((y - 1, x))
        stack.append((y + 1, x))
        stack.append((y, x - 1))
        stack.append((y, x + 1))

    return array, connected


def count_opaque_magenta(path):
    _array, connected = border_connected_magenta(path)
    return int(connected.sum())


def remove_background(path):
    """把与边缘连通的品红背景变透明，其余像素（含主体自带的紫色）原样保留。"""
    array, connected = border_connected_magenta(path)
    array[..., 3] = np.where(connected, 0, array[..., 3])

    # 背景刚变透明的那些格子，RGB 还是粉色，会把缩放后的边缘染紫 —— 补一下
    return bleed_fix(Image.fromarray(array.astype(np.uint8), "RGBA"), rounds=2)


def iter_pngs():
    for dirpath, dirs, files in os.walk(MOD_ROOT):
        dirs[:] = [d for d in dirs if d not in ("obj", "bin", ".vs")]

        for name in sorted(files):
            if name.endswith(".png"):
                yield os.path.join(dirpath, name)


def main():
    parser = argparse.ArgumentParser(description="给还留着品红背景的贴图补做抠图")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--paths", nargs="*", default=None)
    args = parser.parse_args()

    targets = []

    for path in (args.paths or iter_pngs()):
        count = count_opaque_magenta(path)

        if count >= MAGENTA_MIN_PIXELS:
            targets.append((path, count))

    print("命中 %d 张有不透明品红背景的贴图" % len(targets))

    for path, count in targets:
        print("  %-62s 不透明品红=%5d" % (os.path.relpath(path, MOD_ROOT), count))

    if not args.fix or not targets:
        return 0

    for path, _count in targets:
        relative = os.path.relpath(path, MOD_ROOT)
        backup = os.path.join(BACKUP_ROOT, relative)
        os.makedirs(os.path.dirname(backup), exist_ok=True)

        if os.path.exists(backup):
            # 已经有原始备份：这次在**原始像素**上重做，避免"把上一次的结果再抠一遍"
            remove_background(backup).save(path)
        else:
            shutil.copy2(path, backup)
            remove_background(path).save(path)

    print("已补抠图 %d 张；备份在 %s" % (len(targets), BACKUP_ROOT))
    print("---- 复测 ----")

    for path, _count in targets:
        print("  %-62s 不透明品红=%5d"
              % (os.path.relpath(path, MOD_ROOT), count_opaque_magenta(path)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
