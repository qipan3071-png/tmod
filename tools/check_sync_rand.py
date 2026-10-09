# -*- coding: utf-8 -*-
"""联机同步守卫：**AI 里不许直接用 `Main.rand` 参与"行为决策"**。

为什么存在
----------
玩家（2026-10-09）给的规矩：tModLoader 的多人框架**不等于**我们的模组自动支持多人。
它自动同步的是**原版字段**（NPC 位置/速度/生命/目标、`NPC.ai[0..3]`、弹幕基础字段、玩家原版属性…）；
**我们自己的随机结果、计时器、阶段状态**都要自己处理。

`Main.rand` 是最容易漏的一个：`NPC.AI()` 在服务端和**每个客户端**都会跑，
同一句 `interval + Main.rand.Next(-12, 13)` 在两边掷出**不同的数字**，
于是出招时机、弹幕落点、Boss 走位会慢慢错开 —— **单机永远复现不出来**。

正确写法（本仓约定的样板，见 `Common/Systems/WastelandRandom.cs` 与开发说明「联机同步」一节）::

    // ✅ 种子只取**已经同步过的**量（whoAmI / ai[] / 生命 / 世界时间…）
    ctx.AttackDelay = AttackIntervalPhaseOne + WastelandRandom.Roll(NPC.whoAmI, (int)NPC.ai[2], -20, 21);

检查项
------
扫 `Content/NPCs/**` 与 `Content/Projectiles/**` 里的 `Main.rand.<...>`，命中就报错并给行号。

**允许的例外**（白名单，写在下面的 ALLOW 里）：
  · 纯**视觉**的随机：`Dust` / `WastelandFx` / `SoundEngine` / `Emote`（客户端各画各的没关系）；
  · 判定条件里带 `Main.dedServ` 或 `NetmodeID.MultiplayerClient` 提前 return 的（本来就只有一端执行）；
  · 真正的"服务端掷完再广播"之后才用到的随机（这种要写 `// sync-ok` 注释说明）。

用法::

    python tools/check_sync_rand.py            # 全仓扫描（AI / 弹幕）
    python tools/check_sync_rand.py <文件...>  # 只查指定文件
"""
import os
import re
import sys

MOD_ROOT = r"E:\开发\WastelandSoul"
SCAN_DIRS = (
    os.path.join("Content", "NPCs"),
    os.path.join("Content", "Projectiles"),
)

RAND_RE = re.compile(r"Main\.rand\.(Next|NextFloat|NextBool|NextVector2\w*)")

# 命中行里出现这些标记就不算问题
ALLOW_MARKERS = (
    "sync-ok",              # 人工确认过：只有一端执行 / 只影响画面
    "check_sync_rand",      # 检查器自己
    "Dust", "dust",         # 纯尘埃
    "WastelandFx", "WastelandFxSystem",     # 纯特效
    "SoundEngine", "SoundID",               # 声音（本来就只在客户端）
    "Emote",
    "Main.dedServ",         # 条件里已经排除了服务端
    "MultiplayerClient",    # 条件里已经排除了客户端
)


def iter_files(targets=None):
    if targets:
        for path in targets:
            if os.path.isfile(path) and path.endswith(".cs"):
                yield path
        return

    for sub in SCAN_DIRS:
        root = os.path.join(MOD_ROOT, sub)
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.endswith(".cs"):
                    yield os.path.join(dirpath, name)


def main():
    targets = sys.argv[1:]
    problems = []
    scanned = 0

    for path in iter_files(targets):
        scanned += 1
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()

        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("///") or stripped.startswith("*"):
                continue                                    # 注释里提到 Main.rand 不算
            if not RAND_RE.search(line):
                continue
            if any(marker in line for marker in ALLOW_MARKERS):
                continue
            problems.append((path, index, stripped))

    rel = os.path.relpath
    if problems:
        print("联机同步：发现 %d 处 AI/弹幕里直接用 Main.rand（**会分叉**）" % len(problems))
        for path, index, text in problems:
            print("  %s:%d" % (rel(path, MOD_ROOT), index))
            print("      %s" % text[:110])
            print("      修法：改用 WastelandRandom.Roll(已同步的种子…)，或加 // sync-ok 说明为什么安全")
        return 1

    print("联机同步：扫了 %d 个 .cs，AI/弹幕里没有裸露的 Main.rand 决策" % scanned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
