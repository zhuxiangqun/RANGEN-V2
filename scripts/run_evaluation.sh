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

# 检查评测脚本是否存在
EVAL_SCRIPT="${ROOT_DIR}/evaluation_system/comprehensive_evaluation.py"

if [[ ! -f "${EVAL_SCRIPT}" ]]; then
  echo "未找到评测脚本: ${EVAL_SCRIPT}" >&2
  exit 1
fi

# 检查日志文件是否存在
LOG_FILE="${ROOT_DIR}/research_system.log"
if [[ ! -f "${LOG_FILE}" ]]; then
  echo "警告: 未找到日志文件 ${LOG_FILE}" >&2
  echo "请先运行核心系统生成日志: scripts/run_core_with_frames.sh --sample-count 50" >&2
  exit 1
fi

echo "开始运行基于日志的评测系统..."
echo "日志文件: ${LOG_FILE}"
echo "执行: python ${EVAL_SCRIPT}"

# 切换到项目根目录执行
cd "${ROOT_DIR}"
python "${EVAL_SCRIPT}"

echo ""
echo "评测完成！报告位置: comprehensive_eval_results/evaluation_report.md"
