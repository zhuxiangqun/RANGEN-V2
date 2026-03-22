"""
Design Review App
================

HARD-GATE 设计优先门控的可视化界面。

功能:
- 需求输入 → AI 生成设计
- 可视化审查设计
- 一键批准/拒绝
- 查看 HARD-GATE 状态

运行:
    streamlit run apps/design_review_app/app.py --server.port 8504
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入并运行设计审查 UI
from src.access.ui import design_review_ui
design_review_ui.main()
