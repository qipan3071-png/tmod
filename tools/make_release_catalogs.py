# -*- coding: utf-8 -*-
"""从汉化表抽出发布用介绍清单（物品 / Boss与生成怪）。"""
import io
import os
import re
from datetime import datetime

CN = r"E:\开发\WastelandSoulCN\Localization\zh-Hans_Mods.WastelandSoul.hjson"
OUT_DIR = r"E:\开发\发布"
ITEM_OUT = os.path.join(OUT_DIR, "物品介绍清单.txt")
NPC_OUT = os.path.join(OUT_DIR, "Boss与生成怪介绍清单.txt")

NPC_BLURB = {
    "MechanicalCompanion": "城镇 NPC。用机械核心在精灵族遗迹躯体上唤醒。商店用芯片换物资。",
    "Scavenger": "Boss。档位：骷髅王之后、血肉墙之前。每 5 天来袭，或用清道夫信号传感器召唤。",
    "ScavengerRepairDrone": "清道夫二阶段召唤的维修无人机，给 Boss 回血，不攻击玩家。",
    "Archivist": "Boss。档位：困难模式机械三王一级。用归档者残响召唤。",
    "AshHeart": "Boss。击败石巨人后，用灰烬之心余烬召唤。",
    "AshWisp": "灰烬之心战斗中的残灵，给 Boss 回血。",
    "FireplaceGuardian": "Boss。壁炉深处，月亮领主之前。用壁炉通行密钥召唤。",
    "ScrapCrawler": "肉前白天地表。四档剧情怪其一。",
    "IndexMoth": "击败清道夫后，泥土层。",
    "AshStalker": "困难模式且击败归档者后，岩石层/地狱。",
    "HearthWarden": "困难模式且击败灰烬之心后，夜晚地表。",
    "ScrapLeaper": "肉前白天地表，跳跃扑咬。",
    "RustCharger": "肉前白天地表，蓄力冲锋。",
    "GaleWisp": "夜晚地表空中，俯冲追踪。",
    "SpitterFly": "夜晚地表空中，保持距离喷吐。",
    "CaveCrawler": "泥土/岩石层，贴墙爬行。",
    "AshTickBat": "洞穴空中乱飞。",
    "PollutionSlime": "困难模式，地表/泥土层，污染减益。",
    "GearSwarmHive": "困难模式。齿轮群母体。",
    "GearSwarm": "由齿轮蜂巢召唤，不自然刷新。",
    "CinderMender": "困难模式，给同伴回血、自己开盾。",
    "ScrapReaper": "困难模式迷你 Boss，两段招式。",
    "RelayBeetle": "占位槽：清道夫后、肉前、白天地表。设定待补。",
    "NightGnawer": "占位槽：清道夫后、肉前、夜晚地表。设定待补。",
    "LedgerHawk": "占位槽：归档者后、地表。设定待补。",
    "CinderLurker": "占位槽：灰烬之心后、洞穴。设定待补。",
}

BOSS_KEYS = ("Scavenger", "Archivist", "AshHeart", "FireplaceGuardian", "ScrapReaper")


def parse_hjson(path):
    text = io.open(path, encoding="utf-8-sig").read()
    items = {}
    npcs = {}
    checklist = {}
    section = None
    current = None
    current_map = None
    buf_key = None
    buf = []
    in_triple = False

    def flush_item():
        pass

    i = 0
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped in ("Items: {", "NPCs: {", "BossChecklist: {", "Projectiles: {", "Buffs: {", "Tiles: {"):
            section = stripped.split(":")[0]
            current = None
            continue
        if section and stripped == "}":
            # may be inner or section end; if indent of line is 0-ish
            if not line.startswith("\t"):
                section = None
            continue
        if section == "BossChecklist" and ".SpawnInfo:" in stripped:
            key, _, val = stripped.partition(":")
            checklist[key.strip().replace(".SpawnInfo", "")] = val.strip()
            continue
        if section == "NPCs" and ".DisplayName:" in stripped:
            key, _, val = stripped.partition(":")
            npcs[key.strip().replace(".DisplayName", "")] = {"DisplayName": val.strip()}
            continue
        npc_block = re.match(r"^\t([A-Za-z0-9_]+):\s*\{", line)
        if section == "NPCs" and npc_block:
            current = npc_block.group(1)
            npcs.setdefault(current, {})
            continue
        if section == "NPCs" and current and re.match(r"^\t\tDisplayName:\s*(.*)$", line):
            npcs[current]["DisplayName"] = re.match(r"^\t\tDisplayName:\s*(.*)$", line).group(1).strip()
            continue
        if section != "Items":
            continue
        m_open = re.match(r"^(\t)([A-Za-z0-9_]+):\s*\{", line)
        if m_open:
            current = m_open.group(2)
            items[current] = {}
            continue
        if current and re.match(r"^\t\}$", line):
            current = None
            continue
        if current and in_triple:
            if stripped == "'''":
                if not buf:
                    continue
                items[current][buf_key] = "\n".join(buf)
                in_triple = False
                buf = []
                buf_key = None
            else:
                buf.append(stripped)
            continue
        if current:
            m = re.match(r"^\t\t(DisplayName|Tooltip|SetBonus|Tooltip2):\s*(.*)$", line)
            if not m:
                continue
            field, rest = m.group(1), m.group(2).strip()
            if rest in ("'''", ""):
                in_triple = True
                buf_key = field
                buf = []
            elif rest in ('""', "''"):
                items[current][field] = ""
            else:
                if (rest.startswith('"') and rest.endswith('"')) or (rest.startswith("'") and rest.endswith("'")):
                    rest = rest[1:-1]
                items[current][field] = rest
    return items, npcs, checklist


def write_items(items):
    lines = [
        "废土魂穿 · 物品介绍清单",
        "打包时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "说明：以下为模组物品在游戏里看到的名字与介绍（原版物品不含在内）。",
        "合成方式请看合成栏，不写在介绍里。",
        "",
    ]
    for key in sorted(items, key=lambda k: items[k].get("DisplayName", k)):
        block = items[key]
        name = block.get("DisplayName", key)
        lines.append("【%s】" % name)
        tip = block.get("Tooltip", "")
        if tip:
            for row in tip.split("\n"):
                if row:
                    lines.append("  %s" % row)
        else:
            lines.append("  （无额外介绍；数值看面板）")
        bonus = block.get("SetBonus")
        if bonus:
            lines.append("  套装奖励：%s" % bonus.replace("\n", " / "))
        extra = block.get("Tooltip2")
        if extra:
            lines.append("  %s" % extra.replace("\n", " / "))
        lines.append("")
    os.makedirs(OUT_DIR, exist_ok=True)
    io.open(ITEM_OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("items", len(items), ITEM_OUT)


def write_npcs(npcs, checklist):
    lines = [
        "废土魂穿 · Boss 与生成怪介绍清单",
        "打包时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "说明：原版小怪不改。下列为本模组 NPC。占位槽只有刷新时间点，设定未定。",
        "",
        "—— Boss ——",
        "",
    ]
    for key in BOSS_KEYS:
        name = npcs.get(key, {}).get("DisplayName", key)
        lines.append("【%s】" % name)
        if key in checklist:
            lines.append("  召唤/档位：%s" % checklist[key])
        if key in NPC_BLURB:
            lines.append("  %s" % NPC_BLURB[key])
        lines.append("")
    lines.append("—— 城镇 / 战斗召唤物 ——")
    lines.append("")
    for key in ("MechanicalCompanion", "ScavengerRepairDrone", "AshWisp"):
        name = npcs.get(key, {}).get("DisplayName", key)
        lines.append("【%s】" % name)
        lines.append("  %s" % NPC_BLURB.get(key, ""))
        lines.append("")
    lines.append("—— 野外生成怪 ——")
    lines.append("")
    for key in sorted(npcs, key=lambda k: npcs[k].get("DisplayName", k)):
        if key in BOSS_KEYS or key in ("MechanicalCompanion", "ScavengerRepairDrone", "AshWisp"):
            continue
        name = npcs[key].get("DisplayName", key)
        lines.append("【%s】" % name)
        if key in NPC_BLURB:
            lines.append("  %s" % NPC_BLURB[key])
        lines.append("")
    io.open(NPC_OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("npcs", len(npcs), NPC_OUT)


def main():
    items, npcs, checklist = parse_hjson(CN)
    write_items(items)
    write_npcs(npcs, checklist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
