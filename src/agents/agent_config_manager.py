#!/usr/bin/env python3
"""
智能体配置管理器 - 负责智能体配置的统一管理
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .agent_models import AgentConfig


@dataclass
class ConfigSection:
    """配置节"""
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentConfigManager:
    """智能体配置管理器 - 单一职责：配置管理"""
    
    def __init__(self, agent_id: str, config: Optional[AgentConfig] = None):
        """
        初始化配置管理器
        
        Args:
            agent_id: 智能体ID
            config: 初始配置
        """
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # 主配置
        self.config = config or AgentConfig(agent_id=agent_id)
        
        # 配置节管理
        self._sections: Dict[str, ConfigSection] = {
            "agent": ConfigSection("agent"),
            "system": ConfigSection("system"), 
            "ai": ConfigSection("ai")
        }
        
        # 统一配置中心集成
        self.unified_config_center = self._init_unified_config_center()
        
        # 动态参数缓存
        self._dynamic_params_cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 300  # 5分钟缓存
        
        self.logger.info(f"配置管理器初始化完成: {agent_id}")
    
    def _init_unified_config_center(self):
        """初始化统一配置中心"""
        try:
            from ..utils.unified_centers import UnifiedConfigCenter, SmartConfigCenter
            # 优先使用智能配置中心，回退到标准配置中心
            try:
                return SmartConfigCenter()
            except Exception:
                return UnifiedConfigCenter()
        except ImportError:
            self.logger.warning("统一配置中心不可用，使用本地配置")
            return None
    
    def get_config_value(self, key: str, default: Any = None, 
                        context: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取配置值 - 优先使用统一配置中心
        
        Args:
            key: 配置键
            default: 默认值
            context: 上下文信息
            
        Returns:
            配置值
        """
        try:
            # 1. 检查统一配置中心
            if self.unified_config_center:
                value = self._get_from_unified_center(key, context)
                if value is not None:
                    return value
            
            # 2. 检查主配置
            if hasattr(self.config, key):
                return getattr(self.config, key)
            
            # 3. 检查配置节
            for section in self._sections.values():
                if key in section.values:
                    return section.values[key]
            
            # 4. 检查动态参数缓存
            if self._is_cache_valid() and key in self._dynamic_params_cache:
                return self._dynamic_params_cache[key]
            
            # 5. 尝试加载动态参数
            dynamic_value = self._load_dynamic_param(key)
            if dynamic_value is not None:
                return dynamic_value
            
            return default
            
        except Exception as e:
            self.logger.warning(f"获取配置值失败 {key}: {e}")
            return default
    
    def _get_from_unified_center(self, key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """从统一配置中心获取值"""
        if not self.unified_config_center:
            return None
            
        try:
            # 检查是否是智能配置中心
            if hasattr(self.unified_config_center, 'get_smart_config') and callable(getattr(self.unified_config_center, 'get_smart_config')):
                return self.unified_config_center.get_smart_config(key, context or {})  # type: ignore
            else:
                # 使用标准配置中心接口
                # 尝试从不同配置节中查找
                for section_name in ["agent", "system", "ai"]:
                    value = self.unified_config_center.get_config_value(section_name, key)
                    if value is not None:
                        return value
                return None
        except Exception as e:
            self.logger.warning(f"从统一配置中心获取配置失败 {key}: {e}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        import time
        return (time.time() - self._cache_timestamp) < self._cache_ttl
    
    def _load_dynamic_param(self, key: str) -> Any:
        """加载动态参数"""
        try:
            from ..utils.unified_centers import get_smart_config
            value = get_smart_config(key, {"default": None, "agent_id": self.agent_id})
            if value is not None:
                # 更新缓存
                import time
                self._dynamic_params_cache[key] = value
                self._cache_timestamp = time.time()
            return value
        except Exception as e:
            self.logger.warning(f"加载动态参数失败 {key}: {e}")
            return None
    
    def update_config(self, config_data: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            是否更新成功
        """
        try:
            # 1. 更新主配置
            main_config_updated = self._update_main_config(config_data)
            
            # 2. 更新配置节
            sections_updated = self._update_sections(config_data)
            
            # 3. 更新统一配置中心
            center_updated = self._update_unified_center(config_data)
            
            # 4. 清除缓存
            self._clear_cache()
            
            updated_keys = list(config_data.keys())
            self.logger.info(f"配置更新成功: {updated_keys}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            return False
    
    def _update_main_config(self, config_data: Dict[str, Any]) -> bool:
        """更新主配置"""
        updated = False
        for key, value in config_data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                updated = True
        return updated
    
    def _update_sections(self, config_data: Dict[str, Any]) -> bool:
        """更新配置节"""
        updated = False
        for key, value in config_data.items():
            section = self._determine_section(key)
            if section:
                self._sections[section].values[key] = value
                updated = True
        return updated
    
    def _determine_section(self, key: str) -> Optional[str]:
        """确定配置所属的节"""
        system_keys = ["medium_threshold", "low_threshold", "high_threshold", 
                       "default_limit", "large_limit", "medium_buffer"]
        ai_keys = ["DEFAULT_ZERO_VALUE", "DEFAULT_ONE_VALUE", "DEFAULT_CONFIDENCE", 
                  "MAX_CONFIDENCE", "MIN_CONFIDENCE"]
        
        if key in system_keys:
            return "system"
        elif key in ai_keys:
            return "ai"
        else:
            return "agent"
    
    def _update_unified_center(self, config_data: Dict[str, Any]) -> bool:
        """更新统一配置中心"""
        if not self.unified_config_center:
            return False
            
        try:
            # 检查是否是标准配置中心
            if hasattr(self.unified_config_center, 'set_config_value'):
                # 使用标准配置中心接口
                for key, value in config_data.items():
                    section = self._determine_section(key)
                    if section:
                        self.unified_config_center.set_config_value(section, key, value)
                return True
            else:
                # 使用旧的接口
                for key, value in config_data.items():
                    self.unified_config_center.configs[key] = value
                return True
        except Exception as e:
            self.logger.warning(f"更新统一配置中心失败: {e}")
            return False
    
    def _clear_cache(self) -> None:
        """清除缓存"""
        self._dynamic_params_cache.clear()
        self._cache_timestamp = 0
    
    def get_section_config(self, section_name: str) -> Dict[str, Any]:
        """
        获取配置节的所有配置
        
        Args:
            section_name: 节名称
            
        Returns:
            配置字典
        """
        if section_name in self._sections:
            return self._sections[section_name].values.copy()
        return {}
    
    def set_section_config(self, section_name: str, config: Dict[str, Any]) -> bool:
        """
        设置配置节配置
        
        Args:
            section_name: 节名称
            config: 配置字典
            
        Returns:
            是否设置成功
        """
        try:
            if section_name not in self._sections:
                self._sections[section_name] = ConfigSection(section_name)
            
            self._sections[section_name].values.update(config)
            self.logger.info(f"配置节 {section_name} 更新成功")
            return True
        except Exception as e:
            self.logger.error(f"设置配置节失败 {section_name}: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """
        导出完整配置
        
        Returns:
            完整配置字典
        """
        return {
            "main_config": self.config.to_dict(),
            "sections": {name: section.values for name, section in self._sections.items()},
            "dynamic_params": self._dynamic_params_cache.copy(),
            "cache_timestamp": self._cache_timestamp
        }
    
    def import_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        导入配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            是否导入成功
        """
        try:
            # 导入主配置
            if "main_config" in config_dict:
                self.config = AgentConfig.from_dict(config_dict["main_config"])
            
            # 导入配置节
            if "sections" in config_dict:
                for section_name, values in config_dict["sections"].items():
                    self.set_section_config(section_name, values)
            
            # 导入动态参数
            if "dynamic_params" in config_dict:
                self._dynamic_params_cache.update(config_dict["dynamic_params"])
            
            self.logger.info("配置导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """
        验证配置有效性
        
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证主配置
        if not self.config.agent_id:
            errors.append("agent_id 不能为空")
        
        if self.config.timeout <= 0:
            errors.append("timeout 必须大于0")
        
        if self.config.retry_count < 0:
            errors.append("retry_count 不能为负数")
        
        if not 0 <= self.config.confidence_threshold <= 1:
            errors.append("confidence_threshold 必须在0-1之间")
        
        # 验证配置节
        for section_name, section in self._sections.items():
            if not section.values:
                self.logger.warning(f"配置节 {section_name} 为空")
        
        return errors
    
    def reload_dynamic_config(self) -> bool:
        """
        重新加载动态配置
        
        Returns:
            是否重载成功
        """
        try:
            self._clear_cache()
            # 预加载常用动态参数
            common_params = ["learning_rate", "confidence_threshold", "max_iterations", "timeout"]
            for param in common_params:
                self._load_dynamic_param(param)
            
            self.logger.info("动态配置重载完成")
            return True
        except Exception as e:
            self.logger.error(f"动态配置重载失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要
        """
        return {
            "agent_id": self.agent_id,
            "main_config_keys": list(self.config.to_dict().keys()),
            "sections": list(self._sections.keys()),
            "has_unified_center": self.unified_config_center is not None,
            "dynamic_params_count": len(self._dynamic_params_cache),
            "cache_valid": self._is_cache_valid()
        }