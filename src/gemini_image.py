"""
Gemini Image Generator - 通过浏览器自动化生成图像

基于录制分析:
- 发送 prompt 后 URL 变为 /app/{session_id}
- 图像在 model-response 中以 img 标签呈现
- 图像 URL 来自 lh3.googleusercontent.com 或 fife.usercontent.google.com
"""

import base64
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

PROJECT_ROOT = Path(__file__).parent.parent
USERDATA_DIR = PROJECT_ROOT / "userdata"
OUTPUT_DIR = PROJECT_ROOT / "output"

BROWSER_ARGS = ["--disable-blink-features=AutomationControlled", "--no-sandbox"]


class GeminiImageGenerator:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.page: Page | None = None
        self.browser = None
        self.playwright = None
        OUTPUT_DIR.mkdir(exist_ok=True)

    def _ensure_logged_in(self):
        if not (USERDATA_DIR / "Default").exists():
            print("错误: 未找到登录数据")
            print("请先运行: uv run python src/gemini_image.py login")
            sys.exit(1)

    @staticmethod
    def login():
        USERDATA_DIR.mkdir(exist_ok=True)
        print("=" * 50)
        print("  Gemini 登录")
        print("  浏览器即将打开，请完成 Google 账号登录")
        print("  登录成功后程序会自动检测并退出")
        print("=" * 50)

        pw = sync_playwright().start()
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=str(USERDATA_DIR), headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN", args=BROWSER_ARGS,
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://gemini.google.com", wait_until="domcontentloaded")
        print("\n等待登录...")
        while True:
            try:
                if "/app" in page.url:
                    break
                if page.query_selector('rich-textarea'):
                    break
                time.sleep(2)
            except Exception:
                break
        print("登录成功! userdata 已保存到:", USERDATA_DIR)
        browser.close()
        pw.stop()

    def start(self):
        self._ensure_logged_in()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(USERDATA_DIR), headless=self.headless,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN", args=BROWSER_ARGS,
        )
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        self.page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
        try:
            self.page.wait_for_selector('rich-textarea', timeout=30000)
        except Exception:
            pass
        time.sleep(2)
        print("Gemini 已就绪")

    def _activate_image_tool(self):
        """点击 工具 -> 制作图片"""
        inp = self.page.query_selector('rich-textarea p')
        if inp:
            inp.click()
            time.sleep(0.5)
        tool_btn = self.page.query_selector('toolbox-drawer button')
        if tool_btn:
            tool_btn.click()
            time.sleep(1)
            img_btn = (
                self.page.query_selector('toolbox-drawer-item button[role="menuitemcheckbox"]')
                or self.page.query_selector('button:has-text("制作图片"), button:has-text("Create image")')
            )
            if img_btn:
                img_btn.click()
                time.sleep(1)
                print("  已激活「制作图片」工具")
                return True
        return False

    def _extract_images_from_dom(self) -> list[str]:
        """从页面中提取已加载完成的生成图像

        Gemini 生成的图片 DOM:
        <img class="image animate loaded" src="blob:https://gemini.google.com/..." alt="...AI 生成">
        关键: class 包含 'loaded' 表示图片已渲染完成
        """
        return self.page.evaluate("""
        () => {
            const urls = [];
            document.querySelectorAll('img.image.loaded').forEach(img => {
                if (img.src) urls.push(img.src);
            });
            // 兜底: 也检查 blob URL 的图片
            if (urls.length === 0) {
                document.querySelectorAll('img[src^="blob:"]').forEach(img => {
                    if (img.naturalWidth > 100 && img.alt && img.alt.includes('AI')) {
                        urls.push(img.src);
                    }
                });
            }
            return [...new Set(urls)];
        }
        """) or []

    def _count_loading_images(self) -> int:
        """检查正在加载中的图片数量 (有 animate 但没有 loaded)"""
        return self.page.evaluate("""
        () => {
            return document.querySelectorAll('img.image.animate:not(.loaded)').length;
        }
        """)

    def _is_send_button_ready(self) -> bool:
        """检查发送按钮是否恢复就绪状态（生成完成的信号）

        生成中: 按钮变为停止按钮(stop icon)或消失
        生成完: send-button-icon 重新出现
        """
        return self.page.evaluate("""
        () => {
            const icon = document.querySelector('mat-icon.send-button-icon');
            if (!icon) return false;
            // 确认是发送图标而不是停止图标
            const text = icon.textContent.trim();
            // send 图标的 ligature 通常是 'send' 或 'arrow_upward'
            // stop 图标是 'stop' 或 'stop_circle'
            if (text === 'stop' || text === 'stop_circle') return false;
            return true;
        }
        """)

    def generate(self, prompt: str, timeout: int = 120) -> list[str]:
        if not self.page:
            raise RuntimeError("浏览器未启动")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"发送提示词: {prompt}")

        self._activate_image_tool()

        # 输入 prompt
        inp = self.page.query_selector('rich-textarea p') or \
              self.page.query_selector('div[contenteditable="true"]')
        if not inp:
            print("错误: 找不到输入框")
            return []
        inp.click()
        time.sleep(0.3)
        self.page.keyboard.type(prompt, delay=30)
        time.sleep(0.5)

        # 发送
        btn = self.page.query_selector(
            'button:has(mat-icon.send-button-icon), '
            'button[aria-label*="Send"], button[aria-label*="发送"]'
        )
        if btn:
            btn.click()
        else:
            self.page.keyboard.press("Enter")

        print("已发送，等待生成...")

        # 等 URL 变化 -> /app/{session_id}
        try:
            self.page.wait_for_url("**/app/**", timeout=15000)
            sid = self.page.url.split("/app/")[-1].split("?")[0]
            print(f"  会话: {sid}")
        except Exception:
            pass

        # 发送后，发送按钮会消失/变成停止按钮
        # 先等按钮状态变化（确认已开始生成）
        time.sleep(3)
        # 然后等发送按钮恢复 = 生成完成
        # 同时持续检查 DOM 中是否出现图片
        start = time.time()
        send_btn_was_gone = False

        while time.time() - start < timeout:
            time.sleep(3)
            elapsed = int(time.time() - start)

            # 检查是否有图片了
            urls = self._extract_images_from_dom()
            loading = self._count_loading_images()

            if urls:
                if loading > 0:
                    # 有图片已加载，但还有在加载中的，继续等
                    print(f"  {len(urls)} 张已加载, {loading} 张加载中...")
                    continue
                # 全部加载完成
                print(f"  检测到 {len(urls)} 张图像")
                return self._download(timestamp)

            if loading > 0:
                # 图片在加载中但还没 loaded
                if elapsed % 10 < 3:
                    print(f"  图片加载中... ({elapsed}s)")
                continue

            # 检查发送按钮状态
            btn_ready = self._is_send_button_ready()
            if not btn_ready:
                send_btn_was_gone = True  # 确认按钮已变化（正在生成）
            elif send_btn_was_gone:
                # 按钮从消失/停止 恢复为发送 = 生成完成
                print(f"  生成完成，等待图片渲染...")
                time.sleep(8)
                urls = self._extract_images_from_dom()
                if urls:
                    print(f"  共 {len(urls)} 张图像")
                    return self._download(timestamp)
                print("  模型已回复但未生成图像")
                return []

            if elapsed % 10 < 3:
                print(f"  生成中... ({elapsed}s)")

        # 超时前最后尝试
        urls = self._extract_images_from_dom()
        if urls:
            return self._download(timestamp)
        print("超时: 未检测到生成的图像")
        return []

    def _download(self, timestamp: str) -> list[str]:
        """点击每张图片的下载按钮，拦截下载流保存文件"""
        saved = []

        # 方式1: 点击下载按钮拦截下载
        # 先尝试找到图片的下载按钮
        download_count = self.page.evaluate("""
        () => {
            // 找到所有已加载的生成图片
            const imgs = document.querySelectorAll('img.image.loaded');
            return imgs.length;
        }
        """)

        if download_count == 0:
            return saved

        for i in range(download_count):
            try:
                # 点击第 i 张图片触发选中/展开
                self.page.evaluate(f"""
                () => {{
                    const imgs = document.querySelectorAll('img.image.loaded');
                    if (imgs[{i}]) imgs[{i}].click();
                }}
                """)
                time.sleep(1)

                # 找下载按钮并拦截下载
                with self.page.expect_download(timeout=10000) as download_info:
                    # 点击下载按钮
                    dl_btn = self.page.query_selector(
                        'button[aria-label*="下载"], button[aria-label*="Download"], '
                        'button[aria-label*="download"]'
                    )
                    if dl_btn:
                        dl_btn.click()
                    else:
                        continue

                download = download_info.value
                fp = OUTPUT_DIR / f"gemini_{timestamp}_{i+1}.png"
                download.save_as(str(fp))
                size = fp.stat().st_size
                if size < 10240:
                    fp.unlink()
                    continue
                saved.append(str(fp))
                print(f"  已保存: {fp.name} ({size//1024}KB)")

            except Exception:
                # 下载按钮方式失败，回退到 canvas
                pass

        # 方式2: 如果下载按钮没拿到，用 canvas 兜底
        if not saved:
            print("  使用 canvas 方式提取...")
            images_b64 = self.page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('img.image.loaded').forEach(img => {
                    try {
                        const canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        results.push(canvas.toDataURL('image/png').split(',')[1]);
                    } catch(e) {}
                });
                return results;
            }
            """) or []

            for j, b64 in enumerate(images_b64):
                try:
                    body = base64.b64decode(b64)
                    if len(body) < 10240:
                        continue
                    fp = OUTPUT_DIR / f"gemini_{timestamp}_{j+1}.png"
                    fp.write_bytes(body)
                    saved.append(str(fp))
                    print(f"  已保存: {fp.name} ({len(body)//1024}KB)")
                except Exception as e:
                    print(f"  下载失败: {e}")

        return saved

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def main():
    import argparse
    p = argparse.ArgumentParser(description="Gemini Image Generator")
    p.add_argument("prompt", nargs="?", help="提示词，或 'login' 进行登录")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--output", "-o", type=str, default=None)
    args = p.parse_args()

    if args.prompt == "login":
        GeminiImageGenerator.login()
        return

    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output)
        OUTPUT_DIR.mkdir(exist_ok=True)

    gen = GeminiImageGenerator(headless=args.headless)
    try:
        gen.start()
        if args.prompt:
            files = gen.generate(args.prompt)
            if files:
                print(f"\n生成完成! {len(files)} 张图像:")
                for f in files:
                    print(f"  {f}")
            else:
                print("未能获取到图像")
        else:
            print("\n交互模式 - 输入提示词，'quit' 退出")
            while True:
                try:
                    prompt = input("\n提示词> ").strip()
                    if prompt.lower() in ("quit", "exit", "q"):
                        break
                    if not prompt:
                        continue
                    files = gen.generate(prompt)
                    if files:
                        print(f"生成完成! {len(files)} 张图像:")
                        for f in files:
                            print(f"  {f}")
                    else:
                        print("未能获取到图像")
                except (EOFError, KeyboardInterrupt):
                    break
    finally:
        gen.stop()


if __name__ == "__main__":
    main()
