#!/bin/bash
# 清除向量知识库脚本（Shell包装）
# 只清除知识条目、向量索引，不清除知识图谱

# 获取脚本实际路径（支持符号链接）
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 解析参数
BACKUP=true

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            BACKUP=false
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项："
            echo "  --no-backup         不创建备份（默认会备份）"
            echo "  -h, --help          显示此帮助信息"
            echo ""
            echo "示例："
            echo "  # 清除向量知识库（自动备份）"
            echo "  $0"
            echo ""
            echo "  # 清除向量知识库（不备份）"
            echo "  $0 --no-backup"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 切换到项目根目录
cd "$PROJECT_ROOT" || exit 1

# 🆕 修复 macOS OpenMP 冲突问题
# 当多个包（如 NumPy、SciPy、FAISS）使用不同的 OpenMP 实现时会出现此错误
export KMP_DUPLICATE_LIB_OK=TRUE

# 构建Python命令参数
PYTHON_ARGS=()

if [ "$BACKUP" = false ]; then
    PYTHON_ARGS+=("--no-backup")
fi

# 执行Python脚本
echo "🚀 执行向量知识库清理..."
echo "   脚本: knowledge_management_system/scripts/clear_vector_knowledge_base.py"
echo "   参数: ${PYTHON_ARGS[*]}"
echo ""

python3 knowledge_management_system/scripts/clear_vector_knowledge_base.py "${PYTHON_ARGS[@]}"

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 向量知识库清理完成！"
else
    echo ""
    echo "❌ 向量知识库清理失败（退出码: $exit_code）"
fi

exit $exit_code

