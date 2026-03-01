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

# 解析参数
SAMPLE_COUNT=""
DATA_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-count)
      SAMPLE_COUNT="${2:-}"
      shift 2
      ;;
    --data-path)
      DATA_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "未知参数: $1" >&2
      echo "用法: $0 [--sample-count N] [--data-path FILE]" >&2
      exit 1
      ;;
  esac
done

PY_SCRIPT="${ROOT_DIR}/scripts/run_core_with_frames.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "未找到 Python 脚本: ${PY_SCRIPT}" >&2
  exit 1
fi

CMD=("python" "${PY_SCRIPT}")
[[ -n "${SAMPLE_COUNT}" ]] && CMD+=("--sample-count" "${SAMPLE_COUNT}")
[[ -n "${DATA_PATH}" ]] && CMD+=("--data-path" "${DATA_PATH}")

echo "执行: ${CMD[*]}"
"${CMD[@]}"


