"""
统一配置优化器框架
为所有配置文件提供智能化的参数优化和管理
"""

import json
import logging
import statistics
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseConfigOptimizer(ABC):
    """配置优化器基类"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config_data = self._load_config()
        self.optimization_history = []
        self.performance_metrics = []
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败 {self.config_file}: {e}")
            return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 添加元数据
            if 'metadata' not in self.config_data:
                self.config_data['metadata'] = {}
            
            self.config_data['metadata'].update({
                'last_optimized': datetime.now().isoformat(),
                'optimizer_version': '1.0.0',
                'optimization_count': len(self.optimization_history)
            })
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ 配置已保存: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败 {self.config_file}: {e}")
    
    @abstractmethod
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化参数"""
        pass
    
    @abstractmethod
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        pass
    
    def record_performance(self, metrics: Dict[str, Any]):
        """记录性能指标"""
        self.performance_metrics.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })
        
        # 限制历史记录数量
        if len(self.performance_metrics) > get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):
            self.performance_metrics = self.performance_metrics[-get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):]

class UnifiedConfigManager:
    """统一配置管理器"""
    
    def __init__(self):
        self.optimizers = {}
        self._initialize_optimizers()
    
    def _initialize_optimizers(self):
        """初始化所有配置优化器"""
        config_mappings = {
            # 评估相关配置
            'evaluation_optimization.json': EvaluationOptimizer or GenericConfigOptimizer,
            'framework_evaluation.json': FramesEvaluationOptimizer or GenericConfigOptimizer,
            'evaluation_presets.json': FastEvaluationOptimizer or GenericConfigOptimizer,
            'evaluation_modes.json': LightweightEvaluationOptimizer or GenericConfigOptimizer,
            'confidence_config.json': DynamicConfidenceOptimizer or GenericConfigOptimizer,

            # 性能相关配置
            'system_performance.json': PerformanceOptimizer or GenericConfigOptimizer,
            'batch_config.json': BatchProcessingOptimizer or GenericConfigOptimizer,
            'production_settings.json': ProductionConfigOptimizer or GenericConfigOptimizer,

            # 数据处理相关配置
            'data_pipeline.json': DataProcessingOptimizer or GenericConfigOptimizer,
        }
        
        for config_file, optimizer_class in config_mappings.items():
            config_path = f"config/{config_file}"
            if Path(config_path).exists():
                try:
                    # 动态导入优化器类
                    optimizer = self._create_optimizer(optimizer_class, config_path)
                    if optimizer:
                        self.optimizers[config_file] = optimizer
                        logger.info(f"✅ 已加载优化器: {config_file}")
                except Exception as e:
                    logger.warning(f"⚠️ 加载优化器失败 {config_file}: {e}")
    
    def _create_optimizer(self, optimizer_class, config_path: str) -> Optional[BaseConfigOptimizer]:
        """创建优化器实例"""
        try:
            # 直接使用类创建实例
            return optimizer_class(config_path)
        except Exception as e:
            logger.error(f"创建优化器失败 {optimizer_class.__name__ if hasattr(optimizer_class, '__name__') else optimizer_class}: {e}")
            return None
    
    def optimize_all_configs(self, performance_data: Dict[str, Any]):
        """优化所有配置文件"""
        results = {}
        
        for config_file, optimizer in self.optimizers.items():
            try:
                optimization_result = optimizer.optimize_parameters(performance_data)
                optimizer.save_config()
                results[config_file] = optimization_result
                
                logger.info(f"✅ 已优化配置: {config_file}")
                
            except Exception as e:
                logger.error(f"❌ 优化配置失败 {config_file}: {e}")
                results[config_file] = {'error': str(e)}
        
        return results
    
    def get_all_optimization_suggestions(self) -> Dict[str, List[str]]:
        """获取所有优化建议"""
        suggestions = {}
        
        for config_file, optimizer in self.optimizers.items():
            try:
                suggestions[config_file] = optimizer.get_optimization_suggestions()
            except Exception as e:
                logger.error(f"获取建议失败 {config_file}: {e}")
                suggestions[config_file] = [f"获取建议失败: {e}"]
        
        return suggestions
    
    def record_performance_for_all(self, metrics: Dict[str, Any]):
        """为所有优化器记录性能"""
        for optimizer in self.optimizers.values():
            optimizer.record_performance(metrics)

# 导入具体的优化器实现
try:
    from .evaluation_optimizer import (
        EvaluationOptimizer,
        FramesEvaluationOptimizer,
        FastEvaluationOptimizer,
        LightweightEvaluationOptimizer,
        DynamicConfidenceOptimizer
    )
except ImportError:
    logger.warning("无法导入评估优化器，使用通用优化器")
    EvaluationOptimizer = None

try:
    from .performance_optimizer import (
        PerformanceOptimizer,
        BatchProcessingOptimizer,
        ProductionConfigOptimizer
    )
except ImportError:
    logger.warning("无法导入性能优化器，使用通用优化器")
    PerformanceOptimizer = None

try:
    from .data_processing_optimizer import (
        DataProcessingOptimizer,
        FramesDataProcessingOptimizer
    )
except ImportError:
    logger.warning("无法导入数据处理优化器，使用通用优化器")
    DataProcessingOptimizer = None

# 通用优化器（当专用优化器不存在时使用）
class GenericConfigOptimizer(BaseConfigOptimizer):
    """通用配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """通用参数优化逻辑"""
        # 这里可以实现通用的参数优化算法
        return {
            'optimized_parameters': 0,
            'performance_improvement': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
            'method': 'generic'
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取通用优化建议"""
        return [
            "建议实现专门的配置优化器",
            "考虑基于性能数据的参数调整",
            "定期检查和更新配置参数"
        ]

# 全局统一配置管理器实例
_unified_config_manager = None

def get_unified_config_manager() -> UnifiedConfigManager:
    """获取统一配置管理器实例"""
    global _unified_config_manager
    if _unified_config_manager is None:
        _unified_config_manager = UnifiedConfigManager()
    return _unified_config_manager
