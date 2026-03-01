#!/bin/bash
# 安装 pytest 及其依赖

echo "🔧 正在安装 pytest 及其依赖..."

# 检查 Python 版本
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到 Python 命令"
    exit 1
fi

echo "✅ 使用 Python: $($PYTHON_CMD --version)"

# 安装 pytest
echo "📦 安装 pytest..."
$PYTHON_CMD -m pip install pytest

# 安装 pytest-asyncio（用于异步测试）
echo "📦 安装 pytest-asyncio..."
$PYTHON_CMD -m pip install pytest-asyncio

# 安装 psutil（用于性能测试）
echo "📦 安装 psutil..."
$PYTHON_CMD -m pip install psutil

# 验证安装
echo ""
echo "🔍 验证安装..."
$PYTHON_CMD -m pytest --version

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ pytest 安装成功！"
    echo ""
    echo "📝 使用说明:"
    echo "  运行集成测试: pytest tests/test_langgraph_integration.py -v"
    echo "  运行性能测试: pytest tests/test_langgraph_performance_benchmark.py -v"
    echo "  运行编排追踪测试: pytest tests/test_orchestration_tracking.py -v"
else
    echo "❌ pytest 安装失败，请检查错误信息"
    exit 1
fi

