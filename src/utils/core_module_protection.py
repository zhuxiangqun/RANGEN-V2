import os
#!/usr/bin/env python3
"""
核心模块保护器 - 简化版本
功能已合并到utils模块中
"""

import hashlib
import logging
from typing import Set, List, Dict, Any, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ModuleProtectionInfo:
    """模块保护信息"""
    module_name: str
    protection_level: str
    is_protected: bool
    protection_reason: str
    last_accessed: Optional[str] = None


class CoreModuleProtector:
    """核心模块保护器 - 简化版本"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """初始化核心模块保护器"""
        self.context = context or {}
        self.core_modules = self._initialize_core_modules()
        self.protection_rules = self._initialize_protection_rules()
        self.logger = logging.getLogger(__name__)
        self.logger.info("核心模块保护器初始化完成")
    
    def _initialize_core_modules(self) -> Set[str]:
        """初始化核心模块集合"""
        return {
            "src.core",
            "src.utils.unified_centers",
            "src.research_logger",
            "src.agents.base_agent",
            "src.core.interfaces",
            "src.core.agent_factory",
            "src.core.research_executor",
            "src.core.research_analyzer",
            "src.core.research_coordinator"
        }
    
    def is_core_module(self, module_name: str) -> bool:
        """检查是否为核心模块"""
        return module_name in self.core_modules
    
    def protect_module(self, module_name: str, protection_level: str = "standard", 
                      reason: str = "core_module") -> bool:
        """保护模块"""
        try:
            if not self.protection_enabled:
                return False
            
            if module_name in self.protected_modules:
                self.logger.warning(f"模块已受保护: {module_name}")
                return True
            
            self.protected_modules.add(module_name)
            
            protection_info = ModuleProtectionInfo(
                module_name=module_name,
                protection_level=protection_level,
                is_protected=True,
                protection_reason=reason
            )
            
            self.logger.info(f"模块保护成功: {module_name} (级别: {protection_level})")
            return True
            
        except Exception as e:
            self.logger.error(f"模块保护失败: {e}")
            return False
    
    def unprotect_module(self, module_name: str) -> bool:
        """取消模块保护"""
        try:
            if module_name in self.protected_modules:
                self.protected_modules.remove(module_name)
                self.logger.info(f"模块保护已取消: {module_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消模块保护失败: {e}")
            return False
    
    def get_protected_modules(self) -> Set[str]:
        """获取受保护的模块列表"""
        return self.protected_modules.copy()
    
    def cleanup_non_core_modules(self, modules_to_cleanup: List[str]) -> List[str]:
        """清理非核心模块"""
        try:
            if not self.auto_cleanup:
                return []
            
            cleaned_modules = []
            for module_name in modules_to_cleanup:
                if not self.is_core_module(module_name) and module_name not in self.protected_modules:
                    cleaned_modules.append(module_name)
                    
                    # 记录清理历史
                    self.cleanup_history.append({
                        "module_name": module_name,
                        "cleanup_time": self._get_current_timestamp(),
                        "reason": "non_core_module"
                    })
            
            # 限制清理历史大小
            if len(self.cleanup_history) > self.max_cleanup:
                self.cleanup_history = self.cleanup_history[-self.max_cleanup:]
            
            self.logger.info(f"清理了 {len(cleaned_modules)} 个非核心模块")
            return cleaned_modules
            
        except Exception as e:
            self.logger.error(f"模块清理失败: {e}")
            return []
    
    def get_cleanup_history(self) -> List[Dict[str, Any]]:
        """获取清理历史"""
        return self.cleanup_history.copy()
    
    def get_protection_stats(self) -> Dict[str, Any]:
        """获取保护统计信息"""
        return {
            "total_core_modules": len(self.core_modules),
            "protected_modules": len(self.protected_modules),
            "cleanup_history_count": len(self.cleanup_history),
            "protection_enabled": self.protection_enabled,
            "auto_cleanup_enabled": self.auto_cleanup
        }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def reset_protection(self):
        """重置保护状态"""
        self.protected_modules.clear()
        self.cleanup_history.clear()
        self.logger.info("保护状态已重置")


# 全局实例
core_module_protector = CoreModuleProtector()


def get_core_module_protector() -> CoreModuleProtector:
    """获取核心模块保护器实例"""
    return core_module_protector