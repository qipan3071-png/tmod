# -*- coding: utf-8 -*-
"""联机生成守卫：敌对 NPC/弹幕不得用会跳过专用服的门闩。

错误写法（Host & Play 正常、``-server`` 不出弹）::

    if (Main.dedServ || Main.netMode == NetmodeID.MultiplayerClient) return;
    if (!Main.dedServ && Main.netMode != NetmodeID.MultiplayerClient) { NewProjectile... }

正确写法::

    if (!WastelandNet.IsAuthoritativeSide) return;   # 单机 / Host / 专用服都生成
    # 玩家弹幕的子弹：if (Projectile.owner != Main.myPlayer) return;
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "WastelandSoul"))
SCAN = (
    os.path.join("Content", "NPCs"),
    os.path.join("Content", "Projectiles"),
)

BAD = (
    re.compile(r"Main\.dedServ\s*\|\|\s*Main\.netMode\s*==\s*NetmodeID\.MultiplayerClient"),
    re.compile(r"!Main\.dedServ\s*&&\s*Main\.netMode\s*!=\s*NetmodeID\.MultiplayerClient"),
)


def iter_files():
    for sub in SCAN:
        root = os.path.join(ROOT, sub)
        for dirpath, _, names in os.walk(root):
            for name in names:
                if name.endswith(".cs"):
                    yield os.path.join(dirpath, name)


def main():
    hits = []
    for path in iter_files():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, encoding="utf-8") as handle:
            for i, line in enumerate(handle, 1):
                if "sync-ok" in line:
                    continue
                for pat in BAD:
                    if pat.search(line):
                        hits.append("%s:%d  %s" % (rel, i, line.strip()))
                        break

    if hits:
        print("生成门闩会跳过专用服（改用 WastelandNet.IsAuthoritativeSide）：")
        for row in hits:
            print("  " + row)
        return 1

    print("生成门闩：0 处专用服误挡")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
