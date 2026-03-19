# 小红书 MCP 服务器

基于 fastmcp + Playwright 的小红书 MCP 服务器实现。

## 功能

- 登录管理（二维码登录、状态检查）
- 发布图文/视频内容
- 搜索和浏览 Feed
- 点赞、收藏、评论

## 安装

```bash
cd /Users/jintao.qu/Downloads/xiaohongshu-mcp-python

# 安装依赖
uv sync

# 下载浏览器（首次安装需要）
uv run python setup.py
# 或
uv run xhs-setup
```

## 使用方式

### 方式一：MCP Server（Claude Code 等 AI 工具）

```bash
# 无头模式
uv run python main.py

# 显示浏览器窗口
XHS_HEADLESS=false uv run python main.py
```

**Claude Code 配置** (`~/.claude/claude_desktop_config.json`)：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "command": "/Users/jintao.qu/Downloads/xiaohongshu-mcp-python/.venv/bin/python",
      "args": [
        "/Users/jintao.qu/Downloads/xiaohongshu-mcp-python/main.py"
      ],
      "cwd": "/Users/jintao.qu/Downloads/xiaohongshu-mcp-python",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "XHS_HEADLESS": "true",
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "COOKIES_PATH": "/Users/jintao.qu/Downloads/xiaohongshu-mcp-python/cookies.json"
      },
      "type": "stdio"
    }
  }
}
```

### 方式二：Open Claw Skill

项目包含 Open Claw 兼容的 Skill，结构如下：

```
skills/xiaohongshu/
├── SKILL.md           # Skill 定义（YAML frontmatter + 工作流）
├── config/
│   └── accounts.json  # 账号配置
├── scripts/
│   └── run.py         # 命令行入口
└── references/
    └── publish-workflow.md
```

**命令行使用：**

```bash
# 检查登录
python skills/xiaohongshu/scripts/run.py check-login

# 扫码登录
python skills/xiaohongshu/scripts/run.py login

# 发布图文
python skills/xiaohongshu/scripts/run.py publish \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/image.jpg"

# 搜索
python skills/xiaohongshu/scripts/run.py search --keyword "美食"

# 获取首页 Feed
python skills/xiaohongshu/scripts/run.py feeds
```

**部署到 Open Claw：**

将整个项目上传到 Open Claw 平台，Skill 会自动识别 `skills/xiaohongshu/SKILL.md`。

### 方式三：Docker 部署

适合云服务器部署，包含完整环境（Python + Playwright Chromium）。

```bash
# 构建镜像
docker build -t xiaohongshu-mcp .

# 运行容器
docker run -d \
  --name xhs-mcp \
  -p 18060:18060 \
  -v $(pwd)/cookies.json:/app/cookies.json \
  -e XHS_HEADLESS=true \
  xiaohongshu-mcp

# 查看日志
docker logs -f xhs-mcp
```

**Docker 环境说明：**

- 基础镜像：`python:3.11-slim`
- 自动安装 Playwright Chromium 浏览器
- 默认无头模式运行
- Cookies 持久化到 `/app/cookies.json`

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `XHS_HEADLESS` | 无头模式 | `true` |
| `CHROME_PATH` | 自定义浏览器路径（可选） | 不配置则使用 Playwright 自带 Chromium |
| `COOKIES_PATH` | Cookies 文件路径 | `cookies.json` |

## MCP 工具列表

| 工具 | 说明 |
|------|------|
| `check_login_status` | 检查登录状态 |
| `get_login_qrcode` | 获取登录二维码（无头模式返回图片，有头模式弹窗口） |
| `delete_cookies` | 删除 cookies 重置登录 |
| `publish_content` | 发布图文（无头模式后台发布，有头模式显示窗口） |
| `publish_video` | 发布视频内容 |
| `search_feeds` | 搜索内容 |
| `list_feeds` | 获取首页 Feed 列表 |
| `get_feed_detail` | 获取笔记详情 |
| `user_profile` | 获取用户主页 |
| `like_feed` | 点赞/取消点赞 |
| `favorite_feed` | 收藏/取消收藏 |
| `post_comment` | 发表评论 |

**注意**：修改环境变量配置后需要重启 MCP 服务才能生效。