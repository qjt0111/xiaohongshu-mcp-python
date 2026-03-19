"""浏览器管理模块 - Playwright 封装"""
import json
import os
from typing import Optional
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, Playwright

# 获取脚本所在目录，确保 cookies 路径正确
SCRIPT_DIR = Path(__file__).parent.absolute()
COOKIES_FILE = str(SCRIPT_DIR / "cookies.json")


def get_browser_path() -> Optional[str]:
    """
    从环境变量获取浏览器路径

    优先级：
    1. 环境变量 CHROME_PATH（MCP 配置中设置）
    2. 返回 None（使用 Playwright 自带的 Chromium）

    Returns:
        浏览器路径或 None
    """
    env_path = os.environ.get("CHROME_PATH")
    if env_path:
        if os.path.exists(env_path):
            return env_path
        print(f"[browser] 环境变量 CHROME_PATH 指向的路径不存在: {env_path}")
    return None


class BrowserManager:
    """Playwright 浏览器管理器"""

    def __init__(self, headless: bool = True, chrome_path: Optional[str] = None):
        self.headless = headless
        self.chrome_path = chrome_path  # None 表示使用 Playwright 自带的 Chromium
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def get_page(self) -> Page:
        """获取或创建页面实例"""
        if self._page is None:
            self._playwright = await async_playwright().start()

            # 构建启动参数
            launch_args = {
                "headless": self.headless,
                "args": [
                    '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-infobars',
                    '--disable-background-networking',
                    '--disable-breakpad',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-first-run',
                ]
            }

            # 如果配置了自定义浏览器路径，则使用；否则用 Playwright 自带的 Chromium
            if self.chrome_path:
                launch_args["executable_path"] = self.chrome_path
                print(f"[browser] 使用自定义浏览器: {self.chrome_path}")
            else:
                print("[browser] 使用 Playwright 自带的 Chromium")

            self._browser = await self._playwright.chromium.launch(**launch_args)

            # 创建更真实的浏览器上下文
            context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                color_scheme='light',
                has_touch=False,
                is_mobile=False,
                java_script_enabled=True,
                ignore_https_errors=True,
            )

            # 加载已保存的 cookies
            await self._load_cookies(context)

            self._page = await context.new_page()

            # 注入脚本隐藏 webdriver 等自动化特征
            await self._page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
            """)

        return self._page

    async def _load_cookies(self, context):
        """从文件加载 cookies"""
        cookies_path = os.environ.get("COOKIES_PATH", COOKIES_FILE)
        if os.path.exists(cookies_path):
            try:
                cookies = json.load(open(cookies_path, "r"))
                await context.add_cookies(cookies)
                print(f"[browser] 已加载 cookies: {cookies_path}, {len(cookies)} 条")
            except Exception as e:
                print(f"[browser] 加载 cookies 失败: {e}")

    async def save_cookies(self):
        """保存 cookies 到文件"""
        if self._page is None:
            return

        cookies_path = os.environ.get("COOKIES_PATH", COOKIES_FILE)
        try:
            cookies = await self._page.context.cookies()
            json.dump(cookies, open(cookies_path, "w"), indent=2)
            print(f"[browser] 已保存 cookies: {cookies_path}, {len(cookies)} 条")
        except Exception as e:
            print(f"[browser] 保存 cookies 失败: {e}")

    async def close(self):
        """关闭浏览器"""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._page = None
        self._browser = None
        self._playwright = None


# 全局浏览器管理器实例
_browser_manager: Optional[BrowserManager] = None


async def get_browser_manager() -> BrowserManager:
    """获取全局浏览器管理器实例"""
    global _browser_manager
    if _browser_manager is None:
        headless = os.environ.get("XHS_HEADLESS", "true").lower() == "true"
        chrome_path = get_browser_path()  # 从环境变量获取，None 则用自带 Chromium
        _browser_manager = BrowserManager(headless=headless, chrome_path=chrome_path)
    return _browser_manager


async def get_page() -> Page:
    """获取浏览器页面"""
    manager = await get_browser_manager()
    return await manager.get_page()


async def save_cookies():
    """保存 cookies"""
    manager = await get_browser_manager()
    await manager.save_cookies()


async def reset_browser():
    """重置浏览器实例（用于重新加载 cookies）"""
    global _browser_manager
    if _browser_manager is not None:
        await _browser_manager.close()
        _browser_manager = None