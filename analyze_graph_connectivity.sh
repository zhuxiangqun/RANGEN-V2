#!/bin/bash
# 知识图谱连通性分析脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "🚀 执行知识图谱连通性分析..."
echo "   脚本: scripts/analyze_graph_connectivity.py"
echo

python3 scripts/analyze_graph_connectivity.py

