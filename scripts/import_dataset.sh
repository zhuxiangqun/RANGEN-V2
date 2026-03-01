#!/bin/bash
# 数据集导入脚本
# 用法: ./import_dataset.sh <数据集地址>
# 示例: ./import_dataset.sh https://huggingface.co/datasets/google/frames-benchmark
# 示例: ./import_dataset.sh /path/to/local/dataset.json

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ✅ 修改：解析参数，支持 --no-resume 选项
NO_RESUME=false
DATASET_SOURCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-resume)
            NO_RESUME=true
            shift
            ;;
        *)
            if [ -z "$DATASET_SOURCE" ]; then
                DATASET_SOURCE="$1"
            else
                echo -e "${YELLOW}警告: 忽略未知参数: $1${NC}"
            fi
            shift
            ;;
    esac
done

# 检查是否提供了数据集地址
if [ -z "$DATASET_SOURCE" ]; then
    echo -e "${RED}错误: 请提供数据集地址${NC}"
    echo "用法: $0 [--no-resume] <数据集地址>"
    echo ""
    echo "示例:"
    echo "  $0 https://huggingface.co/datasets/google/frames-benchmark"
    echo "  $0 --no-resume https://huggingface.co/datasets/google/frames-benchmark"
    echo "  $0 /path/to/local/dataset.json"
    echo "  $0 --no-resume /path/to/local/dataset.json"
    exit 1
fi

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}警告: 未检测到虚拟环境，建议激活 .venv${NC}"
    if [ -d ".venv" ]; then
        echo -e "${YELLOW}提示: 可以运行 'source .venv/bin/activate' 激活虚拟环境${NC}"
    fi
fi

# 🚀 改进：检查JINA_API_KEY（支持从.env文件读取）
# 首先尝试从 .env 文件加载（如果存在）
if [ -f ".env" ]; then
    # 从 .env 文件中提取 JINA_API_KEY（简单的行解析）
    if grep -q "^JINA_API_KEY=" .env 2>/dev/null; then
        export $(grep "^JINA_API_KEY=" .env | xargs)
        echo -e "${GREEN}✅ 已从 .env 文件加载 JINA_API_KEY${NC}"
    fi
fi

# 检查是否已设置 JINA_API_KEY
if [ -z "$JINA_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  警告: JINA_API_KEY 未设置${NC}"
    echo ""
    echo "文本向量化需要 JINA_API_KEY 才能正常工作。"
    echo "如果没有设置API密钥，导入的数据将无法生成向量，无法进行向量搜索。"
    echo ""
    echo "💡 设置方法（推荐）:"
    echo "   1. 在项目根目录创建 .env 文件，添加："
    echo "      JINA_API_KEY=your-api-key-here"
    echo ""
    echo "   2. 或使用环境变量："
    echo "      export JINA_API_KEY='your-api-key-here'"
    echo ""
    echo "   获取API密钥: https://jina.ai/"
    echo ""
    read -p "是否继续导入（数据将无法向量化）? [y/N]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 已取消导入${NC}"
        exit 1
    fi
    echo ""
fi

echo -e "${GREEN}开始导入数据集...${NC}"
echo "数据集地址: $DATASET_SOURCE"
if [ -n "$JINA_API_KEY" ]; then
    echo "✅ JINA_API_KEY: 已设置"
else
    echo -e "${YELLOW}⚠️  JINA_API_KEY: 未设置（数据将无法向量化）${NC}"
fi
echo ""

# 🚀 检测是否为FRAMES数据集
# 如果是FRAMES数据集，使用新的导入脚本（支持断点续传和Wikipedia内容合并）
if [[ "$DATASET_SOURCE" == *"frames-benchmark"* ]] || [[ "$DATASET_SOURCE" == *"frames"* ]]; then
    echo -e "${GREEN}检测到FRAMES数据集，使用Wikipedia导入模式${NC}"
    echo -e "${YELLOW}提示: 该模式会将每个FRAMES数据项的所有Wikipedia链接内容合并为一个条目${NC}"
    echo ""
    
    # 检查是否有已下载的本地文件
    if [ -f "$PROJECT_ROOT/data/frames_dataset.json" ]; then
        DATASET_FILE="$PROJECT_ROOT/data/frames_dataset.json"
        echo -e "${GREEN}发现本地FRAMES数据集文件: $DATASET_FILE${NC}"
    else
        # 如果没有本地文件，提示用户需要先下载
        echo -e "${YELLOW}未发现本地FRAMES数据集文件，需要先下载${NC}"
        echo -e "${YELLOW}正在下载数据集...${NC}"
        
        # 运行原始的import_dataset.py来下载数据集
        python3 "$PROJECT_ROOT/knowledge_management_system/scripts/import_dataset.py" "$DATASET_SOURCE" --no-fetch-wikipedia
        
        if [ -f "$PROJECT_ROOT/data/frames_dataset.json" ]; then
            DATASET_FILE="$PROJECT_ROOT/data/frames_dataset.json"
            echo -e "${GREEN}数据集下载完成: $DATASET_FILE${NC}"
        else
            echo -e "${RED}错误: 数据集下载失败或文件路径不正确${NC}"
            exit 1
        fi
    fi
    
    # 运行新的Wikipedia导入脚本（支持断点续传）
    echo ""
    if [ "$NO_RESUME" == "true" ] || [ "$IMPORT_NO_RESUME" == "true" ]; then
        echo -e "${GREEN}开始导入Wikipedia内容（从头开始，抓取完整内容）...${NC}"
        RESUME_FLAG="--no-resume"
    else
        echo -e "${GREEN}开始导入Wikipedia内容（支持断点续传，抓取完整内容）...${NC}"
        RESUME_FLAG=""
    fi
    echo -e "${YELLOW}提示: 默认会抓取完整的Wikipedia内容（包含排名列表等精确数据）${NC}"
    echo ""
    python3 "$PROJECT_ROOT/knowledge_management_system/scripts/import_wikipedia_from_frames.py" "$DATASET_FILE" --batch-size 5 $RESUME_FLAG
    
else
    # 其他数据集使用原始导入脚本
    echo -e "${GREEN}使用标准导入模式${NC}"
    # 确保DATASET_SOURCE不为空且不是--no-resume
    if [ -z "$DATASET_SOURCE" ] || [ "$DATASET_SOURCE" == "--no-resume" ]; then
        echo -e "${RED}错误: 未提供有效的数据集地址${NC}"
        echo "用法: $0 [--no-resume] <数据集地址>"
        exit 1
    fi
    python3 "$PROJECT_ROOT/knowledge_management_system/scripts/import_dataset.py" "$DATASET_SOURCE"
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 数据集导入完成！${NC}"
else
    echo ""
    echo -e "${RED}❌ 数据集导入失败！${NC}"
    exit $EXIT_CODE
fi
