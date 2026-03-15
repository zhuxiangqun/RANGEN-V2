"""
NLU Bridge 模块
================

自然语言理解桥接层，用于理解用户需求并匹配相应的能力。

核心功能:
1. 能力类型识别 (CapabilityTypeDetector) - 第一优先级
2. 需求解析 (RequirementParser)
3. 团队构建 (TeamBuilder)

使用方式:
    from src.core.nlu_bridge import CapabilityTypeDetector, detect_capability_type
    
    # 识别能力类型
    result = await detect_capability_type("帮我建立一个研发团队")
    print(result.primary_type)  # -> CapabilityType.TEAM
"""

from src.core.nlu_bridge.capability_type_detector import (
    CapabilityTypeDetector,
    CapabilityType,
    TypeDetectionResult,
    detect_capability_type,
)

from src.core.nlu_bridge.requirement_parser import (
    RequirementParser,
    RequirementAnalysis,
    parse_requirement,
)

from src.core.nlu_bridge.team_builder import (
    TeamBuilder,
    Team,
    TeamRole,
    build_team,
)

__all__ = [
    "CapabilityTypeDetector",
    "CapabilityType",
    "TypeDetectionResult",
    "detect_capability_type",
    "RequirementParser",
    "RequirementAnalysis",
    "parse_requirement",
    "TeamBuilder",
    "Team",
    "TeamRole",
    "build_team",
]
