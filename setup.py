#!/usr/bin/env python3
"""
安装脚本 - 自动下载 Playwright 浏览器

运行方式：
    uv run python setup.py
    或
    uv run xhs-setup
"""
import subprocess
import sys


def install_chromium():
    """下载 Playwright Chromium 浏览器"""
    print("=" * 50)
    print("正在下载 Playwright Chromium 浏览器...")
    print("=" * 50)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("\n✅ Chromium 浏览器下载成功！")
            print(result.stdout)
            return True
        else:
            print(f"\n❌ 下载失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"\n❌ 下载出错: {e}")
        return False


def check_chromium():
    """检查 Chromium 是否已安装"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
        )
        # 如果 dry-run 返回成功，说明需要安装
        return result.returncode != 0 or "download" in result.stdout.lower()
    except:
        return True


def main():
    """主函数"""
    print("小红书 MCP 环境设置")
    print()

    # 检查并安装 Chromium
    if check_chromium():
        success = install_chromium()
        if not success:
            print("\n提示: 手动运行以下命令安装浏览器：")
            print("  uv run playwright install chromium")
            sys.exit(1)
    else:
        print("✅ Chromium 浏览器已安装")

    print("\n环境设置完成！可以运行以下命令启动服务：")
    print("  uv run python main.py")


if __name__ == "__main__":
    main()