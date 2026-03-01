#!/bin/bash
# 系统重启脚本

set -e

echo "=========================================="
echo "系统重启脚本"
echo "=========================================="
echo ""

# 1. 查找并停止运行中的系统进程
echo "1. 查找运行中的系统进程..."
PROCESSES=$(ps aux | grep -E "unified_research_system|simple_langgraph|start_system" | grep -v grep | awk '{print $2}')

if [ -z "$PROCESSES" ]; then
    echo "   ℹ️  没有找到运行中的系统进程"
else
    echo "   找到进程: $PROCESSES"
    echo "   正在停止..."
    echo "$PROCESSES" | xargs kill -TERM 2>/dev/null || true
    sleep 2
    
    # 如果还在运行，强制终止
    REMAINING=$(ps aux | grep -E "unified_research_system|simple_langgraph|start_system" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "   强制终止剩余进程..."
        echo "$REMAINING" | xargs kill -9 2>/dev/null || true
    fi
    
    echo "   ✅ 进程已停止"
fi
echo ""

# 2. 等待进程完全退出
echo "2. 等待进程完全退出..."
sleep 2
echo "   ✅ 等待完成"
echo ""

# 3. 检查环境变量
echo "3. 检查环境变量..."
ENABLE_WORKFLOW=$(python3 -c "import os; print(os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true'))")
ENABLE_VIZ=$(python3 -c "import os; print(os.getenv('ENABLE_BROWSER_VISUALIZATION', 'true'))")

echo "   ENABLE_UNIFIED_WORKFLOW: $ENABLE_WORKFLOW"
echo "   ENABLE_BROWSER_VISUALIZATION: $ENABLE_VIZ"

if [ "$ENABLE_WORKFLOW" != "true" ]; then
    echo "   ⚠️  警告: ENABLE_UNIFIED_WORKFLOW 不是 'true'"
    echo "   💡 设置: export ENABLE_UNIFIED_WORKFLOW=true"
fi
echo ""

# 4. 运行诊断（可选）
read -p "是否在重启前运行诊断? (y/n, 默认n): " run_diagnosis
run_diagnosis=${run_diagnosis:-n}

if [ "$run_diagnosis" == "y" ] || [ "$run_diagnosis" == "Y" ]; then
    echo "4. 运行诊断..."
    python3 scripts/diagnose_workflow.py
    echo ""
fi

# 5. 提示如何启动
echo "=========================================="
echo "系统已停止"
echo "=========================================="
echo ""
echo "📝 启动系统的方法："
echo ""
echo "方法1：使用示例脚本"
echo "   python examples/simple_langgraph_example.py"
echo ""
echo "方法2：使用启动脚本（如果存在）"
echo "   python examples/start_system.py"
echo ""
echo "方法3：在你的代码中"
echo "   from src.unified_research_system import create_unified_research_system"
echo "   system = await create_unified_research_system()"
echo ""
echo "💡 提示："
echo "   - 确保环境变量已设置（ENABLE_UNIFIED_WORKFLOW=true）"
echo "   - 启动后运行验证: python3 scripts/test_workflow_initialization.py"
echo "   - 访问可视化界面: http://localhost:8080"
echo ""

