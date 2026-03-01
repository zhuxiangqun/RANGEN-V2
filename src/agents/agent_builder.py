#!/usr/bin/env python3
"""
智能体建造者 - 使用建造者模式
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional, Type, Union
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np


class Component(ABC):
    """智能体建造者接口 - AI增强版"""
    
    def __init__(self):
        self.agent_id: Optional[str] = None
        self.agent_type: Optional[str] = None
        self.capabilities: List[str] = []
        self.config: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        self._ai_network = None
    
    def set_id(self, agent_id: str) -> 'Component':
        """设置智能体ID"""
        self.agent_id = agent_id
        return self
    
    def set_type(self, agent_type: str) -> 'Component':
        """设置智能体类型"""
        self.agent_type = agent_type
        return self
    
    def add_capability(self, capability: str) -> 'Component':
        """添加能力"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
        return self
    
    def set_capabilities(self, capabilities: List[str]) -> 'Component':
        """设置能力列表"""
        self.capabilities = capabilities.copy()
        return self
    
    def set_config(self, key: str, value: Any) -> 'Component':
        """设置配置"""
        self.config[key] = value
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'Component':
        """设置元数据"""
        self.metadata[key] = value
        return self
    
    @abstractmethod
    def build(self) -> Any:
        """构建智能体"""
        try:
            # 验证构建参数
            if not self._validate_build_parameters():
                raise ValueError("Invalid build parameters")
            
            # 创建智能体实例
            agent = self._create_agent_instance()
            
            # 配置智能体
            self._configure_agent(agent)
            
            # 初始化智能体
            self._initialize_agent(agent)
            
            # 记录构建历史
            self._record_build_history(agent)
            
            return agent
            
        except Exception as e:
            # 记录构建错误
            self._record_build_error(e)
            raise e
    
    def _validate_build_parameters(self) -> bool:
        """验证构建参数"""
        return hasattr(self, 'agent_type') and self.agent_type is not None
    
    def _create_agent_instance(self) -> Any:
        """创建智能体实例"""
        if not hasattr(self, 'agent_type'):
            raise ValueError("Agent type not specified")
        
        # 根据类型创建智能体
        if self.agent_type == 'reasoning':
            return self._create_reasoning_agent()
        elif self.agent_type == 'answer_generation':
            return self._create_answer_generation_agent()
        elif self.agent_type == 'strategy':
            return self._create_strategy_agent()
        else:
            return self._create_default_agent()
    
    def _create_reasoning_agent(self) -> Any:
        """创建推理智能体"""
        from ..services.reasoning_service import ReasoningService
        return ReasoningService()
    
    def _create_answer_generation_agent(self) -> Any:
        """创建答案生成智能体"""
        from ..services.answer_generation_service import AnswerGenerationService
        return AnswerGenerationService()
    
    def _create_strategy_agent(self) -> Any:
        """创建策略智能体"""
        from .intelligent_strategy_agent_wrapper import IntelligentStrategyAgentWrapper
        return IntelligentStrategyAgentWrapper(enable_gradual_replacement=True)
    
    def _create_default_agent(self) -> Any:
        """创建默认智能体"""
        from src.agents.base_agent import BaseAgent
        return BaseAgent()
    
    def _configure_agent(self, agent: Any):
        """配置智能体"""
        if hasattr(self, 'config') and self.config:
            for key, value in self.config.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
    
    def _initialize_agent(self, agent: Any):
        """初始化智能体"""
        if hasattr(agent, 'initialize'):
            agent.initialize()
    
    def _record_build_history(self, agent: Any):
        """记录构建历史"""
        if not hasattr(self, 'build_history'):
            self.build_history = []
        
        self.build_history.append({
            'agent_type': self.agent_type,
            'agent': agent,
            'timestamp': time.time()
        })
    
    def _record_build_error(self, error: Exception):
        """记录构建错误"""
        if not hasattr(self, 'build_errors'):
            self.build_errors = []
        
        self.build_errors.append({
            'error': str(error),
            'timestamp': time.time()
        })
    

class AgentBuilder(Component):
    """智能体建造者"""
    
    def __init__(self):
        super().__init__()
        self._build_strategy: Optional[str] = None
        self._ai_enhanced: bool = False
        self._complexity_score: float = 0.0
        self._capability_requirements: Dict[str, Any] = {}
        self._config_richness: float = 0.0
        self._agent_type_complexity: float = 0.0
        self._build_difficulty: float = 0.0
    
    def set_build_strategy(self, strategy: str) -> 'Component':
        """设置构建策略"""
        self._build_strategy = strategy
        return self
    
    def enable_ai_enhancement(self) -> 'Component':
        """启用AI增强"""
        self._ai_enhanced = True
        return self
    
    def set_complexity_score(self, score: float) -> 'Component':
        """设置复杂度分数"""
        self._complexity_score = score
        return self
    
    def set_capability_requirements(self, requirements: Dict[str, Any]) -> 'Component':
        """设置能力需求"""
        self._capability_requirements = requirements.copy()
        return self

    def set_config_richness(self, richness: float) -> 'Component':
        """设置配置丰富度"""
        self._config_richness = richness
        return self
    
    def set_agent_type_complexity(self, complexity: float) -> 'Component':
        """设置智能体类型复杂度"""
        self._agent_type_complexity = complexity
        return self
    
    def set_build_difficulty(self, difficulty: float) -> 'Component':
        """设置构建难度"""
        self._build_difficulty = difficulty
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建智能体"""
        try:
            # AI智能分析构建需求
            build_requirements = self._ai_analyze_build_requirements()
            
            # AI选择构建策略
            strategy = self._ai_select_build_strategy(build_requirements)
            
            # 执行AI增强构建
            agent_config = self._perform_ai_enhanced_build(strategy)
            
            # AI学习更新
            self._ai_learning_update(agent_config)
            
            self.logger.info(f"智能体构建完成: {self.agent_id}")
            return agent_config
            
        except Exception as e:
            self.logger.error(f"智能体构建失败: {e}")
            return {}
    
    def _ai_analyze_build_requirements(self) -> Dict[str, Any]:
        """AI分析构建需求"""
        return {
            "capabilities": self.capabilities,
            "config": self.config,
            "complexity": self._complexity_score,
            "requirements": self._capability_requirements
        }
    
    def _ai_select_build_strategy(self, requirements: Dict[str, Any]) -> str:
        """AI选择构建策略"""
        if self._build_strategy:
            return self._build_strategy
        
        # 基于复杂度选择策略
        if self._complexity_score > 0.8:
            return "expert"
        elif self._complexity_score > 0.5:
            return "advanced"
        else:
            return "standard"
    
    def _perform_ai_enhanced_build(self, strategy: str) -> Dict[str, Any]:
        """执行AI增强构建"""
        if strategy == "expert":
            return self._expert_build()
        elif strategy == "advanced":
            return self._advanced_build()
        else:
            return self._standard_build()
    
    def _ai_learning_update(self, agent_config: Dict[str, Any]) -> None:
        """AI学习更新"""
        # 更新构建统计
        self.metadata["build_time"] = time.time()
        self.metadata["strategy"] = self._build_strategy
        self.metadata["ai_enhanced"] = self._ai_enhanced
    
    def _expert_build(self) -> Dict[str, Any]:
        """专家级构建"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "config": self.config,
            "metadata": self.metadata,
            "build_level": "expert",
            "ai_enhanced": True
        }
    
    def _advanced_build(self) -> Dict[str, Any]:
        """高级构建"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "config": self.config,
            "metadata": self.metadata,
            "build_level": "advanced",
            "ai_enhanced": True
        }
    
    def _standard_build(self) -> Dict[str, Any]:
        """标准构建"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "config": self.config,
            "metadata": self.metadata,
            "build_level": "standard",
            "ai_enhanced": False
        }
    
    def get_build_info(self) -> Dict[str, Any]:
        """获取构建信息"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "config_keys": list(self.config.keys()),
            "metadata_keys": list(self.metadata.keys()),
            "build_strategy": self._build_strategy,
            "ai_enhanced": self._ai_enhanced,
            "complexity_score": self._complexity_score
        }


class AgentDirector:
    """智能体导演 - 管理构建过程"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._builders: Dict[str, AgentBuilder] = {}
        self._build_history: List[Dict[str, Any]] = []
    
    def register_builder(self, name: str, builder: AgentBuilder) -> None:
        """注册建造者"""
        self._builders[name] = builder
        self.logger.info(f"注册建造者: {name}")
    
    def create_agent(self, builder_name: str, agent_id: str, agent_type: str) -> Optional[Dict[str, Any]]:
        """创建智能体"""
        if builder_name not in self._builders:
            self.logger.error(f"未找到建造者: {builder_name}")
            return None
        
        builder = self._builders[builder_name]
        agent_config = (builder
                       .set_id(agent_id)
                       .set_type(agent_type)
                       .build())
        
        if agent_config:
            self._build_history.append({
                "builder_name": builder_name,
                "agent_id": agent_id,
                "agent_type": agent_type,
                "build_time": time.time(),
                "success": True
            })
        
        return agent_config
    
    def get_build_history(self) -> List[Dict[str, Any]]:
        """获取构建历史"""
        return self._build_history.copy()
    
    def get_builder_info(self, builder_name: str) -> Optional[Dict[str, Any]]:
        """获取建造者信息"""
        if builder_name not in self._builders:
            return None
        
        return self._builders[builder_name].get_build_info()


# 全局导演实例
_agent_director: Optional[AgentDirector] = None


def get_agent_director() -> AgentDirector:
    """获取智能体导演实例"""
    global _agent_director
    if _agent_director is None:
        _agent_director = AgentDirector()
    return _agent_director


def create_agent_builder() -> AgentBuilder:
    """创建智能体建造者"""
    return AgentBuilder()


def build_agent(agent_id: str, agent_type: str, capabilities: List[str], 
                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """快速构建智能体"""
    builder = create_agent_builder()
    
    # 设置基本信息
    builder.set_id(agent_id).set_type(agent_type).set_capabilities(capabilities)
    
    # 设置配置
    if config:
        for key, value in config.items():
            builder.set_config(key, value)
    
    # 计算复杂度
    complexity = _calculate_complexity(capabilities, config or {})
    builder.set_complexity_score(complexity)
    
    # 构建
    return builder.build()


def _calculate_complexity(capabilities: List[str], config: Dict[str, Any]) -> float:
    """计算复杂度"""
    base_complexity = len(capabilities) * 0.1
    config_complexity = len(config) * 0.05
    return min(1.0, base_complexity + config_complexity)