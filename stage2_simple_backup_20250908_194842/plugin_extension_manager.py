"""
插件扩展管理器
支持通过插件扩展功能，实现真正的可扩展性
"""

import logging
import importlib
import importlib.util
import os
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


