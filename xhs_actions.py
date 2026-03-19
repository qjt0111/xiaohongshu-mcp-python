"""小红书操作模块 - 登录、发布、搜索等"""
import json
import os
from typing import Optional
from pathlib import Path
import asyncio

from playwright.async_api import async_playwright, Page

from browser import get_page, save_cookies, get_browser_path, reset_browser

# 获取脚本所在目录，确保 cookies 路径正确
SCRIPT_DIR = Path(__file__).parent.absolute()
COOKIES_FILE = str(SCRIPT_DIR / "cookies.json")


class XHSActions:
    """小红书操作类"""

    def __init__(self, page: Page):
        self.page = page

    # ========== 登录相关 ==========

    async def check_login(self) -> bool:
        """检查登录状态"""
        await self.page.goto("https://www.xiaohongshu.com/explore", timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 如果存在登录按钮，说明未登录
        login_btn = await self.page.query_selector(".login-btn")
        if login_btn:
            return False

        # 检查用户相关元素
        user_selectors = [
            ".side-bar .user",
            ".user-avatar",
            ".right-box .user",
            ".nav-user",
        ]
        for sel in user_selectors:
            el = await self.page.query_selector(sel)
            if el:
                return True

        return False

    async def get_qrcode(self) -> tuple[str, bool]:
        """
        获取登录二维码

        Returns:
            (二维码 base64, 是否已登录)
        """
        await self.page.goto("https://www.xiaohongshu.com/explore", timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 检查是否已登录
        if await self.check_login():
            return "", True

        # 获取二维码图片
        qr_el = await self.page.query_selector(".login-container .qrcode-img")
        if qr_el is None:
            return "", False

        src = await qr_el.get_attribute("src")
        return src or "", False

    # ========== 搜索相关 ==========

    async def search(self, keyword: str, filters: dict = None) -> str:
        """搜索内容"""
        url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_explore_feed"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 只提取需要的关键信息
        result = await self.page.evaluate("""() => {
            if (window.__INITIAL_STATE__ &&
                window.__INITIAL_STATE__.search &&
                window.__INITIAL_STATE__.search.feeds) {
                const feeds = window.__INITIAL_STATE__.search.feeds;
                const feedsData = feeds.value !== undefined ? feeds.value : feeds._value;
                if (feedsData && Array.isArray(feedsData)) {
                    const simplifiedFeeds = feedsData.map(feed => {
                        const noteCard = feed.noteCard || {};
                        return {
                            id: feed.id || noteCard.noteId || "",
                            xsec_token: feed.xsecToken || "",  // 访问令牌，用于获取详情
                            title: noteCard.displayTitle || "",
                            content: noteCard.desc || "",
                            cover: noteCard.cover?.infoList?.[0]?.url || "",
                            images: (noteCard.imageList || []).map(img => img.infoList?.[0]?.url || ""),
                            likes: noteCard.interactInfo?.likedCount || "0",
                            comments: noteCard.interactInfo?.commentCount || "0",
                            collects: noteCard.interactInfo?.collectedCount || "0",
                            author: noteCard.user?.nickname || noteCard.user?.nickName || "",
                            authorId: noteCard.user?.userId || "",
                            type: noteCard.type || "",  // video 或 normal
                        };
                    });
                    return JSON.stringify(simplifiedFeeds);
                }
            }
            return "[]";
        }""")

        return result if result else "[]"

    # ========== Feed 相关 ==========

    async def get_feeds(self) -> str:
        """获取首页 Feed 列表"""
        await self.page.goto("https://www.xiaohongshu.com/explore", timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 只提取关键信息
        result = await self.page.evaluate("""() => {
            if (window.__INITIAL_STATE__) {
                const feeds = window.__INITIAL_STATE__.homeFeed?.feeds || [];
                const simplifiedFeeds = feeds.map(feed => {
                    const noteCard = feed.noteCard || {};
                    return {
                        id: feed.id || noteCard.noteId || "",
                        xsec_token: feed.xsecToken || "",
                        title: noteCard.displayTitle || "",
                        content: noteCard.desc || "",
                        cover: noteCard.cover?.infoList?.[0]?.url || "",
                        likes: noteCard.interactInfo?.likedCount || "0",
                        comments: noteCard.interactInfo?.commentCount || "0",
                        collects: noteCard.interactInfo?.collectedCount || "0",
                        author: noteCard.user?.nickname || noteCard.user?.nickName || "",
                        type: noteCard.type || "",
                    };
                });
                return JSON.stringify(simplifiedFeeds);
            }
            return "[]";
        }""")

        return result if result else "[]"

    async def get_feed_detail(self, feed_id: str, xsec_token: str) -> str:
        """获取 Feed 详情"""
        url = f"https://www.xiaohongshu.com/explore/{feed_id}?xsec_token={xsec_token}&xsec_type=pc_share"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        data = await self.page.evaluate("() => window.__INITIAL_STATE__")
        if data:
            return json.dumps(data, ensure_ascii=False, indent=2)
        return "{}"

    # ========== 发布相关 ==========

    async def publish_content(
        self,
        title: str,
        content: str,
        images: list[str],
        tags: list[str] = None,
        schedule_at: str = None,
        is_original: bool = False,
        visibility: str = "公开可见",
        headless: bool = True,  # 添加参数控制是否有头模式
    ) -> str:
        """发布图文内容"""
        print(f"[publish] 开始发布: {title}, headless={headless}")

        # 直接使用图文发布URL（image tab）
        url = "https://creator.xiaohongshu.com/publish/publish?source=official&from=tab_switch&target=image"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 上传图片
        print(f"[publish] 上传 {len(images)} 张图片")
        for i, img_path in enumerate(images):
            if not os.path.exists(img_path):
                return f"发布失败: 图片不存在: {img_path}"

            selector = ".upload-input" if i == 0 else "input[type=file]"
            file_input = await self.page.query_selector(selector)
            if file_input:
                await file_input.set_input_files(img_path)
                print(f"[publish] 已上传图片 {i+1}/{len(images)}")
                await asyncio.sleep(1)

        # 等待图片预览出现
        await asyncio.sleep(2)

        # 填写标题
        print(f"[publish] 填写标题")
        title_input = await self.page.query_selector("div.d-input input")
        if title_input:
            await title_input.fill(title)

        # 填写正文
        print(f"[publish] 填写正文")
        content_editor = await self.page.query_selector("div.ql-editor")
        if content_editor is None:
            content_editor = await self.page.query_selector('[role="textbox"]')
        if content_editor:
            await content_editor.fill(content)

        # 填写标签
        if tags:
            print(f"[publish] 填写标签: {tags}")
            await self._input_tags_simple(content_editor, tags)

        await asyncio.sleep(1)

        # 点击发布按钮
        print("[publish] 点击发布按钮")
        result = await self.page.evaluate("""() => {
            const btn = document.querySelector('.publish-page-publish-btn button.bg-red');
            if (btn) {
                btn.click();
                return 'clicked';
            }
            return 'not_found';
        }""")

        if result == 'not_found':
            return "发布失败: 未找到发布按钮"

        await asyncio.sleep(2)
        print(f"[publish] 发布完成: {title}")
        return f"发布成功: {title}"

    async def publish_content_with_window(
        self,
        title: str,
        content: str,
        images: list[str],
        tags: list[str] = None,
        timeout: int = 120,
    ) -> str:
        """
        使用浏览器窗口发布（用于调试）
        """
        from browser import get_browser_path
        from playwright.async_api import async_playwright

        chrome_path = get_browser_path()
        cookies_path = os.environ.get("COOKIES_PATH", COOKIES_FILE)

        playwright = None
        browser = None

        try:
            playwright = await async_playwright().start()

            launch_args = {
                "headless": False,
                "args": ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
            }
            if chrome_path:
                launch_args["executable_path"] = chrome_path
            browser = await playwright.chromium.launch(**launch_args)

            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                locale='zh-CN',
            )

            # 加载 cookies
            if os.path.exists(cookies_path):
                cookies = json.load(open(cookies_path, "r"))
                await context.add_cookies(cookies)
                print(f"[publish] 已加载 cookies: {len(cookies)} 条")

            page = await context.new_page()

            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            print(f"[publish] 浏览器窗口已打开")

            # 1. 打开发布页面（直接使用图文发布URL）
            print("[publish] 1. 打开图文发布页面...")
            url = "https://creator.xiaohongshu.com/publish/publish?source=official&from=tab_switch&target=image"
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=30000)
            print("[publish] 页面加载完成")
            await asyncio.sleep(3)

            # 检查是否登录
            login_check = await page.query_selector(".login-btn, .user-info")
            if login_check is not None:
                current_url = page.url
                if "login" in current_url or "login-btn" in str(await login_check.get_attribute("class") or ""):
                    print("[publish] 未登录！请先登录")
                    await asyncio.sleep(30)  # 等待用户登录
                    return "未登录，请先使用 login_with_browser_window 登录"

            # 2. 等待上传区域出现
            print("[publish] 2. 等待上传区域...")
            upload_content = await page.wait_for_selector("div.upload-content", timeout=10000)
            if upload_content:
                print("[publish] 找到上传区域")
            else:
                print("[publish] 未找到上传区域")
                return "未找到上传区域"

            await asyncio.sleep(1)

            # 3. 上传图片
            print(f"[publish] 3. 上传图片 ({len(images)} 张)...")
            for i, img_path in enumerate(images):
                if not os.path.exists(img_path):
                    print(f"[publish] 图片不存在: {img_path}")
                    continue
                selector = ".upload-input" if i == 0 else "input[type=file]"
                file_input = await page.query_selector(selector)
                if file_input:
                    await file_input.set_input_files(img_path)
                    print(f"[publish] 已上传图片 {i+1}: {img_path}")
                    await asyncio.sleep(2)
                else:
                    print(f"[publish] 未找到上传输入框: {selector}")

            await asyncio.sleep(3)

            # 4. 填写标题
            print("[publish] 4. 填写标题...")
            title_input = await page.query_selector("div.d-input input")
            if title_input:
                await title_input.fill(title)
                print(f"[publish] 标题: {title}")
            else:
                print("[publish] 未找到标题输入框")

            # 5. 填写正文
            print("[publish] 5. 填写正文...")
            content_editor = await page.query_selector("div.ql-editor")
            if content_editor:
                await content_editor.fill(content)
                print(f"[publish] 正文: {content[:30]}...")
            else:
                print("[publish] 未找到正文编辑器")

            # 6. 填写标签
            if tags:
                print(f"[publish] 6. 填写标签: {tags}")
                await page.keyboard.press("End")
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
                for tag in tags[:5]:
                    await content_editor.type(f"#{tag.lstrip('#')} ")
                    await asyncio.sleep(0.5)

            await asyncio.sleep(1)

            # 7. 点击发布
            print("[publish] 7. 点击发布按钮...")
            btn = await page.query_selector(".publish-page-publish-btn button.bg-red")
            if btn:
                await btn.click()
                print("[publish] 已点击发布")
            else:
                print("[publish] 未找到发布按钮")

            await asyncio.sleep(5)

            # 保存 cookies
            cookies = await context.cookies()
            json.dump(cookies, open(cookies_path, "w"), indent=2)

            print("[publish] 完成，5秒后关闭浏览器...")
            await asyncio.sleep(5)
            return f"发布完成: {title}"

        except Exception as e:
            print(f"[publish] 错误: {e}")
            import traceback
            traceback.print_exc()
            return f"发布失败: {str(e)}"
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

    async def _input_tags_simple(self, editor, tags: list[str]):
        """简化的标签输入"""
        if not editor or not tags:
            return

        # 移动到末尾
        await self.page.keyboard.press("End")
        await asyncio.sleep(0.3)
        await self.page.keyboard.press("Enter")
        await asyncio.sleep(0.5)

        for tag in tags[:5]:  # 最多5个标签
            tag = tag.lstrip("#")
            await editor.type(f"#{tag} ")
            await asyncio.sleep(0.5)

    async def publish_video(
        self,
        title: str,
        content: str,
        video_path: str,
        tags: list[str] = None,
        schedule_at: str = None,
        visibility: str = "公开可见",
    ) -> str:
        """发布视频内容"""
        if not video_path or not os.path.exists(video_path):
            return f"发布失败: 视频文件不存在: {video_path}"

        # 直接使用视频发布URL
        url = "https://creator.xiaohongshu.com/publish/publish?source=official&from=tab_switch&target=video"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(3)

        # 上传视频
        file_input = await self.page.query_selector(".upload-input")
        if file_input is None:
            file_input = await self.page.query_selector("input[type=file]")
        if file_input:
            await file_input.set_input_files(video_path)
            print(f"[publish_video] 上传视频: {video_path}")
        else:
            return "发布失败: 未找到视频上传输入框"

        # 等待视频处理完成
        print("[publish_video] 等待视频处理...")
        btn = await self._wait_publish_button_clickable(timeout=600)
        if btn is None:
            return "发布失败: 视频处理超时"

        print("[publish_video] 视频处理完成，开始填写内容")

        # 填写标题
        title_input = await self.page.query_selector("div.d-input input")
        if title_input:
            await title_input.fill(title)
            print(f"[publish_video] 填写标题: {title}")
        await asyncio.sleep(1)

        # 填写正文
        content_editor = await self._get_content_editor()
        if content_editor:
            await content_editor.fill(content)

        # 填写标签
        if tags:
            await self._input_tags_v2(content_editor, tags)

        await asyncio.sleep(1)

        # 设置可见范围
        if visibility != "公开可见":
            await self._set_visibility(visibility)

        # 设置定时发布
        if schedule_at:
            await self._set_schedule(schedule_at)

        # 点击发布按钮（使用 JavaScript 点击更可靠）
        await asyncio.sleep(1)
        await self._remove_pop_cover()
        result = await self.page.evaluate("""() => {
            const btn = document.querySelector('.publish-page-publish-btn button.bg-red');
            if (btn) {
                btn.click();
                return 'clicked';
            }
            return 'not_found';
        }""")

        if result == 'not_found':
            return "发布失败: 未找到发布按钮"

        print(f"[publish_video] 点击发布按钮: {result}")
        await asyncio.sleep(3)
        return f"视频发布成功: {title}"

    # ========== 互动相关 ==========

    async def like_feed(self, feed_id: str, xsec_token: str, unlike: bool = False) -> str:
        """点赞/取消点赞"""
        url = f"https://www.xiaohongshu.com/explore/{feed_id}?xsec_token={xsec_token}"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(1)

        like_btn = await self.page.query_selector(".like-wrapper")
        if like_btn:
            await like_btn.click()
            action = "取消点赞" if unlike else "点赞"
            return f"{action}成功: {feed_id}"
        return "操作失败"

    async def favorite_feed(self, feed_id: str, xsec_token: str, unfavorite: bool = False) -> str:
        """收藏/取消收藏"""
        url = f"https://www.xiaohongshu.com/explore/{feed_id}?xsec_token={xsec_token}"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(1)

        fav_btn = await self.page.query_selector(".collect-wrapper")
        if fav_btn:
            await fav_btn.click()
            action = "取消收藏" if unfavorite else "收藏"
            return f"{action}成功: {feed_id}"
        return "操作失败"

    async def post_comment(self, feed_id: str, xsec_token: str, content: str) -> str:
        """发表评论"""
        url = f"https://www.xiaohongshu.com/explore/{feed_id}?xsec_token={xsec_token}"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(1)

        comment_input = await self.page.query_selector(".comment-input-wrapper textarea, .comment-input-wrapper input")
        if comment_input:
            await comment_input.fill(content)
            await asyncio.sleep(0.5)

            send_btn = await self.page.query_selector(".comment-input-wrapper .send-btn, .comment-input-wrapper button")
            if send_btn:
                await send_btn.click()
                return f"评论发表成功: {feed_id}"

        return "评论发表失败"

    # ========== 用户相关 ==========

    async def get_user_profile(self, user_id: str, xsec_token: str) -> str:
        """获取用户主页"""
        url = f"https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={xsec_token}"
        await self.page.goto(url, timeout=60000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        data = await self.page.evaluate("() => window.__INITIAL_STATE__")
        if data:
            return json.dumps(data, ensure_ascii=False, indent=2)
        return "{}"

    # ========== 私有方法 ==========

    async def _set_visibility(self, visibility: str):
        """设置可见范围"""
        dropdown = await self.page.query_selector("div.permission-card-wrapper div.d-select-content")
        if dropdown:
            await dropdown.click()
            await asyncio.sleep(0.5)

            options = await self.page.query_selector_all("div.d-options-wrapper div.d-grid-item div.custom-option")
            for opt in options:
                text = await opt.text_content()
                if text and visibility in text:
                    await opt.click()
                    break

    async def _set_original(self):
        """设置原创声明"""
        cards = await self.page.query_selector_all("div.custom-switch-card")
        for card in cards:
            text = await card.text_content()
            if text and "原创声明" in text:
                switch = await card.query_selector("div.d-switch")
                if switch:
                    await switch.click()
                    await asyncio.sleep(0.8)
                    await self._confirm_original()
                    break

    async def _confirm_original(self):
        """确认原创声明弹窗"""
        checkbox = await self.page.query_selector("div.footer div.d-checkbox input")
        if checkbox:
            await checkbox.click()
            await asyncio.sleep(0.3)

        btn = await self.page.query_selector("div.footer button.custom-button")
        if btn:
            await btn.click()

    async def _set_schedule(self, schedule_at: str):
        """设置定时发布"""
        switch = await self.page.query_selector(".post-time-wrapper .d-switch")
        if switch:
            await switch.click()
            await asyncio.sleep(0.8)

        time_input = await self.page.query_selector(".date-picker-container input")
        if time_input:
            await time_input.fill(schedule_at)

    async def _wait_publish_button_clickable(self, timeout: int = 600) -> Optional[any]:
        """等待发布按钮可点击"""
        selector = ".publish-page-publish-btn button.bg-red"
        for _ in range(timeout):
            btn = await self.page.query_selector(selector)
            if btn:
                visible = await btn.is_visible()
                if visible:
                    disabled = await btn.get_attribute("disabled")
                    if disabled is None:
                        cls = await btn.get_attribute("class")
                        if cls is None or "disabled" not in cls:
                            return btn
            await asyncio.sleep(1)
        return None


# ========== 独立函数：弹出浏览器登录 ==========

async def login_with_browser(timeout: int = 300) -> tuple[bool, str]:
    """
    弹出浏览器窗口进行扫码登录

    Args:
        timeout: 超时时间（秒），默认 5 分钟

    Returns:
        (是否成功, 消息)
    """
    chrome_path = get_browser_path()
    cookies_path = os.environ.get("COOKIES_PATH", COOKIES_FILE)

    playwright = None
    browser = None

    try:
        playwright = await async_playwright().start()

        # 非无头模式，显示浏览器窗口
        launch_args = {
            "headless": False,
            "args": [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
            ]
        }
        if chrome_path:
            launch_args["executable_path"] = chrome_path
        browser = await playwright.chromium.launch(**launch_args)

        context = await browser.new_context(
            viewport={'width': 1200, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
        )

        # 加载已有 cookies
        if os.path.exists(cookies_path):
            try:
                cookies = json.load(open(cookies_path, "r"))
                await context.add_cookies(cookies)
            except:
                pass

        page = await context.new_page()

        # 注入反检测脚本
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        # 打开小红书首页
        await page.goto("https://www.xiaohongshu.com/explore", timeout=60000)
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        await asyncio.sleep(2)

        # 检查是否已登录 - 如果没有登录按钮，说明已登录
        login_btn = await page.query_selector(".login-btn")
        if login_btn is None:
            cookies = await context.cookies()
            json.dump(cookies, open(cookies_path, "w"), indent=2)
            return True, "已处于登录状态"

        print("[login] 浏览器窗口已打开，请在窗口中扫码登录...")
        print(f"[login] 等待登录完成，超时时间: {timeout} 秒")

        # 等待扫码登录 - 使用多种方式检测登录成功
        print("[login] 等待登录成功检测...")
        for i in range(timeout * 2):
            # 方式1: 检查登录按钮是否消失
            login_btn = await page.query_selector(".login-btn")
            if login_btn is None:
                cookies = await context.cookies()
                json.dump(cookies, open(cookies_path, "w"), indent=2)
                print("[login] 登录成功（登录按钮消失），cookies 已保存")
                return True, "登录成功！Cookies 已保存。"

            # 方式2: 检查用户元素
            el = await page.query_selector(".side-bar .user, .user-avatar, .right-box .user")
            if el is not None:
                cookies = await context.cookies()
                json.dump(cookies, open(cookies_path, "w"), indent=2)
                print("[login] 登录成功（检测到用户元素），cookies 已保存")
                return True, "登录成功！Cookies 已保存。"

            # 方式3: 检查URL变化和 session cookie
            current_url = page.url
            if "login" not in current_url and i > 4:
                cookies_list = await context.cookies()
                has_session = any(c.get("name") in ["web_session", "a1", "webId"] for c in cookies_list)
                if has_session:
                    json.dump(cookies_list, open(cookies_path, "w"), indent=2)
                    print("[login] 登录成功（检测到session），cookies 已保存")
                    return True, "登录成功！Cookies 已保存。"

            await asyncio.sleep(0.5)

        return False, f"登录超时（{timeout}秒），请重试"

    except Exception as e:
        return False, f"登录失败: {str(e)}"
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
        # 重置 MCP 服务的浏览器实例，下次使用时会重新加载 cookies
        await reset_browser()
        # 重置 XHSActions 实例
        global _xhs_actions
        _xhs_actions = None


# ========== 全局实例 ==========

_xhs_actions: Optional[XHSActions] = None


async def get_xhs_actions() -> XHSActions:
    """获取小红书操作实例"""
    global _xhs_actions
    if _xhs_actions is None:
        page = await get_page()
        _xhs_actions = XHSActions(page)
    return _xhs_actions