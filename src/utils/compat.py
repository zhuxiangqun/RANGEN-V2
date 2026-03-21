"""向后兼容层 - 保持旧的 import 路径工作"""

import sys
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
else:
    _compat_mappings = {
        "src.api": "src.access.api",
        "src.ui": "src.access.ui",
        "src.core": "src.orchestration",
        "src.tools": "src.agents.tools",
        "src.middleware": "src.access.api.middleware",
    }
    
    for old_path, new_path in _compat_mappings.items():
        if old_path not in sys.modules:
            try:
                __import__(new_path)
                sys.modules[old_path] = sys.modules[new_path]
            except ImportError:
                pass
