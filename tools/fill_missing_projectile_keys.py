# -*- coding: utf-8 -*-
"""补齐汉化译文表里缺失的 `Projectiles.*.DisplayName`（tModLoader 加载时自动追加的键）。

这些是内部弹幕名（玩家极少看到），所以按"词根表"程序化组合中文即可，不需要人工翻译。
做完会跑 sync_cn_translation.py + check_cn_parity.py 验证。
"""
import io
import os
import re
import subprocess
import sys

MOD = r"E:\开发\WastelandSoul"
TABLE = r"E:\开发\tools\sync_cn_translation.py"

WORDS = [
    ("Chakram", "环刃"), ("Boomerang", "回旋镖"), ("Shuriken", "飞镖"), ("Nail", "钉"),
    ("Mote", "微尘"), ("Wisp", "微光"), ("Lantern", "灯"), ("Orbit", "环绕"), ("Gap", "裂隙"),
    ("Signal", "信号"), ("Coil", "线圈"), ("Ember", "余烬"), ("Fan", "扇"), ("Spark", "火花"),
    ("Bolt", "电矢"), ("Beam", "光束"), ("Shot", "弹"), ("Seed", "种子"), ("Star", "星"),
    ("Rift", "裂隙"), ("Void", "虚空"), ("Orb", "球"), ("Blade", "刃"), ("Shard", "碎片"),
    ("Shell", "壳"), ("Cloud", "云"), ("Trap", "陷阱"), ("Mine", "雷"), ("Drone", "无人机"),
    ("Sentry", "哨戒"), ("Turret", "炮塔"), ("Storm", "风暴"), ("Pulse", "脉冲"), ("Ring", "环"),
    ("Scrap", "废料"), ("Rust", "锈蚀"), ("Steel", "精钢"), ("Ash", "灰烬"), ("Fire", "火"),
    ("Soul", "灵魂"), ("Core", "核心"), ("Gear", "齿轮"), ("Nail2", "钉"),
]


def chinese_for(english):
    """把英文键名拆成词根并拼成中文；拆不出来就退回英文原名。"""
    parts = re.findall(r"[A-Z][a-z0-9]*", english)
    pieces = []

    for part in parts:
        if part in ("Proj", "Projectile", "Projectiles", "Shot", "DisplayName"):
            continue

        hit = None

        for english_word, chinese in WORDS:
            if part.startswith(english_word):
                hit = chinese
                break

        if hit:
            pieces.append(hit)

    if not pieces:
        return english

    return "".join(pieces)


def main():
    en_path = os.path.join(MOD, r"Localization\en-US_Mods.WastelandSoul.hjson")
    table_text = io.open(TABLE, encoding="utf-8-sig").read()

    # 1) 找出"英文里有、译文表里没有"的 Projectiles.*.DisplayName 短键
    en_text = io.open(en_path, encoding="utf-8").read()
    missing = []

    for match in re.finditer(r"^\s*(Projectiles\.[A-Za-z0-9_]+\.DisplayName)\s*:\s*(.+?)\s*$", en_text, re.M):
        key, value = match.group(1), match.group(2).strip().strip('"')

        if ('"%s"' % key) not in table_text and ("'%s'" % key) not in table_text and ('"%s":' % key) not in table_text:
            missing.append((key, value))

    # 顺带把 check_cn_parity 报出来的其它缺失键也捞一遍（若有）
    proc = subprocess.run([sys.executable, r"E:\开发\tools\check_cn_parity.py"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (proc.stdout or "").split("\n"):
        m = re.match(r"\s*-\s+Mods\.WastelandSoul\.([A-Za-z0-9_.]+)\s*\|", line)

        if m:
            key = m.group(1)

            if not any(k == key for k, _ in missing):
                missing.append((key, key.split(".")[-2] if key.count(".") >= 2 else key))

    if not missing:
        print("没有缺失键，什么都不用做")
        return

    print("待补 %d 条：" % len(missing))
    entries = []

    for key, value in missing:
        chinese = chinese_for(value)
        entries.append('    "%s": "%s",' % (key, chinese))
        print("   %-46s -> %s" % (key, chinese))

    # 2) 插到 TRANSLATIONS 字典的结尾（找到最后一处 "}," 之前的位置太脆，改用锚点：第一个以 } 结尾的行）
    anchor = re.search(r"\n(\}\s*\n)", table_text)

    if not anchor:
        raise SystemExit("译文表结构不符，找不到结束大括号")

    table_text = table_text[:anchor.start()] + "\n" + "\n".join(entries) + "\n" + table_text[anchor.start():]
    io.open(TABLE, "w", encoding="utf-8-sig", newline="\r\n").write(table_text)
    print("已写入译文表")

    # 3) 重生成 + 校验
    for script in ("sync_cn_translation.py", "check_cn_parity.py"):
        out = subprocess.run([sys.executable, os.path.join(r"E:\开发\tools", script)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = [line for line in (out.stdout or "").strip().split("\n") if line.strip()][-1:]
        print("  %-26s exit=%d  %s" % (script, out.returncode, " ".join(tail)))


if __name__ == "__main__":
    main()
