#!/bin/bash
# 构建向量知识库脚本（Shell包装）
# 从数据源导入知识并构建向量索引，不构建知识图谱

# 获取脚本实际路径（支持符号链接）
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 默认数据集路径
DEFAULT_DATASET_PATH="data/frames_dataset.json"

# 解析参数
DATASET_PATH=""
INPUT_FILE=""
FILE_PATH=""
URL_PATH=""
USE_LLAMAINDEX=false
CHUNK_STRATEGY="sentence"
BATCH_SIZE=10
INCLUDE_FULL_TEXT=true
RESUME=true
SKIP_DUPLICATES=true
RETRY_FAILED=false
FORCE_DOWNLOAD=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dataset-path)
            DATASET_PATH="$2"
            shift 2
            ;;
        --input-file)
            INPUT_FILE="$2"
            shift 2
            ;;
        --file)
            FILE_PATH="$2"
            shift 2
            ;;
        --url)
            URL_PATH="$2"
            shift 2
            ;;
        --use-llamaindex)
            USE_LLAMAINDEX=true
            shift
            ;;
        --chunk-strategy)
            CHUNK_STRATEGY="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --no-full-text)
            INCLUDE_FULL_TEXT=false
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
        --no-skip-duplicates)
            SKIP_DUPLICATES=false
            shift
            ;;
        --force-download)
            FORCE_DOWNLOAD=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项："
            echo "  --dataset-path PATH      FRAMES数据集路径（JSON格式）"
            echo "  --input-file PATH        输入数据文件路径（JSON格式）"
            echo "  --file PATH              🆕 文件路径或URL（支持PDF、Markdown、网页、URL等，需要--use-llamaindex）"
            echo "  --url URL                🆕 网页URL（等同于 --file <URL> --use-llamaindex 的快捷方式）"
            echo "  --use-llamaindex         🆕 使用LlamaIndex处理文件"
            echo "  --chunk-strategy STR     🆕 文档分块策略（sentence|semantic|simple，默认: sentence）"
            echo "  --batch-size SIZE        批次大小（默认: 10）"
            echo "  --no-full-text           不包含完整文本（仅摘要）"
            echo "  --resume                 启用断点续传（默认）"
            echo "  --no-resume              不启用断点续传"
            echo "  --retry-failed           重新处理失败的数据"
            echo "  --no-skip-duplicates     不跳过重复条目"
            echo "  --force-download         强制从 Hugging Face 重新下载数据集"
            echo "  -h, --help              显示此帮助信息"
            echo ""
            echo "示例："
            echo "  # 从FRAMES数据集构建（使用默认路径）"
            echo "  $0"
            echo ""
            echo "  # 从FRAMES数据集构建（指定路径）"
            echo "  $0 --dataset-path data/frames_dataset.json"
            echo ""
            echo "  # 重新处理失败的数据"
            echo "  $0 --dataset-path data/frames_dataset.json --retry-failed"
            echo ""
            echo "  # 从JSON文件构建"
            echo "  $0 --input-file /path/to/data.json --batch-size 50"
            echo ""
            echo "  # 🆕 从PDF文件构建（使用LlamaIndex）"
            echo "  $0 --file /path/to/document.pdf --use-llamaindex"
            echo ""
            echo "  # 🆕 从Markdown文件构建（使用LlamaIndex）"
            echo "  $0 --file /path/to/document.md --use-llamaindex --chunk-strategy semantic"
            echo ""
            echo "  # 🆕 从网页URL构建（使用LlamaIndex）"
            echo "  $0 --url https://example.com/article"
            echo ""
            echo "  # 🆕 从URL构建（使用--file参数）"
            echo "  $0 --file https://example.com/article --use-llamaindex"
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

# 🆕 修复 Keras 3.0 与 Transformers 兼容性问题
export KERAS_BACKEND=tensorflow
export TF_KERAS=1
# 禁用 Keras 版本检查警告
export TF_CPP_MIN_LOG_LEVEL=2
# 设置 Transformers 使用兼容模式
export TRANSFORMERS_NO_KERAS=0

# 构建Python命令参数
PYTHON_ARGS=()

if [ -n "$DATASET_PATH" ]; then
    PYTHON_ARGS+=("--dataset-path" "$DATASET_PATH")
elif [ -n "$INPUT_FILE" ]; then
    PYTHON_ARGS+=("--input-file" "$INPUT_FILE")
elif [ -n "$URL_PATH" ]; then
    # 🆕 URL快捷方式（自动启用LlamaIndex）
    PYTHON_ARGS+=("--url" "$URL_PATH")
    if [ -n "$CHUNK_STRATEGY" ]; then
        PYTHON_ARGS+=("--chunk-strategy" "$CHUNK_STRATEGY")
    fi
elif [ -n "$FILE_PATH" ]; then
    PYTHON_ARGS+=("--file" "$FILE_PATH")
    if [ "$USE_LLAMAINDEX" = true ]; then
        PYTHON_ARGS+=("--use-llamaindex")
    fi
    if [ -n "$CHUNK_STRATEGY" ]; then
        PYTHON_ARGS+=("--chunk-strategy" "$CHUNK_STRATEGY")
    fi
elif [ -f "$DEFAULT_DATASET_PATH" ]; then
    # 使用默认数据集路径
    PYTHON_ARGS+=("--dataset-path" "$DEFAULT_DATASET_PATH")
    echo "ℹ️  使用默认数据集路径: $DEFAULT_DATASET_PATH"
else
    echo "❌ 错误：未指定数据集路径，且默认路径不存在"
    echo "   请使用 --dataset-path 指定数据集路径，或使用 --input-file 指定输入文件，"
    echo "   或使用 --file 指定文件（需要--use-llamaindex），或使用 --url 指定URL"
    exit 1
fi

PYTHON_ARGS+=("--batch-size" "$BATCH_SIZE")

if [ "$INCLUDE_FULL_TEXT" = false ]; then
    PYTHON_ARGS+=("--no-full-text")
fi

if [ "$RESUME" = true ]; then
    PYTHON_ARGS+=("--resume")
else
    PYTHON_ARGS+=("--no-resume")
fi

if [ "$RETRY_FAILED" = true ]; then
    PYTHON_ARGS+=("--retry-failed")
fi

if [ "$SKIP_DUPLICATES" = false ]; then
    PYTHON_ARGS+=("--no-skip-duplicates")
fi

if [ "$FORCE_DOWNLOAD" = true ]; then
    PYTHON_ARGS+=("--force-download")
fi

# 执行Python脚本
echo "🚀 执行向量知识库构建..."
echo "   脚本: knowledge_management_system/scripts/build_vector_knowledge_base.py"
echo "   参数: ${PYTHON_ARGS[*]}"
echo ""

# 🆕 应用Keras兼容性补丁并执行脚本
python3 -c "
import sys
sys.path.insert(0, '.')
import keras_compat_patch
# 现在导入并运行主脚本
import knowledge_management_system.scripts.build_vector_knowledge_base
" "${PYTHON_ARGS[@]}"

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 向量知识库构建完成！"
else
    echo ""
    echo "❌ 向量知识库构建失败（退出码: $exit_code）"
fi

exit $exit_code

