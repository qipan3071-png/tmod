# -*- coding: utf-8 -*-
"""禁止"视觉污染型白色光效"（开发说明.md「特效红线」的机器化守卫）。

为什么存在
----------
玩家三次反馈同一类问题，最后明令禁止：

> 把武器当中的使用时会有的白色激光特效删去，召唤物攻击时会有的也要删去，
> 明令禁止做这种视觉污染的无效特效，特效做的太简陋且干扰操作

已经踩过的三个坑（都改成彩色或删除，并留了注释）：
  1. `ArchivistIndexBeam`：拿 `TextureAssets.MagicPixel`（1x1 白点）拉成
     620x17 的**实心白矩形**当激光 —— 玩家看到的是"大量白线和白色板块"；
  2. `WastelandFxSystem.DrawBolts` 的亮芯 `Color.Lerp(颜色, Color.White, 0.72)`
     —— 不管传什么颜色，画出来都是**白线**（现已改为等比提亮、保持色相）；
  3. `Scavenger` 过载自毁时随机甩的 2 道 72px 白闪电、`SignalProjectiles` 命中时的
     28px 小闪电 —— **不表示任何机制**，纯糊屏，已删除。

本检查器只看"画白色光效"的明显信号，不追求完备；命中就报错并指出行号。

检查项
------
A. 用 `MagicPixel` 画东西 —— 1x1 白点只会被拉伸成白条/白板，一律禁止；
B. 颜色字面量接近纯白（R/G/B 都 > 235）出现在与光效有关的调用里
   （`Bolt` / `Line` / `Glow` / `Spark` / `Beam` / `Streak`）；
C. `Color.Lerp(<任意>, Color.White, 比例 >= 0.6)` —— 这正是白芯的写法。

用法:
    python tools/check_no_white_fx.py            # 全仓扫描
    python tools/check_no_white_fx.py <文件...>  # 只查指定文件
"""
import os
import re
import sys

MOD_ROOT = r"E:\开发\WastelandSoul"
SCAN_DIRS = ("Common", "Content")

WHITE_LEVEL = 235

# 允许"接近白"的例外：这里是明确的材质/贴图色调，不是光效
ALLOW_MARKERS = (
    "check_no_white_fx",
    "特效红线",
    "视觉污染",
)

FX_CALLS = ("Bolt", "Line", "Glow", "Spark", "Beam", "Streak", "Impact")

# 允许 `MagicPixel` 的例外：**只画 1~2 像素的小点**是这套粒子系统的既定做法
# （`DrawSegment` 把小点串成折线、`DrawFlake` 画 8.5x2.6 的小碎片），
# 不是"拿白点拉成白条/白板"。真正的问题是**拉伸成大块**，那个已经在架构上避免：
# 大面积的激光/光柱一律走贴图（见 ArchivistIndexBeam 的教训）。
MAGIC_PIXEL_ALLOWED = {
    r"Common\Effects\WastelandFx.cs",
}

COLOR_LITERAL = re.compile(r"new\s+Color\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")
LERP_WHITE = re.compile(r"Color\.Lerp\s*\([^,]+,\s*Color\.White\s*,\s*([0-9]*\.?[0-9]+)f?\s*\)")


def iter_sources(paths):
    if paths:
        for path in paths:
            yield path
        return

    for folder in SCAN_DIRS:
        base = os.path.join(MOD_ROOT, folder)

        for dirpath, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("obj", "bin", ".vs")]

            for name in sorted(files):
                if name.endswith(".cs"):
                    yield os.path.join(dirpath, name)


def scan(path):
    problems = []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("//") or stripped.startswith("///"):
            continue

        if any(marker in line for marker in ALLOW_MARKERS):
            continue

        # A. MagicPixel：1x1 白点拉伸 = 白条/白板（白名单文件放行，见 MAGIC_PIXEL_ALLOWED）
        if "MagicPixel" in line and os.path.relpath(path, MOD_ROOT) not in MAGIC_PIXEL_ALLOWED:
            problems.append((index, "用 TextureAssets.MagicPixel 画光效（会变成白条/白板）", stripped))

        # B. 白到接近纯白的颜色用在光效调用上
        for match in COLOR_LITERAL.finditer(line):
            r, g, b = (int(match.group(i)) for i in (1, 2, 3))

            if r > WHITE_LEVEL and g > WHITE_LEVEL and b > WHITE_LEVEL:
                if any(call in line for call in FX_CALLS):
                    problems.append((index, "光效颜色接近纯白 (%d,%d,%d)" % (r, g, b), stripped))
                    break

        # C. 向白色插值的"白芯"
        for match in LERP_WHITE.finditer(line):
            amount = float(match.group(1))

            if amount >= 0.6:
                problems.append((index, "Color.Lerp(..., Color.White, %.2f) —— 这就是白芯写法" % amount, stripped))
                break

    return problems


def main():
    args = sys.argv[1:]
    total = 0
    scanned = 0

    for path in iter_sources(args):
        scanned += 1
        problems = scan(path)

        if not problems:
            continue

        relative = os.path.relpath(path, MOD_ROOT)
        print("!! %s" % relative)

        for index, reason, text in problems:
            print("   %s:%d  %s" % (relative, index, reason))
            print("       %s" % text)
            total += 1

    print("-" * 68)
    print("扫描 %d 个 .cs 文件，发现 %d 处'白色光效'违规" % (scanned, total))

    if total:
        print("参照 开发说明.md「特效红线」：光效必须带自己的色相，")
        print("亮芯用等比提亮（WastelandFxSystem.ScaleRgb），不要 Lerp 到白色；")
        print("不要用 MagicPixel 拉白条；不表示机制的光效直接删掉。")
        return 1

    print("OK  没有发现白色光效污染")
    return 0


if __name__ == "__main__":
    sys.exit(main())
