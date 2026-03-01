#!/bin/bash
# 修复 LangGraph 工作流初始化问题

set -e

echo "=========================================="
echo "LangGraph 工作流初始化修复脚本"
echo "=========================================="
echo ""

# 1. 检查 LangGraph 安装
echo "1. 检查 LangGraph 安装..."
if python3 -c "import langgraph" 2>/dev/null; then
    # 尝试多种方式获取版本号（优先使用 importlib.metadata）
    LANGGRAPH_VERSION=$(python3 -c "
try:
    import langgraph
    if hasattr(langgraph, '__version__'):
        print(langgraph.__version__)
    elif hasattr(langgraph, 'version'):
        print(langgraph.version)
    else:
        try:
            from importlib.metadata import version as get_package_version
            print(get_package_version('langgraph'))
        except ImportError:
            try:
                from importlib_metadata import version as get_package_version
                print(get_package_version('langgraph'))
            except ImportError:
                try:
                    import pkg_resources
                    print(pkg_resources.get_distribution('langgraph').version)
                except:
                    print('installed')
except:
    print('unknown')
" 2>/dev/null || echo "installed")
    echo "   ✅ LangGraph 已安装: $LANGGRAPH_VERSION"
else
    echo "   ❌ LangGraph 未安装"
    echo "   📦 正在安装 LangGraph..."
    pip install langgraph
    echo "   ✅ LangGraph 安装完成"
fi
echo ""

# 2. 检查环境变量
echo "2. 检查环境变量..."
ENABLE_WORKFLOW=$(python3 -c "import os; print(os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true'))")
USE_LANGGRAPH=$(python3 -c "import os; print(os.getenv('USE_LANGGRAPH', 'false'))")

echo "   ENABLE_UNIFIED_WORKFLOW: $ENABLE_WORKFLOW"
echo "   USE_LANGGRAPH: $USE_LANGGRAPH"

if [ "$ENABLE_WORKFLOW" != "true" ]; then
    echo "   ⚠️  ENABLE_UNIFIED_WORKFLOW 不是 'true'"
    echo "   💡 建议设置: export ENABLE_UNIFIED_WORKFLOW=true"
fi
echo ""

# 3. 运行诊断
echo "3. 运行诊断..."
python3 scripts/diagnose_workflow.py

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请："
echo "1. 检查 .env 文件中的配置"
echo "2. 查看系统初始化日志"
echo "3. 运行: python3 scripts/diagnose_workflow.py"
echo ""

