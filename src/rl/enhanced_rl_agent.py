#!/usr/bin/env python3
"""
增强强化学习智能体 - 整合强化学习、策略优化和智能决策功能
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re
import numpy as np

# 基础导入
# from base_agent import BaseAgent
# from enhanced_base_agent import EnhancedBaseAgent

# 工具导入
from utils.unified_centers import get_unified_center
from utils.deep_reinforcement_learning import DeepReinforcementLearning

logger = logging.getLogger(__name__)

@dataclass
class AgentResult:
    """智能体结果"""
    query: str
    result: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0

@dataclass
class RLState:
    """强化学习状态"""
    state_id: str
    features: List[float]
    context: Dict[str, Any]
    timestamp: float

@dataclass
class RLAction:
    """强化学习动作"""
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    confidence: float

@dataclass
class RLReward:
    """强化学习奖励"""
    reward_id: str
    value: float
    components: Dict[str, float]
    timestamp: float

class EnhancedRLAgent:
    """增强强化学习智能体 - 整合强化学习、策略优化和智能决策功能"""

    def __init__(self, agent_name: str = "EnhancedRLAgent", use_intelligent_config: bool = True):
        # 基础属性初始化
        self.agent_name = agent_name
        self.use_intelligent_config = use_intelligent_config

        self.is_executing = False
        self._execution_lock = threading.Lock()
        self.agent_name = agent_name

        # 初始化强化学习配置
        self.rl_config = self._get_default_rl_config()
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        self.discount_factor = 0.95
        
        # 强化学习组件
        self.rl_engine = None
        self.state_space_size = 100
        self.action_space_size = 50
        
        # 统计信息
        self.rl_stats = {
            "total_episodes": 0,
            "successful_episodes": 0,
            "failed_episodes": 0,
            "average_reward": 0.0,
            "learning_progress": 0.0,
            "exploration_rate": self.exploration_rate,
            "action_types": {},
            "state_transitions": 0
        }

        # 初始化强化学习引擎
        self._initialize_rl_engine()

        logger.info("✅ 增强强化学习智能体初始化完成")

    def _get_default_rl_config(self) -> Dict[str, Any]:
        """获取默认强化学习配置"""
        return {
            "learning_rate": 0.01,
            "exploration_rate": 0.1,
            "discount_factor": 0.95,
            "batch_size": 32,
            "memory_size": 10000,
            "target_update_frequency": 100,
            "reward_shaping": True,
            "experience_replay": True,
            "double_dqn": True,
            "prioritized_replay": False
        }

    def _initialize_rl_engine(self):
        """初始化强化学习引擎"""
        try:
            self.rl_engine = DeepReinforcementLearning(
                state_size=self.state_space_size,
                action_size=self.action_space_size,
                learning_rate=self.learning_rate,
                discount_factor=self.discount_factor,
                epsilon=self.exploration_rate
            )
            logger.info("✅ 强化学习引擎初始化成功")
        except Exception as e:
            logger.warning(f"强化学习引擎初始化失败: {e}")
            self.rl_engine = None

    async def process_query(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> AgentResult:
        """处理查询"""
        start_time = time.time()
        
        try:
            with self._execution_lock:
                self.is_executing = True
                
                # 更新统计
                self.rl_stats["total_episodes"] += 1
                
                # 分析查询类型
                query_analysis = self._analyze_query(query)
                
                # 创建强化学习状态
                rl_state = self._create_rl_state(query, query_analysis, context)
                
                # 选择动作
                rl_action = await self._select_action(rl_state, query_analysis)
                
                # 执行动作
                execution_result = await self._execute_action(rl_action, rl_state)
                
                # 计算奖励
                rl_reward = self._calculate_reward(execution_result, query_analysis)
                
                # 更新策略
                await self._update_policy(rl_state, rl_action, rl_reward)
                
                # 生成结果
                result = self._generate_result(execution_result, rl_reward, query_analysis)
                
                # 计算置信度
                confidence = self._calculate_confidence(rl_reward, execution_result)
                
                processing_time = time.time() - start_time
                
                # 更新统计
                if rl_reward.value > 0:
                    self.rl_stats["successful_episodes"] += 1
                else:
                    self.rl_stats["failed_episodes"] += 1
                
                self._update_average_reward(rl_reward.value)
                self._update_action_type_stats(rl_action.action_type)
                self.rl_stats["state_transitions"] += 1
                
                return AgentResult(
                    query=query,
                    result=result,
                    confidence=confidence,
                    metadata={
                        "action_type": rl_action.action_type,
                        "reward_value": rl_reward.value,
                        "state_id": rl_state.state_id,
                        "action_id": rl_action.action_id,
                        "processing_time": processing_time,
                        "exploration_rate": self.exploration_rate
                    },
                    processing_time=processing_time
                )
                
        except Exception as e:
            logger.error(f"处理强化学习查询失败: {e}")
            self.rl_stats["failed_episodes"] += 1
            
            return AgentResult(
                query=query,
                result=f"强化学习处理失败: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
                processing_time=time.time() - start_time
            )
        finally:
            self.is_executing = False

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询类型和复杂度"""
        query_lower = query.lower()
        
        # 基础查询类型分析
        query_type = "general"
        complexity = 0.5
        
        if any(word in query_lower for word in ["学习", "训练", "优化", "改进"]):
            query_type = "learning"
            complexity = 0.8
        elif any(word in query_lower for word in ["决策", "选择", "策略", "行动"]):
            query_type = "decision"
            complexity = 0.7
        elif any(word in query_lower for word in ["预测", "估计", "评估", "分析"]):
            query_type = "prediction"
            complexity = 0.6
        elif any(word in query_lower for word in ["探索", "发现", "搜索", "寻找"]):
            query_type = "exploration"
            complexity = 0.9
        
        # 基于长度调整复杂度
        word_count = len(query.split())
        if word_count > 20:
            complexity = min(1.0, complexity + 0.2)
        elif word_count < 5:
            complexity = max(0.2, complexity - 0.2)
        
        return {
            "type": query_type,
            "complexity": complexity,
            "word_count": word_count,
            "keywords": self._extract_keywords(query),
            "urgency": self._assess_urgency(query),
            "learning_potential": self._assess_learning_potential(query)
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        words = query.split()
        keywords = []
        
        for word in words:
            if len(word) > 2 and word.isalpha():
                keywords.append(word.lower())
        
        return keywords[:10]  # 限制关键词数量

    def _assess_urgency(self, query: str) -> str:
        """评估紧急程度"""
        urgent_words = ["紧急", "立即", "马上", "尽快", "急迫"]
        query_lower = query.lower()
        
        if any(word in query_lower for word in urgent_words):
            return "high"
        elif "重要" in query_lower or "关键" in query_lower:
            return "medium"
        else:
            return "low"

    def _assess_learning_potential(self, query: str) -> float:
        """评估学习潜力"""
        learning_words = ["学习", "训练", "优化", "改进", "提升", "发展"]
        query_lower = query.lower()
        
        learning_score = 0.0
        for word in learning_words:
            if word in query_lower:
                learning_score += 0.2
        
        return min(1.0, learning_score)

    def _create_rl_state(self, query: str, query_analysis: Dict[str, Any], 
                        context: Optional[List[Dict[str, Any]]]) -> RLState:
        """创建强化学习状态"""
        state_id = f"state_{int(time.time() * 1000)}"
        
        # 创建状态特征向量
        features = []
        
        # 添加查询特征
        features.append(query_analysis.get("complexity", 0.5))
        features.append(len(query_analysis.get("keywords", [])) / 10.0)
        features.append(query_analysis.get("learning_potential", 0.0))
        
        # 添加紧急程度特征
        urgency_map = {"high": 1.0, "medium": 0.5, "low": 0.0}
        features.append(urgency_map.get(query_analysis.get("urgency", "low"), 0.0))
        
        # 添加上下文特征
        if context:
            features.append(len(context) / 10.0)
            features.append(1.0)  # 有上下文
        else:
            features.append(0.0)
            features.append(0.0)  # 无上下文
        
        # 填充到固定长度
        while len(features) < self.state_space_size:
            features.append(0.0)
        
        features = features[:self.state_space_size]
        
        return RLState(
            state_id=state_id,
            features=features,
            context={
                "query": query,
                "analysis": query_analysis,
                "context": context or []
            },
            timestamp=time.time()
        )

    async def _select_action(self, state: RLState, query_analysis: Dict[str, Any]) -> RLAction:
        """选择动作"""
        action_id = f"action_{int(time.time() * 1000)}"
        
        if self.rl_engine:
            # 使用强化学习引擎选择动作
            try:
                # 使用强化学习引擎选择动作
                # 将状态特征转换为字典格式
                state_dict = {"features": state.features}
                action_result = self.rl_engine.select_action(state_dict)
                
                # 处理返回的动作结果
                if isinstance(action_result, dict):
                    action_index = action_result.get("action", 0)
                else:
                    action_index = int(action_result) if isinstance(action_result, (int, float)) else 0
                
                action_type = self._map_action_index_to_type(action_index)
                parameters = self._get_action_parameters(action_type, query_analysis)
                confidence = self._calculate_action_confidence(action_type, query_analysis)
            except Exception as e:
                logger.warning(f"强化学习动作选择失败: {e}")
                action_type = self._rule_based_action_selection(query_analysis)
                parameters = self._get_action_parameters(action_type, query_analysis)
                confidence = 0.6
        else:
            # 回退到规则基础的动作选择
            action_type = self._rule_based_action_selection(query_analysis)
            parameters = self._get_action_parameters(action_type, query_analysis)
            confidence = 0.6
        
        return RLAction(
            action_id=action_id,
            action_type=action_type,
            parameters=parameters,
            confidence=confidence
        )

    def _map_action_index_to_type(self, action_index: int) -> str:
        """将动作索引映射到动作类型"""
        action_types = ["analyze", "learn", "predict", "explore", "optimize"]
        return action_types[action_index % len(action_types)]

    def _rule_based_action_selection(self, query_analysis: Dict[str, Any]) -> str:
        """基于规则的动作选择"""
        query_type = query_analysis.get("type", "general")
        
        action_mapping = {
            "learning": "learn",
            "decision": "analyze",
            "prediction": "predict",
            "exploration": "explore",
            "general": "optimize"
        }
        
        return action_mapping.get(query_type, "analyze")

    def _get_action_parameters(self, action_type: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """获取动作参数"""
        base_params = {
            "complexity": query_analysis.get("complexity", 0.5),
            "urgency": query_analysis.get("urgency", "low"),
            "learning_potential": query_analysis.get("learning_potential", 0.0)
        }
        
        if action_type == "learn":
            base_params.update({
                "learning_rate": self.learning_rate,
                "exploration_rate": self.exploration_rate,
                "batch_size": 32
            })
        elif action_type == "analyze":
            base_params.update({
                "analysis_depth": 5,
                "confidence_threshold": 0.7
            })
        elif action_type == "predict":
            base_params.update({
                "prediction_horizon": 10,
                "uncertainty_threshold": 0.3
            })
        elif action_type == "explore":
            base_params.update({
                "exploration_budget": 100,
                "novelty_threshold": 0.5
            })
        elif action_type == "optimize":
            base_params.update({
                "optimization_iterations": 50,
                "convergence_threshold": 0.01
            })
        
        return base_params

    def _calculate_action_confidence(self, action_type: str, query_analysis: Dict[str, Any]) -> float:
        """计算动作置信度"""
        base_confidence = 0.7
        
        # 基于查询复杂度调整
        complexity = query_analysis.get("complexity", 0.5)
        complexity_factor = 1.0 - (complexity * 0.3)
        
        # 基于学习潜力调整
        learning_potential = query_analysis.get("learning_potential", 0.0)
        learning_factor = 1.0 + (learning_potential * 0.2)
        
        final_confidence = base_confidence * complexity_factor * learning_factor
        return min(1.0, max(0.0, final_confidence))

    async def _execute_action(self, action: RLAction, state: RLState) -> Dict[str, Any]:
        """执行动作"""
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "learn":
            return await self._execute_learning_action(parameters, state)
        elif action_type == "analyze":
            return await self._execute_analysis_action(parameters, state)
        elif action_type == "predict":
            return await self._execute_prediction_action(parameters, state)
        elif action_type == "explore":
            return await self._execute_exploration_action(parameters, state)
        elif action_type == "optimize":
            return await self._execute_optimization_action(parameters, state)
        else:
            return {"result": "未知动作类型", "success": False}

    async def _execute_learning_action(self, parameters: Dict[str, Any], state: RLState) -> Dict[str, Any]:
        """执行学习动作"""
        return {
            "result": "执行学习动作",
            "success": True,
            "learning_progress": 0.1,
            "new_knowledge": ["学习到新知识"],
            "confidence": 0.8
        }

    async def _execute_analysis_action(self, parameters: Dict[str, Any], state: RLState) -> Dict[str, Any]:
        """执行分析动作"""
        return {
            "result": "执行分析动作",
            "success": True,
            "analysis_depth": parameters.get("analysis_depth", 5),
            "insights": ["分析洞察"],
            "confidence": 0.7
        }

    async def _execute_prediction_action(self, parameters: Dict[str, Any], state: RLState) -> Dict[str, Any]:
        """执行预测动作"""
        return {
            "result": "执行预测动作",
            "success": True,
            "prediction_horizon": parameters.get("prediction_horizon", 10),
            "predictions": ["预测结果"],
            "confidence": 0.6
        }

    async def _execute_exploration_action(self, parameters: Dict[str, Any], state: RLState) -> Dict[str, Any]:
        """执行探索动作"""
        return {
            "result": "执行探索动作",
            "success": True,
            "exploration_budget": parameters.get("exploration_budget", 100),
            "discoveries": ["探索发现"],
            "confidence": 0.9
        }

    async def _execute_optimization_action(self, parameters: Dict[str, Any], state: RLState) -> Dict[str, Any]:
        """执行优化动作"""
        return {
            "result": "执行优化动作",
            "success": True,
            "optimization_iterations": parameters.get("optimization_iterations", 50),
            "improvements": ["优化改进"],
            "confidence": 0.8
        }

    def _calculate_reward(self, execution_result: Dict[str, Any], query_analysis: Dict[str, Any]) -> RLReward:
        """计算奖励"""
        reward_id = f"reward_{int(time.time() * 1000)}"
        
        # 基础奖励
        base_reward = 0.0
        if execution_result.get("success", False):
            base_reward = 1.0
        
        # 基于置信度的奖励
        confidence_reward = execution_result.get("confidence", 0.0) * 0.5
        
        # 基于学习潜力的奖励
        learning_potential = query_analysis.get("learning_potential", 0.0)
        learning_reward = learning_potential * 0.3
        
        # 基于复杂度的奖励
        complexity = query_analysis.get("complexity", 0.5)
        complexity_reward = complexity * 0.2
        
        total_reward = base_reward + confidence_reward + learning_reward + complexity_reward
        
        return RLReward(
            reward_id=reward_id,
            value=total_reward,
            components={
                "base_reward": base_reward,
                "confidence_reward": confidence_reward,
                "learning_reward": learning_reward,
                "complexity_reward": complexity_reward
            },
            timestamp=time.time()
        )

    async def _update_policy(self, state: RLState, action: RLAction, reward: RLReward):
        """更新策略"""
        if self.rl_engine:
            try:
                # 使用强化学习引擎更新策略
                # 注意：这里使用简化的更新方法，因为原始方法可能不存在
                if hasattr(self.rl_engine, 'update_policy'):
                    state_dict = {"features": state.features}
                    next_state_dict = {"features": state.features}
                    self.rl_engine.update_policy(
                        state_dict,
                        action.action_id,
                        reward.value,
                        next_state_dict
                    )
                else:
                    # 使用经验回放更新
                    if hasattr(self.rl_engine, 'store_experience'):
                        state_dict = {"features": state.features}
                        next_state_dict = {"features": state.features}
                        self.rl_engine.store_experience(
                            state_dict,
                            action.action_id,
                            reward.value,
                            next_state_dict
                        )
                
                # 更新探索率
                self.exploration_rate = max(0.01, self.exploration_rate * 0.995)
                self.rl_stats["exploration_rate"] = self.exploration_rate
                
                logger.debug(f"策略更新完成，奖励: {reward.value:.3f}")
            except Exception as e:
                logger.warning(f"策略更新失败: {e}")

    def _generate_result(self, execution_result: Dict[str, Any], reward: RLReward, 
                        query_analysis: Dict[str, Any]) -> str:
        """生成结果"""
        result_parts = []
        
        # 添加执行结果
        result_parts.append(f"执行结果: {execution_result.get('result', '未知')}")
        
        # 添加奖励信息
        result_parts.append(f"奖励值: {reward.value:.3f}")
        
        # 添加置信度
        confidence = execution_result.get("confidence", 0.0)
        result_parts.append(f"置信度: {confidence:.3f}")
        
        # 添加学习进度
        if "learning_progress" in execution_result:
            result_parts.append(f"学习进度: {execution_result['learning_progress']:.3f}")
        
        # 添加具体结果
        if "insights" in execution_result:
            result_parts.append(f"分析洞察: {', '.join(execution_result['insights'])}")
        elif "predictions" in execution_result:
            result_parts.append(f"预测结果: {', '.join(execution_result['predictions'])}")
        elif "discoveries" in execution_result:
            result_parts.append(f"探索发现: {', '.join(execution_result['discoveries'])}")
        elif "improvements" in execution_result:
            result_parts.append(f"优化改进: {', '.join(execution_result['improvements'])}")
        
        return "\n".join(result_parts)

    def _calculate_confidence(self, reward: RLReward, execution_result: Dict[str, Any]) -> float:
        """计算置信度"""
        # 基于奖励的置信度
        reward_confidence = min(1.0, max(0.0, reward.value))
        
        # 基于执行结果的置信度
        execution_confidence = execution_result.get("confidence", 0.0)
        
        # 综合置信度
        combined_confidence = (reward_confidence * 0.6 + execution_confidence * 0.4)
        
        return min(1.0, max(0.0, combined_confidence))

    def _update_average_reward(self, reward_value: float):
        """更新平均奖励"""
        total_episodes = self.rl_stats["total_episodes"]
        current_avg = self.rl_stats["average_reward"]
        
        # 计算新的平均值
        new_avg = (current_avg * (total_episodes - 1) + reward_value) / total_episodes
        self.rl_stats["average_reward"] = new_avg

    def _update_action_type_stats(self, action_type: str):
        """更新动作类型统计"""
        if action_type not in self.rl_stats["action_types"]:
            self.rl_stats["action_types"][action_type] = 0
        self.rl_stats["action_types"][action_type] += 1

    def get_rl_stats(self) -> Dict[str, Any]:
        """获取强化学习统计信息"""
        return self.rl_stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.rl_stats = {
            "total_episodes": 0,
            "successful_episodes": 0,
            "failed_episodes": 0,
            "average_reward": 0.0,
            "learning_progress": 0.0,
            "exploration_rate": self.exploration_rate,
            "action_types": {},
            "state_transitions": 0
        }

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.rl_config.copy()

    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.rl_config.update(config)
        
        # 更新参数
        if "learning_rate" in config:
            self.learning_rate = config["learning_rate"]
        if "exploration_rate" in config:
            self.exploration_rate = config["exploration_rate"]
        if "discount_factor" in config:
            self.discount_factor = config["discount_factor"]

    async def _execute_core_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行核心任务"""
        return {"result": "强化学习任务执行完成", "status": "success"}

# 全局实例
_enhanced_rl_agent = None

def get_enhanced_rl_agent() -> EnhancedRLAgent:
    """获取增强强化学习智能体实例"""
    global _enhanced_rl_agent
    if _enhanced_rl_agent is None:
        _enhanced_rl_agent = EnhancedRLAgent()
    return _enhanced_rl_agent

# 定义缺失的函数
def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """获取智能配置"""
    try:
        center = get_unified_center('get_unified_config_center')
        if center:
            return center.get_smart_config(key, context or {})
    except Exception as e:
        # 记录配置获取错误
        if not hasattr(enhanced_rl_agent, 'config_errors'):
            enhanced_rl_agent.config_errors = []
        enhanced_rl_agent.config_errors.append({
            'key': key,
            'error': str(e),
            'timestamp': time.time()
        })
        # 返回默认配置
        return _get_default_rl_config(key, context or {})
    
def _get_default_rl_config(key: str, context: Dict[str, Any]) -> Any:
    """获取默认RL配置"""
    try:
        # 默认RL配置映射
        default_configs = {
            'learning_rate': 0.001,
            'discount_factor': 0.99,
            'epsilon': 0.1,
            'epsilon_decay': 0.995,
            'epsilon_min': 0.01,
            'batch_size': 32,
            'memory_size': 10000,
            'target_update_freq': 100,
            'exploration_steps': 1000,
            'training_freq': 4
        }
        
        # 根据上下文调整配置
        if context.get('high_exploration', False):
            default_configs['epsilon'] = 0.3
            default_configs['exploration_steps'] = 2000
        
        if context.get('fast_convergence', False):
            default_configs['learning_rate'] = 0.01
            default_configs['target_update_freq'] = 50
        
        return default_configs.get(key, None)
        
    except Exception:
        return None
    return None

def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """创建查询上下文"""
    return {
        "query": query,
        "user_id": user_id,
        "timestamp": time.time()
    }