#!/usr/bin/env python3
"""
提示词工程智能体 - 自我学习和优化提示词
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .expert_agent import ExpertAgent
from .base_agent import AgentResult

logger = logging.getLogger(__name__)


class PromptEngineeringAgent(ExpertAgent):
    """提示词工程智能体 - 自我学习和优化提示词
    
    核心能力：
    1. 提示词模板管理：动态加载、更新、版本控制
    2. 提示词生成和优化：根据查询类型和上下文生成最优提示词
    3. 自我学习和改进：分析效果、自动优化、A/B测试
    """
    
    def __init__(self):
        super().__init__(
            agent_id="prompt_engineering_expert",
            domain_expertise="提示词工程和模板优化",
            capability_level=0.95,
            collaboration_style="analytical"
        )
        
        # 提示词引擎
        self.prompt_engine = None
        
        # 🚀 新增：RL/ML集成
        self.rl_agent = None
        self.ml_rl_integration = None
        self.llm_client = None  # LLM客户端（用于提示词优化）
        self._init_rl_ml_integration()
        
        # 学习数据
        self.performance_tracking: Dict[str, List[Dict[str, Any]]] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_practices: Dict[str, Any] = {}
        
        # 学习配置
        self.learning_config = {
            "enable_auto_optimization": True,
            "ab_test_enabled": True,
            "min_samples_for_optimization": 10,
            "improvement_threshold": 0.05,  # 5%改进阈值
            "enable_rl_optimization": True,  # 🚀 新增：启用RL优化
            "enable_ml_prediction": True,    # 🚀 新增：启用ML预测
        }
        
        # 🚀 新增：A/B测试数据
        self.ab_tests: Dict[str, Dict[str, Any]] = {}  # {template_name: {version_a: {...}, version_b: {...}, ...}}
        
        # 🚀 新增：性能监控
        self.performance_monitor = {
            "alerts": [],
            "thresholds": {
                "min_success_rate": 0.7,
                "max_response_time": 5.0,
                "min_quality_score": 0.6
            },
            "monitoring_enabled": True
        }
        
        logger.info("✅ PromptEngineeringAgent 初始化完成（已集成RL/ML、A/B测试、性能监控）")
    
    def _init_rl_ml_integration(self):
        """🚀 新增：初始化RL/ML集成"""
        try:
            # 初始化RL Agent
            from src.rl.enhanced_rl_agent import EnhancedRLAgent
            self.rl_agent = EnhancedRLAgent(agent_name="prompt_optimizer")
            logger.info("✅ RL Agent 初始化完成")
            
            # 初始化ML/RL集成服务（可选）
            try:
                from src.ai.ml_rl_integration_service import MLRLIntegrationService
                self.ml_rl_integration = MLRLIntegrationService()
                logger.info("✅ ML/RL集成服务初始化完成")
            except Exception as e:
                logger.debug(f"ML/RL集成服务初始化失败（可选）: {e}")
                self.ml_rl_integration = None
        except Exception as e:
            logger.warning(f"⚠️ RL/ML集成初始化失败: {e}，将使用基础优化方法")
            self.rl_agent = None
            self.ml_rl_integration = None
    
    def _get_service(self):
        """获取提示词引擎服务"""
        if self.prompt_engine is None:
            from src.utils.prompt_engine import get_prompt_engine
            self.prompt_engine = get_prompt_engine()
        return self.prompt_engine
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行提示词工程任务
        
        Args:
            context: 任务上下文，包含：
                - task_type: 任务类型（generate_prompt, optimize_template, analyze_effectiveness, learn_from_feedback）
                - query: 查询文本
                - template_name: 模板名称
                - query_type: 查询类型
                - evidence: 证据（可选）
                - enhanced_context: 增强上下文（可选）
                - feedback: 反馈数据（用于学习）
        
        Returns:
            AgentResult: 执行结果
        """
        import time
        start_time = time.time()
        
        if not self.prompt_engine:
            self.prompt_engine = self._get_service()
        
        task_type = context.get("task_type", "generate_prompt")
        
        try:
            if task_type == "generate_prompt":
                return await self._generate_optimized_prompt(context, start_time)
            elif task_type == "optimize_template":
                return await self._optimize_template(context, start_time)
            elif task_type == "analyze_effectiveness":
                return await self._analyze_effectiveness(context, start_time)
            elif task_type == "learn_from_feedback":
                return await self._learn_from_feedback(context, start_time)
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"未知的任务类型: {task_type}",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"提示词工程任务执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _generate_optimized_prompt(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """生成优化的提示词（🚀 增强：支持RL/ML优化）"""
        try:
            template_name = context.get("template_name", "general_query")
            query = context.get("query", "")
            query_type = context.get("query_type", "general")
            evidence = context.get("evidence")
            enhanced_context = context.get("enhanced_context", {})
            
            # 🚀 新增：如果启用RL优化，使用RL选择最优模板
            if self.learning_config.get("enable_rl_optimization") and self.rl_agent:
                try:
                    rl_template = await self._select_template_with_rl(
                        template_name, query, query_type, context
                    )
                    if rl_template:
                        template_name = rl_template
                        logger.debug(f"✅ RL选择了模板: {template_name}")
                except Exception as e:
                    logger.debug(f"RL模板选择失败，使用默认模板: {e}")
            
            # 使用提示词引擎生成提示词
            import asyncio
            loop = asyncio.get_event_loop()
            
            prompt = await loop.run_in_executor(
                None,
                lambda: self.prompt_engine.generate_prompt(
                    template_name=template_name,
                    query=query,
                    query_type=query_type,
                    evidence=evidence,
                    enhanced_context=enhanced_context
                )
            )
            
            # 记录使用情况（用于学习）
            self._track_usage(template_name, {
                "query": query[:100],  # 只记录前100字符
                "query_type": query_type,
                "timestamp": time.time(),
                "template_name": template_name,
                "used_rl": self.learning_config.get("enable_rl_optimization") and self.rl_agent is not None
            })
            
            return AgentResult(
                success=True,
                data={"prompt": prompt, "template_name": template_name},
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"生成提示词失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _optimize_template(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """优化提示词模板"""
        try:
            template_name = context.get("template_name")
            if not template_name:
                return AgentResult(
                    success=False,
                    data=None,
                    error="缺少模板名称",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 分析模板使用效果
            effectiveness = await self._analyze_template_effectiveness(template_name)
            
            # 如果效果不佳，尝试优化
            if effectiveness.get("needs_optimization", False):
                # 使用LLM生成改进建议
                optimization_suggestions = await self._generate_optimization_suggestions(
                    template_name, effectiveness
                )
                
                # 如果启用了A/B测试，创建新版本
                if self.learning_config.get("ab_test_enabled"):
                    new_version = await self._create_optimized_version(
                        template_name, optimization_suggestions
                    )
                    
                    return AgentResult(
                        success=True,
                        data={
                            "template_name": template_name,
                            "effectiveness": effectiveness,
                            "suggestions": optimization_suggestions,
                            "new_version": new_version,
                            "ab_test_created": True
                        },
                        confidence=0.8,
                        processing_time=time.time() - start_time
                    )
                else:
                    return AgentResult(
                        success=True,
                        data={
                            "template_name": template_name,
                            "effectiveness": effectiveness,
                            "suggestions": optimization_suggestions
                        },
                        confidence=0.8,
                        processing_time=time.time() - start_time
                    )
            else:
                return AgentResult(
                    success=True,
                    data={
                        "template_name": template_name,
                        "effectiveness": effectiveness,
                        "message": "模板效果良好，无需优化"
                    },
                    confidence=0.9,
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"优化模板失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _analyze_effectiveness(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """分析提示词效果"""
        try:
            template_name = context.get("template_name")
            if template_name:
                effectiveness = await self._analyze_template_effectiveness(template_name)
            else:
                # 分析所有模板
                effectiveness = await self._analyze_all_templates()
            
            return AgentResult(
                success=True,
                data={"effectiveness": effectiveness},
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"分析效果失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _learn_from_feedback(
        self, 
        context: Dict[str, Any], 
        start_time: float
    ) -> AgentResult:
        """从反馈中学习"""
        try:
            feedback = context.get("feedback", {})
            template_name = feedback.get("template_name")
            success = feedback.get("success", False)
            metrics = feedback.get("metrics", {})
            
            # 记录反馈
            self._record_feedback(template_name, success, metrics)
            
            # 如果启用了自动优化，检查是否需要优化
            if self.learning_config.get("enable_auto_optimization"):
                # 检查是否有足够的样本
                usage_count = len(self.performance_tracking.get(template_name, []))
                if usage_count >= self.learning_config.get("min_samples_for_optimization", 10):
                    # 分析是否需要优化
                    effectiveness = await self._analyze_template_effectiveness(template_name)
                    if effectiveness.get("needs_optimization", False):
                        # 自动触发优化
                        optimization_result = await self._optimize_template(
                            {"template_name": template_name}, start_time
                        )
                        return AgentResult(
                            success=True,
                            data={
                                "feedback_recorded": True,
                                "auto_optimization_triggered": True,
                                "optimization_result": optimization_result.data
                            },
                            confidence=0.8,
                            processing_time=time.time() - start_time
                        )
            
            return AgentResult(
                success=True,
                data={"feedback_recorded": True},
                confidence=0.9,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"学习反馈失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _track_usage(self, template_name: str, usage_data: Dict[str, Any]) -> None:
        """追踪模板使用情况"""
        if template_name not in self.performance_tracking:
            self.performance_tracking[template_name] = []
        
        self.performance_tracking[template_name].append(usage_data)
        
        # 限制历史记录数量（保留最近1000条）
        if len(self.performance_tracking[template_name]) > 1000:
            self.performance_tracking[template_name] = self.performance_tracking[template_name][-1000:]
    
    def _record_feedback(
        self, 
        template_name: str, 
        success: bool, 
        metrics: Dict[str, Any]
    ) -> None:
        """记录反馈"""
        if template_name not in self.performance_tracking:
            self.performance_tracking[template_name] = []
        
        feedback_data = {
            "success": success,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        # 更新最近的记录
        if self.performance_tracking[template_name]:
            last_record = self.performance_tracking[template_name][-1]
            last_record.update(feedback_data)
    
    async def _analyze_template_effectiveness(
        self, 
        template_name: str
    ) -> Dict[str, Any]:
        """分析模板效果"""
        usage_records = self.performance_tracking.get(template_name, [])
        
        if not usage_records:
            return {
                "template_name": template_name,
                "usage_count": 0,
                "needs_optimization": False,
                "message": "暂无使用记录"
            }
        
        # 计算成功率
        success_count = sum(1 for r in usage_records if r.get("success", False))
        success_rate = success_count / len(usage_records) if usage_records else 0.0
        
        # 计算平均响应时间（如果有）
        response_times = [r.get("metrics", {}).get("response_time", 0) 
                         for r in usage_records if r.get("metrics", {}).get("response_time")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # 判断是否需要优化
        needs_optimization = (
            success_rate < 0.7 or  # 成功率低于70%
            (avg_response_time > 30.0 and len(response_times) > 10)  # 平均响应时间超过30秒
        )
        
        return {
            "template_name": template_name,
            "usage_count": len(usage_records),
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "needs_optimization": needs_optimization,
            "recommendation": "需要优化" if needs_optimization else "效果良好"
        }
    
    async def _analyze_all_templates(self) -> Dict[str, Any]:
        """分析所有模板的效果"""
        all_templates = list(self.prompt_engine.templates.keys())
        results = {}
        
        for template_name in all_templates:
            results[template_name] = await self._analyze_template_effectiveness(template_name)
        
        return results
    
    async def _generate_optimization_suggestions(
        self, 
        template_name: str, 
        effectiveness: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        # 使用LLM生成优化建议
        if not self.llm_client:
            self._init_llm_client()
        
        if not self.llm_client:
            return ["建议：分析模板使用情况，识别问题模式"]
        
        try:
            template = self.prompt_engine.templates.get(template_name)
            if not template:
                return []
            
            prompt = f"""分析以下提示词模板的效果，并提供优化建议。

模板名称: {template_name}
模板内容: {template.content[:500]}
效果分析: {json.dumps(effectiveness, ensure_ascii=False, indent=2)}

请提供3-5条具体的优化建议，每条建议应该：
1. 明确指出问题
2. 提供具体的改进方案
3. 说明预期效果

优化建议："""
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_client._call_llm(prompt) if hasattr(self.llm_client, '_call_llm') else ""
            )
            
            # 解析建议（简单按行分割）
            suggestions = [s.strip() for s in response.split('\n') if s.strip() and s.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '•'))]
            
            return suggestions if suggestions else ["建议：分析模板使用情况，识别问题模式"]
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return ["建议：分析模板使用情况，识别问题模式"]
    
    async def _create_optimized_version(
        self, 
        template_name: str, 
        suggestions: List[str]
    ) -> Optional[Dict[str, Any]]:
        """创建优化版本（用于A/B测试）"""
        try:
            template = self.prompt_engine.templates.get(template_name)
            if not template:
                return None
            
            # 使用LLM生成优化版本
            if not self.llm_client:
                self._init_llm_client()
            
            if not self.llm_client:
                return None
            
            prompt = f"""基于以下优化建议，生成改进后的提示词模板。

原始模板: {template.content}
优化建议: {json.dumps(suggestions, ensure_ascii=False, indent=2)}

请生成改进后的模板内容，保持相同的参数占位符（如{{query}}, {{context}}等）。

改进后的模板："""
            
            import asyncio
            loop = asyncio.get_event_loop()
            optimized_content = await loop.run_in_executor(
                None,
                lambda: self.llm_client._call_llm(prompt) if hasattr(self.llm_client, '_call_llm') else ""
            )
            
            # 创建新版本
            new_version_name = f"{template_name}_v2_{int(time.time())}"
            
            return {
                "version_name": new_version_name,
                "original_template": template_name,
                "optimized_content": optimized_content,
                "suggestions": suggestions,
                "created_at": time.time()
            }
        except Exception as e:
            logger.error(f"创建优化版本失败: {e}")
            return None
    
    def _init_llm_client(self):
        """初始化LLM客户端（用于提示词优化）"""
        try:
            # 尝试从统一中心获取LLM集成
            from src.utils.unified_centers import get_unified_center
            unified_center = get_unified_center()
            if unified_center and hasattr(unified_center, 'llm_integration'):
                self.llm_client = unified_center.llm_integration
                logger.debug("✅ LLM客户端初始化完成（从统一中心）")
                return
            
            # Fallback: 尝试直接导入
            from src.core.llm_integration import LLMIntegration
            import os
            config = {
                "model_type": os.getenv("MODEL_TYPE", "deepseek"),
                "api_key": os.getenv("API_KEY", ""),
                "base_url": os.getenv("BASE_URL", "")
            }
            self.llm_client = LLMIntegration(config)
            logger.debug("✅ LLM客户端初始化完成（直接创建）")
        except Exception as e:
            logger.debug(f"LLM客户端初始化失败: {e}")
            self.llm_client = None
    
    # 🚀 新增：RL/ML集成方法
    
    async def _select_template_with_rl(
        self,
        default_template: str,
        query: str,
        query_type: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """使用RL选择最优模板"""
        try:
            if not self.rl_agent:
                return None
            
            # 1. 构建RL状态
            rl_state = self._build_rl_state(default_template, query, query_type, context)
            
            # 2. RL选择动作（模板）
            # 注意：EnhancedRLAgent的接口可能需要调整，这里使用简化版本
            # 实际实现需要根据EnhancedRLAgent的具体接口调整
            
            # 获取可用的模板列表
            available_templates = self._get_available_templates(query_type)
            if not available_templates:
                return default_template
            
            # 使用RL选择（简化版本：基于历史性能）
            # TODO: 完整实现需要调用rl_agent.select_action
            best_template = self._select_best_template_by_performance(
                available_templates, query_type
            )
            
            return best_template if best_template else default_template
            
        except Exception as e:
            logger.debug(f"RL模板选择失败: {e}")
            return None
    
    def _build_rl_state(
        self,
        template_name: str,
        query: str,
        query_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建RL状态"""
        # 获取模板性能
        template_perf = self.performance_tracking.get(template_name, [])
        success_rate = (
            sum(1 for r in template_perf if r.get("success", False)) / len(template_perf)
            if template_perf else 0.5
        )
        
        return {
            "query_type": query_type,
            "template_name": template_name,
            "template_performance": success_rate,
            "query_length": len(query),
            "has_evidence": bool(context.get("evidence")),
            "context_features": {
                "evidence_count": len(context.get("evidence", [])) if isinstance(context.get("evidence"), list) else 0,
                "enhanced_context_keys": list(context.get("enhanced_context", {}).keys())
            }
        }
    
    def _get_available_templates(self, query_type: str) -> List[str]:
        """获取可用的模板列表"""
        if not self.prompt_engine:
            return []
        
        # 根据查询类型搜索模板
        templates = self.prompt_engine.search_templates(category=query_type)
        return [t.name for t in templates] if templates else []
    
    def _select_best_template_by_performance(
        self,
        templates: List[str],
        query_type: str
    ) -> Optional[str]:
        """根据性能选择最佳模板（简化版本，用于RL未完全集成时）"""
        if not templates:
            return None
        
        best_template = None
        best_score = 0.0
        
        for template_name in templates:
            perf = self.performance_tracking.get(template_name, [])
            if not perf:
                continue
            
            success_rate = sum(1 for r in perf if r.get("success", False)) / len(perf)
            usage_count = len(perf)
            
            # 综合评分：成功率 * 使用次数权重
            score = success_rate * min(1.0, usage_count / 10.0)
            
            if score > best_score:
                best_score = score
                best_template = template_name
        
        return best_template
    
    def calculate_prompt_reward(
        self,
        answer_quality: float,
        response_time: float,
        user_satisfaction: Optional[float] = None,
        cost: Optional[float] = None
    ) -> float:
        """🚀 新增：计算提示词RL奖励"""
        # 质量权重：0.6
        quality_score = answer_quality * 0.6
        
        # 时间权重：0.2（越快越好，但不超过阈值）
        time_score = max(0, (5.0 - response_time) / 5.0) * 0.2
        
        # 满意度权重：0.1（如果有）
        satisfaction_score = user_satisfaction * 0.1 if user_satisfaction and user_satisfaction > 0 else 0
        
        # 成本权重：0.1（越低越好，如果有）
        cost_score = 0.0
        if cost is not None:
            cost_score = max(0, (1000 - cost) / 1000) * 0.1
        
        return quality_score + time_score + satisfaction_score + cost_score
    
    async def record_prompt_performance(
        self,
        prompt_type: str,
        template_name: str,
        query: str,
        answer_quality: float,
        response_time: float,
        cost: Optional[float] = None
    ):
        """🚀 新增：记录提示词性能（用于RL学习）"""
        try:
            # 1. 记录性能数据
            if self.prompt_engine:
                self.prompt_engine._record_performance(
                    template_name,
                    success=answer_quality > 0.7,
                    response_time=response_time
                )
            
            # 2. 计算RL奖励
            reward = self.calculate_prompt_reward(
                answer_quality, response_time, None, cost
            )
            
            # 3. 更新RL策略（如果RL Agent可用）
            if self.rl_agent and self.learning_config.get("enable_rl_optimization"):
                try:
                    # 构建RL状态和动作
                    from src.rl.enhanced_rl_agent import RLState, RLAction, RLReward
                    
                    state_dict = self._build_rl_state(template_name, query, prompt_type, {})
                    state = RLState(
                        state_id=f"{prompt_type}_{template_name}",
                        features=state_dict,
                        metadata={"query": query[:100], "template": template_name}
                    )
                    
                    action = RLAction(
                        action_id=f"select_template_{template_name}",
                        action_type="template_selection",
                        parameters={"template_name": template_name},
                        confidence=0.8
                    )
                    
                    rl_reward = RLReward(
                        value=reward,
                        components={
                            "quality": answer_quality,
                            "time": max(0, (5.0 - response_time) / 5.0),
                            "cost": max(0, (1000 - (cost or 0)) / 1000) if cost else 0
                        },
                        timestamp=time.time()
                    )
                    
                    # 调用RL Agent更新策略
                    await self.rl_agent._update_policy(state, action, rl_reward)
                    logger.debug(f"✅ RL策略更新完成: {template_name}, 奖励: {reward:.3f}")
                except Exception as e:
                    logger.debug(f"RL策略更新失败: {e}")
            
            # 4. 记录到性能追踪
            self._track_usage(template_name, {
                "query": query[:100],
                "answer_quality": answer_quality,
                "response_time": response_time,
                "reward": reward,
                "timestamp": time.time()
            })
            
        except Exception as e:
            logger.error(f"记录提示词性能失败: {e}")
    
    # 🚀 新增：A/B测试功能
    
    async def create_ab_test(
        self,
        template_name: str,
        version_a_content: str,
        version_b_content: str,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """创建A/B测试"""
        try:
            version_a_name = f"{template_name}_vA_{int(time.time())}"
            version_b_name = f"{template_name}_vB_{int(time.time())}"
            
            self.prompt_engine.add_template(version_a_name, version_a_content, "ab_test", 0.5)
            self.prompt_engine.add_template(version_b_name, version_b_content, "ab_test", 0.5)
            
            self.ab_tests[template_name] = {
                "version_a": {"name": version_a_name, "content": version_a_content, "traffic": traffic_split, "stats": {"usage": 0, "success": 0, "total_reward": 0.0}},
                "version_b": {"name": version_b_name, "content": version_b_content, "traffic": 1.0 - traffic_split, "stats": {"usage": 0, "success": 0, "total_reward": 0.0}},
                "created_at": time.time(),
                "status": "active"
            }
            
            logger.info(f"✅ A/B测试创建成功: {template_name}")
            return {"template_name": template_name, "version_a": version_a_name, "version_b": version_b_name, "status": "active"}
        except Exception as e:
            logger.error(f"创建A/B测试失败: {e}")
            return {}
    
    async def select_ab_test_version(self, template_name: str, query: str) -> Optional[str]:
        """选择A/B测试版本"""
        if template_name not in self.ab_tests or self.ab_tests[template_name].get("status") != "active":
            return None
        
        import hashlib
        query_hash = int(hashlib.md5(query.encode()).hexdigest(), 16)
        use_version_a = (query_hash % 100) < (self.ab_tests[template_name]["version_a"]["traffic"] * 100)
        version_name = self.ab_tests[template_name]["version_a"]["name"] if use_version_a else self.ab_tests[template_name]["version_b"]["name"]
        version_key = "version_a" if use_version_a else "version_b"
        self.ab_tests[template_name][version_key]["stats"]["usage"] += 1
        return version_name
    
    async def record_ab_test_result(self, template_name: str, version_name: str, success: bool, reward: float):
        """记录A/B测试结果"""
        if template_name not in self.ab_tests:
            return
        for version_key in ["version_a", "version_b"]:
            if self.ab_tests[template_name][version_key]["name"] == version_name:
                stats = self.ab_tests[template_name][version_key]["stats"]
                stats["total_reward"] += reward
                if success:
                    stats["success"] += 1
                break
    
    async def get_ab_test_results(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取A/B测试结果"""
        if template_name not in self.ab_tests:
            return None
        ab_test = self.ab_tests[template_name]
        va_stats, vb_stats = ab_test["version_a"]["stats"], ab_test["version_b"]["stats"]
        va_sr = va_stats["success"] / va_stats["usage"] if va_stats["usage"] > 0 else 0.0
        vb_sr = vb_stats["success"] / vb_stats["usage"] if vb_stats["usage"] > 0 else 0.0
        va_ar = va_stats["total_reward"] / va_stats["usage"] if va_stats["usage"] > 0 else 0.0
        vb_ar = vb_stats["total_reward"] / vb_stats["usage"] if vb_stats["usage"] > 0 else 0.0
        winner = None
        if va_stats["usage"] >= 10 and vb_stats["usage"] >= 10:
            if va_ar > vb_ar * 1.05:
                winner = "version_a"
            elif vb_ar > va_ar * 1.05:
                winner = "version_b"
        return {"template_name": template_name, "version_a": {"name": ab_test["version_a"]["name"], "usage": va_stats["usage"], "success_rate": va_sr, "avg_reward": va_ar}, "version_b": {"name": ab_test["version_b"]["name"], "usage": vb_stats["usage"], "success_rate": vb_sr, "avg_reward": vb_ar}, "winner": winner, "status": ab_test.get("status", "active")}
    
    # 🚀 新增：性能监控功能
    
    def check_performance_alerts(self, template_name: str, success_rate: float, response_time: float, quality_score: float) -> List[Dict[str, Any]]:
        """检查性能告警"""
        alerts = []
        if not self.performance_monitor["monitoring_enabled"]:
            return alerts
        thresholds = self.performance_monitor["thresholds"]
        if success_rate < thresholds["min_success_rate"]:
            alerts.append({"type": "low_success_rate", "template": template_name, "value": success_rate, "threshold": thresholds["min_success_rate"], "severity": "high", "timestamp": time.time()})
            logger.warning(f"⚠️ 性能告警: {template_name} 成功率过低 ({success_rate:.2f} < {thresholds['min_success_rate']:.2f})")
        if response_time > thresholds["max_response_time"]:
            alerts.append({"type": "high_response_time", "template": template_name, "value": response_time, "threshold": thresholds["max_response_time"], "severity": "medium", "timestamp": time.time()})
            logger.warning(f"⚠️ 性能告警: {template_name} 响应时间过长 ({response_time:.2f}s > {thresholds['max_response_time']:.2f}s)")
        if quality_score < thresholds["min_quality_score"]:
            alerts.append({"type": "low_quality_score", "template": template_name, "value": quality_score, "threshold": thresholds["min_quality_score"], "severity": "high", "timestamp": time.time()})
            logger.warning(f"⚠️ 性能告警: {template_name} 质量分数过低 ({quality_score:.2f} < {thresholds['min_quality_score']:.2f})")
        self.performance_monitor["alerts"].extend(alerts)
        if len(self.performance_monitor["alerts"]) > 1000:
            self.performance_monitor["alerts"] = self.performance_monitor["alerts"][-1000:]
        return alerts
    
    def get_performance_alerts(self, template_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取性能告警"""
        alerts = self.performance_monitor["alerts"]
        if template_name:
            alerts = [a for a in alerts if a.get("template") == template_name]
        return alerts
    
    async def auto_optimize_with_monitoring(self):
        """自动优化并监控性能"""
        try:
            for template_name in self.prompt_engine.templates:
                effectiveness = await self._analyze_template_effectiveness(template_name)
                alerts = self.check_performance_alerts(template_name, effectiveness.get("success_rate", 0.0), effectiveness.get("avg_response_time", 0.0), effectiveness.get("quality_score", 0.0))
                if effectiveness.get("needs_optimization", False) or alerts:
                    logger.info(f"🔄 自动优化模板: {template_name}")
                    await self._optimize_template({"template_name": template_name}, time.time())
            logger.info("✅ 自动优化和监控完成")
        except Exception as e:
            logger.error(f"自动优化和监控失败: {e}")

