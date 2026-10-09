# -*- coding: utf-8 -*-
"""Remove the ScavengerGrace armour set (player: "这个不是我写的好像，删去吧").

The set lives in exactly four places; this script edits/deletes all of them and
reports what changed so the removal can be verified afterwards:

  1. Content/Items/Armor/WastelandArmorSets.cs -- the 3 item classes + the abstract base
  2. Content/Items/Armor/ScavengerGrace*.png   -- 6 sprites (icon + equip sheet x 3)
  3. WastelandSoul/Localization/en-US_Mods.WastelandSoul.hjson -- 3 DisplayName/Tooltip blocks
  4. tools/sync_cn_translation.py -- the matching zh-Hans entries (else check_cn_parity fails)

Backups go to .backup/removed-scavenger-grace/.
"""
import glob
import os
import re
import shutil

MAIN = r"E:\开发\WastelandSoul"
BACKUP = r"E:\开发\.backup\removed-scavenger-grace"
ARMOR = os.path.join(MAIN, r"Content\Items\Armor")
SETS_CS = os.path.join(ARMOR, "WastelandArmorSets.cs")
EN_HJSON = os.path.join(MAIN, r"Localization\en-US_Mods.WastelandSoul.hjson")
SYNC_PY = r"E:\开发\tools\sync_cn_translation.py"

NAMES = ("ScavengerGraceHood", "ScavengerGraceJacket", "ScavengerGraceBoots")


def backup(path):
    rel = os.path.relpath(path, r"E:\开发")
    dst = os.path.join(BACKUP, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(path, dst)


def drop_class_block(text, anchor):
    """Delete the [AutoloadEquip...] + class block whose declaration contains `anchor`."""
    start = text.index(anchor)
    # walk back to the attribute line
    head = text.rfind("\n\t[AutoloadEquip", 0, start)

    if head < 0:
        head = text.rfind("\n\tpublic class", 0, start)

    # find the closing brace of the class: first "\n\t}" after start
    tail = text.index("\n\t}\n", start) + len("\n\t}\n")
    return text[:head + 1] + text[tail:]


def main():
    os.makedirs(BACKUP, exist_ok=True)
    report = []

    # 1) code
    backup(SETS_CS)
    text = open(SETS_CS, encoding="utf-8").read()
    before = len(text)

    for name in NAMES:
        text = drop_class_block(text, "public class %s :" % name)

    # the abstract base class
    if "abstract class ScavengerGracePiece" in text:
        head = text.index("/// <summary>清道夫之惠三件")
        tail = text.index("\n\t}\n", text.index("abstract class ScavengerGracePiece")) + len("\n\t}\n")
        text = text[:head] + text[tail:]

    # the section banner
    text = text.replace(
        "\t// ====================================================================================\n"
        "\t// 一、清道夫之惠（Scavenger's Grace）—— 精钢之后的过渡套，主打\"跑得快、摔不死、残血能跑\"\n"
        "\t// ====================================================================================\n\n", "")

    open(SETS_CS, "w", encoding="utf-8", newline="\n").write(text)
    report.append("WastelandArmorSets.cs  %d -> %d 字节" % (before, len(text)))

    # 2) sprites
    for path in sorted(glob.glob(os.path.join(ARMOR, "ScavengerGrace*.png"))):
        backup(path)
        os.remove(path)
        report.append("删除 %s" % os.path.basename(path))

    # 3) en-US localisation blocks
    backup(EN_HJSON)
    lines = open(EN_HJSON, encoding="utf-8").read().splitlines(keepends=True)
    output = []
    skip_depth = 0

    for line in lines:
        stripped = line.strip()

        if skip_depth == 0:
            for name in NAMES:
                if stripped.startswith(name + ": {"):
                    skip_depth = 1
                    break

        if skip_depth:
            if stripped.endswith("}") and not stripped.endswith("{") and skip_depth == 1:
                skip_depth = 0
            continue

        output.append(line)

    open(EN_HJSON, "w", encoding="utf-8", newline="\n").write("".join(output))
    report.append("en-US hjson 去掉 %d 行" % (len(lines) - len(output)))

    # 4) zh-Hans entries in the sync table
    backup(SYNC_PY)
    sync_text = open(SYNC_PY, encoding="utf-8").read()
    removed = 0

    for name in NAMES:
        for suffix in ("DisplayName", "Tooltip"):
            pattern = re.compile(r'^\s*"%s\.%s":.*\n' % (name, suffix), re.M)
            sync_text, count = pattern.subn("", sync_text)
            removed += count

    open(SYNC_PY, "w", encoding="utf-8", newline="\n").write(sync_text)
    report.append("sync_cn_translation.py 去掉 %d 条译文" % removed)

    for line in report:
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
