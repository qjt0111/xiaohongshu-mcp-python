# 首次部署 xiaohongshu-mcp

> Based on [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)

## 环境要求

- macOS / Linux / Windows
- Python 3.11+
- 首次运行自动下载 Chromium (~150MB)

## 部署步骤

### 1. 安装依赖

```bash
cd /Users/jintao.qu/Downloads/xiaohongshu-mcp-python

# 安装依赖
uv sync

# 下载浏览器（首次安装需要）
uv run playwright install chromium
```

### 2. 启动 MCP 服务

```bash
# 无头模式（默认）
uv run python main.py

# 显示浏览器窗口
XHS_HEADLESS=false uv run python main.py
```

### 3. 配置 MCP 客户端

**Claude Code 配置** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "command": "/xxx/.venv/bin/python",
      "args": [
        "/xxx/xiaohongshu-mcp-python/main.py"
      ],
      "cwd": "/xxx/xiaohongshu-mcp-python",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "XHS_HEADLESS": "true",
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "COOKIES_PATH": "/xxx/xiaohongshu-mcp-python/cookies.json"
      },
      "type": "stdio"
    }
  }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `XHS_HEADLESS` | 无头模式 | `true` |
| `CHROME_PATH` | 自定义浏览器路径（可选） | Playwright Chromium |
| `COOKIES_PATH` | Cookies 文件路径 | `cookies.json` |

**注意**：修改环境变量后需要重启 MCP 服务。

## Docker 部署

适合云服务器部署，包含完整环境。

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
```