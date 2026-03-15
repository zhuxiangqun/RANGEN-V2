"""
Dynamic Dimension Mapping System
================================

This module defines dimension mappings for different entity types (Tool, Agent, Skill, Team, Workflow, Service).
Each entity type has specific dimensions based on its capabilities and category.

The mapping is hierarchical:
1. Entity Type (Tool, Agent, Skill, Team, Workflow, Service)
2. Category/Subtype (RETRIEVAL, COMPUTE, reasoning, planning, etc.)
3. Specific Implementation (calculator, search, etc.)

Usage:
    from src.ui.dimension_mapping import get_tool_dimensions, get_agent_dimensions, get_skill_dimensions
    
    dimensions = get_tool_dimensions("calculator", tool_metadata)
    dimensions = get_agent_dimensions("reasoning_agent", agent_metadata)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class EntityType(Enum):
    """Entity types supported by the dimension system"""
    TOOL = "tool"
    AGENT = "agent"
    SKILL = "skill"
    TEAM = "team"
    WORKFLOW = "workflow"
    SERVICE = "service"


# ============================================================
# TOOL Dimension Mappings
# ============================================================

TOOL_CATEGORY_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    # 计算类工具
    "calculator": {
        "dimensions": {
            "accuracy": {
                "name": "计算准确性",
                "weight": 0.4,
                "test": "验证数学运算结果是否正确",
                "test_cases": [
                    {"input": "2 + 3", "expected": 5},
                    {"input": "10 - 4", "expected": 6},
                    {"input": "3 * 7", "expected": 21},
                    {"input": "100 / 4", "expected": 25},
                ]
            },
            "precision": {
                "name": "精度处理",
                "weight": 0.15,
                "test": "验证浮点数精度和舍入",
                "test_cases": [
                    {"input": "1 / 3", "expected_contains": "0.333"},
                    {"input": "0.1 + 0.2", "expected_not": "0.3"},
                ]
            },
            "overflow": {
                "name": "溢出处理",
                "weight": 0.15,
                "test": "验证大数运算是否正确处理",
                "test_cases": [
                    {"input": "9999999999 * 9999999999", "check_error_or_result": True},
                ]
            },
            "error_handling": {
                "name": "错误处理",
                "weight": 0.15,
                "test": "验证无效输入的错误提示",
                "test_cases": [
                    {"input": "abc + 1", "should_error": True},
                    {"input": "10 / 0", "should_error": True},
                ]
            },
            "operator_support": {
                "name": "运算符支持",
                "weight": 0.15,
                "test": "验证支持的运算符种类",
                "test_cases": [
                    {"input": "2 ** 3", "expected": 8},
                    {"input": "10 % 3", "expected": 1},
                ]
            }
        }
    },
    
    # 搜索类工具
    "search": {
        "dimensions": {
            "relevance": {
                "name": "结果相关性",
                "weight": 0.3,
                "test": "搜索结果是否与查询相关",
            },
            "recall": {
                "name": "召回率",
                "weight": 0.2,
                "test": "是否找到足够的相关结果",
            },
            "latency": {
                "name": "响应延迟",
                "weight": 0.15,
                "test": "搜索响应时间",
                "threshold_ms": 3000,
            },
            "diversity": {
                "name": "结果多样性",
                "weight": 0.15,
                "test": "结果是否覆盖不同来源/角度",
            },
            "freshness": {
                "name": "时效性",
                "weight": 0.1,
                "test": "结果是否为最新信息",
            },
            "result_format": {
                "name": "结果格式",
                "weight": 0.1,
                "test": "结果是否包含标题、URL、摘要",
            }
        }
    },
    
    # 检索类工具 (RAG/Vector Search)
    "retrieval": {
        "dimensions": {
            "similarity": {
                "name": "相似度匹配",
                "weight": 0.25,
                "test": "检索结果与查询的语义相似度",
            },
            "recall": {
                "name": "召回率",
                "weight": 0.2,
                "test": "相关文档的召回比例",
            },
            "precision": {
                "name": "精确率",
                "weight": 0.2,
                "test": "检索结果中相关文档的比例",
            },
            "reranking": {
                "name": "重排序效果",
                "weight": 0.1,
                "test": "重排序是否提升相关性",
            },
            "context_window": {
                "name": "上下文窗口",
                "weight": 0.1,
                "test": "是否正确处理上下文",
            },
            "chunking": {
                "name": "分块效果",
                "weight": 0.15,
                "test": "文档分块是否合理",
            }
        }
    },
    
    # 文件操作类工具
    "file": {
        "dimensions": {
            "read_write": {
                "name": "读写正确性",
                "weight": 0.3,
                "test": "文件读写是否正确",
            },
            "permission": {
                "name": "权限处理",
                "weight": 0.15,
                "test": "权限错误是否正确处理",
            },
            "encoding": {
                "name": "编码处理",
                "weight": 0.15,
                "test": "不同编码是否正确处理",
            },
            "path_security": {
                "name": "路径安全",
                "weight": 0.2,
                "test": "路径遍历攻击是否防护",
            },
            "size_limit": {
                "name": "大小限制",
                "weight": 0.1,
                "test": "大文件是否正确处理",
            },
            "atomicity": {
                "name": "原子性",
                "weight": 0.1,
                "test": "操作失败是否回滚",
            }
        }
    },
    
    # 浏览器类工具
    "browser": {
        "dimensions": {
            "render": {
                "name": "渲染正确性",
                "weight": 0.2,
                "test": "页面是否正确渲染",
            },
            "interaction": {
                "name": "交互能力",
                "weight": 0.2,
                "test": "点击、输入等交互是否有效",
            },
            "javascript": {
                "name": "JS执行",
                "weight": 0.15,
                "test": "JavaScript是否正确执行",
            },
            "wait": {
                "name": "等待机制",
                "weight": 0.15,
                "test": "动态内容加载等待",
            },
            "screenshot": {
                "name": "截图能力",
                "weight": 0.1,
                "test": "截图是否完整",
            },
            "navigation": {
                "name": "导航能力",
                "weight": 0.1,
                "test": "页面跳转、后退、前进",
            },
            "cookies": {
                "name": "Cookie处理",
                "weight": 0.1,
                "test": "Cookie读写是否正确",
            }
        }
    },
    
    # API调用类工具
    "api": {
        "dimensions": {
            "status_code": {
                "name": "状态码正确性",
                "weight": 0.2,
                "test": "HTTP状态码是否正确",
            },
            "response_format": {
                "name": "响应格式",
                "weight": 0.2,
                "test": "JSON/XML格式是否正确",
            },
            "retry": {
                "name": "重试机制",
                "weight": 0.15,
                "test": "失败时是否正确重试",
            },
            "timeout": {
                "name": "超时处理",
                "weight": 0.15,
                "test": "超时是否正确处理",
            },
            "auth": {
                "name": "认证处理",
                "weight": 0.15,
                "test": "认证失败是否正确处理",
            },
            "rate_limit": {
                "name": "速率限制",
                "weight": 0.15,
                "test": "是否正确处理速率限制",
            }
        }
    },
    
    # 推理类工具
    "reasoning": {
        "dimensions": {
            "logic_coherence": {
                "name": "逻辑连贯性",
                "weight": 0.25,
                "test": "推理过程是否逻辑连贯",
            },
            "conclusion_accuracy": {
                "name": "结论准确性",
                "weight": 0.25,
                "test": "推理结论是否正确",
            },
            "step_coverage": {
                "name": "步骤完整性",
                "weight": 0.2,
                "test": "是否覆盖所有推理步骤",
            },
            "evidence_usage": {
                "name": "证据使用",
                "weight": 0.15,
                "test": "是否正确使用证据",
            },
            "explainability": {
                "name": "可解释性",
                "weight": 0.15,
                "test": "推理过程是否可解释",
            }
        }
    },
    
    # 通用工具 (默认)
    "default": {
        "dimensions": {
            "functionality": {
                "name": "功能正确性",
                "weight": 0.35,
                "test": "基本功能是否正常工作",
            },
            "error_handling": {
                "name": "错误处理",
                "weight": 0.25,
                "test": "异常情况是否正确处理",
            },
            "output_format": {
                "name": "输出格式",
                "weight": 0.2,
                "test": "输出是否符合预期格式",
            },
            "efficiency": {
                "name": "执行效率",
                "weight": 0.2,
                "test": "执行时间和资源消耗",
            }
        }
    }
}


# ============================================================
# AGENT Dimension Mappings
# ============================================================

AGENT_CAPABILITY_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "reasoning": {
        "dimensions": {
            "reasoning_depth": {
                "name": "推理深度",
                "weight": 0.2,
                "test": "是否进行多步推理",
            },
            "logic_coherence": {
                "name": "逻辑连贯性",
                "weight": 0.2,
                "test": "推理过程是否逻辑连贯",
            },
            "accuracy": {
                "name": "准确性",
                "weight": 0.15,
                "test": "结论是否正确",
            },
            "evidence": {
                "name": "证据支撑",
                "weight": 0.15,
                "test": "是否有证据支持结论",
            },
            "explainability": {
                "name": "可解释性",
                "weight": 0.15,
                "test": "推理过程是否可解释",
            },
            "efficiency": {
                "name": "效率",
                "weight": 0.15,
                "test": "推理效率",
            }
        }
    },
    
    "planning": {
        "dimensions": {
            "plan_completeness": {
                "name": "计划完整性",
                "weight": 0.25,
                "test": "是否覆盖所有必要步骤",
            },
            "step_coverage": {
                "name": "步骤覆盖",
                "weight": 0.2,
                "test": "步骤是否覆盖所有场景",
            },
            "feasibility": {
                "name": "可行性",
                "weight": 0.2,
                "test": "计划是否可执行",
            },
            "adaptability": {
                "name": "适应性",
                "weight": 0.2,
                "test": "是否能根据反馈调整计划",
            },
            "clarity": {
                "name": "清晰度",
                "weight": 0.15,
                "test": "计划描述是否清晰",
            }
        }
    },
    
    "conversation": {
        "dimensions": {
            "relevance": {
                "name": "相关性",
                "weight": 0.25,
                "test": "回复是否与问题相关",
            },
            "completeness": {
                "name": "完整性",
                "weight": 0.2,
                "test": "是否完整回答问题",
            },
            "tone": {
                "name": "语气适当性",
                "weight": 0.15,
                "test": "语气是否适当",
            },
            "clarity": {
                "name": "清晰度",
                "weight": 0.2,
                "test": "表达是否清晰",
            },
            "engagement": {
                "name": "参与度",
                "weight": 0.2,
                "test": "是否有效引导对话",
            }
        }
    },
    
    "validation": {
        "dimensions": {
            "accuracy": {
                "name": "验证准确性",
                "weight": 0.3,
                "test": "验证结果是否正确",
            },
            "coverage": {
                "name": "覆盖完整性",
                "weight": 0.25,
                "test": "是否覆盖所有验证点",
            },
            "false_positive": {
                "name": "误报率",
                "weight": 0.2,
                "test": "误报是否控制在低水平",
            },
            "false_negative": {
                "name": "漏报率",
                "weight": 0.25,
                "test": "是否正确识别所有问题",
            }
        }
    },
    
    "rag": {
        "dimensions": {
            "retrieval_accuracy": {
                "name": "检索准确度",
                "weight": 0.25,
                "test": "检索结果是否准确",
            },
            "context_quality": {
                "name": "上下文质量",
                "weight": 0.2,
                "test": "提供的上下文是否相关",
            },
            "answer_relevance": {
                "name": "答案相关性",
                "weight": 0.2,
                "test": "生成的答案是否回答问题",
            },
            "source_citation": {
                "name": "引用完整性",
                "weight": 0.15,
                "test": "是否正确引用来源",
            },
            "hallucination": {
                "name": "幻觉控制",
                "weight": 0.2,
                "test": "是否产生幻觉内容",
            }
        }
    },
    
    "default": {
        "dimensions": {
            "accuracy": {
                "name": "准确性",
                "weight": 0.2,
                "test": "输出是否正确",
            },
            "completeness": {
                "name": "完整性",
                "weight": 0.2,
                "test": "是否覆盖所有需求",
            },
            "efficiency": {
                "name": "效率",
                "weight": 0.15,
                "test": "执行时间和资源消耗",
            },
            "stability": {
                "name": "稳定性",
                "weight": 0.15,
                "test": "错误处理和容错能力",
            },
            "explainability": {
                "name": "可解释性",
                "weight": 0.15,
                "test": "过程是否可追踪透明",
            },
            "security": {
                "name": "安全性",
                "weight": 0.15,
                "test": "是否有风险内容",
            }
        }
    }
}


# ============================================================
# SKILL Dimension Mappings
# ============================================================

SKILL_TRIGGER_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "code": {
        "dimensions": {
            "code_quality": {
                "name": "代码质量",
                "weight": 0.25,
                "test": "生成的代码质量",
            },
            "security": {
                "name": "安全性",
                "weight": 0.25,
                "test": "是否有安全漏洞",
            },
            "best_practices": {
                "name": "最佳实践",
                "weight": 0.15,
                "test": "是否符合最佳实践",
            },
            "completeness": {
                "name": "完整性",
                "weight": 0.15,
                "test": "代码是否完整可运行",
            },
            "efficiency": {
                "name": "效率",
                "weight": 0.1,
                "test": "代码执行效率",
            },
            "readability": {
                "name": "可读性",
                "weight": 0.1,
                "test": "代码是否易于理解",
            }
        }
    },
    
    "document": {
        "dimensions": {
            "format_compliance": {
                "name": "格式规范",
                "weight": 0.25,
                "test": "是否符合格式要求",
            },
            "extraction_accuracy": {
                "name": "提取准确度",
                "weight": 0.25,
                "test": "信息提取是否准确",
            },
            "structure": {
                "name": "结构化",
                "weight": 0.2,
                "test": "输出结构是否清晰",
            },
            "completeness": {
                "name": "完整性",
                "weight": 0.2,
                "test": "是否提取所有重要信息",
            },
            "readability": {
                "name": "可读性",
                "weight": 0.1,
                "test": "文档是否易于阅读",
            }
        }
    },
    
    "analysis": {
        "dimensions": {
            "depth": {
                "name": "分析深度",
                "weight": 0.25,
                "test": "分析是否深入",
            },
            "insight": {
                "name": "洞察力",
                "weight": 0.2,
                "test": "是否提供有价值的洞察",
            },
            "evidence": {
                "name": "证据充分性",
                "weight": 0.2,
                "test": "分析是否有充分证据",
            },
            "clarity": {
                "name": "清晰度",
                "weight": 0.15,
                "test": "分析是否清晰易懂",
            },
            "actionability": {
                "name": "可操作性",
                "weight": 0.2,
                "test": "是否提供可操作的建议",
            }
        }
    },
    
    "writing": {
        "dimensions": {
            "grammar": {
                "name": "语法正确性",
                "weight": 0.2,
                "test": "语法是否正确",
            },
            "coherence": {
                "name": "连贯性",
                "weight": 0.2,
                "test": "内容是否连贯",
            },
            "tone": {
                "name": "语气适当性",
                "weight": 0.15,
                "test": "语气是否适当",
            },
            "clarity": {
                "name": "清晰度",
                "weight": 0.15,
                "test": "表达是否清晰",
            },
            "audience_fit": {
                "name": "受众适配",
                "weight": 0.15,
                "test": "是否适合目标受众",
            },
            "completeness": {
                "name": "完整性",
                "weight": 0.15,
                "test": "内容是否完整",
            }
        }
    },
    
    "default": {
        "dimensions": {
            "structure": {
                "name": "结构完整性",
                "weight": 0.2,
                "test": "配置信息是否完整",
            },
            "accuracy": {
                "name": "准确性",
                "weight": 0.2,
                "test": "输出结果准确度",
            },
            "practicality": {
                "name": "实用性",
                "weight": 0.2,
                "test": "输出结果是否有用",
            },
            "usability": {
                "name": "可用性",
                "weight": 0.15,
                "test": "是否易于使用",
            },
            "reliability": {
                "name": "可靠性",
                "weight": 0.15,
                "test": "是否稳定可靠",
            },
            "performance": {
                "name": "性能",
                "weight": 0.1,
                "test": "执行效率",
            }
        }
    }
}


# ============================================================
# TEAM Dimension Mappings
# ============================================================

TEAM_TYPE_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "testing": {
        "dimensions": {
            "coverage": {
                "name": "测试覆盖率",
                "weight": 0.25,
                "test": "是否覆盖所有测试场景",
            },
            "design_quality": {
                "name": "设计质量",
                "weight": 0.2,
                "test": "测试用例设计是否合理",
            },
            "edge_cases": {
                "name": "边界情况",
                "weight": 0.15,
                "test": "是否覆盖边界条件",
            },
            "maintainability": {
                "name": "可维护性",
                "weight": 0.15,
                "test": "测试代码是否易于维护",
            },
            "automation": {
                "name": "自动化程度",
                "weight": 0.15,
                "test": "自动化测试比例",
            },
            "execution_efficiency": {
                "name": "执行效率",
                "weight": 0.1,
                "test": "测试执行速度",
            }
        }
    },
    
    "engineering": {
        "dimensions": {
            "code_quality": {
                "name": "代码质量",
                "weight": 0.25,
                "test": "生成的代码质量",
            },
            "architecture": {
                "name": "架构设计",
                "weight": 0.2,
                "test": "架构是否合理",
            },
            "security": {
                "name": "安全性",
                "weight": 0.15,
                "test": "是否有安全考虑",
            },
            "performance": {
                "name": "性能考虑",
                "weight": 0.15,
                "test": "是否考虑性能",
            },
            "maintainability": {
                "name": "可维护性",
                "weight": 0.15,
                "test": "代码是否易于维护",
            },
            "documentation": {
                "name": "文档完整性",
                "weight": 0.1,
                "test": "是否有适当文档",
            }
        }
    },
    
    "marketing": {
        "dimensions": {
            "creativity": {
                "name": "创意性",
                "weight": 0.2,
                "test": "创意是否新颖",
            },
            "relevance": {
                "name": "相关性",
                "weight": 0.2,
                "test": "内容是否与产品相关",
            },
            "tone_appropriateness": {
                "name": "语气适当性",
                "weight": 0.15,
                "test": "语气是否适当",
            },
            "call_to_action": {
                "name": "行动号召",
                "weight": 0.15,
                "test": "是否有有效的CTA",
            },
            "targeting": {
                "name": "目标受众定位",
                "weight": 0.15,
                "test": "是否针对正确受众",
            },
            "effectiveness": {
                "name": "效果",
                "weight": 0.15,
                "test": "营销效果预期",
            }
        }
    },
    
    "design": {
        "dimensions": {
            "usability": {
                "name": "可用性",
                "weight": 0.25,
                "test": "设计是否易于使用",
            },
            "aesthetics": {
                "name": "美观性",
                "weight": 0.2,
                "test": "视觉设计是否美观",
            },
            "consistency": {
                "name": "一致性",
                "weight": 0.15,
                "test": "设计风格是否一致",
            },
            "accessibility": {
                "name": "可访问性",
                "weight": 0.15,
                "test": "是否考虑无障碍",
            },
            "responsiveness": {
                "name": "响应式",
                "weight": 0.15,
                "test": "是否适配不同设备",
            },
            "clarity": {
                "name": "清晰度",
                "weight": 0.1,
                "test": "信息是否清晰",
            }
        }
    },
    
    "default": {
        "dimensions": {
            "coordination": {
                "name": "协作能力",
                "weight": 0.25,
                "test": "成员间协调如何",
            },
            "task_distribution": {
                "name": "任务分配",
                "weight": 0.2,
                "test": "任务分配是否合理",
            },
            "coverage": {
                "name": "覆盖率",
                "weight": 0.2,
                "test": "是否覆盖所有需求",
            },
            "quality": {
                "name": "质量",
                "weight": 0.2,
                "test": "输出质量如何",
            },
            "efficiency": {
                "name": "效率",
                "weight": 0.15,
                "test": "执行速度",
            }
        }
    }
}


# ============================================================
# WORKFLOW Dimension Mappings
# ============================================================

WORKFLOW_TYPE_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "execution_coordinator": {
        "dimensions": {
            "node_execution": {
                "name": "节点执行",
                "weight": 0.2,
                "test": "各节点是否正确执行",
            },
            "flow_control": {
                "name": "流程控制",
                "weight": 0.15,
                "test": "条件分支是否正确",
            },
            "state_management": {
                "name": "状态管理",
                "weight": 0.15,
                "test": "状态流转是否正确",
            },
            "langgraph_generation": {
                "name": "图生成",
                "weight": 0.15,
                "test": "是否生成LangGraph图",
            },
            "output_quality": {
                "name": "输出质量",
                "weight": 0.2,
                "test": "最终输出质量",
            },
            "error_recovery": {
                "name": "错误恢复",
                "weight": 0.15,
                "test": "异常处理能力",
            }
        }
    },
    
    "audit": {
        "dimensions": {
            "issue_detection": {
                "name": "问题检测",
                "weight": 0.25,
                "test": "是否能检测出问题",
            },
            "risk_assessment": {
                "name": "风险评估",
                "weight": 0.2,
                "test": "风险评估是否准确",
            },
            "coverage": {
                "name": "覆盖范围",
                "weight": 0.15,
                "test": "检查是否全面",
            },
            "false_positive": {
                "name": "误报率",
                "weight": 0.15,
                "test": "误报是否合理",
            },
            "suggestion_quality": {
                "name": "建议质量",
                "weight": 0.15,
                "test": "修复建议是否有效",
            },
            "severity_ranking": {
                "name": "严重性排序",
                "weight": 0.1,
                "test": "问题排序是否合理",
            }
        }
    },
    
    "layered": {
        "dimensions": {
            "layer_separation": {
                "name": "层级分离",
                "weight": 0.2,
                "test": "层级是否清晰分离",
            },
            "dependency_management": {
                "name": "依赖管理",
                "weight": 0.2,
                "test": "依赖关系是否正确",
            },
            "information_flow": {
                "name": "信息流",
                "weight": 0.15,
                "test": "信息是否正确流转",
            },
            "abstraction": {
                "name": "抽象程度",
                "weight": 0.15,
                "test": "抽象是否合理",
            },
            "coupling": {
                "name": "耦合度",
                "weight": 0.15,
                "test": "模块间耦合是否合理",
            },
            "cohesion": {
                "name": "内聚度",
                "weight": 0.15,
                "test": "模块内聚是否合理",
            }
        }
    },
    
    "default": {
        "dimensions": {
            "execution": {
                "name": "执行能力",
                "weight": 0.35,
                "test": "是否能正确执行",
            },
            "flow": {
                "name": "流程完整性",
                "weight": 0.3,
                "test": "流程是否完整",
            },
            "quality": {
                "name": "输出质量",
                "weight": 0.35,
                "test": "最终输出质量",
            }
        }
    }
}


# ============================================================
# SERVICE Dimension Mappings
# ============================================================

SERVICE_TYPE_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "llm": {
        "dimensions": {
            "availability": {
                "name": "可用性",
                "weight": 0.2,
                "test": "服务是否可用",
            },
            "response_quality": {
                "name": "响应质量",
                "weight": 0.25,
                "test": "LLM输出质量",
            },
            "latency": {
                "name": "延迟",
                "weight": 0.15,
                "test": "响应时间",
            },
            "token_efficiency": {
                "name": "Token效率",
                "weight": 0.1,
                "test": "Token使用是否合理",
            },
            "error_handling": {
                "name": "错误处理",
                "weight": 0.15,
                "test": "异常情况处理",
            },
            "fallback": {
                "name": "降级能力",
                "weight": 0.15,
                "test": "失败时是否可降级",
            }
        }
    },
    
    "model": {
        "dimensions": {
            "availability": {
                "name": "可用性",
                "weight": 0.2,
                "test": "模型是否可用",
            },
            "inference_speed": {
                "name": "推理速度",
                "weight": 0.2,
                "test": "推理时间",
            },
            "accuracy": {
                "name": "准确性",
                "weight": 0.25,
                "test": "输出准确性",
            },
            "resource_usage": {
                "name": "资源使用",
                "weight": 0.15,
                "test": "CPU/内存使用",
            },
            "batch_support": {
                "name": "批处理支持",
                "weight": 0.1,
                "test": "批处理能力",
            },
            "versioning": {
                "name": "版本管理",
                "weight": 0.1,
                "test": "版本切换能力",
            }
        }
    },
    
    "cache": {
        "dimensions": {
            "hit_rate": {
                "name": "命中率",
                "weight": 0.3,
                "test": "缓存命中率",
            },
            "latency": {
                "name": "延迟",
                "weight": 0.2,
                "test": "缓存读写延迟",
            },
            "consistency": {
                "name": "一致性",
                "weight": 0.2,
                "test": "缓存一致性",
            },
            "eviction": {
                "name": "淘汰策略",
                "weight": 0.15,
                "test": "LRU等策略",
            },
            "capacity": {
                "name": "容量管理",
                "weight": 0.15,
                "test": "容量是否合理",
            }
        }
    },
    
    "config": {
        "dimensions": {
            "availability": {
                "name": "可用性",
                "weight": 0.25,
                "test": "配置是否可读",
            },
            "validation": {
                "name": "验证",
                "weight": 0.2,
                "test": "配置验证是否正确",
            },
            "encryption": {
                "name": "加密",
                "weight": 0.15,
                "test": "敏感信息是否加密",
            },
            "hot_reload": {
                "name": "热加载",
                "weight": 0.2,
                "test": "是否支持热加载",
            },
            "default_values": {
                "name": "默认值",
                "weight": 0.1,
                "test": "默认值是否合理",
            },
            "override": {
                "name": "覆盖机制",
                "weight": 0.1,
                "test": "配置覆盖是否正确",
            }
        }
    },
    
    "skill": {
        "dimensions": {
            "discovery": {
                "name": "发现能力",
                "weight": 0.2,
                "test": "Skill发现是否正确",
            },
            "execution": {
                "name": "执行能力",
                "weight": 0.25,
                "test": "Skill执行是否正确",
            },
            "triggering": {
                "name": "触发准确性",
                "weight": 0.2,
                "test": "触发是否准确",
            },
            "isolation": {
                "name": "隔离性",
                "weight": 0.15,
                "test": "Skill间是否隔离",
            },
            "versioning": {
                "name": "版本管理",
                "weight": 0.1,
                "test": "版本控制",
            },
            "dependency": {
                "name": "依赖处理",
                "weight": 0.1,
                "test": "依赖解析",
            }
        }
    },
    
    "metrics": {
        "dimensions": {
            "collection": {
                "name": "采集能力",
                "weight": 0.25,
                "test": "指标采集是否完整",
            },
            "accuracy": {
                "name": "准确性",
                "weight": 0.25,
                "test": "指标数据是否准确",
            },
            "aggregation": {
                "name": "聚合能力",
                "weight": 0.15,
                "test": "聚合计算是否正确",
            },
            "retention": {
                "name": "保留策略",
                "weight": 0.15,
                "test": "数据保留是否合理",
            },
            "alerting": {
                "name": "告警能力",
                "weight": 0.2,
                "test": "告警是否及时准确",
            }
        }
    },
    
    "default": {
        "dimensions": {
            "availability": {
                "name": "可用性",
                "weight": 0.35,
                "test": "服务是否可用",
            },
            "performance": {
                "name": "性能",
                "weight": 0.3,
                "test": "响应时间",
            },
            "reliability": {
                "name": "可靠性",
                "weight": 0.35,
                "test": "是否稳定可靠",
            }
        }
    }
}


# ============================================================
# SYSTEM MODULE Dimension Mappings (22 core modules)
# ============================================================

SYSTEM_MODULE_DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "llm": {
        "dimensions": {
            "connection": {"name": "连接状态", "weight": 0.3, "test": "LLM连接是否正常"},
            "response_time": {"name": "响应时间", "weight": 0.25, "test": "响应速度是否合理"},
            "response_quality": {"name": "响应质量", "weight": 0.3, "test": "输出质量是否达标"},
            "error_handling": {"name": "错误处理", "weight": 0.15, "test": "异常情况处理"}
        }
    },
    "tools": {
        "dimensions": {
            "registration": {"name": "注册能力", "weight": 0.25, "test": "工具注册是否成功"},
            "discovery": {"name": "发现能力", "weight": 0.25, "test": "工具查找是否正确"},
            "execution": {"name": "执行能力", "weight": 0.3, "test": "工具调用是否成功"},
            "compatibility": {"name": "兼容性", "weight": 0.2, "test": "不同工具是否兼容"}
        }
    },
    "memory": {
        "dimensions": {
            "storage": {"name": "存储能力", "weight": 0.25, "test": "数据是否正确存储"},
            "retrieval": {"name": "检索能力", "weight": 0.25, "test": "数据是否可正确检索"},
            "persistence": {"name": "持久化", "weight": 0.2, "test": "数据是否持久化"},
            "capacity": {"name": "容量管理", "weight": 0.15, "test": "容量是否合理管理"},
            "cleanup": {"name": "清理机制", "weight": 0.15, "test": "过期数据是否清理"}
        }
    },
    "prompt": {
        "dimensions": {
            "generation": {"name": "生成能力", "weight": 0.3, "test": "提示词生成是否正确"},
            "optimization": {"name": "优化能力", "weight": 0.25, "test": "提示词是否优化"},
            "templating": {"name": "模板支持", "weight": 0.2, "test": "模板是否正确应用"},
            "validation": {"name": "验证能力", "weight": 0.25, "test": "提示词是否验证"}
        }
    },
    "execution_loop": {
        "dimensions": {
            "iteration": {"name": "迭代能力", "weight": 0.25, "test": "循环迭代是否正确"},
            "termination": {"name": "终止条件", "weight": 0.2, "test": "终止条件是否正确"},
            "step_tracking": {"name": "步骤追踪", "weight": 0.25, "test": "步骤是否正确追踪"},
            "state_update": {"name": "状态更新", "weight": 0.3, "test": "状态是否正确更新"}
        }
    },
    "state_management": {
        "dimensions": {
            "persistence": {"name": "持久化", "weight": 0.25, "test": "状态是否持久化"},
            "consistency": {"name": "一致性", "weight": 0.3, "test": "状态是否一致"},
            "serialization": {"name": "序列化", "weight": 0.2, "test": "序列化是否正确"},
            "recovery": {"name": "恢复能力", "weight": 0.25, "test": "状态是否可恢复"}
        }
    },
    "error_handling": {
        "dimensions": {
            "detection": {"name": "检测能力", "weight": 0.3, "test": "错误是否检测"},
            "recovery": {"name": "恢复能力", "weight": 0.25, "test": "是否可恢复"},
            "reporting": {"name": "报告能力", "weight": 0.2, "test": "错误报告是否清晰"},
            "logging": {"name": "日志能力", "weight": 0.25, "test": "日志是否完整"}
        }
    },
    "context_management": {
        "dimensions": {
            "tracking": {"name": "追踪能力", "weight": 0.25, "test": "上下文是否追踪"},
            "compression": {"name": "压缩能力", "weight": 0.2, "test": "上下文是否压缩"},
            "retrieval": {"name": "检索能力", "weight": 0.25, "test": "上下文是否可检索"},
            "window": {"name": "窗口管理", "weight": 0.3, "test": "窗口是否正确管理"}
        }
    },
    "cache": {
        "dimensions": {
            "hit_rate": {"name": "命中率", "weight": 0.3, "test": "缓存命中率"},
            "latency": {"name": "延迟", "weight": 0.2, "test": "缓存读写延迟"},
            "consistency": {"name": "一致性", "weight": 0.25, "test": "缓存一致性"},
            "eviction": {"name": "淘汰策略", "weight": 0.25, "test": "LRU等策略"}
        }
    },
    "security": {
        "dimensions": {
            "authentication": {"name": "认证", "weight": 0.25, "test": "认证是否正确"},
            "authorization": {"name": "授权", "weight": 0.25, "test": "授权是否正确"},
            "validation": {"name": "验证", "weight": 0.25, "test": "输入是否验证"},
            "encryption": {"name": "加密", "weight": 0.25, "test": "敏感信息是否加密"}
        }
    },
    "monitoring": {
        "dimensions": {
            "collection": {"name": "采集能力", "weight": 0.3, "test": "指标采集是否完整"},
            "aggregation": {"name": "聚合能力", "weight": 0.25, "test": "聚合计算是否正确"},
            "visualization": {"name": "可视化", "weight": 0.2, "test": "数据是否可视化"},
            "alerting": {"name": "告警能力", "weight": 0.25, "test": "告警是否及时"}
        }
    },
    "routing": {
        "dimensions": {
            "selection": {"name": "选择能力", "weight": 0.3, "test": "路由选择是否正确"},
            "fallback": {"name": "降级能力", "weight": 0.25, "test": "失败时是否降级"},
            "load_balancing": {"name": "负载均衡", "weight": 0.25, "test": "负载是否均衡"},
            "timeout": {"name": "超时处理", "weight": 0.2, "test": "超时是否正确处理"}
        }
    },
    "configuration": {
        "dimensions": {
            "loading": {"name": "加载能力", "weight": 0.3, "test": "配置是否正确加载"},
            "validation": {"name": "验证能力", "weight": 0.25, "test": "配置是否验证"},
            "override": {"name": "覆盖机制", "weight": 0.2, "test": "覆盖是否正确"},
            "hot_reload": {"name": "热加载", "weight": 0.25, "test": "是否支持热加载"}
        }
    },
    "event_system": {
        "dimensions": {
            "publish": {"name": "发布能力", "weight": 0.25, "test": "事件是否发布"},
            "subscribe": {"name": "订阅能力", "weight": 0.25, "test": "事件是否订阅"},
            "dispatch": {"name": "分发能力", "weight": 0.25, "test": "事件是否分发"},
            "ordering": {"name": "顺序性", "weight": 0.25, "test": "事件顺序是否正确"}
        }
    },
    "skill_registry": {
        "dimensions": {
            "discovery": {"name": "发现能力", "weight": 0.3, "test": "Skill发现是否正确"},
            "registration": {"name": "注册能力", "weight": 0.25, "test": "Skill注册是否成功"},
            "execution": {"name": "执行能力", "weight": 0.25, "test": "Skill执行是否正确"},
            "versioning": {"name": "版本管理", "weight": 0.2, "test": "版本控制是否正确"}
        }
    },
    "gateway": {
        "dimensions": {
            "routing": {"name": "路由能力", "weight": 0.25, "test": "请求路由是否正确"},
            "authentication": {"name": "认证能力", "weight": 0.25, "test": "认证是否正确"},
            "rate_limiting": {"name": "限流能力", "weight": 0.25, "test": "限流是否正确"},
            "proxy": {"name": "代理能力", "weight": 0.25, "test": "代理是否正确"}
        }
    },
    "mcp_server": {
        "dimensions": {
            "connection": {"name": "连接能力", "weight": 0.3, "test": "MCP连接是否正常"},
            "protocol": {"name": "协议支持", "weight": 0.25, "test": "协议是否正确"},
            "resource": {"name": "资源管理", "weight": 0.25, "test": "资源是否管理"},
            "lifecycle": {"name": "生命周期", "weight": 0.2, "test": "生命周期是否正确"}
        }
    },
    "retrieval": {
        "dimensions": {
            "search": {"name": "搜索能力", "weight": 0.3, "test": "搜索是否正确"},
            "ranking": {"name": "排序能力", "weight": 0.25, "test": "排序是否合理"},
            "filtering": {"name": "过滤能力", "weight": 0.2, "test": "过滤是否正确"},
            "chunking": {"name": "分块能力", "weight": 0.25, "test": "分块是否合理"}
        }
    },
    "cost_control": {
        "dimensions": {
            "tracking": {"name": "追踪能力", "weight": 0.3, "test": "成本是否追踪"},
            "limiting": {"name": "限制能力", "weight": 0.3, "test": "成本是否限制"},
            "reporting": {"name": "报告能力", "weight": 0.2, "test": "报告是否完整"},
            "optimization": {"name": "优化能力", "weight": 0.2, "test": "成本是否优化"}
        }
    },
    "agent_coordinator": {
        "dimensions": {
            "coordination": {"name": "协调能力", "weight": 0.3, "test": "Agent协调是否正确"},
            "delegation": {"name": "委托能力", "weight": 0.25, "test": "任务委托是否正确"},
            "conflict_resolution": {"name": "冲突解决", "weight": 0.25, "test": "冲突是否解决"},
            "communication": {"name": "通信能力", "weight": 0.2, "test": "通信是否正确"}
        }
    },
    "dependency_injection": {
        "dimensions": {
            "resolution": {"name": "解析能力", "weight": 0.3, "test": "依赖解析是否正确"},
            "lifecycle": {"name": "生命周期", "weight": 0.25, "test": "生命周期是否正确"},
            "scoping": {"name": "作用域", "weight": 0.25, "test": "作用域是否正确"},
            "lazy_loading": {"name": "延迟加载", "weight": 0.2, "test": "延迟加载是否正确"}
        }
    },
    "storage": {
        "dimensions": {
            "write": {"name": "写入能力", "weight": 0.3, "test": "数据是否正确写入"},
            "read": {"name": "读取能力", "weight": 0.3, "test": "数据是否正确读取"},
            "integrity": {"name": "完整性", "weight": 0.2, "test": "数据完整性"},
            "backup": {"name": "备份能力", "weight": 0.2, "test": "备份是否正确"}
        }
    },
    "default": {
        "dimensions": {
            "functionality": {"name": "功能正确性", "weight": 0.4, "test": "基本功能是否正常"},
            "integration": {"name": "集成能力", "weight": 0.3, "test": "模块集成是否正确"},
            "performance": {"name": "性能", "weight": 0.3, "test": "性能是否达标"}
        }
    }
}


# ============================================================
# Helper Functions
# ============================================================

def get_tool_dimensions(tool_name: str, tool_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific tool based on its name and metadata.
    
    Args:
        tool_name: Name of the tool
        tool_metadata: Optional metadata including category, description, etc.
    
    Returns:
        Dictionary of dimension configurations
    """
    # Try to determine type from name
    name_lower = tool_name.lower()
    
    # Check metadata for category
    category = None
    if tool_metadata:
        category = tool_metadata.get('category', '').lower()
    
    # Match based on name patterns
    if any(kw in name_lower for kw in ['calc', 'calculator', 'math']):
        return TOOL_CATEGORY_DIMENSIONS.get("calculator", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['search', 'web_search']):
        return TOOL_CATEGORY_DIMENSIONS.get("search", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['retrieval', 'rag', 'knowledge']):
        return TOOL_CATEGORY_DIMENSIONS.get("retrieval", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['file', 'read', 'write']):
        return TOOL_CATEGORY_DIMENSIONS.get("file", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['browser', 'web']):
        return TOOL_CATEGORY_DIMENSIONS.get("browser", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['api', 'http', 'request']):
        return TOOL_CATEGORY_DIMENSIONS.get("api", TOOL_CATEGORY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['reasoning', 'think']):
        return TOOL_CATEGORY_DIMENSIONS.get("reasoning", TOOL_CATEGORY_DIMENSIONS["default"])
    
    # Check category from metadata
    if category:
        if 'retrieval' in category:
            return TOOL_CATEGORY_DIMENSIONS.get("retrieval", TOOL_CATEGORY_DIMENSIONS["default"])
        elif 'compute' in category:
            return TOOL_CATEGORY_DIMENSIONS.get("calculator", TOOL_CATEGORY_DIMENSIONS["default"])
        elif 'api' in category:
            return TOOL_CATEGORY_DIMENSIONS.get("api", TOOL_CATEGORY_DIMENSIONS["default"])
    
    return TOOL_CATEGORY_DIMENSIONS["default"]


def get_agent_dimensions(agent_name: str, agent_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific agent based on its name and metadata.
    """
    name_lower = agent_name.lower()
    
    if any(kw in name_lower for kw in ['reasoning', 'react', 'think']):
        return AGENT_CAPABILITY_DIMENSIONS.get("reasoning", AGENT_CAPABILITY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['plan', 'planner']):
        return AGENT_CAPABILITY_DIMENSIONS.get("planning", AGENT_CAPABILITY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['chat', 'conversation', 'dialog']):
        return AGENT_CAPABILITY_DIMENSIONS.get("conversation", AGENT_CAPABILITY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['valid', 'check']):
        return AGENT_CAPABILITY_DIMENSIONS.get("validation", AGENT_CAPABILITY_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['rag', 'retriev', 'knowledge']):
        return AGENT_CAPABILITY_DIMENSIONS.get("rag", AGENT_CAPABILITY_DIMENSIONS["default"])
    
    return AGENT_CAPABILITY_DIMENSIONS["default"]


def get_skill_dimensions(skill_name: str, skill_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific skill based on its name and metadata.
    """
    name_lower = skill_name.lower()
    
    # Check triggers from metadata
    triggers = []
    if skill_metadata:
        triggers = skill_metadata.get('triggers', [])
    
    # Match based on name or triggers
    if any(kw in name_lower for kw in ['code', 'programming']) or 'code' in triggers:
        return SKILL_TRIGGER_DIMENSIONS.get("code", SKILL_TRIGGER_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['document', 'doc', 'pdf']) or 'document' in triggers:
        return SKILL_TRIGGER_DIMENSIONS.get("document", SKILL_TRIGGER_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['analysis', 'analyze']) or 'analysis' in triggers:
        return SKILL_TRIGGER_DIMENSIONS.get("analysis", SKILL_TRIGGER_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['write', 'writing', 'content']) or 'writing' in triggers:
        return SKILL_TRIGGER_DIMENSIONS.get("writing", SKILL_TRIGGER_DIMENSIONS["default"])
    
    return SKILL_TRIGGER_DIMENSIONS["default"]


def get_team_dimensions(team_name: str, team_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific team based on its name and metadata.
    """
    name_lower = team_name.lower()
    
    if 'test' in name_lower:
        return TEAM_TYPE_DIMENSIONS.get("testing", TEAM_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['engineer', 'dev', 'code']):
        return TEAM_TYPE_DIMENSIONS.get("engineering", TEAM_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['market', 'sales', 'promo']):
        return TEAM_TYPE_DIMENSIONS.get("marketing", TEAM_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['design', 'ui', 'ux']):
        return TEAM_TYPE_DIMENSIONS.get("design", TEAM_TYPE_DIMENSIONS["default"])
    
    return TEAM_TYPE_DIMENSIONS["default"]


def get_workflow_dimensions(workflow_name: str, workflow_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific workflow based on its name and metadata.
    """
    name_lower = workflow_name.lower().replace(' ', '_')
    
    if 'execution_coordinator' in name_lower or 'coordinator' in name_lower:
        return WORKFLOW_TYPE_DIMENSIONS.get("execution_coordinator", WORKFLOW_TYPE_DIMENSIONS["default"])
    elif 'audit' in name_lower:
        return WORKFLOW_TYPE_DIMENSIONS.get("audit", WORKFLOW_TYPE_DIMENSIONS["default"])
    elif 'layer' in name_lower:
        return WORKFLOW_TYPE_DIMENSIONS.get("layered", WORKFLOW_TYPE_DIMENSIONS["default"])
    
    return WORKFLOW_TYPE_DIMENSIONS["default"]


def get_service_dimensions(service_name: str, service_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific service based on its name and metadata.
    """
    name_lower = service_name.lower().replace(' ', '_')
    
    if any(kw in name_lower for kw in ['llm', 'model_service']):
        return SERVICE_TYPE_DIMENSIONS.get("llm", SERVICE_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['model', 'model_service']):
        return SERVICE_TYPE_DIMENSIONS.get("model", SERVICE_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['cache']):
        return SERVICE_TYPE_DIMENSIONS.get("cache", SERVICE_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['config']):
        return SERVICE_TYPE_DIMENSIONS.get("config", SERVICE_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['skill']):
        return SERVICE_TYPE_DIMENSIONS.get("skill", SERVICE_TYPE_DIMENSIONS["default"])
    elif any(kw in name_lower for kw in ['metric', 'monitor']):
        return SERVICE_TYPE_DIMENSIONS.get("metrics", SERVICE_TYPE_DIMENSIONS["default"])
    
    return SERVICE_TYPE_DIMENSIONS["default"]


def get_system_module_dimensions(module_name: str, module_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get dimensions for a specific system module based on its name and metadata.
    """
    name_lower = module_name.lower().replace(' ', '_')
    
    if 'llm' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("llm", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'tool' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("tools", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'memory' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("memory", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'prompt' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("prompt", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'execution' in name_lower or 'loop' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("execution_loop", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'state' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("state_management", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'error' in name_lower or 'handling' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("error_handling", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'context' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("context_management", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'cache' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("cache", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'security' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("security", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'monitor' in name_lower or 'metric' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("monitoring", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'rout' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("routing", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'config' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("configuration", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'event' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("event_system", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'skill_registry' in name_lower or 'skill_reg' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("skill_registry", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'gateway' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("gateway", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'mcp' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("mcp_server", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'retrieval' in name_lower or 'retrieve' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("retrieval", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'cost' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("cost_control", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'agent_coordinator' in name_lower or 'coordinator' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("agent_coordinator", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'dependency' in name_lower or 'injection' in name_lower or 'di' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("dependency_injection", SYSTEM_MODULE_DIMENSIONS["default"])
    elif 'storage' in name_lower or 'store' in name_lower:
        return SYSTEM_MODULE_DIMENSIONS.get("storage", SYSTEM_MODULE_DIMENSIONS["default"])
    
    return SYSTEM_MODULE_DIMENSIONS["default"]


def calculate_dimension_scores(
    dimension_config: Dict[str, Any],
    execution_result: Dict[str, Any],
    execution_time: float = 0
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate scores for each dimension based on execution results.
    
    Args:
        dimension_config: Dimension configuration from get_*_dimensions()
        execution_result: Results from executing the entity
        execution_time: Time taken for execution in milliseconds
    
    Returns:
        Dictionary with dimension names as keys and scores as values
    """
    dimensions = dimension_config.get("dimensions", {})
    result = {}
    
    for dim_key, dim_config in dimensions.items():
        score = 0.5  # Default score
        weight = dim_config.get("weight", 0)
        dim_name = dim_config.get("name", dim_key)
        
        # Calculate score based on dimension type
        if dim_key == "accuracy":
            # Check if execution was successful and output is correct
            if execution_result.get('success'):
                if execution_result.get('result'):
                    score = 0.8
                    if execution_result.get('quality_score', 0) > 0.7:
                        score = 1.0
                else:
                    score = 0.3
        
        elif dim_key == "efficiency" or dim_key == "latency" or dim_key == "execution_efficiency":
            # Based on execution time
            if execution_time < 1000:
                score = 1.0
            elif execution_time < 3000:
                score = 0.8
            elif execution_time < 5000:
                score = 0.6
            elif execution_time < 10000:
                score = 0.4
            else:
                score = 0.2
        
        elif dim_key == "error_handling" or dim_key == "stability" or dim_key == "reliability":
            # Check for errors
            if execution_result.get('error'):
                score = 0.2
            elif execution_result.get('success', True):
                score = 0.9
            else:
                score = 0.5
        
        elif dim_key == "functionality" or dim_key == "completeness":
            # Check if there's output
            if execution_result.get('result') or execution_result.get('answer'):
                score = 0.8
                if len(str(execution_result.get('result', ''))) > 10:
                    score = 1.0
            else:
                score = 0.3
        
        elif dim_key == "output_format":
            # Check if output is structured
            result_data = execution_result.get('result', {})
            if isinstance(result_data, dict):
                score = 0.8
                if 'output' in result_data or 'data' in result_data:
                    score = 1.0
            elif isinstance(result_data, str) and result_data:
                score = 0.6
        
        elif dim_key == "coverage" or dim_key == "recall":
            # Check execution trace length
            trace = execution_result.get('execution_trace', [])
            if len(trace) >= 5:
                score = 1.0
            elif len(trace) >= 3:
                score = 0.7
            elif len(trace) >= 1:
                score = 0.5
            else:
                score = 0.3
        
        elif dim_key == "relevance":
            # Check if answer relates to input
            answer = str(execution_result.get('answer', ''))
            query = str(execution_result.get('input', ''))
            if query and answer:
                if query.lower()[:10] in answer.lower() or len(answer) > 20:
                    score = 0.8
                if len(answer) > 50:
                    score = 1.0
            else:
                score = 0.3
        
        elif dim_key == "response_quality" or dim_key == "output_quality" or dim_key == "answer_relevance":
            # Check answer quality
            answer = execution_result.get('answer', '') or execution_result.get('result', {})
            if answer:
                if isinstance(answer, str) and len(answer) > 20:
                    score = 0.8
                if len(str(answer)) > 50:
                    score = 1.0
                if any(c in str(answer) for c in '，。！？.!?') and len(str(answer)) > 30:
                    score = min(score + 0.1, 1.0)
            else:
                score = 0.3
        
        elif dim_key == "node_execution":
            # Check execution trace
            trace = execution_result.get('execution_trace', [])
            completed = sum(1 for t in trace if t.get('status') == 'completed')
            if completed >= len(trace) * 0.8:
                score = 1.0
            elif completed >= len(trace) * 0.5:
                score = 0.7
            else:
                score = 0.4
        
        elif dim_key == "flow_control" or dim_key == "langgraph_generation":
            # Check if langgraph diagram exists
            if execution_result.get('langgraph_workflow_diagram') or execution_result.get('langgraph_diagram'):
                score = 1.0
            else:
                score = 0.5
        
        elif dim_key == "availability":
            # Check if service responded
            if execution_result.get('success') and not execution_result.get('error'):
                score = 1.0
            elif execution_result.get('error'):
                score = 0.2
            else:
                score = 0.6
        
        else:
            # Default: check if there's any result
            if execution_result.get('result') or execution_result.get('answer') or execution_result.get('success'):
                score = 0.7
                if execution_result.get('success'):
                    score = 0.9
        
        result[dim_key] = {
            "score": score,
            "name": dim_name,
            "weight": weight,
            "test": dim_config.get("test", "")
        }
    
    return result


def calculate_overall_score(dimensions: Dict[str, Dict[str, Any]]) -> int:
    """
    Calculate weighted overall score from dimensions.
    """
    total_weight = 0
    weighted_sum = 0
    
    for dim_key, dim_data in dimensions.items():
        weight = dim_data.get("weight", 0)
        score = dim_data.get("score", 0.5)
        
        weighted_sum += score * weight
        total_weight += weight
    
    if total_weight > 0:
        return int((weighted_sum / total_weight) * 100)
    return 50


def generate_suggestions(dimensions: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate improvement suggestions based on dimension scores.
    """
    suggestions = []
    
    for dim_key, dim_data in dimensions.items():
        score = dim_data.get("score", 0)
        dim_name = dim_data.get("name", dim_key)
        
        if score < 0.8:
            issue = ""
            suggestion = ""
            
            if score < 0.3:
                issue = "严重不足"
                suggestion = f"需要重点改进 {dim_name} 能力"
            elif score < 0.5:
                issue = "不足"
                suggestion = f"建议优化 {dim_name} 实现"
            elif score < 0.8:
                issue = "可改进"
                suggestion = f"{dim_name} 可以进一步提升"
            
            suggestions.append({
                "dimension": dim_name,
                "dimension_key": dim_key,
                "score": score,
                "issue": issue,
                "suggestion": suggestion
            })
    
    # Sort by score (lowest first)
    suggestions.sort(key=lambda x: x["score"])
    
    return suggestions
