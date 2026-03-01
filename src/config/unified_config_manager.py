#!/usr/bin/env python3
"""
统一配置管理器 - 核心系统配置管理
"""

import json
import os
import yaml
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging


@dataclass
class ConfigSection:
    """配置节"""
    name: str
    config: Dict[str, Any]
    description: str
    last_updated: float
    version: str = "1.0.0"


class UnifiedConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.configs: Dict[str, ConfigSection] = {}
        self.logger = logging.getLogger(__name__)
        self._ensure_config_dir()
        self._load_configs()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(os.path.join(self.config_dir, "sections"), exist_ok=True)
    
    def _load_configs(self):
        """加载所有配置"""
        try:
            # 加载主配置文件
            main_config_path = os.path.join(self.config_dir, "main_config.json")
            if os.path.exists(main_config_path):
                with open(main_config_path, 'r', encoding='utf-8') as f:
                    main_config = json.load(f)
                    self._load_config_sections(main_config)
            
            # 加载配置节文件
            sections_dir = os.path.join(self.config_dir, "sections")
            if os.path.exists(sections_dir):
                for filename in os.listdir(sections_dir):
                    if filename.endswith(('.json', '.yaml', '.yml')):
                        self._load_config_section_file(os.path.join(sections_dir, filename))
            
            # 如果没有加载到任何配置，创建默认配置
            if len(self.configs) == 0:
                self.logger.info("未找到配置文件，创建默认配置")
                self._create_default_configs()
            else:
                self.logger.info(f"加载了 {len(self.configs)} 个配置节")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self._create_default_configs()
    
    def _load_config_sections(self, main_config: Dict[str, Any]):
        """从主配置加载配置节"""
        for section_name, section_data in main_config.items():
            if isinstance(section_data, dict):
                config_section = ConfigSection(
                    name=section_name,
                    config=section_data,
                    description=section_data.get('description', ''),
                    last_updated=section_data.get('last_updated', datetime.now().timestamp()),
                    version=section_data.get('version', '1.0.0')
                )
                self.configs[section_name] = config_section
    
    def _load_config_section_file(self, file_path: str):
        """加载配置节文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:  # yaml
                    data = yaml.safe_load(f)
            
            section_name = os.path.splitext(os.path.basename(file_path))[0]
            config_section = ConfigSection(
                name=section_name,
                config=data,
                description=data.get('description', ''),
                last_updated=data.get('last_updated', datetime.now().timestamp()),
                version=data.get('version', '1.0.0')
            )
            self.configs[section_name] = config_section
            
        except Exception as e:
            self.logger.error(f"加载配置节文件失败 {file_path}: {e}")
    
    def _create_default_configs(self):
        """创建默认配置"""
        default_configs = {
            "system": {
                "name": "RANGEN核心系统",
                "version": "1.0.0",
                "debug_mode": False,
                "log_level": "INFO",
                "max_concurrent_queries": 3,
                "timeout_seconds": 30
            },
            "security": {
                "enable_validation": True,
                "max_input_length": 1000,
                "allowed_file_types": [".txt", ".json", ".csv"],
                "rate_limit_per_minute": 100,
                "enable_encryption": True
            },
            "ai_algorithms": {
                "ml_engine": {
                    "test_size": 0.2,
                    "random_state": 42,
                    "max_iterations": 1000,
                    "validation_split": 0.2
                },
                "rl_engine": {
                    "learning_rate": 0.01,
                    "discount_factor": 0.95,
                    "epsilon": 0.1,
                    "max_episodes": 1000
                },
                "nlp_engine": {
                    "max_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0
                }
            },
            "data_management": {
                "cache_size": 1000,
                "cache_ttl": 3600,
                "enable_persistence": True,
                "backup_interval": 86400,
                "max_file_size": 10485760  # 10MB
            },
            "performance": {
                "enable_monitoring": True,
                "metrics_interval": 60,
                "memory_threshold": 0.8,
                "cpu_threshold": 0.8,
                "enable_profiling": False
            },
            "brain_decision": {
                "nTc_threshold": 0.8,
                "evidence_accumulation_timeout": 30.0,
                "commitment_lock_duration": 5.0,
                "dynamic_threshold_adjustment": True,
                "orthogonal_jump_threshold": 0.7,
                "max_trajectory_points": 100
            }
        }
        
        for section_name, config_data in default_configs.items():
            config_section = ConfigSection(
                name=section_name,
                config=config_data,
                description=f"{section_name}配置",
                last_updated=datetime.now().timestamp(),
                version="1.0.0"
            )
            self.configs[section_name] = config_section
            self._save_config_section(config_section)
    
    def get_config(self, section_name: str, key: str = None, default: Any = None) -> Any:
        """获取配置值"""
        if section_name not in self.configs:
            return default
        
        config = self.configs[section_name].config
        
        if key is None:
            return config
        
        # 支持点号分隔的嵌套键
        keys = key.split('.')
        current = config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set_config(self, section_name: str, key: str, value: Any) -> bool:
        """设置配置值"""
        if section_name not in self.configs:
            # 创建新的配置节
            self.configs[section_name] = ConfigSection(
                name=section_name,
                config={},
                description=f"{section_name}配置",
                last_updated=datetime.now().timestamp(),
                version="1.0.0"
            )
        
        config = self.configs[section_name].config
        
        # 支持点号分隔的嵌套键
        keys = key.split('.')
        current = config
        
        # 创建嵌套结构
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value
        
        # 更新配置节
        self.configs[section_name].last_updated = datetime.now().timestamp()
        
        # 保存配置
        self._save_config_section(self.configs[section_name])
        
        return True
    
    def get_section(self, section_name: str) -> Optional[ConfigSection]:
        """获取配置节"""
        return self.configs.get(section_name)
    
    def list_sections(self) -> list:
        """列出所有配置节"""
        return list(self.configs.keys())
    
    def _save_config_section(self, config_section: ConfigSection):
        """保存配置节到文件"""
        try:
            section_path = os.path.join(self.config_dir, "sections", f"{config_section.name}.json")
            
            section_data = {
                "name": config_section.name,
                "config": config_section.config,
                "description": config_section.description,
                "last_updated": config_section.last_updated,
                "version": config_section.version
            }
            
            with open(section_path, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存配置节失败 {config_section.name}: {e}")
    
    def save_all_configs(self):
        """保存所有配置"""
        try:
            # 保存主配置文件
            main_config = {}
            for section_name, config_section in self.configs.items():
                main_config[section_name] = {
                    "config": config_section.config,
                    "description": config_section.description,
                    "last_updated": config_section.last_updated,
                    "version": config_section.version
                }
            
            main_config_path = os.path.join(self.config_dir, "main_config.json")
            with open(main_config_path, 'w', encoding='utf-8') as f:
                json.dump(main_config, f, ensure_ascii=False, indent=2)
            
            # 保存各个配置节文件
            for config_section in self.configs.values():
                self._save_config_section(config_section)
            
            self.logger.info("所有配置保存完成")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def validate_config(self, section_name: str) -> Dict[str, Any]:
        """验证配置"""
        if section_name not in self.configs:
            return {"valid": False, "errors": ["配置节不存在"]}
        
        config = self.configs[section_name].config
        errors = []
        warnings = []
        
        # 根据配置节类型进行验证
        if section_name == "security":
            if not config.get("enable_validation", True):
                warnings.append("安全验证已禁用")
            
            max_length = config.get("max_input_length", 1000)
            if max_length > 10000:
                warnings.append("最大输入长度过大，可能影响性能")
            elif max_length < 100:
                errors.append("最大输入长度过小")
        
        elif section_name == "ai_algorithms":
            for engine_name, engine_config in config.items():
                if isinstance(engine_config, dict):
                    if "learning_rate" in engine_config:
                        lr = engine_config["learning_rate"]
                        if lr <= 0 or lr > 1:
                            errors.append(f"{engine_name}学习率应在0-1之间")
                    
                    if "test_size" in engine_config:
                        test_size = engine_config["test_size"]
                        if test_size <= 0 or test_size >= 1:
                            errors.append(f"{engine_name}测试集比例应在0-1之间")
        
        elif section_name == "brain_decision":
            ntc_threshold = config.get("nTc_threshold", 0.8)
            if ntc_threshold < 0 or ntc_threshold > 1:
                errors.append("nTc阈值应在0-1之间")
            
            timeout = config.get("evidence_accumulation_timeout", 30.0)
            if timeout < 1 or timeout > 300:
                warnings.append("证据积累超时时间建议在1-300秒之间")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        summary = {
            "total_sections": len(self.configs),
            "sections": {},
            "last_updated": max(
                (config.last_updated for config in self.configs.values()),
                default=0
            )
        }
        
        for section_name, config_section in self.configs.items():
            summary["sections"][section_name] = {
                "version": config_section.version,
                "last_updated": config_section.last_updated,
                "config_keys": len(config_section.config),
                "description": config_section.description
            }
        
        return summary


# 全局实例
_config_manager = None

def get_config_manager() -> UnifiedConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigManager()
    return _config_manager

def get_config(section: str, key: str = None, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return get_config_manager().get_config(section, key, default)

def set_config(section: str, key: str, value: Any) -> bool:
    """便捷函数：设置配置值"""
    return get_config_manager().set_config(section, key, value)
