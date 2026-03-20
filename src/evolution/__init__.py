"""
RANGEN自进化系统
===============
基于Ouroboros理念的自进化引擎，实现真正的自我修改能力。

核心模块:
- engine: 主进化引擎
- git_integration: Git提交和版本管理
- self_modification: 自我修改能力
- multi_model_review: 多模型安全审查
- consciousness: 后台意识循环
- constitution: 宪法检查和执行
"""

from .engine import EvolutionEngine
from .git_integration import GitIntegration
from .self_mod_test import SelfModification
from .multi_model_review import MultiModelReview
from .consciousness import BackgroundConsciousness
from .constitution import ConstitutionChecker
from .usage_analytics import UsageAnalytics

__all__ = [
    "EvolutionEngine",
    "GitIntegration", 
    "SelfModification",
    "MultiModelReview",
    "BackgroundConsciousness",
    "ConstitutionChecker",
    "UsageAnalytics"
]

__version__ = "1.0.0"
__author__ = "RANGEN自进化系统"
__description__ = "具备自我修改能力的创业者数字伙伴进化引擎"