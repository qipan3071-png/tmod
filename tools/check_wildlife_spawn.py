# -*- coding: utf-8 -*-
"""Report Wildlife ModNPC classes missing SpawnChance (must use vanilla tML spawn pool)."""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "WastelandSoul", "Content", "NPCs", "Wildlife"))
CLASS = re.compile(r"public\s+class\s+(\w+)\s*:\s*(?:EraMob|ModNPC)")
SPAWN = re.compile(r"SpawnChance\s*\(")


def main():
    missing = []
    for name in os.listdir(ROOT):
        if not name.endswith(".cs") or name == "WastelandNaturalSpawn.cs":
            continue
        path = os.path.join(ROOT, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if "abstract class" in text and "EraMob" in text:
            continue
        for m in CLASS.finditer(text):
            cls = m.group(1)
            if cls in ("WildlifeAI",):
                continue
            # crude: class block until next "public class" at column 0
            start = m.start()
            next_cls = text.find("\n\tpublic class ", start + 1)
            chunk = text[start:next_cls if next_cls > 0 else len(text)]
            if not SPAWN.search(chunk):
                missing.append("%s (%s)" % (cls, name))

    if not missing:
        print("Wildlife NPC：全部实现 SpawnChance（tML 自然刷怪池）")
        return 0

    print("Wildlife NPC 缺少 SpawnChance：%d" % len(missing))
    for line in missing:
        print("  ", line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
