#!/bin/bash

# 重启知识图谱构建进程的脚本
# 用法：
#   ./restart_build_knowledge_graph.sh        # 前台运行（可以看到日志）
#   ./restart_build_knowledge_graph.sh -b     # 后台运行（不显示日志）
#   ./restart_build_knowledge_graph.sh --background  # 后台运行（不显示日志）

echo "🛑 步骤1: 停止当前进程..."

# 查找进程（排除当前脚本和grep本身）
PIDS=$(ps aux | grep -E "build_knowledge_graph\.py|python.*build_knowledge_graph" | grep -v grep | grep -v "restart_build_knowledge_graph" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ 没有找到运行中的进程"
else
    echo "找到以下进程:"
    ps aux | grep -E "build_knowledge_graph\.py|python.*build_knowledge_graph" | grep -v grep | grep -v "restart_build_knowledge_graph"
    
    echo ""
    echo "正在停止进程..."
    for PID in $PIDS; do
        echo "  停止进程 $PID..."
        kill $PID 2>/dev/null
    done
    
    # 等待进程停止
    sleep 2
    
    # 检查是否还有进程
    REMAINING=$(ps aux | grep -E "build_knowledge_graph\.py|python.*build_knowledge_graph" | grep -v grep | grep -v "restart_build_knowledge_graph" | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "⚠️  进程仍在运行，强制停止..."
        for PID in $REMAINING; do
            kill -9 $PID 2>/dev/null
        done
        sleep 1
    fi
    
    echo "✅ 进程已停止"
fi

echo ""
echo "🔍 步骤2: 确认代码已更新..."

# 检查代码是否包含修复（检查stream=False和timeout_tuple）
if grep -q "stream=False" src/core/llm_integration.py && grep -q "timeout_tuple" src/core/llm_integration.py; then
    echo "✅ 代码已包含修复（使用stream=False和timeout_tuple）"
    echo "   检查结果:"
    grep -n "stream=False" src/core/llm_integration.py | head -2
    grep -n "timeout_tuple" src/core/llm_integration.py | head -2
else
    echo "⚠️  警告：代码可能未包含最新修复"
    echo "   请确认 src/core/llm_integration.py 中包含 stream=False 和 timeout_tuple"
    read -p "是否继续重启？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 步骤3: 重新启动进程..."

# 检查脚本是否存在
if [ ! -f "./build_knowledge_graph.sh" ]; then
    echo "❌ 找不到 build_knowledge_graph.sh 脚本"
    exit 1
fi

# 启动进程
echo "正在启动知识图谱构建进程..."
echo ""

# 检查是否有 --background 或 -b 参数
BACKGROUND=false
if [[ "$1" == "--background" ]] || [[ "$1" == "-b" ]]; then
    BACKGROUND=true
fi

if [ "$BACKGROUND" = true ]; then
    # 后台运行，并将输出重定向到日志文件
    echo "   注意：进程将在后台运行，可以使用以下命令查看日志："
    echo "   tail -f logs/knowledge_management.log"
    echo ""
    
    nohup ./build_knowledge_graph.sh > /dev/null 2>&1 &
    
    # 获取新启动的进程PID
    NEW_PID=$!
    sleep 2
    
    # 检查进程是否成功启动
    if ps -p $NEW_PID > /dev/null 2>&1; then
        echo "✅ 进程已重启（PID: $NEW_PID）"
    else
        echo "⚠️  进程可能启动失败，请检查日志："
        echo "   tail -100 logs/knowledge_management.log"
    fi
    
    echo ""
    echo "📝 查看日志命令:"
    echo "   tail -f logs/knowledge_management.log | grep -E '超时|timeout|LLM|属性'"
else
    # 前台运行，可以看到实时日志
    echo "   进程将在前台运行，日志会实时显示在终端"
    echo "   按 Ctrl+C 可以停止进程"
    echo ""
    
    # 直接运行，不后台化
    ./build_knowledge_graph.sh
fi

echo ""
echo "📊 验证方法:"
echo "   观察日志，应该看到："
echo "   - 🔧 使用超时设置: connect=5.0s, read=240.0s"
echo "   - 🔧 发送请求: url=..., timeout=(5.0, 240.0), timeout_type=<class 'tuple'>"
echo "   - 不再出现 read timeout=5.0 的错误"
echo "   - 如果出现超时，应该是接近240秒的超时，而不是5秒"

