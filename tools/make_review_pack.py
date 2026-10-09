# -*- coding: utf-8 -*-
"""测评包：把刚构建出来的两个 .tmod + 安装说明打包好（以前是手工复制 + 手工压缩）。

用法
----
    python tools/make_review_pack.py                 # 用 .tml-build 里的产物
    python tools/make_review_pack.py --src-dir D:\\x # 换一个构建产物目录
    python tools/make_review_pack.py --keep-hash     # 不刷新说明里的 sha256

产物
----
    E:\\开发\\测评包\\WastelandSoul.tmod          <- 从构建目录复制
    E:\\开发\\测评包\\WastelandSoulCN.tmod        <- 同上
    E:\\开发\\测评包\\安装与测评说明.txt          <- 只更新"文件清单 + sha256 + 日期"，正文不动
    E:\\开发\\WastelandSoul_测评包.zip            <- 上面三件压成一个包（.gitignore 挡了 *.zip）

⚠️ 两条设计决定
--------------
1. **说明正文不重新生成**：那份 7.6 KB 的《安装与测评说明》是手写的（含"报 bug 的正确姿势"
   这类只有人写才像话的东西）。脚本**只改**"包里的文件 + 大小 + sha256 + 打包日期"这一小段，
   其余原文一字不动 —— 这样玩家改过的措辞不会被覆盖。
2. **哈希用完整的 sha256**：以前说明里写的是"前 16 位"，容易被抄错；现在写全 64 位，
   并在括号里给个 16 位短哈希方便肉眼对。
"""
import argparse
import hashlib
import os
import re
import sys
import zipfile
from datetime import datetime

REPO = r"E:\开发"
PACK_DIR = os.path.join(REPO, "测评包")
README = os.path.join(PACK_DIR, "安装与测评说明.txt")
ZIP_PATH = os.path.join(REPO, "WastelandSoul_测评包.zip")
DEFAULT_SRC_DIR = os.path.join(REPO, ".tml-build", "Mods")

MAIN_NAME = "WastelandSoul.tmod"
PATCH_NAME = "WastelandSoulCN.tmod"


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def human_size(size):
    if size >= 1024 * 1024:
        return "%.2f MB" % (size / (1024 * 1024))
    if size >= 1024:
        return "%.1f KB" % (size / 1024)
    return "%d B" % size


def update_readme(entries):
    """只刷新说明里的"文件清单 + 哈希"那几行；正文一字不动。"""
    text = open(README, encoding="utf-8-sig").read()   # utf-8-sig：顺手吃掉可能的 BOM
    lines = text.splitlines(keepends=True)
    out = []
    main_done = patch_done = False
    stamped = False
    stamp = "（本包打包时间：%s）\n" % datetime.now().strftime("%Y-%m-%d %H:%M")

    for line in lines:
        line = line.replace("\ufeff", "")               # 别让 BOM 混进正文
        if line.startswith("（本包打包时间："):          # 旧的时间戳先丢掉，最后统一插一条
            continue
        if MAIN_NAME in line and "sha256" in line:
            size, digest = entries[MAIN_NAME]
            out.append("   - `%s`      —— 主模组（%s，sha256 `%s`，短哈希 `%s`）\n"
                       % (MAIN_NAME, human_size(size), digest, digest[:16].upper()))
            main_done = True
            continue
        if PATCH_NAME in line and "sha256" in line:
            size, digest = entries[PATCH_NAME]
            out.append("   - `%s`    —— 中文汉化补丁（%s，sha256 `%s`，短哈希 `%s`）\n"
                       % (PATCH_NAME, human_size(size), digest, digest[:16].upper()))
            patch_done = True
            continue
        if not stamped and line.startswith("废土魂穿 / WastelandSoul"):
            out.append(line.rstrip("\n") + "\n")
            out.append(stamp)
            stamped = True
            continue
        out.append(line)

    if not (main_done and patch_done):
        raise SystemExit("说明里没找到两个 .tmod 的 sha256 行（%s / %s），不敢乱改"
                         % (MAIN_NAME, PATCH_NAME))

    if not stamped:
        out.insert(0, stamp)

    body = "".join(out)
    open(README, "w", encoding="utf-8", newline="").write(body)

    # 说明别处可能还留着旧格式（"sha256 前 16 位"）的哈希，扫出来提醒
    return [l for l in body.splitlines() if re.search(r"sha256 前 \d+ 位", l)]


def main():
    parser = argparse.ArgumentParser(description="打包测评包（.tmod + 说明 + zip）")
    parser.add_argument("--src-dir", default=DEFAULT_SRC_DIR,
                        help="构建产物目录（默认 .tml-build\\Mods）")
    parser.add_argument("--keep-hash", action="store_true", help="不刷新说明里的 sha256")
    args = parser.parse_args()

    missing = [n for n in (MAIN_NAME, PATCH_NAME)
               if not os.path.isfile(os.path.join(args.src_dir, n))]
    if missing:
        raise SystemExit("构建产物缺失：%s（先跑 tools\\ws_pipeline.ps1）"
                         % "、".join(os.path.join(args.src_dir, n) for n in missing))

    os.makedirs(PACK_DIR, exist_ok=True)
    entries = {}

    for name in (MAIN_NAME, PATCH_NAME):
        source = os.path.join(args.src_dir, name)
        target = os.path.join(PACK_DIR, name)
        with open(source, "rb") as src, open(target, "wb") as dst:
            dst.write(src.read())
        size = os.path.getsize(target)
        digest = sha256_of(target)
        entries[name] = (size, digest)
        print("  %-22s %10d B  %s" % (name, size, digest[:16].upper()))

    if not args.keep_hash:
        stale = update_readme(entries)
        print("  说明已刷新：%s" % README)
        for line in stale:
            print("  ⚠️ 说明里还有旧格式的哈希行，建议手动改：%s" % line.strip())

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in (MAIN_NAME, PATCH_NAME):
            archive.write(os.path.join(PACK_DIR, name), name)
        archive.write(README, os.path.basename(README))

    print("  压缩包：%s（%s）" % (ZIP_PATH, human_size(os.path.getsize(ZIP_PATH))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
