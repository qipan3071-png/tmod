# -*- coding: utf-8 -*-
"""把物品 / NPC 清单写成带数值、合成和掉落的版本。"""
import io
import os
import re
from datetime import datetime

MOD_ROOT = r"E:\开发\WastelandSoul"

VANILLA = {
    "Amber": "琥珀", "AnkhShield": "十字章护盾", "BeetleHusk": "甲虫壳",
    "Blinkroot": "闪耀根", "Bone": "骨头", "Book": "书", "Bottle": "瓶子",
    "BottledWater": "瓶装水", "Bowl": "碗", "Cactus": "仙人掌", "Campfire": "篝火",
    "Chest": "宝箱", "ChlorophyteBar": "叶绿锭", "Cloud": "云", "Compass": "罗盘",
    "Coral": "珊瑚", "CrimtaneBar": "猩红锭", "CrossNecklace": "十字项链",
    "CrystalShard": "水晶碎块", "CursedFlame": "诅咒焰", "Daybloom": "太阳花",
    "DemoniteBar": "魔矿锭", "DivingHelmet": "潜水头盔", "Ectoplasm": "灵质",
    "FallenStar": "坠落之星", "Fireblossom": "火焰花", "Flipper": "脚蹼",
    "FragmentSolar": "日耀碎片", "FrozenShield": "冰冻护盾", "Gel": "凝胶",
    "Glass": "玻璃", "GoldBar": "金锭", "HallowedBar": "神圣锭", "Hay": "干草",
    "HeartLantern": "红心灯笼", "HellstoneBar": "狱石锭", "HermesBoots": "赫尔墨斯靴",
    "Ichor": "灵液", "IronBar": "铁锭", "LeadBar": "铅锭", "Leather": "皮革",
    "LifeFruit": "生命果", "MagicMirror": "魔镜", "MagmaStone": "岩浆石",
    "MeteoriteBar": "陨石锭", "Moonglow": "月光草", "Mushroom": "蘑菇",
    "MusketBall": "火枪子弹", "NightOwlPotion": "夜枭药水", "Obsidian": "黑曜石",
    "PixieDust": "妖精尘", "PocketMirror": "袖珍镜", "PygmyNecklace": "矮人项链",
    "Rope": "绳", "ShadowScale": "暗影鳞片", "ShinePotion": "光芒药水",
    "ShinyRedBalloon": "闪亮红气球", "Silk": "丝绸", "SiltBlock": "泥沙",
    "SilverBullet": "银子弹", "SoulofLight": "光明之魂", "SoulofNight": "暗影之魂",
    "SummoningPotion": "召唤药水", "TatteredCloth": "破布", "TissueSample": "组织样本",
    "Torch": "火把", "TungstenBullet": "钨子弹", "Wire": "电线", "Wood": "木材",
}

TILES = {
    "Anvils": "铁砧", "EarlyAnvil": "铁砧",
    "MythrilAnvil": "秘银砧或山铜砧", "HardmodeAnvil": "秘银砧或山铜砧",
    "Furnaces": "熔炉", "EarlyForge": "熔炉",
    "AdamantiteForge": "精金熔炉或钛金熔炉", "HardmodeForge": "精金熔炉或钛金熔炉",
    "DemonAltar": "恶魔祭坛或猩红祭坛", "SummonAltar": "恶魔祭坛或猩红祭坛",
    "WorkBenches": "工作台", "HeavyWorkBench": "重型工作台",
    "TinkerersWorkbench": "工匠作坊", "LunarCraftingStation": "远古操纵机",
    "Loom": "织布机", "Bottles": "放置的瓶子", "Bookcases": "书架",
    "CookingPots": "烹饪锅",
}

RARITY = {
    "White": "白", "Blue": "蓝", "Green": "绿", "Orange": "橙",
    "LightRed": "浅红", "Pink": "粉", "LightPurple": "浅紫", "Lime": "黄绿",
    "Yellow": "黄", "Cyan": "青", "Red": "红", "Purple": "紫", "Quest": "任务",
}

TIER = {
    "Early": "橙（前期）",
    "EarlyLate": "浅红（骷髅王后）",
    "MidLate": "黄绿（世纪之花后）",
    "Late": "红（月前）",
}

CLASS_CN = {
    "Melee": "近战", "Magic": "魔法", "Ranged": "远程",
    "Summon": "召唤", "Generic": "通用", "Throwing": "投掷",
}

GROUPS = {
    "IronBar": "铁/铅锭",
    "IronOrLead": "铁/铅锭",
    "GoldBarGroup": "金锭或铂金锭",
    "CobaltBarGroup": "钴锭或钯金锭",
}

SHOP_WHEN = {
    "scavengerDefeated": "击败清道夫后",
    "archivistDefeated": "击败归档者后",
    "ashHeartDefeated": "击败灰烬之心后",
}

SECTIONS = (
    "清道夫档", "归档者档", "灰烬之心档", "壁炉档", "C 线武器", "鞭",
    "锈蚀、废料与裂隙", "护甲", "饰品", "弹药", "药水与食物",
    "材料与任务道具", "袋子、奖杯与旗帜", "其他",
)

PROP_RE = re.compile(
    r"(?:public|protected|private|internal)\s+(?:override|virtual)\s+"
    r"[\w.<>,\[\]?]+\s+(\w+)\s*=>\s*([^;]+);"
)
CONST_RE = re.compile(r"const\s+int\s+(\w+)\s*=\s*(\d+)")
CLASS_RE = re.compile(
    r"(?:public |private |internal )?(abstract )?class\s+(\w+)\s*:\s*([^{\n]+)"
)


def _brace_end(src, open_at):
    depth = 0
    for i in range(open_at, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(src) - 1


def _method(body, name):
    match = re.search(
        r"(?:public|protected|private|internal)\s+(?:override\s+)?[\w<>\[\].]+\s+"
        + name + r"\s*\([^)]*\)\s*\{",
        body,
    )
    if not match:
        return ""
    open_at = match.end() - 1
    return body[open_at + 1:_brace_end(body, open_at)]


def _props(body):
    found = {}
    for match in PROP_RE.finditer(body):
        found[match.group(1)] = match.group(2).strip()
    for match in CONST_RE.finditer(body):
        found[match.group(1)] = match.group(2)
    return found


def scan_classes():
    classes = {}
    for dirpath, dirnames, filenames in os.walk(MOD_ROOT):
        dirnames[:] = [d for d in dirnames if d not in ("obj", "bin")]
        for filename in filenames:
            if not filename.endswith(".cs"):
                continue
            path = os.path.join(dirpath, filename)
            src = io.open(path, encoding="utf-8").read()
            for match in CLASS_RE.finditer(src):
                abstract = bool(match.group(1))
                name = match.group(2)
                base = match.group(3).strip().split(".")[-1].split("<")[0].strip()
                open_at = src.find("{", match.end())
                if open_at < 0:
                    continue
                body = src[open_at + 1:_brace_end(src, open_at)]
                classes[name] = {
                    "base": base,
                    "abstract": abstract,
                    "body": body,
                    "path": path.replace("\\", "/"),
                    "props": _props(body),
                }
    return classes


def _merged_props(classes, name, seen=None):
    seen = seen or set()
    if name in seen or name not in classes:
        return {}
    seen.add(name)
    info = classes[name]
    merged = _merged_props(classes, info["base"], seen)
    merged.update(info["props"])
    return merged


def _int_expr(expr, props, depth=0):
    if expr is None or depth > 6:
        return None
    text = expr.strip().rstrip("f")
    if text in props:
        return _int_expr(props[text], props, depth + 1)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?[\d\s\+\-\*/\(\)]+", text):
        try:
            return int(eval(text))  # noqa: S307  only digits and arithmetic
        except Exception:
            return None
    return None


def _price_text(expr, props):
    if expr is None:
        return None
    text = expr.strip()
    if text in props:
        return _price_text(props[text], props)
    if text in ("0", "0f"):
        return "不可出售"
    match = re.search(r"(?:sellPrice|buyPrice)\((.*)\)", text)
    if not match:
        amount = _int_expr(text, props)
        if amount is None:
            return None
        return _coins(amount)
    parts = {}
    for key, value in re.findall(r"(platinum|gold|silver|copper)\s*:\s*(\d+)", match.group(1)):
        parts[key] = int(value)
    # positional: sellPrice(platinum, gold, silver, copper) is rare here
    order = ("platinum", "gold", "silver", "copper")
    units = {"platinum": "铂", "gold": "金", "silver": "银", "copper": "铜"}
    bits = ["%d %s" % (parts[key], units[key]) for key in order if parts.get(key)]
    return " ".join(bits) if bits else "不可出售"


def _coins(amount):
    if amount <= 0:
        return "不可出售"
    platinum, rest = divmod(int(amount), 1000000)
    gold, rest = divmod(rest, 10000)
    silver, copper = divmod(rest, 100)
    bits = []
    for value, label in ((platinum, "铂"), (gold, "金"), (silver, "银"), (copper, "铜")):
        if value:
            bits.append("%d %s" % (value, label))
    return " ".join(bits) if bits else "不可出售"


def _rarity(expr, props):
    if expr is None:
        return None
    text = expr.strip()
    if text in props:
        return _rarity(props[text], props)
    match = re.search(r"WastelandRarityTiers\.(\w+)", text)
    if match:
        return TIER.get(match.group(1), match.group(1))
    match = re.search(r"ItemRarityID\.(\w+)", text)
    if match:
        return RARITY.get(match.group(1), match.group(1))
    return None


def _damage_class(expr, props):
    if expr is None:
        return None
    text = expr.strip()
    if text in props:
        return _damage_class(props[text], props)
    match = re.search(r"DamageClass\.(\w+)", text)
    if match:
        return CLASS_CN.get(match.group(1), match.group(1))
    return None


def _assign(body, field):
    match = re.search(r"Item\.%s\s*=\s*([^;]+);" % field, body)
    return match.group(1).strip() if match else None


def _npc_assign(body, field):
    match = re.search(r"NPC\.%s\s*=\s*([^;]+);" % field, body)
    return match.group(1).strip() if match else None


def item_stats(classes, name):
    if name not in classes:
        return {}
    info = classes[name]
    props = _merged_props(classes, name)
    defaults = _method(info["body"], "SetDefaults")
    base = info["base"]
    if "Item." not in defaults and base in classes:
        defaults = _method(classes[base]["body"], "SetDefaults") or defaults
    stats = {}

    if base == "WastelandWhip":
        stats["kind"] = "召唤鞭"
    elif base == "WastelandAmmo" or info["path"].find("/Ammo/") >= 0:
        stats["kind"] = "弹药"
    elif base == "WastelandAccessory" or "accessory = true" in defaults:
        stats["kind"] = "饰品"
    elif base in ("WastelandSummonItem",):
        stats["kind"] = "Boss 召唤物"
    elif base == "WastelandBossBag":
        stats["kind"] = "掉落袋"
    elif base in ("WastelandPotion",):
        stats["kind"] = "药水或食物"

    damage = _int_expr(_assign(defaults, "damage"), props)
    if damage is None:
        damage = _int_expr(props.get("Damage"), props)
    if damage:
        stats["damage"] = damage

    klass = _damage_class(_assign(defaults, "DamageType"), props) or _damage_class(props.get("Class"), props)
    if klass:
        stats["klass"] = klass
    elif base == "WastelandWhip":
        stats["klass"] = "召唤"

    for field, key in (("knockBack", "knock"), ("useTime", "use"), ("crit", "crit"), ("mana", "mana"), ("defense", "defense")):
        value = _int_expr(_assign(defaults, field), props) if field != "knockBack" else None
        if field == "knockBack":
            raw = _assign(defaults, field)
            if raw:
                number = _int_expr(raw, props)
                if number is None and re.fullmatch(r"[\d.]+f?", raw):
                    number = raw.rstrip("f")
                if number not in (None, 0):
                    stats[key] = number
            elif props.get("Knockback"):
                raw = props["Knockback"]
                number = _int_expr(raw, props)
                stats[key] = number if number is not None else raw.rstrip("f")
            continue
        if value is None and field == "useTime":
            value = _int_expr(props.get("UseTime") or props.get("Animation"), props)
        if value is None and field == "defense":
            value = _int_expr(props.get("Defense"), props)
        if value:
            stats[key] = value

    rare = _rarity(_assign(defaults, "rare"), props) or _rarity(props.get("Rarity"), props)
    if rare:
        stats["rare"] = rare
    sell = _price_text(_assign(defaults, "value"), props) or _price_text(props.get("SellPrice") or props.get("SellCopper"), props)
    if sell:
        stats["sell"] = sell

    frames = _int_expr(props.get("BuffDuration"), props)
    if frames:
        seconds = frames / 60.0
        if seconds >= 60 and seconds % 60 == 0:
            stats["buff"] = "%d 分钟" % (seconds // 60)
        elif seconds >= 60:
            stats["buff"] = "%d 分 %d 秒" % (seconds // 60, seconds % 60)
        else:
            stats["buff"] = "%g 秒" % seconds

    comment = re.search(r"NPC\.lifeMax\s*=\s*\d+\s*;\s*//\s*(.+)", defaults)
    return stats


def _ingredient_name(token, kind, names):
    if kind == "group" or token == "IronOrLead":
        return GROUPS.get(token, token)
    if kind == "van":
        return VANILLA.get(token, token)
    return names.get(token, token)


def _parse_recipes(body, props, names):
    method = _method(body, "AddRecipes")
    if not method:
        return []
    recipes = []
    for part in re.split(r"CreateRecipe\s*\(", method)[1:]:
        ings = []
        for match in re.finditer(r"AddIngredient<(\w+)>\(([^)]*)\)", part):
            count = _int_expr(match.group(2) or "1", props) or 1
            ings.append((_ingredient_name(match.group(1), "mod", names), count))
        for match in re.finditer(r"AddIngredient\(\s*ItemID\.(\w+)\s*(?:,\s*(\w+))?\s*\)", part):
            count = _int_expr(match.group(2) or "1", props) or 1
            token = "IronOrLead" if match.group(1) in ("IronBar", "LeadBar") else match.group(1)
            kind = "group" if token == "IronOrLead" else "van"
            ings.append((_ingredient_name(token, kind, names), count))
        for match in re.finditer(r"AddRecipeGroup\(\s*(?:RecipeGroupID\.)?(\w+)\s*,\s*(\d+)\s*\)", part):
            ings.append((_ingredient_name(match.group(1), "group", names), int(match.group(2))))
        tile_match = re.search(r"AddTile\(\s*(?:TileID\.|WastelandCraftingStations\.)?(\w+)\s*\)", part)
        tile = None
        if tile_match:
            token = tile_match.group(1)
            if token == "CraftTile":
                tile = TILES.get(re.search(r"TileID\.(\w+)", props.get("CraftTile", "")).group(1), None) if "TileID." in props.get("CraftTile", "") else None
            else:
                tile = TILES.get(token, token)
        recipes.append((tuple(ings), tile))
    unique = []
    for recipe in recipes:
        if recipe not in unique:
            unique.append(recipe)
    return unique


def recipes_for(classes, name, names):
    if name not in classes:
        return []
    props = _merged_props(classes, name)
    own = _parse_recipes(classes[name]["body"], props, names)
    if own:
        return own
    base = classes[name]["base"]
    if base in classes:
        return _parse_recipes(classes[base]["body"], props, names)
    return []


def _recipe_line(recipes):
    if not recipes:
        return None
    lines = []
    for ings, tile in recipes:
        bits = ["%s ×%s" % (label, count) for label, count in ings]
        text = " + ".join(bits)
        if tile:
            text += "，%s" % tile
        lines.append(text)
    return " 或 ".join(lines)


def section_of(info, name):
    path = info["path"] if info else ""
    if "/Whips/" in path:
        return "鞭"
    if "Boss1Scavenger" in path:
        return "清道夫档"
    if "Boss2Archivist" in path:
        return "归档者档"
    if "Boss3AshHeart" in path:
        return "灰烬之心档"
    if "Boss4Fireplace" in path:
        return "壁炉档"
    if "/CLine/" in path:
        return "C 线武器"
    if any(bit in path for bit in ("/Rust/", "/Scrap/", "/Rift/", "/Signal/")):
        return "锈蚀、废料与裂隙"
    if "/Armor/" in path or "/UpgradeTrees/" in path:
        return "护甲"
    if "/Accessories/" in path:
        return "饰品"
    if "/Ammo/" in path:
        return "弹药"
    if "/Consumables/" in path:
        return "药水与食物"
    if "/Materials/" in path or "/Soul/" in path:
        return "材料与任务道具"
    if "/Bags/" in path or "/Decor/" in path or name.endswith("Trophy") or "Banner" in name:
        return "袋子、奖杯与旗帜"
    return "其他"


def _fmt_drop(chance, label, low=None, high=None):
    if chance <= 1:
        head = "必定"
    else:
        head = "1/%d" % chance
    if low and high and (low != 1 or high != 1):
        return "%s %s ×%d~%d" % (head, label, low, high)
    if low and low > 1 and high in (None, low):
        return "%s %s ×%d" % (head, label, low)
    return "%s %s" % (head, label)


def _type_name(token):
    return token.split(".")[-1]


def _loot_from_method(method, names):
    drops = []
    seen = []
    for match in re.finditer(
        r"ItemDropRule\.Common\(\s*(?:ModContent\.ItemType<([\w.]+)>\(\)|ItemID\.(\w+))\s*,\s*(\d+)(?:\s*,\s*(\d+)\s*,\s*(\d+))?",
        method,
    ):
        token = _type_name(match.group(1) or match.group(2))
        label = names.get(token) or VANILLA.get(token, token)
        chance = int(match.group(3))
        low = int(match.group(4)) if match.group(4) else None
        high = int(match.group(5)) if match.group(5) else None
        line = _fmt_drop(chance, label, low, high)
        if line not in seen:
            seen.append(line)
            drops.append((token, line))
    for match in re.finditer(r"ItemDropRule\.OneFromOptions\(\s*(\d+)\s*,([^)]+)\)", method):
        chance = int(match.group(1))
        labels = [names.get(_type_name(token), _type_name(token)) for token in re.findall(r"ItemType<([\w.]+)>", match.group(2))]
        if labels:
            drops.append((None, "1/%d 随机其一：%s" % (chance, "、".join(labels))))
    return drops


def _bag_open_text(classes, bag_name, names):
    if bag_name not in classes:
        return None
    props = _merged_props(classes, bag_name)
    body = classes[bag_name]["body"]
    bits = []
    for match in re.finditer(r"ItemType<(\w+)>\(\)\s*,\s*(\d+)\s*,\s*(\d+)", body):
        bits.append("%s ×%s~%s" % (names.get(match.group(1), match.group(1)), match.group(2), match.group(3)))
    for match in re.finditer(r"ItemID\.(\w+)\s*,\s*(\d+)\s*,\s*(\d+)", body):
        bits.append("%s ×%s~%s" % (VANILLA.get(match.group(1), match.group(1)), match.group(2), match.group(3)))
    index = _int_expr(props.get("BossIndex"), props)
    souls = {1: "SoulFragmentScavenger", 2: "SoulFragmentSecond", 3: "SoulFragmentThird", 4: "SoulFragmentFourth"}
    if index in souls:
        bits.append("%s（每个世界一次）" % names.get(souls[index], souls[index]))
    folder = {1: "Boss1Scavenger", 2: "Boss2Archivist", 3: "Boss3AshHeart", 4: "Boss4Fireplace"}.get(index)
    exclusives = []
    if folder:
        for key, info in classes.items():
            if info["abstract"]:
                continue
            if folder in info["path"] and key.lower().endswith("ex"):
                exclusives.append(names.get(key, key))
    text = "、".join(bits)
    if exclusives:
        text += "；再随机 1 件专属武器（%s）" % "、".join(sorted(exclusives))
    return text


def _negated(text, token):
    index = text.find(token)
    if index < 0:
        return False
    i = index - 1
    while i >= 0 and (text[i].isalnum() or text[i] in "._"):
        i -= 1
    return i >= 0 and text[i] == "!"


def _zero_ifs(method):
    conds = []
    start = 0
    while True:
        found = method.find("if", start)
        if found < 0:
            break
        paren = method.find("(", found)
        if paren < 0 or paren - found > 8:
            start = found + 2
            continue
        depth = 0
        end = paren
        while end < len(method):
            if method[end] == "(":
                depth += 1
            elif method[end] == ")":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        cond = method[paren + 1:end]
        if re.match(r"\s*\{?\s*return\s+0f", method[end + 1:end + 30]):
            conds.append(cond)
        start = end + 1
    return conds


def spawn_summary(body):
    method = _method(body, "SpawnChance")
    if not method:
        return None
    tern = re.search(r"Main\.hardMode\s*\?\s*([0-9.]+)f\s*:\s*([0-9.]+)f", method)
    returns = [value for value in re.findall(r"return\s+([0-9.]+)f\s*;", method) if float(value) > 0]
    if not tern and not returns:
        return "不自然刷新"
    bits = []
    zones = {
        "ZoneOverworldHeight": "地表",
        "ZoneDirtLayerHeight": "泥土",
        "ZoneRockLayerHeight": "岩石",
        "ZoneUnderworldHeight": "地狱",
    }
    flags = (
        ("scavengerDefeated", "清道夫后"),
        ("archivistDefeated", "归档者后"),
        ("ashHeartDefeated", "灰烬之心后"),
    )
    for cond in _zero_ifs(method):
        if _negated(cond, "Main.hardMode"):
            bits.append("困难")
        elif "Main.hardMode" in cond:
            bits.append("肉前")
        if _negated(cond, "Main.dayTime"):
            bits.append("白天")
        elif "Main.dayTime" in cond:
            bits.append("夜晚")
        for token, label in flags:
            if _negated(cond, token):
                bits.append(label)
        found = [(label, _negated(cond, token)) for token, label in zones.items() if token in cond]
        if len(found) >= 2 and "&&" in cond and all(neg for _, neg in found):
            bits.append("或".join(label for label, _ in found))
        else:
            bits.extend(label for label, neg in found if neg)
    ordered = []
    for bit in bits:
        if bit not in ordered:
            ordered.append(bit)
    if tern:
        weight = "权重 困难 %s / 肉前 %s" % (tern.group(1), tern.group(2))
    else:
        weight = "权重 " + returns[-1]
    where = " ".join(ordered)
    return (where + "  " if where else "") + weight


def _shop_sources(classes, names):
    sources = {}
    info = classes.get("MechanicalCompanion")
    if not info:
        return sources
    for match in re.finditer(
        r"Priced<[^>]*\.(\w+)>\((\d+)\)(?:\s*,\s*new Condition\(\"[^\"]+\", \(\) => WastelandStorySystem\.(\w+)\))?",
        info["body"],
    ):
        item, price, flag = match.group(1), match.group(2), match.group(3)
        text = "智械人商店，芯片 ×%s" % price
        if flag:
            text += "（%s）" % SHOP_WHEN.get(flag, flag)
        sources.setdefault(item, []).append(text)
    return sources


def _era_drops(classes, name, names):
    props = _merged_props(classes, name)
    low = _int_expr(props.get("ChipMin"), props)
    high = _int_expr(props.get("ChipMax"), props)
    drops = []
    if low:
        drops.append(("Chip", _fmt_drop(1, names.get("Chip", "芯片"), low, high)))
    rare = re.search(r"RareWeapons\s*=>\s*new\[\]\s*\{([^}]*)\}", classes[name]["body"], re.S)
    if rare and "ItemType<" in rare.group(1):
        labels = [names.get(token, token) for token in re.findall(r"ItemType<(\w+)>", rare.group(1))]
        if labels:
            drops.append((None, "1/22 随机其一：%s" % "、".join(labels)))
    return drops


def _global_extra(classes, names):
    extra = {}
    sources = {}
    for info in classes.values():
        if info["base"] != "GlobalNPC":
            continue
        method = _method(info["body"], "ModifyNPCLoot")
        early = re.search(
            r"if\s*\(\s*npc\.type\s*!=\s*ModContent\.NPCType<(\w+)>\(\)\s*\)\s*\{\s*return\s*;\s*\}",
            method,
        )
        if early:
            rest = method[early.end():]
            npc = early.group(1)
            for token, line in _loot_from_method(rest, names):
                if line not in extra.setdefault(npc, []):
                    extra[npc].append(line)
                if token:
                    sources.setdefault(token, []).append(npc)
        for match in re.finditer(
            r"if\s*\(\s*npc\.type\s*==\s*ModContent\.NPCType<(\w+)>\(\)\s*\)\s*\{",
            method,
        ):
            npc = match.group(1)
            open_at = match.end() - 1
            block = method[open_at + 1:_brace_end(method, open_at)]
            for token, line in _loot_from_method(block, names):
                if line not in extra.setdefault(npc, []):
                    extra[npc].append(line)
                if token:
                    sources.setdefault(token, []).append(npc)
    return extra, sources


def _drop_sources(classes, names, npcs):
    sources = {}
    for name, info in classes.items():
        if name not in npcs:
            continue
        method = _method(info["body"], "ModifyNPCLoot")
        if method:
            pairs = _loot_from_method(method, names)
        elif info.get("base") == "EraMob":
            pairs = _era_drops(classes, name, names)
        else:
            pairs = []
        who = names.get(name, name)
        for token, _line in pairs:
            if token:
                sources.setdefault(token, []).append(who)
    return sources


def emit(items, npcs, checklist, item_out, npc_out, blurbs, boss_keys):
    classes = scan_classes()
    names = {}
    for key, block in items.items():
        names[key] = block.get("DisplayName", key)
    for key, block in npcs.items():
        names[key] = block.get("DisplayName", key)

    shop = _shop_sources(classes, names)
    global_extra, global_sources = _global_extra(classes, names)
    dropped_by = _drop_sources(classes, names, npcs)
    for token, whos in global_sources.items():
        for who in whos:
            label = names.get(who, who)
            bucket = dropped_by.setdefault(token, [])
            if label not in bucket:
                bucket.append(label)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    grouped = {title: [] for title in SECTIONS}
    for key in items:
        info = classes.get(key)
        grouped[section_of(info, key)].append(key)

    lines = [
        "废土魂穿 · 物品介绍清单",
        "打包时间：%s" % stamp,
        "说明：只列本模组物品。介绍是游戏里看到的句子。",
        "伤害、击退、使用间隔、防御、暴击是普通模式基础值。专家和大师还会再乘原版倍率。",
        "合成写在这里，游戏内的物品介绍不写做法。铁/铅写成「或」，两条配方并成一条。",
        "售价是卖给 NPC 的价格，不是购买价。",
        "",
    ]
    for title in SECTIONS:
        keys = grouped[title]
        if not keys:
            continue
        keys.sort(key=lambda k: items[k].get("DisplayName", k))
        lines.append("======== %s（%d） ========" % (title, len(keys)))
        lines.append("")
        for key in keys:
            block = items[key]
            lines.append("【%s】" % block.get("DisplayName", key))
            stats = item_stats(classes, key)
            bits = []
            if stats.get("kind"):
                bits.append(stats["kind"])
            elif stats.get("klass"):
                bits.append(stats["klass"])
            if stats.get("klass") and stats.get("kind") and stats["klass"] not in stats.get("kind", ""):
                bits.append(stats["klass"])
            if stats.get("damage"):
                bits.append("伤害 %s" % stats["damage"])
            if stats.get("defense"):
                bits.append("防御 %s" % stats["defense"])
            if stats.get("knock") not in (None, 0, "0"):
                bits.append("击退 %s" % stats["knock"])
            if stats.get("use"):
                bits.append("使用间隔 %s" % stats["use"])
            if stats.get("mana"):
                bits.append("魔力 %s" % stats["mana"])
            if stats.get("crit"):
                bits.append("额外暴击 %s" % stats["crit"])
            if bits:
                lines.append("  " + "　".join(bits))
            meta = []
            if stats.get("rare"):
                meta.append("稀有度 " + stats["rare"])
            if stats.get("sell"):
                meta.append("售价 " + stats["sell"])
            if stats.get("buff"):
                meta.append("持续时间 " + stats["buff"])
            if meta:
                lines.append("  " + "　".join(meta))
            tip = block.get("Tooltip", "")
            if tip:
                for row in tip.split("\n"):
                    if row:
                        lines.append("  %s" % row)
            else:
                lines.append("  （没有额外介绍，效果看面板）")
            bonus = block.get("SetBonus")
            if bonus:
                lines.append("  套装奖励：%s" % bonus.replace("\n", " / "))
            extra = block.get("Tooltip2")
            if extra:
                lines.append("  %s" % extra.replace("\n", " / "))
            recipe = _recipe_line(recipes_for(classes, key, names))
            if recipe:
                lines.append("  合成：%s" % recipe)
            elif key.lower().endswith("ex") and classes.get(key) and "Boss" in classes[key]["path"]:
                lines.append("  获取：只从对应 Boss 的掉落袋随机开出，没有合成")
            origins = []
            origins.extend(shop.get(key, []))
            killers = dropped_by.get(key, [])
            if len(killers) > 4:
                origins.append("多个野外怪")
            else:
                for who in killers:
                    if who not in origins:
                        origins.append(who)
            if origins and not (recipe and key.lower().endswith("ex")):
                lines.append("  另外：%s" % "；".join(origins))
            lines.append("")

    os.makedirs(os.path.dirname(item_out), exist_ok=True)
    io.open(item_out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("items", len(items), item_out)

    npc_lines = [
        "废土魂穿 · Boss 与生成怪介绍清单",
        "打包时间：%s" % stamp,
        "说明：原版小怪不改。下面只列本模组 NPC。",
        "生命、防御、接触伤害是普通模式基础值。专家、大师和多人会按原版再乘。",
        "清道夫在大师模式另有一档：生命再乘 0.88，接触伤害再乘 0.75。",
        "野外自然刷新还要：主世界宽度至少 1200、不在玩家安全区、不在壁炉子世界。权重是 SpawnChance 的返回值。",
        "占位槽只有刷新窗口，名字和打法都还没定。",
        "",
        "—— Boss ——",
        "",
    ]
    town = ("MechanicalCompanion", "ScavengerRepairDrone", "AshWisp")

    def one_npc(key):
        info = classes.get(key, {})
        body = info.get("body", "")
        defaults = _method(body, "SetDefaults")
        props = _merged_props(classes, key) if key in classes else {}
        name = npcs.get(key, {}).get("DisplayName", key)
        npc_lines.append("【%s】" % name)
        life = _int_expr(_npc_assign(defaults, "lifeMax"), props)
        defense = _int_expr(_npc_assign(defaults, "defense"), props)
        damage_expr = _npc_assign(defaults, "damage")
        damage = _int_expr(damage_expr, props)
        panel = []
        if life:
            panel.append("生命 %d" % life)
        if defense is not None:
            panel.append("防御 %d" % defense)
        if damage is not None:
            panel.append("接触伤害 %d" % damage)
        kb = _npc_assign(defaults, "knockBackResist")
        if kb and kb not in ("0f", "0"):
            panel.append("击退抗性 %s" % kb.rstrip("f"))
        if panel:
            npc_lines.append("  " + "　".join(panel))
        note = re.search(r"NPC\.lifeMax\s*=\s*\d+\s*;\s*//\s*(.+)", defaults)
        if note:
            npc_lines.append("  定位：%s" % note.group(1).strip())
        if key in checklist:
            npc_lines.append("  召唤：%s" % checklist[key])
        spawn = spawn_summary(body) if body else None
        if spawn:
            npc_lines.append("  刷新：%s" % spawn)
        if key in blurbs and key not in checklist:
            npc_lines.append("  行为：%s" % blurbs[key])
        method = _method(body, "ModifyNPCLoot") if body else ""
        pairs = _loot_from_method(method, names) if method else []
        if not pairs and info.get("base") == "EraMob":
            pairs = _era_drops(classes, key, names)
        drops = [line for _token, line in pairs]
        for line in global_extra.get(key, []):
            if line not in drops:
                drops.append(line)
        if "DefeatedByPlayer" in body or "LeadingConditionRule" in (method or ""):
            npc_lines.append("  掉落条件：正常击败才掉；过载自毁不掉、不推进剧情。")
        bag_name = None
        for match in re.finditer(r"ItemType<([\w.]+Bag)>", method or ""):
            bag_name = _type_name(match.group(1))
        if drops:
            npc_lines.append("  掉落：%s" % "；".join(drops))
        opened = _bag_open_text(classes, bag_name, names) if bag_name else None
        if opened:
            npc_lines.append("  开袋：%s" % opened)
        npc_lines.append("")

    for key in boss_keys:
        one_npc(key)
    npc_lines.append("—— 城镇 / 战斗召唤物 ——")
    npc_lines.append("")
    for key in town:
        one_npc(key)
    npc_lines.append("—— 野外生成怪 ——")
    npc_lines.append("")
    rest = [key for key in npcs if key not in boss_keys and key not in town]
    rest.sort(key=lambda k: npcs[k].get("DisplayName", k))
    for key in rest:
        one_npc(key)

    io.open(npc_out, "w", encoding="utf-8", newline="\n").write("\n".join(npc_lines) + "\n")
    print("npcs", len(npcs), npc_out)
