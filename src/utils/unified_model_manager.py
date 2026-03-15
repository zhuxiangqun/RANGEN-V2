"""
统一模型管理器
整合所有模型管理功能，提供智能、动态、可扩展的模型管理
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List, Union, Type
from datetime import datetime
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ModelLifecycleManager:
    """模型生命周期管理器"""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_states: Dict[str, str] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    def register_model(self, name: str, model: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """注册模型"""
        try:
            # 验证输入
            if not self._validate_model_registration(name, model):
                return False
            
            with self.lock:
                # 检查模型是否已存在
                if name in self.models:
                    logger.warning(f"模型已存在: {name}")
                    return False
                
                # 注册模型
                self.models[name] = model
                self.model_states[name] = 'registered'
                self.model_metadata[name] = metadata or {}
                self.model_metadata[name]['registered_at'] = datetime.now()
                
                # 记录注册历史
                self._record_model_registration(name, model, metadata)
                
                logger.info(f"模型注册成功: {name}")
                return True
                
        except Exception as e:
            logger.error(f"模型注册失败: {e}")
            return False
    
    def _validate_model_registration(self, name: str, model: Any) -> bool:
        """验证模型注册"""
        if not isinstance(name, str) or not name.strip():
            return False
        
        if model is None:
            return False
        
        return True
    
    def _record_model_registration(self, name: str, model: Any, metadata: Optional[Dict[str, Any]]):
        """记录模型注册历史"""
        if not hasattr(self, 'registration_history'):
            self.registration_history = []
        
        self.registration_history.append({
            'action': 'register_model',
            'name': name,
            'model_type': type(model).__name__,
            'metadata': metadata,
            'timestamp': time.time()
        })

    def unregister_model(self, name: str) -> bool:
        """注销模型"""
        with self.lock:
            if name in self.models:
                del self.models[name]
                del self.model_states[name]
                del self.model_metadata[name]
                logger.info(f"模型注销成功: {name}")
                return True
            return False

    def get_model(self, name: str) -> Optional[Any]:
        """获取模型"""
        return self.models.get(name)

    def get_model_state(self, name: str) -> str:
        """获取模型状态"""
        return self.model_states.get(name, 'unknown')

    def update_model_state(self, name: str, state: str) -> bool:
        """更新模型状态"""
        with self.lock:
            if name in self.model_states:
                self.model_states[name] = state
                self.model_metadata[name]['last_state_change'] = datetime.now()
                logger.info(f"模型状态更新: {name} -> {state}")
                return True
            return False

    def get_model_metadata(self, name: str) -> Dict[str, Any]:
        """获取模型元数据"""
        return self.model_metadata.get(name, {})

class ModelPerformanceTracker:
    """模型性能跟踪器"""

    def __init__(self):
        self.performance_data: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.RLock()

    def record_performance(self, model_name: str, metrics: Dict[str, Any]) -> None:
        """记录性能指标"""
        with self.lock:
            if model_name not in self.performance_data:
                self.performance_data[model_name] = []

            metrics['timestamp'] = datetime.now()
            self.performance_data[model_name].append(metrics)

            if len(self.performance_data[model_name]) > 1000:
                self.performance_data[model_name] = self.performance_data[model_name][-1000:]

    def get_performance_summary(self, model_name: str) -> Dict[str, Any]:
        """获取性能摘要"""
        if model_name not in self.performance_data:
            return {
                "model_name": model_name,
                "status": "not_found",
                "message": f"模型 {model_name} 未找到",
                "timestamp": time.time()
            }

        records = self.performance_data[model_name]
        if not records:
            return {
                "model_name": model_name,
                "status": "no_data",
                "message": f"模型 {model_name} 暂无性能数据",
                "timestamp": time.time(),
                "record_count": 0
            }

        summary = {}
        for key in records[0].keys():
            if key != 'timestamp' and isinstance(records[0][key], (int, float)):
                values = [record[key] for record in records if key in record and isinstance(record[key], (int, float))]
                if values:
                    summary[f'avg_{key}'] = sum(values) / len(values)
                    summary[f'min_{key}'] = min(values)
                    summary[f'max_{key}'] = max(values)

        summary['total_records'] = len(records)
        summary['last_record'] = records[-1]['timestamp'].isoformat()

        return summary

    def get_all_performance_summaries(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型的性能摘要"""
        return {name: self.get_performance_summary(name) for name in self.performance_data.keys()}

class ModelConfigManager:
    """模型配置管理器"""

    def __init__(self):
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'model_config.json')
        self.lock = threading.RLock()
        self._load_configs()

    def _load_configs(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.configs = json.load(f)
                logger.info("模型配置加载成功")
            else:
                self.configs = self._get_default_configs()
                logger.info("使用默认模型配置")
        except Exception as e:
            logger.warning(f"加载模型配置失败，使用默认配置: {e}")
            self.configs = self._get_default_configs()

    def _get_default_configs(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'default_model': {
                'type': 'generic',
                'version': '1.0.0',
                'parameters': {},
                'hyperparameters': {}
            },
            'model_types': {
                'llm': {
                    'base_config': {'temperature': 0.7, 'max_tokens': 4000},
                    'supported_models': ['deepseek-chat', 'deepseek-reasoner', 'step-3.5-flash', 'local-llama', 'local-qwen', 'custom-trained']
                },
                'embedding': {
                    'base_config': {'model': 'text-embedding-ada-002'},
                    'supported_models': ['text-embedding-ada-002', 'text-embedding-3-small']
                },
                'classification': {
                    'base_config': {'threshold': 0.7},
                    'supported_models': ['bert-base-chinese', 'roberta-base']
                }
            }
        }

    def get_model_config(self, model_name: str, config_type: str = 'base') -> Dict[str, Any]:
        """获取模型配置"""
        with self.lock:
            if model_name in self.configs:
                return self.configs[model_name].get(config_type, {})
            return {}

    def update_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """更新模型配置"""
        with self.lock:
            self.configs[model_name] = config
            try:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.configs, f, indent=2, ensure_ascii=False)
                logger.info(f"模型配置更新成功: {model_name}")
                return True
            except Exception as e:
                logger.error(f"保存模型配置失败: {e}")
                return False

class UnifiedModelManager:
    """统一模型管理器 - 整合所有模型管理功能"""

    def __init__(self):
        self.lifecycle_manager = ModelLifecycleManager()
        self.performance_tracker = ModelPerformanceTracker()
        self.config_manager = ModelConfigManager()

        # 冗余和故障转移功能
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.current_provider: Optional[str] = None
        self.failover_enabled = True
        self.health_check_interval = 5  # 健康检查间隔（分钟）
        self.max_failures = 3
        self.provider_failures: Dict[str, int] = {}
        self.switch_history: List[Dict[str, Any]] = []

        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_reset': datetime.now()
        }

        # 初始化冗余配置
        self._init_redundancy_config()

        logger.info("✅ 统一模型管理器初始化完成（支持冗余和故障转移）")

    def _init_redundancy_config(self):
        """初始化冗余配置"""
        try:
            from src.utils.unified_centers import get_unified_center
            config_center = get_unified_center('get_unified_config_center')
            api_services = config_center.get_parameter("api_services", {})

            # 加载DeepSeek及其备用模型
            if "deepseek" in api_services:
                deepseek_config = api_services["deepseek"]

                # 主提供商
                self.providers["deepseek"] = {
                    "name": "deepseek",
                    "api_url": deepseek_config["api_url"],
                    "model": deepseek_config["model"],
                    "api_key_env": "DEEPSEEK_API_KEY",
                    "priority": 0,
                    "healthy": True,
                    "last_check": datetime.now()
                }

                # 备用提供商
                backup_models = deepseek_config.get("backup_models", [])
                for backup in backup_models:
                    provider_name = backup["provider"]
                    if provider_name in api_services:
                        provider_config = api_services[provider_name]
                        self.providers[provider_name] = {
                            "name": provider_name,
                            "api_url": provider_config["api_url"],
                            "model": backup["model"],
                            "api_key_env": f"{provider_name.upper()}_API_KEY",
                            "priority": backup["priority"],
                            "healthy": True,
                            "last_check": datetime.now()
                        }

            # 设置当前提供商
            self._select_best_provider()

        except Exception as e:
            logger.error(f"初始化冗余配置失败: {e}")

    def _select_best_provider(self):
        """选择最佳提供商"""
        if not self.providers:
            return

        # 按优先级和健康状态排序
        healthy_providers = [
            (name, provider) for name, provider in self.providers.items()
            if provider["healthy"]
        ]

        if not healthy_providers:
            logger.error("没有健康的模型提供商可用")
            return

        # 按优先级排序（优先级数字越小越优先）
        healthy_providers.sort(key=lambda x: x[1]["priority"])

        best_provider = healthy_providers[0][0]
        if self.current_provider != best_provider:
            old_provider = self.current_provider
            self.current_provider = best_provider

            # 记录切换事件
            switch_event = {
                "timestamp": datetime.now(),
                "from_provider": old_provider or "none",
                "to_provider": best_provider,
                "reason": "auto_switch" if old_provider else "initial_selection"
            }
            self.switch_history.append(switch_event)

            logger.info(f"✅ 切换到最佳模型提供商: {best_provider}")

    def get_model(self, model_name: str) -> Optional[Any]:
        """统一的模型获取接口"""
        try:
            model = self.lifecycle_manager.get_model(model_name)
            if model:
                self._record_operation_success()
                return model
            else:
                logger.warning(f"模型不存在: {model_name}")
                self._record_operation_failure()
                return None
        except Exception as e:
            logger.error(f"获取模型失败: {model_name}, 错误: {e}")
            self._record_operation_failure()
            return None

    def register_model(self, name: str, model: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """注册模型"""
        try:
            success = self.lifecycle_manager.register_model(name, model, metadata)
            if success:
                self._record_operation_success()
            else:
                self._record_operation_failure()
            return success
        except Exception as e:
            logger.error(f"注册模型失败: {name}, 错误: {e}")
            self._record_operation_failure()
            return False

    def unregister_model(self, name: str) -> bool:
        """注销模型"""
        try:
            success = self.lifecycle_manager.unregister_model(name)
            if success:
                self._record_operation_success()
            else:
                self._record_operation_failure()
            return success
        except Exception as e:
            logger.error(f"注销模型失败: {name}, 错误: {e}")
            self._record_operation_failure()
            return False

    def manage_model_lifecycle(self, operation: str, model_name: str, **kwargs) -> bool:
        """管理模型生命周期"""
        try:
            if operation == 'start':
                return self.lifecycle_manager.update_model_state(model_name, 'running')
            elif operation == 'stop':
                return self.lifecycle_manager.update_model_state(model_name, 'stopped')
            elif operation == 'pause':
                return self.lifecycle_manager.update_model_state(model_name, 'paused')
            elif operation == 'resume':
                return self.lifecycle_manager.update_model_state(model_name, 'running')
            else:
                logger.warning(f"未知的生命周期操作: {operation}")
                return False
        except Exception as e:
            logger.error(f"生命周期管理失败: {operation} {model_name}, 错误: {e}")
            return False

    def record_model_performance(self, model_name: str, metrics: Dict[str, Any]) -> None:
        """记录模型性能"""
        self.performance_tracker.record_performance(model_name, metrics)

    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """获取模型性能"""
        return self.performance_tracker.get_performance_summary(model_name)

    def get_all_model_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型性能"""
        return self.performance_tracker.get_all_performance_summaries()

    def get_model_config(self, model_name: str, config_type: str = 'base') -> Dict[str, Any]:
        """获取模型配置"""
        return self.config_manager.get_model_config(model_name, config_type)

    def update_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """更新模型配置"""
        return self.config_manager.update_model_config(model_name, config)

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        model = self.lifecycle_manager.get_model(model_name)
        if not model:
            return {}

        return {
            'name': model_name,
            'state': self.lifecycle_manager.get_model_state(model_name),
            'metadata': self.lifecycle_manager.get_model_metadata(model_name),
            'performance': self.get_model_performance(model_name),
            'config': self.get_model_config(model_name)
        }

    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型信息"""
        models_info = {}
        for name in self.lifecycle_manager.models.keys():
            models_info[name] = self.get_model_info(name)
        return models_info

    def _record_operation_success(self):
        """记录操作成功"""
        self.performance_metrics['total_operations'] += 1
        self.performance_metrics['successful_operations'] += 1

    def _record_operation_failure(self):
        """记录操作失败"""
        self.performance_metrics['total_operations'] += 1
        self.performance_metrics['failed_operations'] += 1

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total = self.performance_metrics['total_operations']
        successful = self.performance_metrics['successful_operations']
        failed = self.performance_metrics['failed_operations']

        success_rate = successful / total if total > 0 else 0

        return {
            'total_operations': total,
            'successful_operations': successful,
            'failed_operations': failed,
            'success_rate': success_rate,
            'last_reset': self.performance_metrics['last_reset'].isoformat()
        }

    def reset_performance_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_reset': datetime.now()
        }
        logger.info("性能指标已重置")

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'manager_version': '1.0.0',
            'total_models': len(self.lifecycle_manager.models),
            'active_models': len([name for name, state in self.lifecycle_manager.model_states.items()
                                if state == 'running']),
            'performance_metrics': self.get_performance_metrics(),
            'config_file': self.config_manager.config_file
        }

    def get_failover_status(self) -> Dict[str, Any]:
        """获取故障转移状态"""
        return {
            "current_provider": self.current_provider,
            "providers": {
                name: {
                    "healthy": provider["healthy"],
                    "priority": provider["priority"],
                    "failures": self.provider_failures.get(name, 0)
                }
                for name, provider in self.providers.items()
            },
            "failover_enabled": self.failover_enabled,
            "recent_switches": self.switch_history[-10:] if self.switch_history else []
        }

_unified_model_manager = None

def get_unified_model_manager() -> UnifiedModelManager:
    """获取统一模型管理器实例"""
    global _unified_model_manager
    if _unified_model_manager is None:
        _unified_model_manager = UnifiedModelManager()
    return _unified_model_manager
