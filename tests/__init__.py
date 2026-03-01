"""
RANGEN 测试框架

统一测试入口，提供完整的测试覆盖率和质量保证
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 测试框架已加载环境变量')
except ImportError:
    print('⚠️ python-dotenv未安装')

__version__ = "1.0.0"
__all__ = [
    'run_all_tests',
    'run_unit_tests',
    'run_integration_tests',
    'run_performance_tests',
    'generate_test_report'
]
