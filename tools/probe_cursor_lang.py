# -*- coding: utf-8 -*-
"""探针：Cursor 启动后，界面语言相关的东西有没有落到磁盘上。

用法：python tools/probe_cursor_lang.py [日志目录名]
不带参数就取 %APPDATA%\\Cursor\\logs 下最新的目录。
"""
import os
import re
import sys

LOGS = os.path.join(os.environ["APPDATA"], "Cursor", "logs")
PATTERNS = ["nls", "locale", "zh-cn", "l10n", "language", "translation"]
SKIP = re.compile(r"(cursor-agent|mcp-server|telemetry|network|tasks\.|hooks)", re.I)


def latest_dir():
    if len(sys.argv) > 1:
        return os.path.join(LOGS, sys.argv[1])
    if not os.path.isdir(LOGS):
        return None
    dirs = [os.path.join(LOGS, d) for d in os.listdir(LOGS) if os.path.isdir(os.path.join(LOGS, d))]
    return max(dirs, key=os.path.getmtime) if dirs else None


def main():
    boot = latest_dir()
    if not boot or not os.path.isdir(boot):
        print("找不到日志目录")
        return 1

    print("日志目录：%s" % boot)
    total = 0
    for root, _dirs, files in os.walk(boot):
        for name in files:
            if not name.endswith(".log") or SKIP.search(name):
                continue
            path = os.path.join(root, name)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for line in text.splitlines():
                low = line.lower()
                if any(p in low for p in PATTERNS) and "cursor-agent" not in low:
                    print("  %s: %s" % (os.path.relpath(path, boot), line.strip()[:200]))
                    total += 1
                    if total > 40:
                        print("  …（截断）")
                        return 0
    if total == 0:
        print("  这次会话的日志里没有任何语言相关记录（NLS 通常也不写日志）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
