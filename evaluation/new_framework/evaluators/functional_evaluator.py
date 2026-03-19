"""
功能能力评估器 - 评估系统实际能做什么

基于实际运行测试，而非静态代码分析
"""

import requests
import asyncio
from typing import Dict, Any, List, Optional
from base_evaluator import BaseEvaluator, EvaluationResult, EvaluationStatus


class FunctionalCapabilityEvaluator(BaseEvaluator):
    """基于实际运行的功能能力评估"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.test_cases = self._load_test_cases()
    
    @property
    def dimension_name(self) -> str:
        return "functionality"
    
    @property
    def weight(self) -> float:
        return 0.25
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        return [
            {
                "category": "reasoning",
                "query": "什么是机器学习？",
                "expected_keywords": ["机器学习", "算法", "数据"],
                "min_keyword_match": 1
            },
            {
                "category": "reasoning", 
                "query": "解释强化学习的基本概念",
                "expected_keywords": ["奖励", "状态", "动作", "智能体"],
                "min_keyword_match": 2
            },
            {
                "category": "reasoning",
                "query": "请解释什么是深度学习",
                "expected_keywords": ["神经网络", "层次", "特征"],
                "min_keyword_match": 1
            },
            {
                "category": "tool_usage",
                "query": "搜索最新的AI新闻",
                "expected_tools": ["search", "retrieval"],
                "min_tool_match": 1
            },
            {
                "category": "context",
                "query": "继续我们之前讨论的话题",
                "expected_behavior": "context_aware"
            },
            {
                "category": "multi_step",
                "query": "首先解释什么是AI，然后说明机器学习和AI的区别",
                "expected_behavior": "multi_step_reasoning"
            }
        ]
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "reasoning": await self._evaluate_reasoning(),
            "tool_usage": await self._evaluate_tool_usage(),
            "context_awareness": await self._evaluate_context_awareness(),
            "multi_step": await self._evaluate_multi_step()
        }
        
        valid_scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"测试了 {len(results)} 个功能维度"
        }
    
    async def _evaluate_reasoning(self) -> Dict[str, Any]:
        """评估推理能力"""
        test_cases = [tc for tc in self.test_cases if tc["category"] == "reasoning"]
        correct = 0
        
        for case in test_cases:
            try:
                response = await self._call_api(case["query"])
                if response and self._check_keywords(response, case.get("expected_keywords", [])):
                    correct += 1
            except Exception as e:
                self.logger.warning(f"推理测试失败: {case['query']}, error: {e}")
        
        score = correct / len(test_cases) if test_cases else 0.0
        return {
            "score": score,
            "correct": correct,
            "total": len(test_cases),
            "method": "实际问答测试"
        }
    
    async def _evaluate_tool_usage(self) -> Dict[str, Any]:
        """评估工具使用能力"""
        test_cases = [tc for tc in self.test_cases if tc["category"] == "tool_usage"]
        success = 0
        
        for case in test_cases:
            try:
                response = await self._call_api(case["query"])
                if response and "tool" in str(response).lower():
                    success += 1
            except Exception:
                pass
        
        score = success / len(test_cases) if test_cases else 0.0
        return {
            "score": score,
            "success": success,
            "total": len(test_cases),
            "method": "工具调用测试"
        }
    
    async def _evaluate_context_awareness(self) -> Dict[str, Any]:
        """评估上下文感知能力"""
        try:
            session_id = "eval_test_context"
            await self._call_api("我们讨论机器学习", session_id=session_id)
            response = await self._call_api("它的优缺点是什么？", session_id=session_id)
            
            if response and "机器学习" in str(response):
                return {"score": 1.0, "method": "多轮对话测试"}
            return {"score": 0.5, "method": "多轮对话测试"}
        except Exception as e:
            self.logger.warning(f"上下文测试失败: {e}")
            return {"score": 0.0, "error": str(e)}
    
    async def _evaluate_multi_step(self) -> Dict[str, Any]:
        """评估多步骤推理"""
        test_cases = [tc for tc in self.test_cases if tc["category"] == "multi_step"]
        
        if not test_cases:
            return {"score": None}
        
        success = 0
        for case in test_cases:
            try:
                response = await self._call_api(case["query"])
                text = str(response).lower()
                if "ai" in text and "机器学习" in text:
                    success += 1
            except Exception:
                pass
        
        score = success / len(test_cases) if test_cases else 0.0
        return {
            "score": score,
            "success": success,
            "total": len(test_cases),
            "method": "多步骤推理测试"
        }
    
    async def _call_api(self, query: str, session_id: Optional[str] = None) -> Optional[Dict]:
        """调用API"""
        try:
            url = f"{self.system_url}/chat"
            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.debug(f"API调用失败: {e}")
            return None
    
    def _check_keywords(self, response: Any, expected_keywords: List[str]) -> bool:
        """检查响应是否包含关键词"""
        text = str(response).lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in text)
        return matches >= 1


class AgentCapabilityEvaluator(BaseEvaluator):
    """智能体能力评估"""
    
    @property
    def dimension_name(self) -> str:
        return "agent_capability"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "agent_count": await self._count_agents(),
            "skill_count": await self._count_skills(),
            "tool_count": await self._count_tools()
        }
        
        max_counts = {"agent_count": 30, "skill_count": 20, "tool_count": 40}
        scores = {
            k: min(results[k]["count"] / max_counts[k], 1.0) 
            for k in results 
            if results[k]["count"] is not None
        }
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0.0
        
        return {
            "dimension": self.dimension_name,
            "score": max(0, min(1, overall_score)),
            "status": "completed",
            "metrics": results,
            "details": f"系统包含 {results.get('agent_count', {}).get('count', 0)} 个Agent, "
                   f"{results.get('skill_count', {}).get('count', 0)} 个Skill, "
                   f"{results.get('tool_count', {}).get('count', 0)} 个Tool"
        }
    
    async def _count_agents(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/agents", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {"count": data.get("total", 0)}
        except Exception:
            pass
        return {"count": None}
    
    async def _count_skills(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/skills", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {"count": data.get("total", 0)}
        except Exception:
            pass
        return {"count": None}
    
    async def _count_tools(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.system_url}/api/v1/tools", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {"count": data.get("total", 0)}
        except Exception:
            pass
        return {"count": None}
