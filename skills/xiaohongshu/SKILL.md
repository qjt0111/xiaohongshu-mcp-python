---
name: xiaohongshu
description: >
  小红书自动化操作技能。支持登录管理、内容发布（图文/视频）、搜索浏览、互动操作（点赞/收藏/评论）。
  基于 Playwright 实现浏览器自动化，支持无头模式运行。
---

# 小红书自动化操作

通过 MCP 工具实现小红书平台的自动化操作。

## 功能列表

| 功能 | 工具名称 | 说明 |
|------|----------|------|
| 登录检查 | check_login_status | 检查当前登录状态 |
| 获取二维码 | get_login_qrcode | 获取登录二维码（无头模式返回图片，有头模式弹窗口） |
| 发布图文 | publish_content | 发布图文（无头模式后台发布，有头模式显示窗口） |
| 发布视频 | publish_video | 发布视频内容 |
| 搜索内容 | search_feeds | 搜索小红书笔记 |
| 获取首页 | list_feeds | 获取首页 Feed 列表 |
| 笔记详情 | get_feed_detail | 获取笔记详情和评论 |
| 用户主页 | user_profile | 获取用户主页信息 |
| 点赞 | like_feed | 点赞/取消点赞笔记 |
| 收藏 | favorite_feed | 收藏/取消收藏笔记 |
| 评论 | post_comment | 发表评论 |

## 前置条件

1. 确保已安装依赖：
   - 本地运行：`uv sync && uv run playwright install chromium`
   - Docker 部署：`docker build -t xiaohongshu-mcp .`
2. 确保已登录小红书账号

## Step 1: 检查登录状态

首先检查登录状态：

```
调用 check_login_status 工具
```

- 如果返回"已登录"，继续后续操作
- 如果返回"未登录"，进入 Step 2

## Step 2: 扫码登录

```
调用 get_login_qrcode 工具
```

行为由 `XHS_HEADLESS` 配置控制：

- **无头模式**（默认）：返回二维码图片，用户用小红书 App 扫码
- **有头模式**：弹出浏览器窗口，在窗口中扫码登录

登录成功后 cookies 会自动保存，后续操作无需重复登录。

**注意**：修改配置后需要重启 MCP 服务才能生效。

## Step 3: 根据需求选择操作

### 3.1 发布图文

```
调用 publish_content 工具，参数：
- title: 标题（最多20字）
- content: 正文内容
- images: 图片路径列表（至少1张，支持本地路径或HTTP URL）
- tags: 话题标签列表（可选）
- visibility: 可见范围（可选，默认"公开可见"）
```

### 3.2 发布视频

```
调用 publish_video 工具，参数：
- title: 标题（最多20字）
- content: 正文内容
- video: 本地视频文件路径
- tags: 话题标签列表（可选）
- visibility: 可见范围（可选）
```

### 3.3 搜索内容

```
调用 search_feeds 工具，参数：
- keyword: 搜索关键词
```

返回搜索结果列表，包含笔记ID、标题、封面、互动数据等。

### 3.4 获取笔记详情

```
调用 get_feed_detail 工具，参数：
- feed_id: 笔记ID（从搜索结果获取）
- xsec_token: 访问令牌（从搜索结果获取）
```

### 3.5 互动操作

```
# 点赞
调用 like_feed 工具

# 收藏
调用 favorite_feed 工具

# 评论
调用 post_comment 工具
```

## 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| XHS_HEADLESS | 无头模式 | true |
| CHROME_PATH | 自定义浏览器路径（可选） | 不配置则使用 Playwright 自带 Chromium |
| COOKIES_PATH | Cookies 文件路径 | cookies.json |

## 注意事项

- 发布内容前必须先登录
- 图文发布至少需要1张图片
- 标题长度限制20字
- 图片支持本地路径和 HTTP URL
- 无头模式默认开启，适合服务器部署