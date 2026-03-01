#!/bin/bash
# 构建知识图谱脚本（Shell包装）
# 从已导入的知识条目（向量数据库）中提取实体和关系，构建知识图谱

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
BATCH_SIZE=100
EXTRACT_ENTITIES=true
EXTRACT_RELATIONS=true
RESUME=true
RETRY_FAILED=false
NO_RETRY_FAILED=false  # 🚀 新增：是否禁用自动重试失败的条目

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --no-entities)
            EXTRACT_ENTITIES=false
            shift
            ;;
        --no-relations)
            EXTRACT_RELATIONS=false
            shift
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --no-resume)
            RESUME=false
            shift
            ;;
        --retry-failed)
            RETRY_FAILED=true
            shift
            ;;
        --no-retry-failed)
            NO_RETRY_FAILED=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项："
            echo "  --batch-size SIZE        每批处理的条目数（默认: 100）"
            echo "  --no-entities            不提取实体"
            echo "  --no-relations           不提取关系"
            echo "  --resume                 启用断点续传（默认）"
            echo "  --no-resume              不启用断点续传（从头开始）"
            echo "  --retry-failed           只重新处理之前失败的条目（不处理未处理的条目）"
            echo "  --no-retry-failed        不自动重试失败的条目（默认会自动重试）"
            echo "  -h, --help              显示此帮助信息"
            echo ""
            echo "示例："
            echo "  # 从所有条目构建（自动断点续传）"
            echo "  $0"
            echo ""
            echo "  # 重新处理失败的条目"
            echo "  $0 --retry-failed"
            echo ""
            echo "  # 指定批次大小"
            echo "  $0 --batch-size 50"
            echo ""
            echo "  # 不提取实体，只提取关系"
            echo "  $0 --no-entities"
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

PYTHON_ARGS+=("--batch-size" "$BATCH_SIZE")

if [ "$EXTRACT_ENTITIES" = false ]; then
    PYTHON_ARGS+=("--no-entities")
fi

if [ "$EXTRACT_RELATIONS" = false ]; then
    PYTHON_ARGS+=("--no-relations")
fi

if [ "$RESUME" = true ]; then
    PYTHON_ARGS+=("--resume")
else
    PYTHON_ARGS+=("--no-resume")
fi

if [ "$RETRY_FAILED" = true ]; then
    PYTHON_ARGS+=("--retry-failed")
fi

if [ "$NO_RETRY_FAILED" = true ]; then
    PYTHON_ARGS+=("--no-retry-failed")
fi

# 执行Python脚本
echo "🚀 执行知识图谱构建..."
echo "   脚本: knowledge_management_system/scripts/build_knowledge_graph.py"
echo "   参数: ${PYTHON_ARGS[*]}"
echo ""

python3 knowledge_management_system/scripts/build_knowledge_graph.py "${PYTHON_ARGS[@]}"

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 知识图谱构建完成！"
else
    echo ""
    echo "❌ 知识图谱构建失败（退出码: $exit_code）"
fi

exit $exit_code

