"""
结果处理器模块

从 UnifiedResearchSystem 拆分出来的结果处理功能
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    answer: str
    confidence: float
    reasoning: Optional[str] = None
    observations: Optional[List[Dict[str, Any]]] = None


class ResultProcessor:
    """
    结果处理器
    
    处理和转换:
    - Agent 结果
    - 观察结果
    - 推理过程
    """
    
    def __init__(self):
        # 最小答案长度
        self._min_answer_length = 10
        
        # 置信度阈值
        self._confidence_threshold = 0.5
    
    def _is_task_complete(
        self, 
        thought: str, 
        observations: List[Dict[str, Any]]
    ) -> bool:
        """
        判断任务是否完成
        
        基于思考和观察判断
        """
        # 如果没有观察，任务未完成
        if not observations:
            return False
        
        # 检查最后几个观察
        recent_observations = observations[-3:] if len(observations) > 3 else observations
        
        for obs in recent_observations:
            # 检查是否有错误
            if obs.get("error"):
                return True
            
            # 检查是否有最终答案
            if obs.get("type") == "final_answer":
                return True
            
            # 检查观察内容
            content = str(obs.get("content", ""))
            if any(keyword in content.lower() for keyword in ["完成", "完毕", "final", "complete", "done"]):
                return True
        
        return False
    
    def _generate_result(
        self, 
        observations: List[Dict[str, Any]], 
        thoughts: List[str],
        execution_time: float
    ) -> ProcessingResult:
        """
        从观察和思考生成结果
        """
        # 提取答案
        answer = ""
        confidence = 0.0
        reasoning_steps = []
        
        # 从观察中提取信息
        for obs in observations:
            obs_type = obs.get("type", "")
            content = obs.get("content", "")
            
            if obs_type == "final_answer":
                answer = content
                confidence = obs.get("confidence", 0.8)
            elif obs_type == "reasoning":
                reasoning_steps.append(content)
        
        # 如果没有最终答案，尝试从内容中提取
        if not answer:
            if observations:
                last_obs = observations[-1]
                answer = str(last_obs.get("content", ""))
        
        # 构建推理过程
        reasoning = "\n".join([
            f"Step {i+1}: {step[:200]}..."
            for i, step in enumerate(thoughts[-5:])
        ])
        
        # 计算置信度
        if not confidence:
            confidence = self._calculate_confidence(observations, thoughts)
        
        # 检查答案有效性
        if len(answer) < self._min_answer_length:
            success = False
            confidence = 0.0
        else:
            success = True
        
        return ProcessingResult(
            success=success,
            answer=answer[:5000],  # 限制长度
            confidence=confidence,
            reasoning=reasoning,
            observations=observations,
        )
    
    def _calculate_confidence(
        self, 
        observations: List[Dict[str, Any]], 
        thoughts: List[str]
    ) -> float:
        """
        计算置信度
        
        基于:
        - 观察数量
        - 思考深度
        - 工具调用成功率
        """
        base_confidence = 0.5
        
        # 观察数量因子
        obs_factor = min(0.2, len(observations) * 0.02)
        
        # 思考深度因子
        thought_factor = min(0.2, len(thoughts) * 0.02)
        
        # 工具调用成功率
        tool_calls = [obs for obs in observations if obs.get("type") == "tool_result"]
        if tool_calls:
            successful_calls = sum(1 for tc in tool_calls if not tc.get("error"))
            success_rate = successful_calls / len(tool_calls)
            tool_factor = success_rate * 0.1
        else:
            tool_factor = 0.0
        
        confidence = base_confidence + obs_factor + thought_factor + tool_factor
        return min(1.0, confidence)
    
    def _format_observations_for_think(
        self, 
        observations: List[Dict[str, Any]]
    ) -> str:
        """
        格式化观察结果用于思考提示
        """
        formatted = []
        
        for i, obs in enumerate(observations[-10:], 1):  # 只取最近10个
            obs_type = obs.get("type", "unknown")
            content = obs.get("content", "")
            tool = obs.get("tool", "")
            error = obs.get("error")
            
            if error:
                formatted.append(f"{i}. [ERROR] {error}")
            elif tool:
                formatted.append(f"{i}. [Tool: {tool}] {content[:200]}...")
            else:
                formatted.append(f"{i}. {content[:200]}...")
        
        return "\n".join(formatted)
    
    def _parse_action_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析行动响应
        
        从 LLM 响应中提取行动
        """
        import json
        
        # 尝试 JSON 解析
        try:
            # 查找 JSON 块
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        # 尝试简单解析
        lines = response.strip().split("\n")
        action = {}
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                action[key.strip().lower()] = value.strip()
        
        if action:
            return action
        
        return None
    
    def extract_answer_from_result(
        self, 
        agent_result: Any
    ) -> str:
        """
        从 AgentResult 提取答案
        """
        # 尝试不同格式
        if hasattr(agent_result, "answer"):
            return str(agent_result.answer)
        
        if hasattr(agent_result, "data"):
            data = agent_result.data
            if isinstance(data, str):
                return data
            if isinstance(data, dict):
                return data.get("answer", str(data))
        
        if hasattr(agent_result, "result"):
            return str(agent_result.result)
        
        return str(agent_result)
    
    def merge_agent_results(
        self, 
        results: List[Any]
    ) -> Dict[str, Any]:
        """
        合并多个 Agent 结果
        """
        answers = []
        confidences = []
        errors = []
        
        for result in results:
            if hasattr(result, "answer") and result.answer:
                answers.append(result.answer)
            
            if hasattr(result, "confidence"):
                confidences.append(result.confidence)
            
            if hasattr(result, "error") and result.error:
                errors.append(result.error)
        
        # 选择置信度最高的答案
        if confidences:
            best_idx = confidences.index(max(confidences))
            best_answer = answers[best_idx] if best_idx < len(answers) else ""
            avg_confidence = sum(confidences) / len(confidences)
        else:
            best_answer = answers[0] if answers else ""
            avg_confidence = 0.5
        
        return {
            "answer": best_answer,
            "confidence": avg_confidence,
            "answers_count": len(answers),
            "errors": errors,
        }
