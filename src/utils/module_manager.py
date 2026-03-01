#!/usr/bin/env python3
"""
模块管理器
提供模块的动态加载和管理功能
"""
import os
import sys
import importlib
import logging
import time
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    path: str
    loaded: bool
    last_accessed: float
    dependencies: List[str]


class ModuleManager:
    """模块管理器"""
    
    def __init__(self):
        """初始化模块管理器"""
        self.logger = logging.getLogger(__name__)
        self.modules: Dict[str, ModuleInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.module_paths: List[str] = []
        
        # 添加默认路径
        self.add_module_path("src")
        self.add_module_path("src/utils")
        self.add_module_path("src/agents")
        self.add_module_path("src/ai")
        self.add_module_path("src/core")
        
        self.logger.info("模块管理器初始化完成")
    
    def add_module_path(self, path: str) -> bool:
        """添加模块路径"""
        try:
            # 验证路径
            if not self._validate_module_path(path):
                return False
            
            # 检查路径是否已存在
            if path in self.module_paths:
                self.logger.warning(f"模块路径已存在: {path}")
                return False
            
            # 添加路径
            self.module_paths.append(path)
            if path not in sys.path:
                sys.path.insert(0, path)
            
            # 记录路径添加历史
            self._record_path_addition(path)
            
            self.logger.info(f"添加模块路径: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加模块路径失败: {e}")
            return False
    
    def _validate_module_path(self, path: str) -> bool:
        """验证模块路径"""
        if not isinstance(path, str) or not path.strip():
            return False
        
        # 检查路径是否存在
        if not os.path.exists(path):
            self.logger.warning(f"路径不存在: {path}")
            return False
        
        return True
    
    def _record_path_addition(self, path: str):
        """记录路径添加历史"""
        if not hasattr(self, 'path_history'):
            self.path_history = []
        
        self.path_history.append({
            'action': 'add_path',
            'path': path,
            'timestamp': time.time()
        })
    
    def remove_module_path(self, path: str) -> bool:
        """移除模块路径"""
        try:
            if path in self.module_paths:
                self.module_paths.remove(path)
                if path in sys.path:
                    sys.path.remove(path)
                self.logger.info(f"移除模块路径: {path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除模块路径失败: {e}")
            return False
    
    def register_module(self, name: str, path: str, dependencies: Optional[List[str]] = None) -> bool:
        """注册模块"""
        try:
            if name in self.modules:
                self.logger.warning(f"模块 {name} 已存在")
                return False
            
            module_info = ModuleInfo(
                name=name,
                path=path,
                loaded=False,
                last_accessed=0.0,
                dependencies=dependencies or []
            )
            
            self.modules[name] = module_info
            self.logger.info(f"注册模块: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册模块失败: {e}")
            return False
    
    def load_module(self, name: str) -> bool:
        """加载模块"""
        try:
            if name not in self.modules:
                self.logger.error(f"模块 {name} 未注册")
                return False
            
            module_info = self.modules[name]
            
            # 检查依赖
            if not self._check_dependencies(module_info.dependencies):
                self.logger.error(f"模块 {name} 的依赖未满足")
                return False
            
            # 加载模块
            module = importlib.import_module(name)
            self.loaded_modules[name] = module
            module_info.loaded = True
            module_info.last_accessed = time.time()
            
            self.logger.info(f"加载模块: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模块失败: {e}")
            return False
    
    def unload_module(self, name: str) -> bool:
        """卸载模块"""
        try:
            if name not in self.modules:
                self.logger.warning(f"模块 {name} 未注册")
                return False
            
            if name in self.loaded_modules:
                del self.loaded_modules[name]
                self.modules[name].loaded = False
                self.logger.info(f"卸载模块: {name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"卸载模块失败: {e}")
            return False
    
    def reload_module(self, name: str) -> bool:
        """重新加载模块"""
        try:
            if name not in self.modules:
                self.logger.error(f"模块 {name} 未注册")
                return False
            
            if name in self.loaded_modules:
                importlib.reload(self.loaded_modules[name])
                self.modules[name].last_accessed = time.time()
                self.logger.info(f"重新加载模块: {name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"重新加载模块失败: {e}")
            return False
    
    def get_module(self, name: str) -> Optional[Any]:
        """获取模块"""
        try:
            if name not in self.modules:
                self.logger.error(f"模块 {name} 未注册")
                return {
                    "error": f"模块 {name} 未注册",
                    "module_name": name,
                    "timestamp": time.time(),
                    "available_modules": list(self.modules.keys())
                }
            
            module_info = self.modules[name]
            
            # 如果模块未加载，尝试加载
            if not module_info.loaded:
                if not self.load_module(name):
                    return {
                        "error": f"模块 {name} 加载失败",
                        "module_name": name,
                        "timestamp": time.time(),
                        "load_status": "failed"
                    }
            
            # 更新访问时间
            module_info.last_accessed = time.time()
            
            return self.loaded_modules.get(name)
            
        except Exception as e:
            self.logger.error(f"获取模块失败: {e}")
            return {
                "error": f"获取模块失败: {e}",
                "status": "error",
                "module_name": module_name,
                "timestamp": time.time()
            }
    
    def get_module_class(self, module_name: str, class_name: str) -> Optional[Type]:
        """获取模块中的类"""
        try:
            module = self.get_module(module_name)
            if not module:
                return {
                    "error": f"模块 {module_name} 不存在",
                    "status": "module_not_found",
                    "module_name": module_name,
                    "class_name": class_name,
                    "timestamp": time.time()
                }
            
            if hasattr(module, class_name):
                return getattr(module, class_name)
            
            return {
                "error": f"类 {class_name} 在模块 {module_name} 中不存在",
                "status": "class_not_found",
                "module_name": module_name,
                "class_name": class_name,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取模块类失败: {e}")
            return {
                "error": f"获取模块类失败: {e}",
                "status": "error",
                "module_name": module_name,
                "class_name": class_name,
                "timestamp": time.time()
            }
    
    def create_module_instance(self, module_name: str, class_name: str, *args, **kwargs) -> Optional[Any]:
        """创建模块实例"""
        try:
            module_class = self.get_module_class(module_name, class_name)
            if not module_class:
                return {
                    "error": f"模块类 {class_name} 在模块 {module_name} 中不存在",
                    "status": "class_not_found",
                    "module_name": module_name,
                    "class_name": class_name,
                    "timestamp": time.time()
                }
            
            instance = module_class(*args, **kwargs)
            return instance
            
        except Exception as e:
            self.logger.error(f"创建模块实例失败: {e}")
            return {
                "error": f"创建模块实例失败: {e}",
                "status": "instance_creation_failed",
                "module_name": module_name,
                "class_name": class_name,
                "timestamp": time.time()
            }
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖"""
        for dep in dependencies:
            if dep not in self.modules or not self.modules[dep].loaded:
                return False
        return True
    
    def get_module_info(self, name: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self.modules.get(name)
    
    def list_modules(self) -> List[str]:
        """列出所有模块"""
        return list(self.modules.keys())
    
    def list_loaded_modules(self) -> List[str]:
        """列出已加载的模块"""
        return [name for name, info in self.modules.items() if info.loaded]
    
    def get_module_statistics(self) -> Dict[str, Any]:
        """获取模块统计信息"""
        total_modules = len(self.modules)
        loaded_modules = len(self.list_loaded_modules())
        
        return {
            "total_modules": total_modules,
            "loaded_modules": loaded_modules,
            "load_rate": loaded_modules / total_modules if total_modules > 0 else 0.0,
            "module_paths": len(self.module_paths),
            "modules": {
                name: {
                    "loaded": info.loaded,
                    "dependencies": info.dependencies,
                    "last_accessed": info.last_accessed
                }
                for name, info in self.modules.items()
            }
        }
    
    def cleanup_unused_modules(self, max_idle_time: float = 3600.0) -> int:
        """清理未使用的模块"""
        try:
            current_time = time.time()
            unused_modules = []
            
            for name, info in self.modules.items():
                if info.loaded and (current_time - info.last_accessed) > max_idle_time:
                    unused_modules.append(name)
            
            cleaned_count = 0
            for name in unused_modules:
                if self.unload_module(name):
                    cleaned_count += 1
            
            self.logger.info(f"清理了 {cleaned_count} 个未使用的模块")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理未使用模块失败: {e}")
            return 0
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "status": "active",
            "total_modules": len(self.modules),
            "loaded_modules": len(self.list_loaded_modules()),
            "module_paths": self.module_paths,
            "statistics": self.get_module_statistics()
        }


def get_module_manager() -> ModuleManager:
    """获取模块管理器实例"""
    return ModuleManager()


if __name__ == "__main__":
    # 测试模块管理器
    manager = ModuleManager()
    
    # 注册模块
    manager.register_module("test_module", "test_module", ["os"])
    
    # 加载模块
    success = manager.load_module("test_module")
    print(f"加载模块: {success}")
    
    # 获取模块
    module = manager.get_module("test_module")
    print(f"获取模块: {module is not None}")
    
    # 获取统计信息
    stats = manager.get_module_statistics()
    print(f"统计信息: {stats}")
    
    # 获取管理器状态
    status = manager.get_manager_status()
    print(f"管理器状态: {status}")