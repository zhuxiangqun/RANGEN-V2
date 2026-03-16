#!/usr/bin/env python3
"""
Enhanced Validation Agent with Review Pipeline Integration

将 ReviewPipeline 集成到 ValidationAgent:
- 执行验证后自动进行 L2 评审
- 基于评审结果决定是否需要重试
- 记录判断历史用于评价
"""
import time
import os
import json
import re
from typing import Dict, Any, Optional

from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger
from src.core.llm_integration import LLMIntegration
from src.prompts.validation.verify import VALIDATION_SYSTEM_PROMPT, VALIDATION_USER_PROMPT


logger = get_logger(__name__)


class ReviewableValidationAgent(IAgent):
    """
    支持评审的验证 Agent
    
    集成 ReviewPipeline，实现：
    - 验证后自动评审
    - 基于评审结果决策
    - 判断力记录
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, enable_review: bool = True):
        if config is None:
            config = AgentConfig(
                name="validation_agent",
                description="Validates claims and checks for hallucinations",
                version="2.0.0"
            )
        super().__init__(config)
        
        # LLM 配置
        llm_config = {
            "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": os.getenv("VALIDATION_MODEL", "deepseek-chat"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        }
        self.llm = LLMIntegration(llm_config)
        
        # 评审配置
        self.enable_review = enable_review
        self._review_results = []
        
        logger.info(f"ReviewableValidationAgent initialized: {self.config.name}")
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        if "claim" not in inputs and "answer" not in inputs:
            logger.error("Input validation failed: 'claim' or 'answer' is required")
            return False
        return True
    
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """
        执行验证 + 评审
        """
        start_time = time.time()
        
        # Step 1: 验证
        validation_result = await self._run_validation(inputs)
        
        # Step 2: 评审 (如果启用)
        review_result = None
        if self.enable_review:
            review_result = await self._run_review(validation_result, context)
            
            # Step 3: 基于评审结果决策
            decision = self._make_decision(review_result)
            
            # 记录判断
            self._record_judgment(validation_result, review_result, decision)
            
            # 如果评审不通过，返回修改建议
            if decision == "revise" or decision == "block":
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.NEEDS_REVISION,
                    output={
                        "validation": validation_result,
                        "review": review_result,
                        "decision": decision,
                        "suggestions": self._get_suggestions(review_result)
                    },
                    execution_time=time.time() - start_time,
                    metadata={"review_passed": False}
                )
        
        execution_time = time.time() - start_time
        
        return AgentResult(
            agent_name=self.config.name,
            status=ExecutionStatus.COMPLETED,
            output={
                "validation": validation_result,
                "review": review_result,
                "decision": "proceed" if review_result else "direct"
            },
            execution_time=execution_time,
            metadata={"review_passed": True if review_result else None}
        )
    
    async def _run_validation(self, inputs: Dict[str, Any]) -> Dict:
        """执行验证"""
        target = inputs.get("claim") or inputs.get("answer")
        evidence = inputs.get("evidence", [])
        evidence_str = "\n".join([f"- {e}" for e in evidence]) if evidence else "No explicit evidence provided."
        
        prompt = f"{VALIDATION_SYSTEM_PROMPT}\n\n{VALIDATION_USER_PROMPT.format(claim=target, evidence=evidence_str)}"
        
        logger.info(f"Validating: {target[:50]}...")
        response = self.llm._call_llm(prompt)
        
        result = {
            "is_valid": False,
            "confidence": 0.0,
            "reasoning": "Failed to parse",
            "status": "error"
        }
        
        if response:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    result["reasoning"] = response
            else:
                result["reasoning"] = response
        
        return result
    
    async def _run_review(self, validation_result: Dict, context: Optional[Dict]) -> Dict:
        """执行评审"""
        try:
            from src.core.review_pipeline import ReviewPipeline, ReviewLevel
            from src.core.review_integration import ReviewDecisionMaker
            
            pipeline = ReviewPipeline(name="validation_review")
            
            # 准备评审内容
            artifact_content = {
                "validation_result": validation_result,
                "claim": context.get("claim") if context else ""
            }
            
            # 执行 L2 评审
            report = await pipeline.review(
                artifact_name="validation_result",
                artifact_content=artifact_content,
                level=ReviewLevel.L2_PEER,
                intent_statement=context.get("intent", "") if context else "验证声明准确性",
                context=context or {}
            )
            
            # 转换为简化格式
            return {
                "score": report.score,
                "result": report.result.value,
                "findings": [
                    {
                        "category": f.category,
                        "message": f.message,
                        "blocking": f.blocking
                    }
                    for f in report.findings
                ],
                "decision": ReviewDecisionMaker.decide(report.to_dict())
            }
            
        except ImportError:
            logger.warning("Review pipeline not available, skipping review")
            return None
    
    def _make_decision(self, review_result: Dict) -> str:
        """基于评审结果做决策"""
        if not review_result:
            return "proceed"
        
        from src.core.review_integration import ReviewDecisionMaker
        return ReviewDecisionMaker.decide(review_result)
    
    def _record_judgment(self, validation_result: Dict, review_result: Dict, decision: str):
        """记录判断用于评价"""
        try:
            from src.core.judgment_evaluation import JudgmentEvaluationSystem, JudgmentType
            
            # 简单的内存记录
            self._review_results.append({
                "validation": validation_result,
                "review": review_result,
                "decision": decision,
                "timestamp": time.time()
            })
            
        except ImportError:
            pass
    
    def _get_suggestions(self, review_result: Dict) -> list:
        """获取修改建议"""
        if not review_result or not review_result.get("findings"):
            return []
        
        suggestions = []
        for finding in review_result["findings"]:
            if finding.get("suggestion"):
                suggestions.append(finding["suggestion"])
            elif finding.get("message"):
                suggestions.append(finding["message"])
        
        return suggestions
    
    def get_review_stats(self) -> Dict:
        """获取评审统计"""
        if not self._review_results:
            return {"total": 0}
        
        total = len(self._review_results)
        passed = sum(1 for r in self._review_results if r["decision"] == "proceed")
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0
        }


def create_reviewable_validation_agent(enable_review: bool = True) -> ReviewableValidationAgent:
    """创建支持评审的验证 Agent"""
    return ReviewableValidationAgent(enable_review=enable_review)
