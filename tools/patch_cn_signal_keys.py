# -*- coding: utf-8 -*-
"""把主模组 zh-Hans 里已经有、但译文表（sync_cn_translation.TRANSLATIONS）里漏掉的键补进去。

背景：上一轮有人把 Signal*/Rift*/Orbit/Starstring/GapChakram/VoidSeed 这批键的中文
直接写进了 `WastelandSoul/Localization/zh-Hans_Mods.WastelandSoul.hjson`（模组自己那份），
却没进汉化补丁的译文表 —— 于是 `--sync` 会把它们写成 `// English` 占位注释，
`check_cn_parity.py` 报 31 条"中文缺失（必须有）"。

这个脚本把它们从模组那份 zh-Hans 里读出来，补成 `"Items.Xxx.DisplayName": "..."` 这种形式
插进译文表（已存在的不动，幂等）。
"""
import io
import os
import re
import sys

MOD_ZH = r"E:\开发\WastelandSoul\Localization\zh-Hans_Mods.WastelandSoul.hjson"
TOOL = r"E:\开发\tools\sync_cn_translation.py"

SECTION = re.compile(r"^(\w+):\s*\{\s*$")
CLASS = re.compile(r"^\t(\w+):\s*\{\s*$")
LEAF = re.compile(r"^\t\t(\w+):\s*(.+?)\s*$")


def read_pairs():
    """读出 `章节.类.键 -> 中文`（只认两级嵌套，正是这个文件的结构）。"""
    pairs = {}
    section = None
    klass = None

    for raw in io.open(MOD_ZH, encoding="utf-8").read().split("\n"):
        line = raw.rstrip()

        if not line.strip() or line.strip().startswith("//"):
            continue

        m = SECTION.match(line)
        if m:
            section, klass = m.group(1), None
            continue

        if line.strip() == "}":
            if klass is not None:
                klass = None
            else:
                section = None
            continue

        m = CLASS.match(line)
        if m:
            klass = m.group(1)
            continue

        m = LEAF.match(line)
        if m and section and klass:
            pairs["%s.%s.%s" % (section, klass, m.group(1))] = m.group(2)

    return pairs


def main():
    pairs = read_pairs()
    source = io.open(TOOL, encoding="utf-8").read()
    missing = [(k, v) for k, v in sorted(pairs.items()) if ('"%s"' % k) not in source]

    if not missing:
        print("译文表里没有遗漏（%d 条都在）" % len(pairs))
        return 0

    marker = "    # ---- 由 patch_cn_signal_keys.py 补录（模组 zh-Hans 里已有、译文表漏掉的键） ----"
    block = [marker]
    for key, value in missing:
        block.append('    "%s": "%s",' % (key, value))

    if marker in source:
        source = source.replace(marker + "\n", marker + "\n" + "\n".join(block[1:]) + "\n")
    else:
        source = source.rstrip("\n") + "\n\n" + "\n".join(block) + "\n"

    io.open(TOOL, "w", encoding="utf-8", newline="").write(source)
    print("补录 %d 条：" % len(missing))
    for key, value in missing:
        print("   +", key, "=", value[:40])
    return 0


if __name__ == "__main__":
    sys.exit(main())
