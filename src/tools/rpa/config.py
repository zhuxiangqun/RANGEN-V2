"""
RPA系统配置
"""
import os
from pathlib import Path
from typing import Dict, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# RPA系统配置
RPA_CONFIG = {
    "core_system": {
        "script_path": PROJECT_ROOT / "scripts" / "run_core_with_frames.py",
        "log_path": PROJECT_ROOT / "research_system.log",
        "default_sample_count": 10,
        "default_timeout": 1800.0,
    },
    "evaluation_system": {
        "script_path": PROJECT_ROOT / "evaluation_system" / "comprehensive_evaluation.py",
        "report_path": PROJECT_ROOT / "comprehensive_eval_results",
    },
    "frontend": {
        "monitor_path": PROJECT_ROOT / "frontend_monitor",
        "backend_path": PROJECT_ROOT / "frontend_monitor" / "backend",
        "frontend_path": PROJECT_ROOT / "frontend_monitor",
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "backend_url": os.getenv("BACKEND_URL", "http://localhost:5001"),
    },
    "rpa": {
        "work_dir": PROJECT_ROOT / "rpa_system" / "work",
        "reports_dir": PROJECT_ROOT / "rpa_system" / "reports",
        "logs_dir": PROJECT_ROOT / "rpa_system" / "logs",
        "state_file": PROJECT_ROOT / "rpa_system" / "state.json",
    },
    "ui": {
        "host": os.getenv("RPA_UI_HOST", "0.0.0.0"),
        "port": int(os.getenv("RPA_UI_PORT", "8888")),
        "debug": os.getenv("RPA_UI_DEBUG", "false").lower() == "true",
    },
}

# 创建必要的目录
for key, value in RPA_CONFIG.items():
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            if isinstance(sub_value, Path) and "dir" in sub_key or "path" in sub_key:
                if sub_value.suffix:  # 文件
                    sub_value.parent.mkdir(parents=True, exist_ok=True)
                else:  # 目录
                    sub_value.mkdir(parents=True, exist_ok=True)

