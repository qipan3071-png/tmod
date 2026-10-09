# -*- coding: utf-8 -*-
"""Add // sync-ok to Main.rand lines that only affect dust/fx in the following block."""
import os
import re
import sys

MOD_ROOT = os.path.join(os.path.dirname(__file__), "..", "WastelandSoul")
RAND_RE = re.compile(r"Main\.rand\.")
BEHAVIOR = re.compile(
    r"(NPC\.velocity|Projectile\.velocity\s*[+=]|localAI\[.*Main\.rand|NewProjectile|StrikeNPC|minion\.ai\[.*Main\.rand|NPC\.HitInfo)"
)


def block_after(lines, i):
    parts = []
    for j in range(i + 1, min(i + 10, len(lines))):
        parts.append(lines[j])
        if lines[j].strip() == "}":
            break
    return "".join(parts)


def main():
    changed = 0
    for sub in ("Content/NPCs", "Content/Projectiles"):
        root = os.path.normpath(os.path.join(MOD_ROOT, sub))
        for dp, _, fns in os.walk(root):
            for fn in fns:
                if not fn.endswith(".cs"):
                    continue
                path = os.path.join(dp, fn)
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
                out = []
                mod = False
                for i, line in enumerate(lines):
                    if RAND_RE.search(line) and "sync-ok" not in line:
                        blk = block_after(lines, i)
                        combined = line + blk
                        if BEHAVIOR.search(combined):
                            out.append(line)
                            continue
                        if any(x in blk for x in ("Dust", "WastelandFx", "WastelandSpark", "SoundEngine")):
                            line = line.rstrip("\n\r") + " // sync-ok: visual only\n"
                            mod = True
                            changed += 1
                    out.append(line)
                if mod:
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        f.writelines(out)
    print("annotated", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
