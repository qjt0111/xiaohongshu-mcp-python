---
name: xiaohongshu-mcp
description: Operate Xiaohongshu (小红书/RED) via local MCP service. Use when user wants to search notes, publish content (image/video), interact with posts (like/comment/favorite), or check account status on Xiaohongshu. Requires MCP service running via stdio.
---

# xiaohongshu-mcp

小红书 MCP 服务操作。

## 快速开始

1. **检查登录状态**
   ```
   调用 check_login_status 工具
   ```

2. **登录小红书**
   ```
   调用 get_login_qrcode 工具
   ```
   - 无头模式（默认）：返回二维码图片，用户扫码
   - 有头模式：弹出浏览器窗口，在窗口中扫码

## 可用工具

| 工具 | 说明 |
|------|------|
| `check_login_status` | 检查登录状态 |
| `get_login_qrcode` | 获取登录二维码 |
| `delete_cookies` | 重置登录状态 |
| `publish_content` | 发布图文 |
| `publish_video` | 发布视频 |
| `search_feeds` | 搜索内容 |
| `list_feeds` | 首页推荐 |
| `get_feed_detail` | 笔记详情 |
| `user_profile` | 用户主页 |
| `like_feed` | 点赞/取消点赞 |
| `favorite_feed` | 收藏/取消收藏 |
| `post_comment` | 发表评论 |

## 内容限制

- 标题 ≤20 字
- 正文 ≤1000 字
- 每日 ≤50 篇
- 图文流量优于视频

## References

- **首次部署**: [references/deploy.md](references/deploy.md) — 安装依赖、启动服务、配置 MCP 客户端
- **使用指南**: [references/usage.md](references/usage.md) — 工具详解、运营知识、错误排查

## Credits

Based on [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) by [@xpzouying](https://github.com/xpzouying)

Project: [qjt0111/xiaohongshu-mcp-python](https://github.com/qjt0111/xiaohongshu-mcp-python)