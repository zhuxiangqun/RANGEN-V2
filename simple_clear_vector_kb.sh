#!/bin/bash
# 简化的向量知识库清理脚本（Shell包装）
# 绕过复杂的依赖，直接清理文件

# 获取脚本实际路径（支持符号链接）
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

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
            echo "  # 清理向量知识库（自动备份）"
            echo "  $0"
            echo ""
            echo "  # 清理向量知识库（不备份）"
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

# 构建Python命令参数
PYTHON_ARGS=()

if [ "$BACKUP" = false ]; then
    PYTHON_ARGS+=("--no-backup")
fi

# 执行Python脚本
echo "🚀 执行简化的向量知识库清理..."
echo "   脚本: scripts/simple_clear_vector_kb.py"
echo "   参数: ${PYTHON_ARGS[*]}"
echo ""

python3 scripts/simple_clear_vector_kb.py "${PYTHON_ARGS[@]}"

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 向量知识库清理完成！"
    echo "💡 提示: 重启相关服务后，知识库将被重新构建"
else
    echo ""
    echo "❌ 向量知识库清理失败（退出码: $exit_code）"
fi

exit $exit_code
