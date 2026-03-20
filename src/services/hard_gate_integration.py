"""
HARD-GATE 集成到 RANGEN 主工作流
=================================

此模块将 HARD-GATE 设计优先门控集成到 RANGEN 的实体创建流程中。

集成点:
- UnifiedCreator.create_from_natural_language() → 设计优先流程
- 实体创建前必须先完成设计审查

流程:
1. 用户请求创建实体 (Agent/Skill/Tool)
2. HARD-GATE 检查是否需要设计
3. 如果需要:
   a. 需求发现 (RequirementDiscovery)
   b. AI 设计生成 (AIDesignGenerator)
   c. 设计审查 (ComponentDesignReview)
   d. 批准/拒绝 (Approval)
4. 批准后执行实际创建
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DesignRequired(Enum):
    """设计需求级别"""
    NOT_REQUIRED = "not_required"      # 不需要设计，直接创建
    REQUIRED = "required"              # 需要设计
    EXISTING_OK = "existing_ok"        # 现有实体已满足需求


@dataclass
class DesignGateResult:
    """HARD-GATE 检查结果"""
    design_required: DesignRequired
    design_id: Optional[str] = None
    design_status: Optional[str] = None  # pending, approved, rejected
    entity_type: Optional[str] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class HardGateIntegration:
    """
    HARD-GATE 与 RANGEN 主工作流的集成
    
    在实体创建流程中嵌入设计优先门控。
    """
    
    def __init__(self):
        self._enabled = True  # 可通过配置禁用
        self._auto_approve_threshold = 0.9  # 高置信度自动批准
    
    def is_enabled(self) -> bool:
        """检查 HARD-GATE 是否启用"""
        import os
        return os.getenv("RANGEN_HARD_GATE_ENABLED", "true").lower() in ("1", "true", "yes")
    
    async def check_design_required(
        self,
        description: str,
        entity_type: str
    ) -> DesignGateResult:
        """
        检查是否需要设计
        
        Args:
            description: 实体描述
            entity_type: 实体类型 (agent/skill/tool)
            
        Returns:
            DesignGateResult: 设计需求检查结果
        """
        if not self.is_enabled():
            return DesignGateResult(
                design_required=DesignRequired.NOT_REQUIRED,
                entity_type=entity_type,
                message="HARD-GATE 已禁用"
            )
        
        try:
            # 检查是否需要设计的逻辑
            simple_patterns = [
                "简单的", "基础的", "basic", "simple",
                "只需要", "只要", "just"
            ]
            
            is_simple = any(p in description.lower() for p in simple_patterns)
            
            # 检查是否已有类似实体
            existing = self._check_existing_entities(entity_type, description)
            if existing and is_simple:
                return DesignGateResult(
                    design_required=DesignRequired.EXISTING_OK,
                    entity_type=entity_type,
                    message=f"现有实体 '{existing}' 可能满足需求",
                    details={"existing_entity": existing}
                )
            
            # Agent 和 Tool 通常需要设计
            if entity_type.lower() in ("agent", "tool"):
                return DesignGateResult(
                    design_required=DesignRequired.REQUIRED,
                    entity_type=entity_type,
                    message="此类型实体需要先完成设计"
                )
            
            # Skill 可以简化处理
            if entity_type.lower() == "skill":
                return DesignGateResult(
                    design_required=DesignRequired.NOT_REQUIRED,
                    entity_type=entity_type,
                    message="Skill 可使用简化流程"
                )
            
            return DesignGateResult(
                design_required=DesignRequired.NOT_REQUIRED,
                entity_type=entity_type,
                message="不需要设计"
            )
            
        except Exception as e:
            logger.error(f"Design required check failed: {e}")
            return DesignGateResult(
                design_required=DesignRequired.NOT_REQUIRED,
                entity_type=entity_type,
                message=f"检查失败，默认跳过设计: {e}"
            )
    
    def _check_existing_entities(self, entity_type: str, description: str) -> Optional[str]:
        """检查是否有现有实体满足需求"""
        # 简化实现：可以根据描述匹配现有实体
        # 实际应该查询数据库或注册表
        return None
    
    async def execute_design_workflow(
        self,
        description: str,
        entity_type: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整的设计工作流
        
        Args:
            description: 实体描述
            entity_type: 实体类型
            requirements: 额外需求
            
        Returns:
            设计工作流结果
        """
        if not self.is_enabled():
            return {
                "success": False,
                "message": "HARD-GATE 已禁用",
                "design_id": None,
                "design": None
            }
        
        try:
            from src.agents.requirement_discovery import RequirementDiscoveryAgent
            from src.agents.ai_design_generator import AIDesignGenerator
            from src.agents.hard_gate import HARD_GATE
            
            # 1. 需求发现
            logger.info(f"Starting requirement discovery for {entity_type}")
            discovery = RequirementDiscoveryAgent()
            discovered = discovery.discover_requirements(description)
            
            requirements_text = "\n".join([
                f"- **{r.title}**: {r.description}"
                for r in discovered.requirements
            ])
            
            # 2. 生成设计
            logger.info(f"Generating design for {entity_type}")
            generator = AIDesignGenerator()
            design = generator.generate_design(requirements_text)
            
            # 3. 提交到 HARD-GATE
            logger.info(f"Submitting design to HARD-GATE")
            gate = HARD_GATE()
            
            # 开始设计阶段并提交设计
            design_spec = gate.start_design_phase(
                title=design.title if hasattr(design, 'title') else "Generated Design",
                description=requirements_text
            )
            
            # 4. 组件设计审查
            from src.agents.component_design_review import ComponentDesignReview
            reviewer = ComponentDesignReview()
            review_result = reviewer.review_design(design, component_type=entity_type.lower())
            
            # 5. 返回结果（等待批准）
            design_id = f"design_{hash(description) % 100000}"
            
            return {
                "success": True,
                "message": "设计已生成，请在 UI 中审查并批准",
                "design_id": design_id,
                "design": design,
                "review_result": review_result,
                "requirements": requirements_text,
                "status": "pending_approval"
            }
            
        except Exception as e:
            logger.error(f"Design workflow failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"设计流程失败: {e}",
                "design_id": None,
                "design": None,
                "error": str(e)
            }
    
    async def approve_design(self, design_id: str, approved_by: str = "api") -> Dict[str, Any]:
        """
        批准设计
        
        Args:
            design_id: 设计ID
            approved_by: 批准者
            
        Returns:
            批准结果
        """
        try:
            from src.agents.hard_gate import HARD_GATE
            
            gate = HARD_GATE()
            success = gate.approve_design(approved_by=approved_by)
            
            if success:
                return {
                    "success": True,
                    "message": "设计已批准",
                    "design_id": design_id
                }
            else:
                return {
                    "success": False,
                    "message": "设计批准失败",
                    "design_id": design_id
                }
                
        except Exception as e:
            logger.error(f"Design approval failed: {e}")
            return {
                "success": False,
                "message": f"批准失败: {e}"
            }
    
    def can_write_code(self) -> Tuple[bool, str]:
        """
        检查是否可以编写代码
        
        Returns:
            (can_write, reason)
        """
        if not self.is_enabled():
            return True, "HARD-GATE disabled"
        
        try:
            from src.agents.hard_gate import HARD_GATE
            
            gate = HARD_GATE()
            status = gate.get_status()
            
            can_write = status.get("can_write", False)
            phase = status.get("phase", "unknown")
            
            if can_write:
                return True, f"HARD-GATE phase: {phase}"
            else:
                return False, f"Design not approved. Current phase: {phase}"
                
        except Exception as e:
            logger.error(f"can_write_code check failed: {e}")
            return False, f"Check failed: {e}"
    
    def get_gate_status(self) -> Dict[str, Any]:
        """
        获取 HARD-GATE 状态
        
        Returns:
            状态字典
        """
        try:
            from src.agents.hard_gate import HARD_GATE
            
            gate = HARD_GATE()
            return gate.get_status()
        except Exception as e:
            logger.error(f"get_gate_status failed: {e}")
            return {}


# Global instance
_hard_gate_integration: Optional[HardGateIntegration] = None


def get_hard_gate_integration() -> HardGateIntegration:
    """获取 HARD-GATE 集成实例"""
    global _hard_gate_integration
    if _hard_gate_integration is None:
        _hard_gate_integration = HardGateIntegration()
    return _hard_gate_integration
