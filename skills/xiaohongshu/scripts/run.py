#!/usr/bin/env python3
"""
小红书 Skill 入口脚本

用法:
    python scripts/run.py check-login
    python scripts/run.py login
    python scripts/run.py publish --title "标题" --content "正文" --images "img1.jpg" "img2.jpg"
    python scripts/run.py search --keyword "关键词"
    python scripts/run.py feeds
    python scripts/run.py detail --feed-id "xxx" --xsec-token "xxx"
"""
import argparse
import asyncio
import json
import os
import sys

# 添加项目根目录到 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from xhs_actions import get_xhs_actions, save_cookies, login_with_browser, COOKIES_FILE


async def cmd_check_login():
    """检查登录状态"""
    actions = await get_xhs_actions()
    logged_in = await actions.check_login()
    if logged_in:
        print("STATUS: LOGGED_IN")
        print("MESSAGE: 已登录")
    else:
        print("STATUS: NOT_LOGGED_IN")
        print("MESSAGE: 未登录，请先登录")
    return 0 if logged_in else 1


async def cmd_login(timeout: int = 300):
    """扫码登录（根据配置决定模式）"""
    headless = os.environ.get("XHS_HEADLESS", "true").lower() == "true"

    if headless:
        # 无头模式：通过 XHSActions 获取二维码
        actions = await get_xhs_actions()
        qr_base64, already_logged_in = await actions.get_qrcode()

        if already_logged_in:
            print("STATUS: LOGIN_SUCCESS")
            print("MESSAGE: 已处于登录状态")
            return 0

        if not qr_base64:
            print("STATUS: LOGIN_FAILED")
            print("MESSAGE: 获取二维码失败，请重试")
            return 1

        print("STATUS: QR_CODE_READY")
        print("MESSAGE: 请用小红书 App 扫码登录")
        print(f"QR_CODE: {qr_base64[:50]}..." if len(qr_base64) > 50 else f"QR_CODE: {qr_base64}")
        return 0
    else:
        # 有头模式：弹出浏览器窗口
        success, message = await login_with_browser(timeout)
        if success:
            print("STATUS: LOGIN_SUCCESS")
            print(f"MESSAGE: {message}")
            return 0
        else:
            print("STATUS: LOGIN_FAILED")
            print(f"MESSAGE: {message}")
            return 1


async def cmd_publish(args):
    """发布图文"""
    actions = await get_xhs_actions()

    # 检查登录
    if not await actions.check_login():
        print("STATUS: NOT_LOGGED_IN")
        print("MESSAGE: 未登录，请先登录")
        return 1

    result = await actions.publish_content(
        title=args.title,
        content=args.content,
        images=args.images,
        tags=args.tags or [],
        schedule_at=args.schedule_at,
        is_original=args.is_original,
        visibility=args.visibility or "公开可见",
    )

    if "成功" in result:
        print("STATUS: PUBLISH_SUCCESS")
        print(f"MESSAGE: {result}")
        return 0
    else:
        print("STATUS: PUBLISH_FAILED")
        print(f"MESSAGE: {result}")
        return 1


async def cmd_publish_video(args):
    """发布视频"""
    actions = await get_xhs_actions()

    # 检查登录
    if not await actions.check_login():
        print("STATUS: NOT_LOGGED_IN")
        print("MESSAGE: 未登录，请先登录")
        return 1

    result = await actions.publish_video(
        title=args.title,
        content=args.content,
        video_path=args.video,
        tags=args.tags or [],
        schedule_at=args.schedule_at,
        visibility=args.visibility or "公开可见",
    )

    if "成功" in result:
        print("STATUS: PUBLISH_SUCCESS")
        print(f"MESSAGE: {result}")
        return 0
    else:
        print("STATUS: PUBLISH_FAILED")
        print(f"MESSAGE: {result}")
        return 1


async def cmd_search(args):
    """搜索内容"""
    actions = await get_xhs_actions()
    result = await actions.search(args.keyword)
    print(f"RESULT: {result}")
    return 0


async def cmd_feeds():
    """获取首页 Feed"""
    actions = await get_xhs_actions()
    result = await actions.get_feeds()
    print(f"RESULT: {result}")
    return 0


async def cmd_detail(args):
    """获取笔记详情"""
    actions = await get_xhs_actions()
    result = await actions.get_feed_detail(args.feed_id, args.xsec_token)
    print(f"RESULT: {result}")
    return 0


async def cmd_like(args):
    """点赞/取消点赞"""
    actions = await get_xhs_actions()
    result = await actions.like_feed(args.feed_id, args.xsec_token, args.unlike)
    print(f"MESSAGE: {result}")
    return 0


async def cmd_favorite(args):
    """收藏/取消收藏"""
    actions = await get_xhs_actions()
    result = await actions.favorite_feed(args.feed_id, args.xsec_token, args.unfavorite)
    print(f"MESSAGE: {result}")
    return 0


async def cmd_comment(args):
    """发表评论"""
    actions = await get_xhs_actions()
    result = await actions.post_comment(args.feed_id, args.xsec_token, args.content)
    print(f"MESSAGE: {result}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="小红书 Skill 命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # check-login
    subparsers.add_parser("check-login", help="检查登录状态")

    # login
    login_parser = subparsers.add_parser("login", help="扫码登录")
    login_parser.add_argument("--timeout", type=int, default=300, help="超时时间（秒）")

    # publish
    publish_parser = subparsers.add_parser("publish", help="发布图文")
    publish_parser.add_argument("--title", required=True, help="标题")
    publish_parser.add_argument("--content", required=True, help="正文内容")
    publish_parser.add_argument("--images", nargs="+", required=True, help="图片路径")
    publish_parser.add_argument("--tags", nargs="+", help="话题标签")
    publish_parser.add_argument("--schedule-at", help="定时发布时间")
    publish_parser.add_argument("--is-original", action="store_true", help="声明原创")
    publish_parser.add_argument("--visibility", default="公开可见", help="可见范围")

    # publish-video
    video_parser = subparsers.add_parser("publish-video", help="发布视频")
    video_parser.add_argument("--title", required=True, help="标题")
    video_parser.add_argument("--content", required=True, help="正文内容")
    video_parser.add_argument("--video", required=True, help="视频文件路径")
    video_parser.add_argument("--tags", nargs="+", help="话题标签")
    video_parser.add_argument("--schedule-at", help="定时发布时间")
    video_parser.add_argument("--visibility", default="公开可见", help="可见范围")

    # search
    search_parser = subparsers.add_parser("search", help="搜索内容")
    search_parser.add_argument("--keyword", required=True, help="搜索关键词")

    # feeds
    subparsers.add_parser("feeds", help="获取首页 Feed")

    # detail
    detail_parser = subparsers.add_parser("detail", help="获取笔记详情")
    detail_parser.add_argument("--feed-id", required=True, help="笔记ID")
    detail_parser.add_argument("--xsec-token", required=True, help="访问令牌")

    # like
    like_parser = subparsers.add_parser("like", help="点赞")
    like_parser.add_argument("--feed-id", required=True, help="笔记ID")
    like_parser.add_argument("--xsec-token", required=True, help="访问令牌")
    like_parser.add_argument("--unlike", action="store_true", help="取消点赞")

    # favorite
    fav_parser = subparsers.add_parser("favorite", help="收藏")
    fav_parser.add_argument("--feed-id", required=True, help="笔记ID")
    fav_parser.add_argument("--xsec-token", required=True, help="访问令牌")
    fav_parser.add_argument("--unfavorite", action="store_true", help="取消收藏")

    # comment
    comment_parser = subparsers.add_parser("comment", help="发表评论")
    comment_parser.add_argument("--feed-id", required=True, help="笔记ID")
    comment_parser.add_argument("--xsec-token", required=True, help="访问令牌")
    comment_parser.add_argument("--content", required=True, help="评论内容")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 执行命令
    commands = {
        "check-login": lambda: cmd_check_login(),
        "login": lambda: cmd_login(args.timeout),
        "publish": lambda: cmd_publish(args),
        "publish-video": lambda: cmd_publish_video(args),
        "search": lambda: cmd_search(args),
        "feeds": lambda: cmd_feeds(),
        "detail": lambda: cmd_detail(args),
        "like": lambda: cmd_like(args),
        "favorite": lambda: cmd_favorite(args),
        "comment": lambda: cmd_comment(args),
    }

    return asyncio.run(commands[args.command]())


if __name__ == "__main__":
    sys.exit(main())