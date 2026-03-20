#!/usr/bin/env python3
"""
Context Passing Protocol - 上下文传递协议

基于文章洞见实现"意图说明"标准化：
- 原型旁边需要附带意图说明
- 临时实现 vs 刻意设计需区分
- 验收标准必须明确
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ContextType(Enum):
    """上下文类型"""
    INTENT = "intent"           # 意图说明
    TEMPORARY = "temporary"     # 临时实现
    DESIGNED = "designed"       # 刻意设计
    ACCEPTANCE = "acceptance"   # 验收标准


class ContextQuality(Enum):
    """上下文质量等级"""
    COMPLETE = "complete"       # 完整
    PARTIAL = "partial"          # 部分
    MISSING = "missing"          # 缺失


@dataclass
class IntentStatement:
    """
    意图说明
    
    回答"为什么做"而非"做什么"
    """
    problem: str                 # 要解决的用户问题
    goal: str                    # 目标
    constraints: List[str] = field(default_factory=list)  # 约束条件
    tradeoffs: List[str] = field(default_factory=list)   # 已知的权衡
    
    def to_dict(self) -> Dict:
        return {
            "problem": self.problem,
            "goal": self.goal,
            "constraints": self.constraints,
            "tradeoffs": self.tradeoffs
        }


@dataclass
class ImplementationNote:
    """
    实现说明
    
    区分临时实现和刻意设计
    """
    is_temporary: bool           # 是否临时
    reason: str                  # 原因
    expected_lifetime: str = ""  # 预期生命周期
    should_be_replaced_by: str = ""  # 应该被什么替换


@dataclass
class AcceptanceCriteria:
    """
    验收标准
    
    明确什么条件下可以接受
    """
    criteria: List[str] = field(default_factory=list)  # 标准列表
    must_have: List[str] = field(default_factory=list)  # 必须有
    nice_to_have: List[str] = field(default_factory=list)  # 最好有
    
    def is_met(self, result: Any) -> bool:
        """检查是否满足验收标准"""
        # 简化实现 - 实际应该根据具体结果判断
        return True
    
    def to_dict(self) -> Dict:
        return {
            "criteria": self.criteria,
            "must_have": self.must_have,
            "nice_to_have": self.nice_to_have
        }


@dataclass
class ArtifactContext:
    """
    产物上下文
    
    完整记录一个产物的上下文信息
    """
    artifact_name: str           # 产物名称
    artifact_type: str           # 产物类型 (code, doc, design, etc.)
    intent: Optional[IntentStatement] = None  # 意图
    implementation_note: Optional[ImplementationNote] = None  # 实现说明
    acceptance: Optional[AcceptanceCriteria] = None  # 验收标准
    
    # 元数据
    created_by: str = ""
    created_at: str = ""
    version: str = "1.0.0"
    
    # 传递历史
    passed_from: List[str] = field(default_factory=list)  # 传递历史
    review_history: List[Dict] = field(default_factory=list)  # 评审历史
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def add_pass(self, agent_name: str):
        """记录传递"""
        self.passed_from.append(agent_name)
    
    def add_review(self, review_result: Dict):
        """添加评审结果"""
        self.review_history.append(review_result)
    
    def to_dict(self) -> Dict:
        return {
            "artifact_name": self.artifact_name,
            "artifact_type": self.artifact_type,
            "intent": self.intent.to_dict() if self.intent else None,
            "implementation_note": {
                "is_temporary": self.implementation_note.is_temporary,
                "reason": self.implementation_note.reason,
                "expected_lifetime": self.implementation_note.expected_lifetime,
                "should_be_replaced_by": self.implementation_note.should_be_replaced_by
            } if self.implementation_note else None,
            "acceptance": self.acceptance.to_dict() if self.acceptance else None,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "version": self.version,
            "passed_from": self.passed_from,
            "review_history": self.review_history
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ContextPassingProtocol:
    """
    上下文传递协议管理器
    
    确保上下文在 Agent 之间传递时完整
    """
    
    @staticmethod
    def create_context(
        artifact_name: str,
        artifact_type: str,
        problem: str,
        goal: str,
        is_temporary: bool = False,
        temp_reason: str = "",
        criteria: List[str] = None
    ) -> ArtifactContext:
        """创建产物上下文"""
        
        intent = IntentStatement(
            problem=problem,
            goal=goal
        )
        
        impl_note = None
        if is_temporary:
            impl_note = ImplementationNote(
                is_temporary=True,
                reason=temp_reason
            )
        
        acceptance = None
        if criteria:
            acceptance = AcceptanceCriteria(criteria=criteria)
        
        return ArtifactContext(
            artifact_name=artifact_name,
            artifact_type=artifact_type,
            intent=intent,
            implementation_note=impl_note,
            acceptance=acceptance
        )
    
    @staticmethod
    def validate_context(context: ArtifactContext) -> ContextQuality:
        """验证上下文完整性"""
        
        # 检查必要字段
        if not context.intent or not context.intent.problem:
            return ContextQuality.MISSING
        
        if not context.intent.goal:
            return ContextQuality.MISSING
        
        # 检查可选字段
        has_acceptance = context.acceptance and context.acceptance.criteria
        has_impl_note = context.implementation_note is not None
        
        if has_acceptance and has_impl_note:
            return ContextQuality.COMPLETE
        elif has_acceptance or has_impl_note:
            return ContextQuality.PARTIAL
        
        return ContextQuality.PARTIAL
    
    @staticmethod
    def format_for_prompt(context: ArtifactContext) -> str:
        """格式化为 Prompt 的一部分"""
        
        parts = []
        
        # 意图说明
        if context.intent:
            parts.append("## 意图说明")
            parts.append(f"**问题**: {context.intent.problem}")
            parts.append(f"**目标**: {context.intent.goal}")
            
            if context.intent.constraints:
                parts.append(f"**约束**: {', '.join(context.intent.constraints)}")
            
            if context.intent.tradeoffs:
                parts.append(f"**权衡**: {', '.join(context.intent.tradeoffs)}")
        
        # 实现说明
        if context.implementation_note:
            parts.append("\n## 实现说明")
            if context.implementation_note.is_temporary:
                parts.append("⚠️ **临时实现** - " + context.implementation_note.reason)
            else:
                parts.append("✅ **刻意设计**")
        
        # 验收标准
        if context.acceptance:
            parts.append("\n## 验收标准")
            for criterion in context.acceptance.criteria:
                parts.append(f"- {criterion}")
        
        # 传递历史
        if context.passed_from:
            parts.append(f"\n**传递路径**: {' → '.join(context.passed_from)}")
        
        return "\n".join(parts)


# === 便捷函数 ===

def create_artifact_context(
    name: str,
    type: str,
    problem: str,
    goal: str,
    is_temp: bool = False,
    criteria: List[str] = None
) -> ArtifactContext:
    """快速创建产物上下文"""
    return ContextPassingProtocol.create_context(
        artifact_name=name,
        artifact_type=type,
        problem=problem,
        goal=goal,
        is_temporary=is_temp,
        criteria=criteria
    )


def validate_and_report(context: ArtifactContext) -> Dict:
    """验证上下文并生成报告"""
    quality = ContextPassingProtocol.validate_context(context)
    
    return {
        "artifact": context.artifact_name,
        "quality": quality.value,
        "has_intent": context.intent is not None,
        "has_acceptance": context.acceptance is not None,
        "has_implementation_note": context.implementation_note is not None,
        "passed_from_count": len(context.passed_from)
    }
