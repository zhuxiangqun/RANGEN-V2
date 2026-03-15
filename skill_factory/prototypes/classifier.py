"""
Skill Factory 原型分类器

基于决策树自动将AI技能分类到五大原型之一：
1. workflow - 工作流原型：有序的流程化操作
2. expert - 专家原型：具备深厚的领域知识和决策树
3. coordinator - 协调者原型：问题分类和任务分配
4. quality_gate - 质量门槛原型：验证和拦截作用
5. mcp_integration - MCP集成原型：工具服务器调用和管理
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from src.core.llm_integration import LLMIntegration
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告: 无法导入LLMIntegration，将使用简化分类模式")


class PrototypeType(Enum):
    """五大技能原型类型"""
    WORKFLOW = "workflow"
    EXPERT = "expert"
    COORDINATOR = "coordinator"
    QUALITY_GATE = "quality_gate"
    MCP_INTEGRATION = "mcp_integration"


@dataclass
class ClassificationResult:
    """分类结果"""
    prototype: PrototypeType
    confidence: float
    decision_path: List[str] = field(default_factory=list)
    reasoning: str = ""
    template_suggestions: List[str] = field(default_factory=list)


class SkillPrototypeClassifier:
    """技能原型分类器
    
    使用决策树和LLM辅助将技能分类到五大原型之一。
    """
    
    # 决策树问题定义
    DECISION_TREE = [
        {
            "id": "q1",
            "text": "这个技能是否包含明确的、有序的工作流程阶段，每个阶段有明确的输入、处理和输出？",
            "yes_prototype": PrototypeType.WORKFLOW,
            "no_next": "q2"
        },
        {
            "id": "q2",
            "text": "这个技能是否需要深厚的领域专业知识，能够基于知识库进行复杂决策？",
            "yes_prototype": PrototypeType.EXPERT,
            "no_next": "q3"
        },
        {
            "id": "q3",
            "text": "这个技能的主要功能是否是对问题进行分类，并将子任务分配给其他专业技能？",
            "yes_prototype": PrototypeType.COORDINATOR,
            "no_next": "q4"
        },
        {
            "id": "q4",
            "text": "这个技能是否主要用于验证、检查或拦截，确保工作质量或安全性？",
            "yes_prototype": PrototypeType.QUALITY_GATE,
            "no_next": "q5"
        },
        {
            "id": "q5",
            "text": "这个技能是否主要涉及调用外部工具、API或MCP服务器，并管理这些调用？",
            "yes_prototype": PrototypeType.MCP_INTEGRATION,
            "no_next": "fallback"
        }
    ]
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化分类器
        
        Args:
            llm_config: LLM配置，如果为None则使用简化模式
        """
        self.llm_integration = None
        self.use_llm = False
        
        if LLM_AVAILABLE and llm_config:
            try:
                self.llm_integration = LLMIntegration(llm_config)
                self.use_llm = True
                print("✅ LLM集成已启用，使用智能分类模式")
            except Exception as e:
                print(f"⚠️ LLM集成失败，使用简化模式: {e}")
                self.use_llm = False
    
    def classify(self, skill_description: str, skill_requirements: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """分类技能到原型
        
        Args:
            skill_description: 技能描述文本
            skill_requirements: 技能需求字典（可选）
            
        Returns:
            ClassificationResult: 分类结果
        """
        if self.use_llm and self.llm_integration:
            # 使用LLM辅助的智能分类
            return self._classify_with_llm(skill_description, skill_requirements)
        else:
            # 使用基于规则的简化分类
            return self._classify_simple(skill_description)
    
    def _classify_with_llm(self, skill_description: str, requirements: Optional[Dict[str, Any]]) -> ClassificationResult:
        """使用LLM进行智能分类"""
        decision_path = []
        reasoning_parts = []
        
        for question in self.DECISION_TREE:
            # 使用LLM回答问题
            llm_prompt = f"""
            技能描述: {skill_description}
            
            需求: {json.dumps(requirements, ensure_ascii=False) if requirements else "无"}
            
            问题: {question['text']}
            
            请只回答 'yes' 或 'no'，并简要说明理由（用|分隔）。
            
            示例: yes|这个技能确实包含明确的工作流程阶段
            """
            
            try:
                response = self.llm_integration.call_llm(llm_prompt, max_tokens=100)
                if response:
                    parts = response.split("|", 1)
                    answer = parts[0].strip().lower()
                    reason = parts[1].strip() if len(parts) > 1 else ""
                    
                    decision_path.append(f"问题: {question['text']}")
                    decision_path.append(f"回答: {answer}")
                    reasoning_parts.append(reason)
                    
                    if answer == 'yes' and 'yes_prototype' in question:
                        return ClassificationResult(
                            prototype=question['yes_prototype'],
                            confidence=0.85,
                            decision_path=decision_path,
                            reasoning="; ".join(reasoning_parts),
                            template_suggestions=self._get_template_suggestions(question['yes_prototype'])
                        )
                else:
                    # LLM响应失败，继续下一个问题
                    decision_path.append(f"问题: {question['text']} [LLM响应失败]")
                    continue
                    
            except Exception as e:
                decision_path.append(f"问题: {question['text']} [错误: {str(e)}]")
                continue
        
        # 如果所有问题都回答no或失败，使用专家原型作为默认
        return ClassificationResult(
            prototype=PrototypeType.EXPERT,
            confidence=0.7,
            decision_path=decision_path,
            reasoning="默认使用专家原型",
            template_suggestions=self._get_template_suggestions(PrototypeType.EXPERT)
        )
    
    def _classify_simple(self, skill_description: str) -> ClassificationResult:
        """使用简化规则分类"""
        description_lower = skill_description.lower()
        decision_path = []
        
        # 关键词匹配
        workflow_keywords = ["流程", "阶段", "步骤", "顺序", "pipeline", "workflow", "阶段化"]
        expert_keywords = ["专家", "知识", "领域", "决策", "专业", "expert", "knowledge", "domain"]
        coordinator_keywords = ["协调", "分配", "调度", "分类", "router", "coordinator", "分配"]
        quality_keywords = ["验证", "检查", "质量", "安全", "拦截", "quality", "validation", "gate"]
        mcp_keywords = ["工具", "api", "mcp", "调用", "外部", "服务器", "tool", "api", "mcp"]
        
        # 检查关键词
        for keywords, prototype, name in [
            (workflow_keywords, PrototypeType.WORKFLOW, "工作流原型"),
            (expert_keywords, PrototypeType.EXPERT, "专家原型"),
            (coordinator_keywords, PrototypeType.COORDINATOR, "协调者原型"),
            (quality_keywords, PrototypeType.QUALITY_GATE, "质量门槛原型"),
            (mcp_keywords, PrototypeType.MCP_INTEGRATION, "MCP集成原型")
        ]:
            matched = any(keyword in description_lower for keyword in keywords)
            if matched:
                decision_path.append(f"关键词匹配: {name}")
                return ClassificationResult(
                    prototype=prototype,
                    confidence=0.75,
                    decision_path=decision_path,
                    reasoning=f"检测到{name}相关关键词",
                    template_suggestions=self._get_template_suggestions(prototype)
                )
        
        # 默认使用专家原型
        decision_path.append("无匹配关键词，使用默认原型")
        return ClassificationResult(
            prototype=PrototypeType.EXPERT,
            confidence=0.6,
            decision_path=decision_path,
            reasoning="默认使用专家原型",
            template_suggestions=self._get_template_suggestions(PrototypeType.EXPERT)
        )
    
    def _get_template_suggestions(self, prototype: PrototypeType) -> List[str]:
        """获取模板建议"""
        suggestions = {
            PrototypeType.WORKFLOW: [
                "workflow_template.yaml",
                "phase_based_template.yaml",
                "pipeline_template.yaml"
            ],
            PrototypeType.EXPERT: [
                "expert_template.yaml",
                "knowledge_based_template.yaml",
                "decision_tree_template.yaml"
            ],
            PrototypeType.COORDINATOR: [
                "coordinator_template.yaml",
                "router_template.yaml",
                "dispatcher_template.yaml"
            ],
            PrototypeType.QUALITY_GATE: [
                "quality_gate_template.yaml",
                "validation_template.yaml",
                "checkpoint_template.yaml"
            ],
            PrototypeType.MCP_INTEGRATION: [
                "mcp_integration_template.yaml",
                "tool_management_template.yaml",
                "api_coordinator_template.yaml"
            ]
        }
        return suggestions.get(prototype, ["generic_template.yaml"])
    
    def get_prototype_info(self, prototype_type: PrototypeType) -> Dict[str, Any]:
        """获取原型详细信息"""
        info_map = {
            PrototypeType.WORKFLOW: {
                "name": "工作流原型",
                "description": "有序的流程化操作，包含明确的阶段和门槛",
                "use_cases": ["部署检查清单", "功能生命周期管理", "审批流程"],
                "characteristics": ["阶段化", "顺序性", "门槛检查", "状态追踪"]
            },
            PrototypeType.EXPERT: {
                "name": "专家原型",
                "description": "具备深厚的领域知识和决策树",
                "use_cases": ["HTTP模式", "断路器", "指标分析", "安全评估"],
                "characteristics": ["知识驱动", "决策树", "专业判断", "领域特定"]
            },
            PrototypeType.COORDINATOR: {
                "name": "协调者原型",
                "description": "能够对问题进行分类，并将任务分配给对应的专业技能",
                "use_cases": ["智能路由", "任务分发", "多技能协调"],
                "characteristics": ["分类能力", "调度逻辑", "资源分配", "任务委派"]
            },
            PrototypeType.QUALITY_GATE: {
                "name": "质量门槛原型",
                "description": "起到'拦截作用'，在工作推进前进行验证",
                "use_cases": ["代码审查", "安全扫描", "架构验证", "合规检查"],
                "characteristics": ["验证逻辑", "拦截机制", "质量标准", "检查点"]
            },
            PrototypeType.MCP_INTEGRATION: {
                "name": "MCP集成原型",
                "description": "教会AI Agent使用工具服务器，明确调用顺序和错误处理",
                "use_cases": ["工具调用", "API集成", "外部服务协调"],
                "characteristics": ["工具管理", "协议适配", "错误处理", "结果解析"]
            }
        }
        return info_map.get(prototype_type, {})


# 快速使用示例
if __name__ == "__main__":
    classifier = SkillPrototypeClassifier()
    
    # 测试用例
    test_cases = [
        "创建一个代码审查工具，需要检查代码质量、安全漏洞和性能问题",
        "开发一个智能路由系统，根据问题类型选择最合适的处理Agent",
        "实现一个部署流水线，包含构建、测试、部署和验证阶段",
        "创建一个金融分析专家，能够分析股票数据和提供投资建议",
        "开发一个MCP服务器管理器，协调多个外部工具的调用"
    ]
    
    for i, description in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {description}")
        result = classifier.classify(description)
        info = classifier.get_prototype_info(result.prototype)
        print(f"  分类结果: {info['name']}")
        print(f"  置信度: {result.confidence}")
        print(f"  模板建议: {', '.join(result.template_suggestions)}")
        print(f"  推理: {result.reasoning[:100]}...")