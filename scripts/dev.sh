#!/bin/bash

# Home Cloud Server 开发脚本
# 使用 uv 进行依赖管理和开发

set -e

echo "🚀 Home Cloud Server 开发环境"

case "$1" in
    "install")
        echo "📦 安装依赖..."
        uv sync
        echo "✅ 依赖安装完成"
        ;;
    "install-prod")
        echo "📦 安装生产依赖..."
        uv sync --no-dev
        echo "✅ 生产依赖安装完成"
        ;;
    "run")
        echo "🏃 启动应用..."
        uv run python main.py
        ;;
    "run-dev")
        echo "🏃 启动开发服务器..."
        FLASK_ENV=development uv run python main.py
        ;;
    "test")
        echo "🧪 运行测试..."
        uv run pytest
        ;;
    "format")
        echo "🎨 格式化代码..."
        uv run black .
        uv run isort .
        echo "✅ 代码格式化完成"
        ;;
    "lint")
        echo "🔍 代码检查..."
        uv run flake8 .
        echo "✅ 代码检查完成"
        ;;
    "type-check")
        echo "🔍 类型检查..."
        uv run mypy .
        echo "✅ 类型检查完成"
        ;;
    "check")
        echo "🔍 运行所有检查..."
        uv run black .
        uv run isort .
        uv run flake8 .
        uv run mypy .
        uv run pytest
        echo "✅ 所有检查完成"
        ;;
    "clean")
        echo "🧹 清理缓存..."
        rm -rf .pytest_cache
        rm -rf .mypy_cache
        rm -rf htmlcov
        rm -rf .coverage
        find . -type d -name __pycache__ -delete
        find . -type f -name "*.pyc" -delete
        echo "✅ 清理完成"
        ;;
    "add")
        if [ -z "$2" ]; then
            echo "❌ 请指定要添加的包名"
            echo "用法: ./scripts/dev.sh add <package_name>"
            exit 1
        fi
        echo "📦 添加依赖: $2"
        uv add "$2"
        ;;
    "add-dev")
        if [ -z "$2" ]; then
            echo "❌ 请指定要添加的开发包名"
            echo "用法: ./scripts/dev.sh add-dev <package_name>"
            exit 1
        fi
        echo "📦 添加开发依赖: $2"
        uv add --dev "$2"
        ;;
    *)
        echo "📖 可用命令:"
        echo "  install      - 安装所有依赖"
        echo "  install-prod - 安装生产依赖"
        echo "  run          - 运行应用"
        echo "  run-dev      - 运行开发服务器"
        echo "  test         - 运行测试"
        echo "  format       - 格式化代码"
        echo "  lint         - 代码检查"
        echo "  type-check   - 类型检查"
        echo "  check        - 运行所有检查"
        echo "  clean        - 清理缓存"
        echo "  add <pkg>    - 添加依赖"
        echo "  add-dev <pkg> - 添加开发依赖"
        ;;
esac 