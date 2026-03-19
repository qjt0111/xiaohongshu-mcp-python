#!/usr/bin/env python3
"""
小红书 MCP 服务器 - fastmcp 实现

使用方法:
    uv run python main.py

MCP 工具列表:
    - check_login_status: 检查登录状态
    - get_login_qrcode: 获取登录二维码（无头模式返回图片，有头模式弹窗口）
    - delete_cookies: 删除 cookies 重置登录
    - publish_content: 发布图文（无头模式后台发布，有头模式显示窗口）
    - publish_video: 发布视频内容
    - search_feeds: 搜索内容
    - list_feeds: 获取首页 Feed 列表
    - get_feed_detail: 获取笔记详情
    - user_profile: 获取用户主页
    - like_feed: 点赞/取消点赞
    - favorite_feed: 收藏/取消收藏
    - post_comment: 发表评论
"""
import base64
import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

from xhs_actions import get_xhs_actions, save_cookies, login_with_browser, COOKIES_FILE
from browser import get_browser_manager

# 创建 MCP 服务器
mcp = FastMCP("xiaohongshu-mcp")


# ========== 登录相关工具 ==========

@mcp.tool()
async def check_login_status() -> str:
    """检查小红书登录状态"""
    actions = await get_xhs_actions()
    logged_in = await actions.check_login()
    if logged_in:
        return "✅ 已登录\n\n你可以使用其他功能了。"
    else:
        return "❌ 未登录\n\n请使用 get_login_qrcode 工具获取二维码进行登录。"


@mcp.tool()
async def get_login_qrcode(timeout: int = 300) -> list:
    """
    获取登录二维码

    行为由 XHS_HEADLESS 配置控制：
    - 无头模式（默认）：返回二维码图片，用户扫码
    - 有头模式：弹出浏览器窗口，在窗口中扫码

    Args:
        timeout: 有头模式下的等待超时时间（秒），默认 300 秒

    注意：修改配置后需要重启 MCP 服务才能生效。
    """
    headless = os.environ.get("XHS_HEADLESS", "true").lower() == "true"

    if headless:
        # 无头模式：返回二维码图片
        actions = await get_xhs_actions()
        qr_base64, already_logged_in = await actions.get_qrcode()

        if already_logged_in:
            return [TextContent(type="text", text="你当前已处于登录状态")]

        if not qr_base64:
            return [TextContent(type="text", text="获取二维码失败，请重试")]

        # 从 data:image/png;base64,... 格式中提取 base64 数据
        if qr_base64.startswith("data:image"):
            parts = qr_base64.split(",", 1)
            if len(parts) == 2:
                image_data = parts[1]
                mime_part = parts[0].split(":")[1].split(";")[0]
            else:
                image_data = qr_base64
                mime_part = "image/png"
        else:
            image_data = qr_base64
            mime_part = "image/png"

        return [
            TextContent(type="text", text="请用小红书 App 扫码登录 👇"),
            ImageContent(type="image", data=image_data, mimeType=mime_part),
        ]
    else:
        # 有头模式：弹出浏览器窗口
        success, message = await login_with_browser(timeout)
        if success:
            return [TextContent(type="text", text=f"✅ {message}")]
        else:
            return [TextContent(type="text", text=f"❌ {message}")]


@mcp.tool()
async def delete_cookies() -> str:
    """
    删除 cookies 文件，重置登录状态

    删除后需要重新登录。
    """
    cookies_path = os.environ.get("COOKIES_PATH", COOKIES_FILE)
    if os.path.exists(cookies_path):
        os.remove(cookies_path)
        return f"Cookies 已成功删除，登录状态已重置。\n\n删除的文件路径: {cookies_path}"
    return "Cookies 文件不存在，无需删除。"


# ========== 发布相关工具 ==========

@mcp.tool()
async def publish_content(
    title: str,
    content: str,
    images: list[str],
    tags: list[str] = None,
    schedule_at: str = None,
    is_original: bool = False,
    visibility: str = "公开可见",
) -> str:
    """
    发布小红书图文内容

    行为由 XHS_HEADLESS 配置控制：
    - 无头模式（默认）：后台发布，直接返回结果
    - 有头模式：显示浏览器窗口，可以看到整个发布过程

    Args:
        title: 内容标题（小红书限制：最多20个中文字或英文单词）
        content: 正文内容，不包含以#开头的标签内容
        images: 图片路径列表（至少需要1张图片），支持本地绝对路径
        tags: 话题标签列表（可选），如 ["美食", "旅行"]
        schedule_at: 定时发布时间（可选），ISO8601格式
        is_original: 是否声明原创（可选）
        visibility: 可见范围（可选），支持: 公开可见、仅自己可见、仅互关好友可见

    注意：修改配置后需要重启 MCP 服务才能生效。
    """
    # 验证标题长度
    if len(title) > 20:
        return "发布失败: 标题长度超过限制（最多20个字）"

    if not images:
        return "发布失败: 至少需要1张图片"

    headless = os.environ.get("XHS_HEADLESS", "true").lower() == "true"

    if headless:
        # 无头模式：后台发布
        actions = await get_xhs_actions()
        result = await actions.publish_content(
            title=title,
            content=content,
            images=images,
            tags=tags or [],
            schedule_at=schedule_at,
            is_original=is_original,
            visibility=visibility,
        )
        return result
    else:
        # 有头模式：显示浏览器窗口
        from xhs_actions import XHSActions
        actions = XHSActions(None)  # type: ignore
        result = await actions.publish_content_with_window(
            title=title,
            content=content,
            images=images,
            tags=tags or [],
        )
        return result


@mcp.tool()
async def publish_video(
    title: str,
    content: str,
    video: str,
    tags: list[str] = None,
    schedule_at: str = None,
    visibility: str = "公开可见",
) -> str:
    """
    发布小红书视频内容（仅支持本地单个视频文件）

    Args:
        title: 内容标题（小红书限制：最多20个中文字或英文单词）
        content: 正文内容
        video: 本地视频绝对路径（如 /Users/user/video.mp4）
        tags: 话题标签列表（可选）
        schedule_at: 定时发布时间（可选），ISO8601格式
        visibility: 可见范围（可选）
    """
    # 验证标题长度
    if len(title) > 20:
        return "发布失败: 标题长度超过限制（最多20个字）"

    if not video:
        return "发布失败: 缺少视频文件路径"

    if not os.path.exists(video):
        return f"发布失败: 视频文件不存在: {video}"

    actions = await get_xhs_actions()
    result = await actions.publish_video(
        title=title,
        content=content,
        video_path=video,
        tags=tags or [],
        schedule_at=schedule_at,
        visibility=visibility,
    )
    return result


# ========== 搜索和浏览工具 ==========

@mcp.tool()
async def search_feeds(keyword: str) -> str:
    """
    搜索小红书内容

    Args:
        keyword: 搜索关键词
    """
    if not keyword:
        return "搜索失败: 缺少关键词参数"

    actions = await get_xhs_actions()
    result = await actions.search(keyword)
    return result


@mcp.tool()
async def list_feeds() -> str:
    """获取首页 Feeds 列表"""
    actions = await get_xhs_actions()
    result = await actions.get_feeds()
    return result


@mcp.tool()
async def get_feed_detail(
    feed_id: str,
    xsec_token: str,
    load_all_comments: bool = False,
) -> str:
    """
    获取小红书笔记详情

    Args:
        feed_id: 小红书笔记ID，从Feed列表获取
        xsec_token: 访问令牌，从Feed列表的xsecToken字段获取
        load_all_comments: 是否加载全部评论（可选）
    """
    if not feed_id or not xsec_token:
        return "获取失败: 缺少 feed_id 或 xsec_token 参数"

    actions = await get_xhs_actions()
    result = await actions.get_feed_detail(feed_id, xsec_token)
    return result


# ========== 用户相关工具 ==========

@mcp.tool()
async def user_profile(user_id: str, xsec_token: str) -> str:
    """
    获取指定的小红书用户主页

    Args:
        user_id: 小红书用户ID，从Feed列表获取
        xsec_token: 访问令牌，从Feed列表的xsecToken字段获取
    """
    if not user_id or not xsec_token:
        return "获取失败: 缺少 user_id 或 xsec_token 参数"

    actions = await get_xhs_actions()
    result = await actions.get_user_profile(user_id, xsec_token)
    return result


# ========== 互动相关工具 ==========

@mcp.tool()
async def like_feed(
    feed_id: str,
    xsec_token: str,
    unlike: bool = False,
) -> str:
    """
    为指定笔记点赞或取消点赞

    Args:
        feed_id: 小红书笔记ID
        xsec_token: 访问令牌
        unlike: 是否取消点赞，true为取消点赞
    """
    if not feed_id or not xsec_token:
        return "操作失败: 缺少 feed_id 或 xsec_token 参数"

    actions = await get_xhs_actions()
    result = await actions.like_feed(feed_id, xsec_token, unlike)
    return result


@mcp.tool()
async def favorite_feed(
    feed_id: str,
    xsec_token: str,
    unfavorite: bool = False,
) -> str:
    """
    收藏指定笔记或取消收藏

    Args:
        feed_id: 小红书笔记ID
        xsec_token: 访问令牌
        unfavorite: 是否取消收藏，true为取消收藏
    """
    if not feed_id or not xsec_token:
        return "操作失败: 缺少 feed_id 或 xsec_token 参数"

    actions = await get_xhs_actions()
    result = await actions.favorite_feed(feed_id, xsec_token, unfavorite)
    return result


@mcp.tool()
async def post_comment(
    feed_id: str,
    xsec_token: str,
    content: str,
) -> str:
    """
    发表评论到小红书笔记

    Args:
        feed_id: 小红书笔记ID
        xsec_token: 访问令牌
        content: 评论内容
    """
    if not feed_id or not xsec_token:
        return "发表评论失败: 缺少 feed_id 或 xsec_token 参数"

    if not content:
        return "发表评论失败: 缺少评论内容"

    actions = await get_xhs_actions()
    result = await actions.post_comment(feed_id, xsec_token, content)
    return result


# ========== 资源清理 ==========

async def cleanup():
    """清理资源"""
    manager = await get_browser_manager()
    await manager.close()


def main():
    """启动 MCP 服务器"""
    print("=" * 50)
    print("小红书 MCP 服务器启动中...")
    print("=" * 50)
    print()
    print("已注册的 MCP 工具:")
    print("  - check_login_status: 检查登录状态")
    print("  - get_login_qrcode: 获取登录二维码（无头返回图片，有头弹窗口）")
    print("  - delete_cookies: 删除 cookies 重置登录")
    print("  - publish_content: 发布图文（无头后台发布，有头显示窗口）")
    print("  - publish_video: 发布视频内容")
    print("  - search_feeds: 搜索内容")
    print("  - list_feeds: 获取首页 Feed 列表")
    print("  - get_feed_detail: 获取笔记详情")
    print("  - user_profile: 获取用户主页")
    print("  - like_feed: 点赞/取消点赞")
    print("  - favorite_feed: 收藏/取消收藏")
    print("  - post_comment: 发表评论")
    print()

    mcp.run()


if __name__ == "__main__":
    main()