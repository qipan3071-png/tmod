# -*- coding: utf-8 -*-
"""用 Playwright 驱动本机 Edge 访问 ChatGPT：自己提交提示词、把生成的原图存下来。

用法
----
1) 首次登录（只需一次，之后登录状态留在 .chatgpt-profile 里）：
     python tools/chatgpt_art.py --login
   会弹出一个 Edge 窗口打开 chatgpt.com；你在里面登录，
   脚本检测到输入框出现就打印「登录成功」并自动关闭（cookies 已落盘）。

2) 出图：
     python tools/chatgpt_art.py --prompt "..." --out "E:/开发/art-inbox/raw/sheet.png"
     python tools/chatgpt_art.py --image "ref.png" --prompt-file pose.txt --out out.png
   流程：打开 chatgpt.com → 可选附上参考图 → 把提示词打进输入框 → 回车 → 等图片出现 →
   **在页面里 fetch 图片 blob 拿到原始字节**（不是屏幕截图）→ 写成本地 PNG。
   失败时退化为"对图片元素做原始分辨率截图"。
   附图时只保存提交之后新出现的图，不会把参考图本身存下来。

要点
----
* 用 `channel="msedge"`（系统已装的 Edge），不额外下载 Chromium。
* 持久化配置目录默认 `E:/开发/.chatgpt-profile`，可用 --profile 覆盖。
* 全程 headful（有界面），因为 ChatGPT 对无头浏览器常拦验证。
* 只做"提问 + 存图"，不点任何会改账号设置的东西。
"""
import argparse
import base64
import hashlib
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

DEFAULT_PROFILE = r"E:\开发\.chatgpt-profile"
CHAT_URL = "https://chatgpt.com/"
COMPOSER = "div#prompt-textarea, div.ProseMirror[contenteditable='true'], textarea#prompt-textarea"
IMAGE_SELECTOR = "img[src^='blob:'], img[src*='oaiusercontent'], img[alt*='enerated'], img[alt*='已生成']"


def log(message):
    print("[chatgpt_art] " + message, flush=True)


def wait_composer(page, timeout_ms):
    page.wait_for_selector(COMPOSER, timeout=timeout_ms, state="visible")
    return page.query_selector(COMPOSER)


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def start_new_chat(page):
    """避免套用上一次对话里已经生成的图。侧栏按钮常被挡住，改用 JS click。"""
    clicked = page.evaluate(
        """
        () => {
          const el = document.querySelector('[data-testid="create-new-chat-button"]')
            || document.querySelector('a[href="/"]');
          if (!el) { return false; }
          el.click();
          return true;
        }
        """
    )
    if clicked:
        time.sleep(1.5)
        wait_composer(page, 30000)
        log("已开新对话")
        return

    page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=120000)
    wait_composer(page, 60000)
    log("用首页重进作为新对话")


def generation_busy(page):
    return bool(page.evaluate(
        """
        () => {
          const labels = Array.from(document.querySelectorAll("button"))
            .map(b => ((b.getAttribute("aria-label") || "") + " " + (b.textContent || "")).toLowerCase());
          return labels.some(t => t.includes("stop generating") || t.includes("stop streaming") || t.includes("停止"));
        }
        """
    ))


def list_large_image_urls(page):
    return page.evaluate(
        """
        () => Array.from(document.querySelectorAll("img"))
          .filter(i => (i.naturalWidth || 0) >= 300)
          .map(i => i.currentSrc || i.src)
        """
    ) or []


def attach_image(page, image_path):
    """把本地参考图塞进 ChatGPT 输入框（隐藏的 input[type=file]）。"""
    path = os.path.abspath(image_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    file_input = page.query_selector("input[type='file']")
    if file_input is None:
        for label in ("Add files and more", "添加文件", "Attach", "上传"):
            button = page.get_by_role("button", name=re.compile(label, re.I))
            try:
                if button.count() > 0:
                    button.first.click()
                    break
            except Exception:  # noqa: BLE001
                pass
        file_input = page.wait_for_selector("input[type='file']", timeout=8000, state="attached")

    file_input.set_input_files(path)
    log("已附参考图：%s" % path)
    page.wait_for_timeout(4000)
    try:
        page.wait_for_function(
            "() => [...document.querySelectorAll(\"input[type=file]\")].some(f => f.files && f.files.length > 0)",
            timeout=12000,
        )
    except Exception:  # noqa: BLE001
        log("没等到文件控件确认，仍继续提交")


def save_image_from_page(page, out_path, ignore_urls=None, ignore_hashes=None):
    """在页面里 fetch 图片 blob，拿原始字节；成功返回 True。"""
    ignore = set(ignore_urls or [])
    script = """
    async (ignore) => {
      const imgs = Array.from(document.querySelectorAll("img"))
        .filter(i => (i.currentSrc || i.src || "").length > 0)
        .filter(i => (i.naturalWidth || 0) >= 300)
        .filter(i => ignore.indexOf(i.currentSrc || i.src) < 0);
      if (!imgs.length) { return null; }
      const img = imgs[imgs.length - 1];
      const url = img.currentSrc || img.src;
      try {
        const r = await fetch(url);
        const buf = await r.arrayBuffer();
        let binary = "";
        const bytes = new Uint8Array(buf);
        const chunk = 0x8000;
        for (let i = 0; i < bytes.length; i += chunk) {
          binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
        }
        return { b64: btoa(binary), w: img.naturalWidth, h: img.naturalHeight, url: url.slice(0, 40) };
      } catch (e) { return { error: String(e) }; }
    }
    """

    for attempt in range(1, 4):
        result = page.evaluate(script, list(ignore))

        if not result:
            log("第 %d 次：页面里还没找到够大的图片" % attempt)
            time.sleep(5)
            continue

        if result.get("error"):
            log("第 %d 次 fetch 失败：%s" % (attempt, result["error"]))
            time.sleep(5)
            continue

        data = base64.b64decode(result["b64"])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "wb") as handle:
            handle.write(data)

        digest = hashlib.sha256(data).hexdigest()
        if digest in (ignore_hashes or set()):
            log("跳过：这张和参考图/旧图是同一份（%s）" % digest[:12])
            try:
                os.remove(out_path)
            except OSError:
                pass
            return False

        log("已存原图：%s（%d 字节，页面报告 %dx%d）" % (out_path, len(data), result["w"], result["h"]))
        return True

    return False


def save_image_by_screenshot(page, out_path):
    """兜底：对图片元素本身做截图（原始分辨率附近，但仍是渲染结果）。"""
    element = page.query_selector(IMAGE_SELECTOR)

    if element is None:
        return False

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    element.screenshot(path=out_path)
    log("兜底截图已存：%s（%d 字节）" % (out_path, os.path.getsize(out_path)))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", action="store_true", help="打开浏览器等你登录一次")
    parser.add_argument("--prompt", help="要提交的提示词")
    parser.add_argument("--prompt-file", help="提示词文件（比 --prompt 更适合长文本）")
    parser.add_argument("--out", help="图片保存路径")
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--timeout", type=int, default=240, help="等图的秒数")
    parser.add_argument("--image", help="一并上传的参考图（动作帧要贴着同一张定稿时用）")
    args = parser.parse_args()

    prompt = args.prompt

    if args.prompt_file:
        prompt = open(args.prompt_file, encoding="utf-8").read()

    if not args.login and not (prompt and args.out):
        parser.error("要么 --login，要么同时给 --prompt/--prompt-file 和 --out")

    with sync_playwright() as play:
        context = play.chromium.launch_persistent_context(
            args.profile,
            channel="msedge",
            headless=False,
            viewport={"width": 1440, "height": 960},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        time.sleep(1.5)
        try:
            page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=120000)
        except Exception as exc:  # noqa: BLE001
            log("第一次打开失败：%s，换页再进" % exc)
            page = context.new_page()
            page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=120000)

        if args.login:
            log("请在打开的窗口里登录 ChatGPT（最多等 10 分钟）…")
            try:
                wait_composer(page, 600000)
                log("登录成功 —— 登录状态已保存到 %s，窗口即将关闭" % args.profile)
            except Exception as exc:  # noqa: BLE001
                log("没等到输入框：%s" % exc)
                context.close()
                return 2
            context.close()
            return 0

        try:
            wait_composer(page, 120000)
        except Exception:  # noqa: BLE001
            log("没找到输入框 —— 可能需要先跑一次 --login 登录")
            context.close()
            return 3

        start_new_chat(page)

        if args.image:
            attach_image(page, args.image)

        ignore_urls = list_large_image_urls(page)
        ignore_hashes = set()
        if args.image:
            ignore_hashes.add(file_sha(args.image))
        log("提交前提到 %d 张大图（会跳过，不当作新出的图）" % len(ignore_urls))

        log("提交提示词（%d 字）…" % len(prompt))
        box = page.query_selector(COMPOSER)
        box.click()
        page.keyboard.insert_text(prompt)
        time.sleep(0.5)
        page.keyboard.press("Enter")

        log("已提交，等出图（最多 %d 秒）…" % args.timeout)
        deadline = time.time() + args.timeout
        ok = False
        first_wait = True

        while time.time() < deadline:
            time.sleep(12 if first_wait else 7)
            first_wait = False

            if generation_busy(page):
                log("还在生成，继续等…")
                continue

            current = list_large_image_urls(page)
            if not any(url not in ignore_urls for url in current):
                continue

            if save_image_from_page(page, args.out, ignore_urls=ignore_urls, ignore_hashes=ignore_hashes):
                ok = True
                break

        if not ok:
            log("没抓到原图，试兜底截图…")
            ok = save_image_by_screenshot(page, args.out)

        context.close()
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
