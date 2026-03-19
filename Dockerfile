# ---- build stage ----
FROM python:3.11-slim AS builder

WORKDIR /src

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml ./

# 安装依赖
RUN uv pip install --system -e .

# ---- run stage ----
FROM python:3.11-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 安装系统依赖（Playwright 需要的库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    wget \
    ca-certificates \
    # Playwright 浏览器依赖
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    fonts-liberation \
    # 清理
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目文件
COPY . .

# 安装 Playwright Chromium 浏览器
RUN python -m playwright install chromium

# 创建目录
RUN mkdir -p /app/images && chmod 777 /app/images

# 环境变量
ENV XHS_HEADLESS=true
ENV COOKIES_PATH=/app/cookies.json

EXPOSE 18060

# 启动 MCP 服务
CMD ["python", "main.py"]