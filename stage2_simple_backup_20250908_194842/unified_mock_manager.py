"""
统一Mock管理器
整合所有分散的Mock类定义，提供统一的Mock对象管理
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

@dataclass
class MockConfig:
    """Mock配置"""
    default_confidence: Optional[float] = None
    default_threshold: Optional[float] = None
    default_quality: Optional[float] = None
    default_complexity: Optional[float] = None

class UnifiedMockManager:
    """统一Mock管理器"""
    
    def __init__(self, config: Optional[MockConfig] = None):
        # 使用智能配置系统获取默认配置
        if config is None:
            mock_context = create_query_context(query_type="mock_config")
            config = MockConfig(
                default_confidence=get_smart_config("mock_default_confidence", mock_context),
                default_threshold=get_smart_config("mock_default_threshold", mock_context),
                default_quality=get_smart_config("mock_default_quality", mock_context),
                default_complexity=get_smart_config("mock_default_complexity", mock_context)
            )

        self.config = config
        self.mock_objects: Dict[str, Any] = {}
        self.usage_stats: Dict[str, int] = {}
        self._initialize_mock_objects()
    
    def _initialize_mock_objects(self):
        """初始化所有Mock对象"""
        self.mock_objects['MockThresholdManager'] = self._create_mock_threshold_manager()
        self.mock_objects['MockConfigManager'] = self._create_mock_config_manager()
        self.mock_objects['MockIntelligentReplacer'] = self._create_mock_intelligent_replacer()
        self.mock_objects['MockUnifiedScorer'] = self._create_mock_unified_scorer()
        
        logger.info(f"✅ 初始化了 {len(self.mock_objects)} 个Mock对象")
    
    def _create_mock_threshold_manager(self):
        """创建Mock阈值管理器"""
        class MockThresholdManager:
            def __init__(self, config: MockConfig):
                self.config = config
            
            def get_dynamic_threshold(self, threshold_type: str, context: Optional[str] = None, default: Optional[float] = None) -> float:
                if default is None:
                    default = self.config.default_threshold
                
                if threshold_type == "confidence":
                    return self.config.default_confidence
                elif threshold_type == "quality":
                    return self.config.default_quality
                elif threshold_type == "complexity":
                    return self.config.default_complexity
                else:
                    return default
        
        return MockThresholdManager(self.config)
    
    def _create_mock_config_manager(self):
        """创建Mock配置管理器"""
        class MockConfigManager:
            def __init__(self, config: MockConfig):
                self.config = config
                self._config_cache = {}
            
            def get_config(self, key: str, default: Any = None) -> Any:
                return self._config_cache.get(key, default)
            
            def set_config(self, key: str, value: Any):
                self._config_cache[key] = value
        
        return MockConfigManager(self.config)
    
    def _create_mock_intelligent_replacer(self):
        """创建Mock智能替换器"""
        class MockIntelligentReplacer:
            def __init__(self, config: MockConfig):
                self.config = config
            
            def get_intelligent_confidence(self, context: str, param_type: str = "default") -> float:
                return self.config.default_confidence
            
            def get_intelligent_threshold(self, context: str, param_type: str = "default") -> float:
                return self.config.default_threshold
        
        return MockIntelligentReplacer(self.config)
    
    def _create_mock_unified_scorer(self):
        """创建Mock统一评分器"""
        class MockUnifiedScorer:
            def __init__(self, config: MockConfig):
                self.config = config
            
            def get_dynamic_confidence(self, context: str, **kwargs) -> float:
                return self.config.default_confidence
            
            def get_dynamic_confidence_threshold(self, context: str, **kwargs) -> float:
                return self.config.default_confidence
            
            def get_dynamic_complexity_score(self, context: str, **kwargs) -> float:
                return self.config.default_complexity
            
            def get_dynamic_quality_threshold(self, context: str, **kwargs) -> float:
                return self.config.default_quality
        
        return MockUnifiedScorer(self.config)
    
    def get_mock_object(self, mock_type: str) -> Any:
        """获取指定类型的Mock对象"""
        if mock_type not in self.mock_objects:
            logger.warning(f"⚠️ 未知的Mock类型: {mock_type}")
            return None
        
        self.usage_stats[mock_type] = self.usage_stats.get(mock_type, 0) + 1
        return self.mock_objects[mock_type]
    
    def get_usage_stats(self) -> Dict[str, int]:
        """获取使用统计"""
        return self.usage_stats.copy()

# 全局实例
_unified_mock_manager = None

def get_unified_mock_manager(config: Optional[MockConfig] = None) -> UnifiedMockManager:
    """获取统一Mock管理器实例"""
    global _unified_mock_manager
    if _unified_mock_manager is None:
        _unified_mock_manager = UnifiedMockManager(config)
    return _unified_mock_manager

# 便捷函数
def get_mock_threshold_manager() -> Any:
    """获取Mock阈值管理器"""
    manager = get_unified_mock_manager()
    return manager.get_mock_object('MockThresholdManager')

def get_mock_config_manager() -> Any:
    """获取Mock配置管理器"""
    manager = get_unified_mock_manager()
    return manager.get_mock_object('MockConfigManager')

def get_mock_intelligent_replacer() -> Any:
    """获取Mock智能替换器"""
    manager = get_unified_mock_manager()
    return manager.get_mock_object('MockIntelligentReplacer')

def get_mock_unified_scorer() -> Any:
    """获取Mock统一评分器"""
    manager = get_unified_mock_manager()
    return manager.get_mock_object('MockUnifiedScorer')
