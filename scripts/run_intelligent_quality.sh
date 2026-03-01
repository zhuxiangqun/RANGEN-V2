#!/usr/bin/env bash
set -euo pipefail

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 自动激活本地 venv（如存在）
if [[ -d "${ROOT_DIR}/.venv" ]]; then
  # shellcheck source=/dev/null
  source "${ROOT_DIR}/.venv/bin/activate"
fi

# 检查智能质量分析脚本是否存在
QUALITY_SCRIPT="${ROOT_DIR}/evaluation/run_intelligent_quality_evaluation.py"

if [[ ! -f "${QUALITY_SCRIPT}" ]]; then
  echo "未找到智能质量分析脚本: ${QUALITY_SCRIPT}" >&2
  exit 1
fi

# 检查src目录是否存在
SRC_DIR="${ROOT_DIR}/src"
if [[ ! -d "${SRC_DIR}" ]]; then
  echo "未找到src目录: ${SRC_DIR}" >&2
  echo "智能质量分析系统需要分析核心系统的源码" >&2
  exit 1
fi

# 解析命令行参数
USE_PROGRESSIVE=""
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --progressive)
      USE_PROGRESSIVE="--use-progressive"
      shift
      ;;
    --help|-h)
      echo "智能质量分析系统"
      echo ""
      echo "用法: $0 [选项]"
      echo ""
      echo "选项:"
      echo "  --progressive    使用渐进式分析模式"
      echo "  --help, -h       显示此帮助信息"
      echo ""
      echo "功能:"
      echo "  - 分析核心系统源码质量"
      echo "  - 检测硬编码、伪智能、作弊行为"
      echo "  - 生成质量分析报告"
      echo ""
      echo "输出:"
      echo "  - JSON报告: intelligent_quality_comprehensive_evaluation_*.json"
      echo "  - 控制台显示详细分析结果"
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      echo "使用 --help 查看帮助信息" >&2
      exit 1
      ;;
  esac
done

echo "开始运行智能质量分析系统..."
echo "源码目录: ${SRC_DIR}"
echo "执行: python ${QUALITY_SCRIPT} ${USE_PROGRESSIVE}"

# 切换到项目根目录执行
cd "${ROOT_DIR}"
python "${QUALITY_SCRIPT}" ${USE_PROGRESSIVE}

echo ""
echo "智能质量分析完成！"
echo "查看生成的JSON报告文件了解详细结果"
