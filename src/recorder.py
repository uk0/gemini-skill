"""
Gemini Web Recorder - 浏览器请求拦截 & 操作录制器

功能:
1. 首次运行: 打开 Gemini 页面，用户手动登录，保存 userdata
2. 后续运行: 自动加载 userdata 免登录
3. 拦截所有网络请求并记录
4. 记录页面点击操作
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Request, Response

PROJECT_ROOT = Path(__file__).parent.parent
USERDATA_DIR = PROJECT_ROOT / "userdata"
RECORDINGS_DIR = PROJECT_ROOT / "recordings"


class GeminiRecorder:
    def __init__(self):
        self.requests_log: list[dict] = []
        self.clicks_log: list[dict] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording = False

        USERDATA_DIR.mkdir(exist_ok=True)
        RECORDINGS_DIR.mkdir(exist_ok=True)

    def _on_request(self, request: Request):
        """拦截并记录所有请求"""
        if not self.recording:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": request.url,
            "resource_type": request.resource_type,
            "headers": dict(request.headers),
            "post_data": None,
        }

        try:
            if request.post_data:
                entry["post_data"] = request.post_data
        except Exception:
            pass

        self.requests_log.append(entry)

        # 实时打印关键请求
        url = request.url
        if any(kw in url for kw in [
            "batchexecute", "generate", "image", "upload",
            "blob", "attachment", "proactiveBackend",
        ]):
            print(f"  [REQ] {request.method} {url[:120]}")

    def _on_response(self, response: Response):
        """记录响应状态"""
        if not self.recording:
            return

        url = response.url
        if any(kw in url for kw in [
            "batchexecute", "generate", "image", "upload",
            "blob", "attachment", "proactiveBackend",
        ]):
            content_type = response.headers.get("content-type", "")
            print(f"  [RES] {response.status} {url[:100]} [{content_type[:50]}]")

            # 尝试捕获响应体
            try:
                body = response.text()
                if body and len(body) < 50000:
                    for entry in reversed(self.requests_log):
                        if entry["url"] == url and "response" not in entry:
                            entry["response"] = {
                                "status": response.status,
                                "headers": dict(response.headers),
                                "body": body[:20000],
                            }
                            break
            except Exception:
                pass

    def _inject_click_tracker(self, page: Page):
        """注入 JS 追踪页面点击"""
        page.evaluate("""
        () => {
            if (window.__gemini_click_tracker) return;
            window.__gemini_click_tracker = true;
            window.__click_log = [];

            document.addEventListener('click', (e) => {
                const el = e.target;
                const entry = {
                    timestamp: new Date().toISOString(),
                    tag: el.tagName,
                    id: el.id || null,
                    className: el.className || null,
                    text: (el.textContent || '').trim().substring(0, 100),
                    ariaLabel: el.getAttribute('aria-label') || null,
                    role: el.getAttribute('role') || null,
                    xpath: getXPath(el),
                    rect: el.getBoundingClientRect().toJSON(),
                };
                window.__click_log.push(entry);
                console.log('[CLICK]', JSON.stringify(entry));
            }, true);

            function getXPath(el) {
                if (!el || el.nodeType !== 1) return '';
                const parts = [];
                while (el && el.nodeType === 1) {
                    let idx = 1;
                    let sib = el.previousSibling;
                    while (sib) {
                        if (sib.nodeType === 1 && sib.tagName === el.tagName) idx++;
                        sib = sib.previousSibling;
                    }
                    parts.unshift(el.tagName.toLowerCase() + '[' + idx + ']');
                    el = el.parentNode;
                }
                return '/' + parts.join('/');
            }
        }
        """)

    def _collect_clicks(self, page: Page) -> list[dict]:
        """收集页面点击记录"""
        try:
            return page.evaluate("() => window.__click_log || []")
        except Exception:
            return []

    def _save_recording(self):
        """保存录制数据"""
        output = {
            "session_id": self.session_id,
            "recorded_at": datetime.now().isoformat(),
            "total_requests": len(self.requests_log),
            "total_clicks": len(self.clicks_log),
            "requests": self.requests_log,
            "clicks": self.clicks_log,
        }

        filepath = RECORDINGS_DIR / f"session_{self.session_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n录制数据已保存: {filepath}")
        print(f"  请求数: {len(self.requests_log)}")
        print(f"  点击数: {len(self.clicks_log)}")

        # 额外保存一份精简的 API 请求摘要
        api_requests = [
            r for r in self.requests_log
            if any(kw in r["url"] for kw in [
                "batchexecute", "generate", "image", "upload",
                "blob", "attachment", "proactiveBackend",
            ])
        ]
        if api_requests:
            summary_path = RECORDINGS_DIR / f"api_summary_{self.session_id}.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(api_requests, f, ensure_ascii=False, indent=2)
            print(f"  API 摘要: {summary_path} ({len(api_requests)} 条)")

    def run(self):
        """启动录制器"""
        has_userdata = (USERDATA_DIR / "Default").exists()

        print("=" * 60)
        print("  Gemini Web Recorder")
        print("=" * 60)

        if has_userdata:
            print("  检测到已保存的登录数据，将自动加载")
        else:
            print("  首次运行，请在浏览器中手动登录 Google 账号")
            print("  登录完成后回到终端按 Enter 继续")

        print()
        print("  操作说明:")
        print("  - 浏览器打开后，进行你想录制的操作")
        print("  - 所有网络请求和点击会被自动记录")
        print("  - 在终端输入 's' + Enter 保存并退出")
        print("  - 在终端输入 'q' + Enter 直接退出不保存")
        print("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(USERDATA_DIR),
                headless=False,
                viewport={"width": 1280, "height": 900},
                locale="en-US",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # 绑定请求拦截
            page.on("request", self._on_request)
            page.on("response", self._on_response)

            # 导航到 Gemini
            page.goto("https://gemini.google.com", wait_until="domcontentloaded")
            print("\n浏览器已打开 Gemini")

            if not has_userdata:
                print("\n>>> 请在浏览器中完成登录 <<<")
                print(">>> 登录完成后，页面会自动跳转到 Gemini 主页 <<<")
                # 等待登录完成 - 检测 URL 变化
                try:
                    page.wait_for_url("**/app**", timeout=300000)
                except Exception:
                    pass
                print("登录数据已保存到 userdata/")

            # 等待页面稳定后再注入
            time.sleep(3)

            # 注入点击追踪 (页面导航后需要重新注入)
            def safe_inject(p: Page):
                try:
                    self._inject_click_tracker(p)
                except Exception:
                    pass

            safe_inject(page)

            # 页面导航时重新注入
            page.on("load", lambda: safe_inject(page))

            # 监听新页面也注入追踪
            def on_page(new_page: Page):
                new_page.on("request", self._on_request)
                new_page.on("response", self._on_response)
                try:
                    new_page.wait_for_load_state("domcontentloaded")
                    safe_inject(new_page)
                except Exception:
                    pass

            browser.on("page", on_page)

            # 开始录制
            self.recording = True
            print("\n录制已开始... 在浏览器中操作 Gemini")
            print("输入 's' 保存退出 | 'q' 放弃退出\n")

            import select
            import threading

            stop_flag = threading.Event()
            save_flag = threading.Event()

            def input_listener():
                while not stop_flag.is_set():
                    try:
                        cmd = input().strip().lower()
                        if cmd == "s":
                            save_flag.set()
                            stop_flag.set()
                        elif cmd == "q":
                            stop_flag.set()
                    except EOFError:
                        stop_flag.set()

            listener = threading.Thread(target=input_listener, daemon=True)
            listener.start()

            # 主循环: 定期收集点击数据
            while not stop_flag.is_set():
                try:
                    time.sleep(2)
                    for p_page in browser.pages:
                        try:
                            clicks = self._collect_clicks(p_page)
                            if clicks:
                                new_clicks = clicks[len(self.clicks_log):]
                                for c in new_clicks:
                                    print(f"  [CLICK] {c.get('tag')} "
                                          f"text=\"{c.get('text', '')[:40]}\" "
                                          f"aria=\"{c.get('ariaLabel', '')}\"")
                                self.clicks_log = clicks
                        except Exception:
                            pass
                except KeyboardInterrupt:
                    save_flag.set()
                    break

            self.recording = False

            if save_flag.is_set():
                # 最后收集一次点击
                for p_page in browser.pages:
                    try:
                        self.clicks_log = self._collect_clicks(p_page)
                    except Exception:
                        pass
                self._save_recording()
            else:
                print("\n录制已取消，数据未保存")

            browser.close()

        print("完成!")


if __name__ == "__main__":
    recorder = GeminiRecorder()
    recorder.run()
