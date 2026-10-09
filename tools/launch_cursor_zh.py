# -*- coding: utf-8 -*-
"""用简体中文启动 Cursor（两条通道同时给）。

为什么要两条通道（都是实测出来的）
--------------------------------
| 通道 | 谁读它 | 作用 |
| --- | --- | --- |
| `--lang=zh-CN` 命令行参数 | **Electron / Chromium** 自己 | 决定渲染进程的 `--lang`（界面框架语言、右键菜单、原生对话框） |
| 环境变量 `VSCODE_NLS_CONFIG` | Cursor 的 `bootstrap-fork.js` / `cli.js` | 决定 VS Code 内核那 1150 个模块的文案（命令面板、设置项标题…） |

⚠️ 两个坑：
1. **不能直接用 CreateProcess 启动**（`Start-Process` / `cmd start`）：Electron 初始化 crashpad
   会失败并秒退（退出码 0、不写日志）。必须交给**资源管理器**：`explorer.exe <exe> <args>`。
2. 环境变量要**由 explorer 继承**才能传进去，所以本脚本用 `subprocess.Popen(["explorer.exe", ...], env=...)`，
   让 explorer 做父进程。

用法
----
    python tools/launch_cursor_zh.py                # 以简体中文启动 Cursor
    python tools/launch_cursor_zh.py --dry-run      # 只打印配置
    python tools/launch_cursor_zh.py --verify       # 启动后读进程命令行，确认 --lang 生效
"""
import argparse
import json
import os
import subprocess
import sys
import time

CURSOR_EXE = r"E:\新建文件夹\cursor\Cursor.exe"
EXT_ROOT = os.path.join(os.environ["USERPROFILE"], ".cursor", "extensions")
PACK_PREFIX = "ms-ceintl.vscode-language-pack-zh-hans"
LANG_CHROMIUM = "zh-CN"      # 给 Electron/Chromium（--lang）
LANG_VSCODE = "zh-cn"        # 给 VS Code 内核（VSCODE_NLS_CONFIG）


def find_pack():
    cands = []
    if os.path.isdir(EXT_ROOT):
        for name in os.listdir(EXT_ROOT):
            if name.startswith(PACK_PREFIX):
                cands.append(os.path.join(EXT_ROOT, name))
    if not cands:
        raise SystemExit("没找到中文语言包：%s\\%s*" % (EXT_ROOT, PACK_PREFIX))
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[0]


def build_nls_config(pack_dir):
    manifest = json.load(open(os.path.join(pack_dir, "package.json"), encoding="utf-8"))
    entry = next((l for l in manifest.get("contributes", {}).get("localizations", [])
                  if l.get("languageId") == LANG_VSCODE), None)
    if entry is None:
        raise SystemExit("语言包里没有 languageId=%s 的条目" % LANG_VSCODE)
    messages = os.path.join(pack_dir, "translations", "main.i18n.json")
    if not os.path.isfile(messages):
        raise SystemExit("语言包缺少 translations/main.i18n.json")
    return {
        "userLocale": LANG_VSCODE,
        "osLocale": LANG_VSCODE,
        "resolvedLanguage": LANG_VSCODE,
        "languagePack": {
            "languageId": LANG_VSCODE,
            "languageName": entry.get("languageName", "Chinese Simplified"),
            "localizedLanguageName": entry.get("localizedLanguageName", "中文(简体)"),
            "messagesFile": messages,
            "translationsConfigFile": messages,
            "extensionId": manifest.get("name", "vscode-language-pack-zh-hans"),
        },
        "packExtension": pack_dir,
    }


def renderer_langs():
    """读所有 Cursor 进程的 --lang（用 CIM，不依赖外部工具）。"""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='Cursor.exe'\" | "
             "ForEach-Object { $t = if ($_.CommandLine -match '--type=([a-zA-Z-]+)') { $Matches[1] } else { 'main' }; "
             "$l = if ($_.CommandLine -match '--lang=([A-Za-z-]+)') { $Matches[1] } else { '-' }; "
             "\"$t $l\" }"],
            capture_output=True, text=True, timeout=60)
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception as exc:                       # noqa: BLE001 - 探针失败不影响启动
        return ["<读取失败: %s>" % exc]


def main():
    parser = argparse.ArgumentParser(description="用简体中文启动 Cursor")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true", help="启动后读进程命令行确认")
    args = parser.parse_args()

    if not os.path.isfile(CURSOR_EXE):
        raise SystemExit("找不到 Cursor.exe：%s" % CURSOR_EXE)

    pack_dir = find_pack()
    config = build_nls_config(pack_dir)
    print("语言包 : %s" % pack_dir)
    print("Chromium --lang : %s" % LANG_CHROMIUM)
    print("VS Code locale  : %s" % LANG_VSCODE)

    if args.dry_run:
        print("VSCODE_NLS_CONFIG = %s" % json.dumps(config, ensure_ascii=False))
        print("（--dry-run：没有启动）")
        return 0

    env = dict(os.environ)
    env["VSCODE_NLS_CONFIG"] = json.dumps(config, ensure_ascii=True)

    # explorer 作为父进程：既解决 crashpad 秒退，又把环境变量带进去
    subprocess.Popen(["explorer.exe", CURSOR_EXE, "--lang=%s" % LANG_CHROMIUM], env=env)
    print("已启动 Cursor（zh-CN）。若它本来就在运行，改动不会生效 —— 先完全退出再跑本脚本。")

    if args.verify:
        for _ in range(12):
            time.sleep(5)
            langs = renderer_langs()
            if any(l.endswith(LANG_CHROMIUM) for l in langs):
                print("✅ 渲染进程已是 --lang=%s：%s" % (LANG_CHROMIUM, sorted(set(langs))))
                return 0
            if langs and not langs[0].startswith("<"):
                print("  等待中… 当前: %s" % sorted(set(langs)))
        print("⚠️ 没等到 %s，当前: %s" % (LANG_CHROMIUM, sorted(set(renderer_langs()))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
