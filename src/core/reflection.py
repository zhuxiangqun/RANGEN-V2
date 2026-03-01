#!/usr/bin/env python3
"""
Reflection 反思机制
让Agent能够自我批评和持续改进
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReflectionType(str, Enum):
    """反思类型"""
    SUCCESS = "success"           # 成功反思
    FAILURE = "failure"          # 失败反思
    PARTIAL = "partial"         # 部分成功
    IMPROVEMENT = "improvement"  # 改进建议


@dataclass
class ReflectionResult:
    """反思结果"""
    reflection_type: ReflectionType
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    improved_output: Any = None
    confidence: float = 0.0
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflection_type": self.reflection_type.value,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "improved_output": self.improved_output,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


class ReflectionPrompt:
    """反思提示模板"""
    
    @staticmethod
    def generate_critical_prompt(task: str, output: Any, context: Dict) -> str:
        """生成批评性反思提示"""
        return f"""
你是一个严格的代码审查员。请分析以下任务执行结果，找出所有问题。

任务: {task}

执行输出:
{json.dumps(output, indent=2, ensure_ascii=False, default=str)}

上下文:
{json.dumps(context, indent=2, ensure_ascii=False)}

请分析并输出JSON格式的反思结果:
{{
    "issues": ["问题1", "问题2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "reflection_type": "failure|partial|success",
    "confidence": 0.0-1.0,
    "reasoning": "你的推理过程"
}}

只输出JSON，不要其他内容。
"""

    @staticmethod
    def generate_improvement_prompt(task: str, output: Any, issues: List[str]) -> str:
        """生成改进提示"""
        return f"""
任务: {task}

当前输出:
{json.dumps(output, indent=2, ensure_ascii=False, default=str)}

发现的问题:
{chr(10).join(f"- {issue}" for issue in issues)}

请根据上述问题，生成改进后的输出。
只输出改进后的内容，不要解释。
"""


class ReflectionAgent:
    """反思型Agent
    
    让AI能够:
    1. 分析自己输出的问题
    2. 提出改进建议
    3. 生成改进后的版本
    """
    
    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.reflection_history: List[ReflectionResult] = []
        
        logger.info("Reflection Agent initialized")
    
    async def reflect(
        self, 
        task: str, 
        output: Any, 
        context: Optional[Dict] = None
    ) -> ReflectionResult:
        """执行反思
        
        Args:
            task: 任务描述
            output: 执行输出
            context: 上下文信息
            
        Returns:
            反思结果
        """
        ctx = context or {}
        
        # 生成反思提示
        prompt = ReflectionPrompt.generate_critical_prompt(task, output, ctx)
        
        # 如果有LLM提供者，使用它
        if self.llm_provider:
            try:
                result = await self.llm_provider.generate(prompt)
                reflection = self._parse_reflection(result)
            except Exception as e:
                logger.warning(f"LLM reflection failed: {e}")
                reflection = self._basic_reflect(task, output, ctx)
        else:
            # 基础反思（无LLM）
            reflection = self._basic_reflect(task, output, ctx)
        
        # 保存到历史
        self.reflection_history.append(reflection)
        
        # 记录日志
        logger.info(
            f"Reflection: {reflection.reflection_type.value} "
            f"({len(reflection.issues)} issues, "
            f"{len(reflection.suggestions)} suggestions)"
        )
        
        return reflection
    
    def _basic_reflect(
        self, 
        task: str, 
        output: Any, 
        context: Dict
    ) -> ReflectionResult:
        """基础反思（无LLM）"""
        
        issues = []
        suggestions = []
        reflection_type = ReflectionType.SUCCESS
        confidence = 0.5
        
        # 检查输出类型
        if output is None:
            issues.append("输出为空")
            reflection_type = ReflectionType.FAILURE
            confidence = 0.9
        
        # 检查错误
        if isinstance(output, dict):
            if output.get("error"):
                issues.append(f"执行出错: {output.get('error')}")
                reflection_type = ReflectionType.FAILURE
                confidence = 0.9
            elif not output.get("success", True):
                issues.append("执行未成功")
                reflection_type = ReflectionType.PARTIAL
                confidence = 0.7
        
        # 生成建议
        if issues:
            suggestions.append("检查任务分解是否正确")
            suggestions.append("验证工具调用参数")
        
        return ReflectionResult(
            reflection_type=reflection_type,
            issues=issues,
            suggestions=suggestions,
            confidence=confidence,
            reasoning="Basic reflection without LLM"
        )
    
    def _parse_reflection(self, llm_output: str) -> ReflectionResult:
        """解析LLM输出的反思结果"""
        try:
            # 尝试解析JSON
            data = json.loads(llm_output)
            
            return ReflectionResult(
                reflection_type=ReflectionType(data.get("reflection_type", "partial")),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                improved_output=data.get("improved_output"),
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", "")
            )
        except json.JSONDecodeError:
            # JSON解析失败，使用基础反思
            return self._basic_reflect("unknown", llm_output, {})
    
    async def improve(
        self, 
        task: str, 
        output: Any, 
        issues: List[str]
    ) -> Any:
        """根据问题改进输出
        
        Args:
            task: 任务
            output: 原始输出
            issues: 发现的问题
            
        Returns:
            改进后的输出
        """
        prompt = ReflectionPrompt.generate_improvement_prompt(task, output, issues)
        
        if self.llm_provider:
            try:
                improved = await self.llm_provider.generate(prompt)
                return improved
            except Exception as e:
                logger.warning(f"LLM improvement failed: {e}")
        
        # 无LLM时返回原始输出
        return output
    
    async def iterative_reflect(
        self, 
        task: str, 
        output: Any, 
        context: Optional[Dict] = None,
        max_iterations: int = 3
    ) -> ReflectionResult:
        """迭代反思
        
        多次反思直到收敛或达到最大次数
        """
        current_output = output
        current_issues = []
        
        for i in range(max_iterations):
            # 执行反思
            reflection = await self.reflect(task, current_output, context)
            
            # 如果成功或无问题，停止
            if reflection.reflection_type == ReflectionType.SUCCESS:
                return reflection
            
            # 如果没有新问题，停止
            new_issues = set(reflection.issues) - set(current_issues)
            if not new_issues:
                return reflection
            
            current_issues.extend(new_issues)
            
            # 尝试改进
            current_output = await self.improve(
                task, current_output, reflection.issues
            )
        
        # 达到最大迭代次数
        return ReflectionResult(
            reflection_type=ReflectionType.PARTIAL,
            issues=current_issues,
            suggestions=["需要更多迭代或人工介入"],
            confidence=0.3,
            reasoning=f"Max iterations ({max_iterations}) reached"
        )
    
    def get_history(self) -> List[ReflectionResult]:
        """获取反思历史"""
        return self.reflection_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取反思统计"""
        if not self.reflection_history:
            return {"total": 0}
        
        type_counts = {}
        total_issues = 0
        total_suggestions = 0
        
        for r in self.reflection_history:
            t = r.reflection_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
            total_issues += len(r.issues)
            total_suggestions += len(r.suggestions)
        
        return {
            "total": len(self.reflection_history),
            "by_type": type_counts,
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "avg_confidence": sum(r.confidence for r in self.reflection_history) / len(self.reflection_history)
        }


class ReflexionAgent(ReflectionAgent):
    """Reflexion Agent - 结构化反思
    
    相比基础Reflection，Reflexion:
    - 在可追踪的日志中记录历史
    - 记录假设和推理过程
    - 适合从多次失败中学习
    """
    
    def __init__(self, llm_provider=None):
        super().__init__(llm_provider)
        
        # Reflexion特有的: 行为日志
        self.behavior_log: List[Dict[str, Any]] = []
        self.hypotheses: List[str] = []
        
        logger.info("Reflexion Agent initialized")
    
    async def reflect_with_trace(
        self, 
        task: str, 
        action: str,
        result: Any,
        context: Optional[Dict] = None
    ) -> ReflectionResult:
        """带追踪的反思
        
        记录每个行为和结果，用于后续分析
        """
        # 记录行为
        trace_entry = {
            "task": task,
            "action": action,
            "result": result,
            "context": context
        }
        self.behavior_log.append(trace_entry)
        
        # 执行反思
        reflection = await self.reflect(task, result, context)
        
        # 如果反思发现问题，记录假设
        if reflection.issues:
            hypothesis = self._generate_hypothesis(task, action, reflection.issues)
            self.hypotheses.append(hypothesis)
        
        return reflection
    
    def _generate_hypothesis(
        self, 
        task: str, 
        action: str, 
        issues: List[str]
    ) -> str:
        """生成假设"""
        return f"Task '{task}' with action '{action}' failed due to: {', '.join(issues)}"
    
    def get_behavior_log(self) -> List[Dict[str, Any]]:
        """获取行为日志"""
        return self.behavior_log
    
    def get_hypotheses(self) -> List[str]:
        """获取假设列表"""
        return self.hypotheses
    
    def analyze_failures(self) -> Dict[str, Any]:
        """分析失败模式"""
        if not self.behavior_log:
            return {"total_actions": 0}
        
        # 统计失败
        failures = []
        for entry in self.behavior_log:
            result = entry.get("result", {})
            if isinstance(result, dict) and not result.get("success", True):
                failures.append({
                    "task": entry.get("task"),
                    "action": entry.get("action"),
                    "error": result.get("error")
                })
        
        return {
            "total_actions": len(self.behavior_log),
            "failure_count": len(failures),
            "failure_rate": len(failures) / len(self.behavior_log) if self.behavior_log else 0,
            "failures": failures,
            "hypotheses": self.hypotheses
        }


# 便捷函数
def create_reflection_agent(llm_provider=None) -> ReflectionAgent:
    """创建反思Agent"""
    return ReflectionAgent(llm_provider)


def create_reflexion_agent(llm_provider=None) -> ReflexionAgent:
    """创建Reflexion Agent"""
    return ReflexionAgent(llm_provider)
