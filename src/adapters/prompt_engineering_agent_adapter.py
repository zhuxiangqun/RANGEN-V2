#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PromptEngineeringAgent → ToolOrchestrator 迁移适配器

将 PromptEngineeringAgent 的调用适配到 ToolOrchestrator，实现平滑迁移。
注意：PromptEngineeringAgent专注于提示词工程，而ToolOrchestrator专注于工具选择和编排。
适配器将提示词工程任务转换为工具编排任务。
"""

from typing import Dict, Any, Optional, List
import logging

from .base_adapter import MigrationAdapter
from ..agents.tool_orchestrator import ToolOrchestrator
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class PromptEngineeringAgentAdapter(MigrationAdapter):
    """PromptEngineeringAgent → ToolOrchestrator 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="PromptEngineeringAgent",
            target_agent_name="ToolOrchestrator"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（ToolOrchestrator）"""
        return ToolOrchestrator()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        PromptEngineeringAgent 参数格式:
        {
            'task_type': str,  # 'generate_prompt', 'optimize_template', 'analyze_effectiveness', 'learn_from_feedback'
            'query': str,  # 查询文本
            'template_name': str,  # 模板名称
            'query_type': str,  # 查询类型
            'evidence': List,  # 证据（可选）
            'enhanced_context': Dict,  # 增强上下文（可选）
            'feedback': Dict,  # 反馈数据（用于学习）
            ...
        }
        
        ToolOrchestrator 参数格式:
        {
            'action': str,  # 'select_tool', 'create_chain', 'execute_chain', 'optimize_prompt', 'stats'
            'task_description': str,  # 任务描述 (select_tool时需要)
            'required_capabilities': List,  # 所需能力列表 (select_tool时需要)
            'chain_name/description/steps': Dict,  # 工具链信息 (create_chain时需要)
            'chain_id': str,  # 工具链ID (execute_chain时需要)
            'tool_name': str,  # 工具名称 (optimize_prompt时需要)
            'performance_history': List,  # 性能历史 (optimize_prompt时需要)
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        task_type = old_context.get("task_type", "generate_prompt")
        query = old_context.get("query", "")
        template_name = old_context.get("template_name", "")
        query_type = old_context.get("query_type", "")
        evidence = old_context.get("evidence", [])
        enhanced_context = old_context.get("enhanced_context", {})
        feedback = old_context.get("feedback", {})
        
        # 将task_type映射到action
        action_mapping = {
            "generate_prompt": "optimize_prompt",  # 生成提示词 -> 优化提示词
            "optimize_template": "optimize_prompt",  # 优化模板 -> 优化提示词
            "analyze_effectiveness": "optimize_prompt",  # 分析效果 -> 优化提示词（需要性能历史）
            "learn_from_feedback": "optimize_prompt",  # 从反馈学习 -> 优化提示词
        }
        action = action_mapping.get(task_type, "optimize_prompt")
        
        # 转换参数格式
        adapted.update({
            "action": action,
            # 对于optimize_prompt操作
            "tool_name": template_name or "prompt_template",
            "task_description": query or f"优化{query_type}类型的提示词模板",
            "required_capabilities": ["prompt_generation", "template_optimization"],
            # 性能历史（从feedback中提取）
            "performance_history": self._extract_performance_history(feedback),
            # 保留原始参数供参考
            "query": query,
            "template_name": template_name,
            "query_type": query_type,
            "evidence": evidence,
            "enhanced_context": enhanced_context,
            "feedback": feedback,
            "_original_task_type": task_type,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "task_type": task_type,
            "mapped_action": action
        })
        
        return adapted
    
    def _extract_performance_history(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从feedback中提取性能历史"""
        performance_history = []
        
        if isinstance(feedback, dict):
            # 如果feedback包含性能数据
            if "performance" in feedback:
                perf = feedback["performance"]
                if isinstance(perf, list):
                    performance_history = perf
                elif isinstance(perf, dict):
                    performance_history = [perf]
            elif "history" in feedback:
                performance_history = feedback["history"]
            elif "metrics" in feedback:
                # 将metrics转换为性能历史格式
                metrics = feedback["metrics"]
                if isinstance(metrics, dict):
                    performance_history = [{
                        "timestamp": metrics.get("timestamp"),
                        "success_rate": metrics.get("success_rate", 0.0),
                        "response_time": metrics.get("response_time", 0.0),
                        "quality_score": metrics.get("quality_score", 0.0),
                    }]
        
        return performance_history
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        ToolOrchestrator 返回格式:
        {
            'success': bool,
            'data': {
                'selected_tool': str,  # 选择的工具
                'tool_chain': Dict,  # 工具链
                'execution_result': Dict,  # 执行结果
                'optimized_prompt': str,  # 优化的提示词
                ...
            },
            'confidence': float,
            ...
        }
        
        PromptEngineeringAgent 期望格式:
        {
            'success': bool,
            'data': {
                'prompt': str,  # 生成的提示词
                'template': str,  # 模板
                'effectiveness': Dict,  # 效果分析
                'optimization_result': Dict,  # 优化结果
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            data = new_result.data if hasattr(new_result, 'data') else {}
            
            # 提取提示词工程相关数据
            prompt_data = self._extract_prompt_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": prompt_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取提示词工程相关数据
            prompt_data = self._extract_prompt_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": prompt_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_prompt": "prompt" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_prompt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从ToolOrchestrator的结果中提取提示词工程数据"""
        prompt_data = {}
        
        # 提取优化的提示词
        if "optimized_prompt" in data:
            prompt_data["prompt"] = data["optimized_prompt"]
            prompt_data["template"] = data["optimized_prompt"]
        elif "prompt" in data:
            prompt_data["prompt"] = data["prompt"]
            prompt_data["template"] = data["prompt"]
        
        # 提取执行结果（可能包含效果分析）
        if "execution_result" in data:
            exec_result = data["execution_result"]
            if isinstance(exec_result, dict):
                prompt_data["effectiveness"] = exec_result
                prompt_data["optimization_result"] = exec_result
        
        # 提取工具链信息（可能包含模板信息）
        if "tool_chain" in data:
            tool_chain = data["tool_chain"]
            if isinstance(tool_chain, dict):
                if "prompt_template" in tool_chain:
                    prompt_data["template"] = tool_chain["prompt_template"]
        
        # 如果没有找到提示词数据，返回空结构
        if not prompt_data or "prompt" not in prompt_data:
            prompt_data = {
                "prompt": "",
                "template": "",
                "effectiveness": {},
                "optimization_result": {}
            }
        
        return prompt_data

