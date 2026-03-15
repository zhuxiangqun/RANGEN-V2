"""
智能体集成管理器 - 统一管理所有智能体与核心系统的集成
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from src.utils.prompt_engine import get_prompt_engine, PromptEngine
from src.utils.unified_dependency_manager import get_dependency
from src.utils.unified_scoring_center import get_unified_intelligent_scorer
from src.utils.unified_intelligent_center import get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class AgentIntegrationConfig:
    """智能体集成配置"""
    agent_name: str
    use_prompt_engine: bool = True
    use_intelligent_scorer: bool = True
    use_threshold_manager: bool = True
    use_config_manager: bool = True
    integration_priority: int = 1

class AgentIntegrationManager:
    """智能体集成管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_configs: Dict[str, AgentIntegrationConfig] = {}
        self.integration_status: Dict[str, Dict[str, bool]] = {}
        
        # 初始化核心系统
        self._init_core_systems()
        
        # 注册默认智能体配置
        self._register_default_agents()
    
    def _init_core_systems(self):
        """初始化核心系统"""
        try:
            self.prompt_engine = get_prompt_engine()
            self.intelligent_scorer = get_unified_intelligent_scorer()
            self.threshold_manager = get_unified_intelligent_center()
            self.config_manager = get_dependency('unified_config_center')
            self.logger.info("核心系统初始化成功")
        except Exception as e:
            self.logger.warning(f"核心系统初始化失败: {e}")
            self.prompt_engine = None
            self.intelligent_scorer = None
            self.threshold_manager = None
            self.config_manager = None
    
    def _register_default_agents(self):
        """注册默认智能体配置"""
        default_agents = [
            ("EnhancedReasoningAgent", 1),
            ("EnhancedKnowledgeRetrievalAgent", 2),
            ("EnhancedAnswerGenerationAgent", config.DEFAULT_MAX_RETRIES),
            ("EnhancedAnalysisAgent", 4),
            ("EnhancedCitationAgent", config.DEFAULT_TOP_K),
            ("IntelligentCoordinatorAgent", 6),
            ("FactVerificationAgent", 7),
            ("LearningSystem", 8),
            ("IntelligentStrategyAgent", 9),
            ("EnhancedRLAgent", config.DEFAULT_SMALL_LIMIT),
        ]
        
        for agent_name, priority in default_agents:
            self.register_agent(agent_name, priority)
    
    def register_agent(self, agent_name: str, priority: int = 1):
        """注册智能体"""
        config = AgentIntegrationConfig(
            agent_name=agent_name,
            integration_priority=priority
        )
        self.agent_configs[agent_name] = config
        self.integration_status[agent_name] = {
            "prompt_engine": False,
            "intelligent_scorer": False,
            "threshold_manager": False,
            "config_manager": False
        }
        self.logger.info(f"智能体 {agent_name} 注册成功，优先级: {priority}")
    
    def get_integration_services(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体的集成服务"""
        if agent_name not in self.agent_configs:
            self.logger.warning(f"智能体 {agent_name} 未注册")
            return {}
        
        services = {}
        
        # 提示词引擎集成
        if self.prompt_engine and self.agent_configs[agent_name].use_prompt_engine:
            services["prompt_engine"] = self.prompt_engine
            self.integration_status[agent_name]["prompt_engine"] = True
        
        # 智能评分器集成
        if self.intelligent_scorer and self.agent_configs[agent_name].use_intelligent_scorer:
            services["intelligent_scorer"] = self.intelligent_scorer
            self.integration_status[agent_name]["intelligent_scorer"] = True
        
        # 阈值管理器集成
        if self.threshold_manager and self.agent_configs[agent_name].use_threshold_manager:
            services["threshold_manager"] = self.threshold_manager
            self.integration_status[agent_name]["threshold_manager"] = True
        
        # 配置管理器集成
        if self.config_manager and self.agent_configs[agent_name].use_config_manager:
            services["config_manager"] = self.config_manager
            self.integration_status[agent_name]["config_manager"] = True
        
        return services
    
    def optimize_agent_integration(self, agent_name: str):
        """优化智能体集成"""
        if agent_name not in self.agent_configs:
            return
        
        config = self.agent_configs[agent_name]
        status = self.integration_status[agent_name]
        
        # 根据优先级调整集成策略
        if config.integration_priority <= config.DEFAULT_MAX_RETRIES:  # 高优先级智能体
            config.use_prompt_engine = True
            config.use_intelligent_scorer = True
            config.use_threshold_manager = True
            config.use_config_manager = True
        elif config.integration_priority <= 6:  # 中优先级智能体
            config.use_prompt_engine = True
            config.use_intelligent_scorer = True
            config.use_threshold_manager = False
            config.use_config_manager = True
        else:  # 低优先级智能体
            config.use_prompt_engine = True
            config.use_intelligent_scorer = False
            config.use_threshold_manager = False
            config.use_config_manager = False
        
        self.logger.info(f"智能体 {agent_name} 集成优化完成")
    
    def get_integration_report(self) -> Dict[str, Any]:
        """获取集成报告"""
        report = {
            "total_agents": len(self.agent_configs),
            "integration_status": self.integration_status,
            "core_systems": {
                "prompt_engine": self.prompt_engine is not None,
                "intelligent_scorer": self.intelligent_scorer is not None,
                "threshold_manager": self.threshold_manager is not None,
                "config_manager": self.config_manager is not None
            },
            "optimization_recommendations": []
        }
        
        # 生成优化建议
        for agent_name, status in self.integration_status.items():
            if not any(status.values()):
                report["optimization_recommendations"].append(
                    f"智能体 {agent_name} 建议启用核心系统集成"
                )
        
        return report
    
    def validate_integration(self, agent_name: str) -> bool:
        """验证智能体集成状态"""
        if agent_name not in self.integration_status:
            return False
        
        status = self.integration_status[agent_name]
        return any(status.values())

# 全局实例
_agent_integration_manager = None

def get_agent_integration_manager() -> AgentIntegrationManager:
    """获取智能体集成管理器实例"""
    global _agent_integration_manager
    if _agent_integration_manager is None:
        _agent_integration_manager = AgentIntegrationManager()
    return _agent_integration_manager
