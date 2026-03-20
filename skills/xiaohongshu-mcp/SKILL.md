---
name: xiaohongshu-service-custom
description: >
  小红书 MCP 客户端，支持笔记搜索、内容发布（图文/视频）、互动操作（点赞/评论/收藏）。
  Use when: 用户要发小红书、搜索小红书、查看笔记详情、点赞评论收藏。
  NOT for: 小红书数据分析、批量爬取、自动化营销工具。
metadata:
  openclaw:
    emoji: "📕"
    requires:
      bins: ["python3", "uv"]
      env: ["XHS_HEADLESS"]
---

# xiaohongshu-mcp

小红书 MCP 服务操作。

## When to Run

详细的触发条件和前置检查请参阅 [门控文档](references/gating.md)。

AI 需在收到用户请求后，首先阅读门控文档，判断是否满足所有条件，再决定是否执行工作流。

## 使用方式

### 无头模式（默认）
```bash
# 检查登录
python skills/xiaohongshu-service/scripts/run.py check-login

# 扫码登录（返回二维码图片）
XHS_HEADLESS=true python skills/xiaohongshu-service/scripts/run.py login

# 发布图文
XHS_HEADLESS=true python skills/xiaohongshu-service/scripts/run.py publish \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/image.jpg"
```

### 有头模式（显示浏览器窗口）
```bash
# 扫码登录（弹出浏览器窗口）
XHS_HEADLESS=false python skills/xiaohongshu-service/scripts/run.py login

# 发布图文（显示浏览器窗口）
XHS_HEADLESS=false python skills/xiaohongshu-service/scripts/run.py publish \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/image.jpg"
```

## Workflow

### 1. 检查服务状态
```bash
python skills/xiaohongshu-service/scripts/run.py check-login
```
- 成功返回登录状态 → 继续
- 服务无响应 → 提示用户检查 MCP 配置（参考 `references/deploy.md`）

### 2. 登录认证（如需要）
根据模式选择：

**无头模式**：
```bash
XHS_HEADLESS=true python skills/xiaohongshu-service/scripts/run.py login
```
- 返回二维码图片，引导用户扫码
- 扫码成功后自动保存登录状态

**有头模式**：
```bash
XHS_HEADLESS=false python skills/xiaohongshu-service/scripts/run.py login
```
- 弹出浏览器窗口，用户窗口内扫码
- 登录成功后自动保存登录状态

### 3. 执行用户请求的操作

#### 3.1 发布图文
```bash
python skills/xiaohongshu-service/scripts/run.py publish \
  --title "美食分享" \
  --content "今天做了一道好吃的菜，分享给大家" \
  --images "/Users/user/food1.jpg" "/Users/user/food2.jpg" \
  --tags "美食" "家常菜" "烹饪" \
  --visibility "公开可见"
```

**参数说明**：
- `--title`: 标题（最多20字，必需）
- `--content`: 正文内容（必需）
- `--images`: 图片路径列表，至少1张（必需）
- `--tags`: 话题标签列表（可选）
- `--visibility`: 可见范围（可选，默认"公开可见"）
- `--schedule-at`: 定时发布时间（可选）
- `--is-original`: 声明原创（可选）

#### 3.2 发布视频
```bash
python skills/xiaohongshu-service/scripts/run.py publish-video \
  --title "美食制作过程" \
  --content "详细展示制作步骤" \
  --video "/Users/user/cooking.mp4" \
  --tags "美食" "教程" "烹饪"
```

#### 3.3 搜索内容
```bash
python skills/xiaohongshu-service/scripts/run.py search --keyword "美食"
```

#### 3.4 获取首页 Feed
```bash
python skills/xiaohongshu-service/scripts/run.py feeds
```

#### 3.5 获取笔记详情
```bash
python skills/xiaohongshu-service/scripts/run.py detail \
  --feed-id "12345" \
  --xsec-token "abc123"
```

#### 3.6 互动操作
```bash
# 点赞
python skills/xiaohongshu-service/scripts/run.py like \
  --feed-id "12345" \
  --xsec-token "abc123"

# 收藏
python skills/xiaohongshu-service/scripts/run.py favorite \
  --feed-id "12345" \
  --xsec-token "abc123"

# 发表评论
python skills/xiaohongshu-service/scripts/run.py comment \
  --feed-id "12345" \
  --xsec-token "abc123" \
  --content "很棒的内容！"
```

## Output Format

### 登录相关
```
STATUS: LOGGED_IN
MESSAGE: 已登录

STATUS: QR_CODE_READY
MESSAGE: 请用小红书 App 扫码登录
QR_CODE: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

### 发布成功
✅ 发布成功
📝 标题：{title}
🔗 链接：{note_url}

### 搜索结果
🔍 搜索结果："{keyword}"
1. {标题} - {作者} ({点赞数}赞)
2. ...

### 互动操作
❤️ 已点赞：{笔记标题}
💬 已评论：{评论内容}

## Tools Required

| 工具 | 来源 | 用途 |
|------|------|------|
| xiaohongshu run.py | 本项目 | 小红书操作 |
| uv | astral.sh | Python 依赖管理 |
| Playwright | pip | 浏览器自动化 |

## Environment Variables

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `XHS_HEADLESS` | 无头模式 | `true` |
| `CHROME_PATH` | 自定义浏览器路径 | Playwright Chromium |
| `COOKIES_PATH` | Cookies 文件路径 | `cookies.json` |

## Available Tools

| 命令 | 说明 |
|------|------|
| `check-login` | 检查登录状态 |
| `login` | 获取登录二维码 |
| `publish` | 发布图文 |
| `publish-video` | 发布视频 |
| `search` | 搜索内容 |
| `feeds` | 首页推荐 |
| `detail` | 笔记详情 |
| `like` | 点赞/取消点赞 |
| `favorite` | 收藏/取消收藏 |
| `comment` | 发表评论 |

## Error Handling

### 常见错误及解决方案

1. **未登录错误**
   ```
   STATUS: NOT_LOGGED_IN
   MESSAGE: 未登录，请先登录
   ```
   解决：先执行 `login` 命令

2. **标题超长**
   ```
   STATUS: PUBLISH_FAILED
   MESSAGE: 标题长度超过限制
   ```
   解决：缩短标题至 20 字以内

3. **图片不存在**
   ```
   STATUS: PUBLISH_FAILED
   MESSAGE: 图片文件不存在
   ```
   解决：检查图片路径是否正确

## Content Limits

- 标题 ≤ 20 字（硬限制）
- 正文 ≤ 1000 字（硬限制）
- 每日发布 ≤ 50 篇
- 图文流量优于视频

## References

- **门控文档**: [references/gating.md](references/gating.md) — 触发条件、前置检查、工作流守护
- **部署指南**: [references/deploy.md](references/deploy.md) — 安装依赖、启动服务、配置 MCP 客户端
- **使用详解**: [references/usage.md](references/usage.md) — 工具详解、运营知识、错误排查
