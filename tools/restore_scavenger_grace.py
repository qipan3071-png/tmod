# -*- coding: utf-8 -*-
"""把「清道夫恩典」（ScavengerGrace，射手套装）加回来。

背景：玩家先让我删掉它（"不是我写的"），随后自己发现——**它是射手的套装**
（兜帽给 Ranged +5%、靴子给攻速 + 移速，套装奖励是摔落免疫 + 残血加速），
所以要求原样恢复。上一轮我把它和**盗贼**（`SalvagedSteelRogue*`）搞混了；
盗贼确实要删，清道夫恩典要留。

做法：只做**定点插回**，不整文件回滚（避免把后来对盗贼/战士做的改动一起退回去）。
  1. 6 张 PNG 直接从 .backup/removed-scavenger-grace/ 拷回；
  2. WastelandArmorSets.cs 在"灰烬之心"分节前插回 3 个物品类 + 抽象基类；
  3. en-US hjson 插回 3 个条目块；sync_cn_translation.py 插回 4 条译文。
"""
import os
import shutil

ROOT = r"E:\开发"
BAK = os.path.join(ROOT, ".backup", "removed-scavenger-grace")
MAIN = os.path.join(ROOT, "WastelandSoul")
ARMOR = os.path.join(MAIN, r"Content\Items\Armor")
SETS_CS = os.path.join(ARMOR, "WastelandArmorSets.cs")
EN_HJSON = os.path.join(MAIN, r"Localization\en-US_Mods.WastelandSoul.hjson")
SYNC_PY = os.path.join(ROOT, "tools", "sync_cn_translation.py")

NAMES = ("ScavengerGraceHood", "ScavengerGraceJacket", "ScavengerGraceBoots")


def extract_class_block(text, name):
    """Cut the [AutoloadEquip...] + class block whose declaration contains `name`."""
    start = text.index("public class %s :" % name)
    head = text.rfind("\n\t[AutoloadEquip", 0, start)
    tail = text.index("\n\t}\n", start) + len("\n\t}\n")
    return text[head + 1:tail]


def extract_abstract_block(text, name):
    start = text.index("abstract class %s" % name)
    head = text.rindex("\n\t/// <summary>", 0, start)
    tail = text.index("\n\t}\n", start) + len("\n\t}\n")
    return text[head + 1:tail]


def main():
    old_sets = open(os.path.join(BAK, r"WastelandSoul\Content\Items\Armor\WastelandArmorSets.cs"),
                    encoding="utf-8").read()
    old_en = open(os.path.join(BAK, r"WastelandSoul\Localization\en-US_Mods.WastelandSoul.hjson"),
                  encoding="utf-8").read()
    old_sync = open(os.path.join(BAK, r"tools\sync_cn_translation.py"), encoding="utf-8").read()

    # 1) sprites
    restored = []
    for name in ("ScavengerGraceBoots", "ScavengerGraceBoots_Legs", "ScavengerGraceHood",
                 "ScavengerGraceHood_Head", "ScavengerGraceJacket", "ScavengerGraceJacket_Body"):
        src = os.path.join(BAK, r"WastelandSoul\Content\Items\Armor", name + ".png")
        shutil.copy2(src, os.path.join(ARMOR, name + ".png"))
        restored.append(name + ".png")

    # 2) code
    block = []
    block.append("\t// ====================================================================================")
    block.append("\t// 一、清道夫之惠（Scavenger's Grace）—— 精钢之后的过渡套，主打\"跑得快、摔不死、残血能跑\"")
    block.append("\t// ====================================================================================")
    block.append("")

    for name in NAMES:
        block.append(extract_class_block(old_sets, name).rstrip("\n"))
        block.append("")

    block.append(extract_abstract_block(old_sets, "ScavengerGracePiece").rstrip("\n"))
    block.append("")

    text = open(SETS_CS, encoding="utf-8").read()
    anchor = "\t// ====================================================================================\n\t// 二、灰烬之心"
    text = text.replace(anchor, "\n".join(block) + "\n" + anchor, 1)
    open(SETS_CS, "w", encoding="utf-8", newline="\n").write(text)

    # 3) en-US localisation
    blocks = []

    for name in NAMES:
        start = old_en.index("\t\t%s: {" % name)
        end = old_en.index("\t\t}\n", start) + len("\t\t}\n")
        blocks.append(old_en[start:end])

    text = open(EN_HJSON, encoding="utf-8").read()
    local_anchor = "\t\tAshHeartMask: {"
    text = text.replace(local_anchor, "".join(blocks) + "\n" + local_anchor, 1)
    open(EN_HJSON, "w", encoding="utf-8", newline="\n").write(text)

    # 4) zh-Hans translation table
    lines = []

    for raw in old_sync.splitlines(keepends=True):
        stripped = raw.strip()

        if any(stripped.startswith('"%s.' % name) for name in NAMES):
            lines.append(raw)

    text = open(SYNC_PY, encoding="utf-8").read()
    sync_anchor = '    "MechanicalCompanion.DisplayName"'
    text = text.replace(sync_anchor, "".join(lines) + sync_anchor, 1)
    open(SYNC_PY, "w", encoding="utf-8", newline="\n").write(text)

    print("恢复贴图 %d 张" % len(restored))
    print("插入代码块 %d 段 + 抽象基类 1 段" % len(NAMES))
    print("插入 en-US 条目 %d 块 / 译文 %d 条" % (len(blocks), len(lines)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
