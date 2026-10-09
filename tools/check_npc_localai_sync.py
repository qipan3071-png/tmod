# -*- coding: utf-8 -*-
"""Report NPC localAI usage (tML does not sync localAI — behavior state should use ai[]).

Pipeline: REPORT ONLY (exit 0). Tracks remaining debt after batch 50~51 wildlife migration.
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "WastelandSoul", "Content", "NPCs"))
PAT = re.compile(r"\.localAI\[")


def main():
    rows = []
    for dirpath, _, files in os.walk(ROOT):
        for name in files:
            if not name.endswith(".cs"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, os.path.join(ROOT, "..", "..")).replace("\\", "/")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            has_extra_ai = "ReceiveExtraAI" in text and "SendExtraAI" in text
            n = 0
            for line in text.splitlines():
                if not PAT.search(line) or line.strip().startswith("//"):
                    continue
                if "sync-ok" in line:
                    continue
                if has_extra_ai and (".localAI[1]" in line or ".localAI[2]" in line):
                    continue
                n += 1
            if n:
                rows.append((n, rel))

    rows.sort(key=lambda x: (-x[0], x[1]))
    if not rows:
        print("NPC localAI：0 处待关注（行为状态应已迁 ai[] 或 ExtraAI）")
        return 0

    total = sum(r[0] for r in rows)
    print("NPC localAI 引用（未同步，需 ai[] / SendExtraAI / sync-ok）：%d 处 / %d 个文件" % (total, len(rows)))
    for n, rel in rows[:20]:
        print("  %3d  %s" % (n, rel))
    if len(rows) > 20:
        print("  ... 另有 %d 个文件" % (len(rows) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main())
