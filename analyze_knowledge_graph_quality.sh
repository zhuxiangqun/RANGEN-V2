#!/bin/bash
# 分析知识图谱内容质量脚本（Shell包装）

# 获取脚本实际路径（支持符号链接）
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT" || exit 1

# 执行Python脚本
echo "🚀 执行知识图谱内容质量分析..."
echo "   脚本: scripts/analyze_knowledge_graph_quality.py"
echo ""

python3 scripts/analyze_knowledge_graph_quality.py

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 知识图谱内容质量分析完成！"
else
    echo ""
    echo "❌ 知识图谱内容质量分析失败（退出码: $exit_code）"
fi

exit $exit_code

