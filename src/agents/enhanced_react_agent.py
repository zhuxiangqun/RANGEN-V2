#!/usr/bin/env python3
"""
Enhanced ReAct Agent with Autonomous Decision Making
增强版ReAct Agent - 集成自主决策引擎
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.agents.react_agent import ReActAgent, Action
from src.core.context_engineering.autonomous_decision import (
    AutonomousDecisionEngine, 
    DecisionType,
    Decision
)


@dataclass
class EnhancedReActConfig:
    """增强版ReAct配置"""
    enable_autonomous_decision: bool = True
    confidence_threshold: float = 0.8
    max_iterations: int = 10
    enable_self_reflection: bool = True
    reflection_threshold: float = 0.7


class EnhancedReActAgent(ReActAgent):
    """
    增强版ReAct Agent
    
    在原有ReAct能力基础上，增加：
    1. 自主决策引擎 - 自动决定下一步行动
    2. 自我反思机制 - 评估答案质量
    3. 信心度追踪 - 动态判断是否继续
    """
    
    def __init__(
        self, 
        agent_name: str = "EnhancedReActAgent",
        enhanced_config: Optional[EnhancedReActConfig] = None
    ):
        # 调用父类初始化
        super().__init__(agent_name=agent_name)
        
        # 初始化配置
        self.enhanced_config = enhanced_config or EnhancedReActConfig()
        
        # 初始化自主决策引擎
        if self.enhanced_config.enable_autonomous_decision:
            self.decision_engine = AutonomousDecisionEngine(
                max_iterations=self.enhanced_config.max_iterations,
                confidence_threshold=self.enhanced_config.confidence_threshold
            )
        else:
            self.decision_engine = None
        
        # 自我反思历史
        self.reflection_history: List[Dict[str, Any]] = []
        
        # 当前信心度
        self.current_confidence: float = 0.0
        
        self.logger.info(f"✅ EnhancedReActAgent 初始化完成: {agent_name}")
    
    async def _make_autonomous_decision(
        self,
        query: str,
        current_context: str,
        last_result: Optional[str] = None
    ) -> Decision:
        """使用自主决策引擎做出决策"""
        if not self.decision_engine:
            return Decision(
                decision_type=DecisionType.EXECUTE,
                confidence=0.5,
                reasoning="使用默认决策",
                suggested_action="continue"
            )
        
        available_tools = [t["name"] for t in self.tool_registry.list_tools()]
        
        decision = self.decision_engine.analyze_and_decide(
            query=query,
            current_context=current_context,
            last_tool_result=last_result,
            available_tools=available_tools
        )
        
        self.current_confidence = decision.confidence
        return decision
    
    def should_continue(self, iteration: int) -> bool:
        """判断是否应该继续循环"""
        if self.decision_engine:
            return self.decision_engine.should_continue(
                confidence=self.current_confidence,
                iteration=iteration
            )
        
        return iteration < self.enhanced_config.max_iterations
    
    async def _self_reflect(
        self,
        current_result: str,
        query: str
    ) -> Dict[str, Any]:
        """自我反思 - 评估当前答案质量"""
        if not self.enhanced_config.enable_self_reflection:
            return {"needs_improvement": False, "confidence": 1.0}
        
        reflection = {
            "query": query,
            "result": current_result[:500],
            "needs_improvement": False,
            "confidence": 0.8,
            "suggestions": []
        }
        
        # 检查答案长度
        if len(current_result) < 50:
            reflection["needs_improvement"] = True
            reflection["suggestions"].append("答案过短，可能不完整")
            reflection["confidence"] *= 0.5
        
        # 检查关键词
        query_keywords = query.split()[:5]
        missing_keywords = [k for k in query_keywords if k.lower() not in current_result.lower()]
        if missing_keywords:
            reflection["needs_improvement"] = True
            reflection["suggestions"].append(f"可能缺少关键词: {missing_keywords[:3]}")
            reflection["confidence"] *= 0.7
        
        self.current_confidence = reflection["confidence"]
        self.reflection_history.append(reflection)
        
        return reflection


# 便捷函数
def create_enhanced_react_agent(
    agent_name: str = "EnhancedReActAgent",
    enable_autonomous_decision: bool = True,
    enable_self_reflection: bool = True,
    confidence_threshold: float = 0.8,
    max_iterations: int = 10
) -> EnhancedReActAgent:
    """创建增强版ReAct Agent的便捷函数"""
    config = EnhancedReActConfig(
        enable_autonomous_decision=enable_autonomous_decision,
        enable_self_reflection=enable_self_reflection,
        confidence_threshold=confidence_threshold,
        max_iterations=max_iterations
    )
    return EnhancedReActAgent(agent_name=agent_name, enhanced_config=config)
