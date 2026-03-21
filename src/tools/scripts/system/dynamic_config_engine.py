#!/usr/bin/env python3
"""
动态配置引擎 - 阶段2: 实现配置热重载和版本控制
支持运行时配置更新、版本管理和回滚机制
"""

import os
import json
import time
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ConfigVersion:
    """配置版本"""
    version_id: str
    timestamp: datetime
    config_data: Dict[str, Any]
    change_description: str
    author: str
    checksum: str
    parent_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'version_id': self.version_id,
            'timestamp': self.timestamp.isoformat(),
            'config_data': self.config_data,
            'change_description': self.change_description,
            'author': self.author,
            'checksum': self.checksum,
            'parent_version': self.parent_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigVersion':
        """从字典创建"""
        return cls(
            version_id=data['version_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            config_data=data['config_data'],
            change_description=data['change_description'],
            author=data['author'],
            checksum=data['checksum'],
            parent_version=data.get('parent_version')
        )

@dataclass
class ConfigChange:
    """配置变更"""
    key: str
    old_value: Any
    new_value: Any
    change_type: str  # 'add', 'update', 'delete'
    timestamp: datetime
    reason: str
    author: str

class DynamicConfigEngine:
    """动态配置引擎"""
    
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置存储
        self.current_config = {}
        self.config_versions: List[ConfigVersion] = []
        self.pending_changes: List[ConfigChange] = []
        
        # 文件监控
        self.file_watchers = {}
        self.watch_threads: Dict[str, threading.Thread] = {}
        
        # 变更监听器
        self.change_listeners: List[Callable[[str, Any, Any], None]] = []
        
        # 版本控制
        self.current_version = None
        self.version_file = self.config_dir / "versions.json"
        
        # 初始化
        self._load_static_config()
        self._load_versions()
        self._start_file_watchers()
    
    def _load_static_config(self):
        """加载静态配置"""
        try:
            from src.config.defaults import DEFAULT_VALUES
            system_config = DEFAULT_VALUES.get('system_thresholds', {})
            
            # 展平配置结构
            for category, configs in system_config.items():
                if isinstance(configs, dict):
                    for key, value in configs.items():
                        if isinstance(value, dict) and 'description' not in value:
                            self.current_config[f"{category}.{key}"] = value
                        elif not isinstance(value, dict) or 'description' in value:
                            self.current_config[f"{category}.{key}"] = value
            
            logger.info(f"✅ 加载了 {len(self.current_config)} 个静态配置项")
            
        except Exception as e:
            logger.error(f"加载静态配置失败: {e}")
    
    def _load_versions(self):
        """加载版本历史"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                
                self.config_versions = [
                    ConfigVersion.from_dict(v) for v in versions_data
                ]
                
                if self.config_versions:
                    # 加载最新版本
                    latest_version = max(self.config_versions, key=lambda v: v.timestamp)
                    self.current_config.update(latest_version.config_data)
                    self.current_version = latest_version.version_id
                
                logger.info(f"✅ 加载了 {len(self.config_versions)} 个配置版本")
            
        except Exception as e:
            logger.error(f"加载版本历史失败: {e}")
    
    def _start_file_watchers(self):
        """启动文件监控"""
        # 监控defaults.py文件变化
        self._watch_file("./src/config/defaults.py", self._on_defaults_file_change)
        
        # 监控环境变量变化 (通过定时检查)
        self._start_env_watcher()
    
    def _watch_file(self, filepath: str, callback: Callable):
        """监控文件变化"""
        def watcher():
            last_mtime = 0
            while True:
                try:
                    if os.path.exists(filepath):
                        current_mtime = os.path.getmtime(filepath)
                        if current_mtime > last_mtime and last_mtime > 0:
                            logger.info(f"📁 文件变更检测: {filepath}")
                            callback(filepath)
                        last_mtime = current_mtime
                    
                    time.sleep(2)  # 每2秒检查一次
                    
                except Exception as e:
                    logger.error(f"文件监控异常: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=watcher, daemon=True)
        thread.start()
        self.watch_threads[filepath] = thread
    
    def _start_env_watcher(self):
        """启动环境变量监控"""
        def env_watcher():
            last_env_hash = ""
            while True:
                try:
                    # 计算环境变量的哈希
                    env_vars = {k: v for k, v in os.environ.items() 
                              if k.startswith(('CACHE_', 'MODEL_', 'LOG_', 'CONFIG_', 'API_', 'DB_'))}
                    current_hash = hashlib.md5(str(sorted(env_vars.items())).encode()).hexdigest()
                    
                    if current_hash != last_env_hash and last_env_hash:
                        logger.info("🌍 环境变量变更检测")
                        self._on_env_change(env_vars)
                    
                    last_env_hash = current_hash
                    time.sleep(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))  # 每10秒检查一次
                    
                except Exception as e:
                    logger.error(f"环境变量监控异常: {e}")
                    time.sleep(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
        
        thread = threading.Thread(target=env_watcher, daemon=True)
        thread.start()
        self.watch_threads['environment'] = thread
    
    def _on_defaults_file_change(self, filepath: str):
        """处理defaults.py文件变更"""
        logger.info("🔄 defaults.py文件变更，重新加载配置")
        
        # 重新加载静态配置
        old_config = self.current_config.copy()
        self._load_static_config()
        
        # 比较变化
        self._compare_and_notify_changes(old_config, self.current_config, "defaults_file_change")
    
    def _on_env_change(self, new_env_vars: Dict[str, str]):
        """处理环境变量变更"""
        logger.info("🔄 环境变量变更，更新配置")
        
        # 重新应用环境变量覆盖
        self._apply_environment_overrides()
    
    def _apply_environment_overrides(self):
        """应用环境变量覆盖"""
        for key in list(self.current_config.keys()):
            env_key = key.upper().replace('.', '_')
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # 转换类型
                try:
                    original_value = self.current_config[key]
                    if isinstance(original_value, int):
                        self.current_config[key] = int(env_value)
                    elif isinstance(original_value, float):
                        self.current_config[key] = float(env_value)
                    elif isinstance(original_value, bool):
                        self.current_config[key] = env_value.lower() in ('true', '1', 'yes')
                    else:
                        self.current_config[key] = env_value
                    
                    logger.info(f"🌍 环境变量覆盖: {key} = {self.current_config[key]}")
                    
                except Exception as e:
                    logger.error(f"环境变量类型转换失败 {key}: {e}")
    
    def _compare_and_notify_changes(self, old_config: Dict[str, Any], 
                                  new_config: Dict[str, Any], reason: str):
        """比较配置变化并通知监听器"""
        changes = []
        
        # 检测新增和修改
        for key, new_value in new_config.items():
            if key not in old_config:
                changes.append(ConfigChange(
                    key=key, old_value=None, new_value=new_value,
                    change_type='add', timestamp=datetime.now(),
                    reason=reason, author="system"
                ))
            elif old_config[key] != new_value:
                changes.append(ConfigChange(
                    key=key, old_value=old_config[key], new_value=new_value,
                    change_type='update', timestamp=datetime.now(),
                    reason=reason, author="system"
                ))
        
        # 检测删除
        for key, old_value in old_config.items():
            if key not in new_config:
                changes.append(ConfigChange(
                    key=key, old_value=old_value, new_value=None,
                    change_type='delete', timestamp=datetime.now(),
                    reason=reason, author="system"
                ))
        
        # 通知监听器
        for change in changes:
            self._notify_change_listeners(change)
        
        if changes:
            logger.info(f"🔄 检测到 {len(changes)} 个配置变更")
    
    def _notify_change_listeners(self, change: ConfigChange):
        """通知配置变更监听器"""
        for listener in self.change_listeners:
            try:
                listener(change.key, change.old_value, change.new_value)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")
    
    def get_config(self, key: str) -> Any:
        """获取配置值"""
        return self.current_config.get(key)
    
    def set_config(self, key: str, value: Any, author: str = "system", 
                  description: str = "") -> bool:
        """设置配置值并创建新版本"""
        try:
            old_value = self.current_config.get(key)
            
            # 更新配置
            self.current_config[key] = value
            
            # 创建配置变更记录
            change = ConfigChange(
                key=key, old_value=old_value, new_value=value,
                change_type='add' if old_value is None else 'update',
                timestamp=datetime.now(), reason=description, author=author
            )
            
            # 创建新版本
            self._create_new_version([change], author, description)
            
            # 通知监听器
            self._notify_change_listeners(change)
            
            logger.info(f"✅ 配置已更新: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
            return False
    
    def _create_new_version(self, changes: List[ConfigChange], author: str, description: str):
        """创建新配置版本"""
        try:
            # 生成版本ID
            timestamp = datetime.now()
            content = f"{timestamp.isoformat()}_{author}_{description}"
            version_id = hashlib.md5(content.encode()).hexdigest()[:8]
            
            # 计算配置校验和
            config_str = json.dumps(self.current_config, sort_keys=True)
            checksum = hashlib.md5(config_str.encode()).hexdigest()
            
            # 创建版本对象
            version = ConfigVersion(
                version_id=version_id,
                timestamp=timestamp,
                config_data=self.current_config.copy(),
                change_description=description,
                author=author,
                checksum=checksum,
                parent_version=self.current_version
            )
            
            # 添加到版本历史
            self.config_versions.append(version)
            self.current_version = version_id
            
            # 保存版本到文件
            self._save_versions()
            
            logger.info(f"📝 创建配置版本: {version_id}")
            
        except Exception as e:
            logger.error(f"创建配置版本失败: {e}")
    
    def _save_versions(self):
        """保存版本历史到文件"""
        try:
            versions_data = [v.to_dict() for v in self.config_versions[-get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):]]  # 只保存最近100个版本
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存版本历史失败: {e}")
    
    def rollback_to_version(self, version_id: str, author: str = "system") -> bool:
        """回滚到指定版本"""
        try:
            # 查找版本
            target_version = None
            for version in self.config_versions:
                if version.version_id == version_id:
                    target_version = version
                    break
            
            if not target_version:
                logger.error(f"版本不存在: {version_id}")
                return False
            
            # 备份当前配置
            old_config = self.current_config.copy()
            
            # 应用目标版本配置
            self.current_config = target_version.config_data.copy()
            self.current_version = version_id
            
            # 记录变更
            changes = []
            for key, new_value in self.current_config.items():
                old_value = old_config.get(key)
                if old_value != new_value:
                    changes.append(ConfigChange(
                        key=key, old_value=old_value, new_value=new_value,
                        change_type='rollback', timestamp=datetime.now(),
                        reason=f"回滚到版本 {version_id}", author=author
                    ))
            
            # 通知监听器
            for change in changes:
                self._notify_change_listeners(change)
            
            logger.info(f"🔄 已回滚到版本: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"回滚版本失败: {e}")
            return False
    
    def get_version_history(self, limit: int = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [v.to_dict() for v in self.config_versions[-limit:]]
    
    def add_change_listener(self, callback: Callable[[ConfigChange], None]):
        """添加配置变更监听器"""
        self.change_listeners.append(callback)
    
    def export_config(self, filepath: str):
        """导出当前配置"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'version': self.current_version,
                'config': self.current_config,
                'versions': self.get_version_history(5)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ 配置已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            'current_version': self.current_version,
            'total_versions': len(self.config_versions),
            'total_configs': len(self.current_config),
            'active_watchers': len(self.watch_threads),
            'change_listeners': len(self.change_listeners),
            'uptime': time.time() - (self.config_versions[0].timestamp.timestamp() 
                                   if self.config_versions else time.time())
        }

# 全局动态配置引擎实例
_dynamic_config_engine = None

def get_dynamic_config_engine() -> DynamicConfigEngine:
    """获取动态配置引擎实例"""
    global _dynamic_config_engine
    if _dynamic_config_engine is None:
        _dynamic_config_engine = DynamicConfigEngine()
    return _dynamic_config_engine

def get_dynamic_config(key: str) -> Any:
    """获取动态配置"""
    return get_dynamic_config_engine().get_config(key)

def set_dynamic_config(key: str, value: Any, author: str = "system", 
                      description: str = "") -> bool:
    """设置动态配置"""
    return get_dynamic_config_engine().set_config(key, value, author, description)

# 便捷函数
def rollback_config(version_id: str) -> bool:
    """回滚配置"""
    return get_dynamic_config_engine().rollback_to_version(version_id)

def export_current_config(filepath: str):
    """导出当前配置"""
    get_dynamic_config_engine().export_config(filepath)

def get_config_history(limit: int = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))) -> List[Dict[str, Any]]:
    """获取配置历史"""
    return get_dynamic_config_engine().get_version_history(limit)

def add_config_change_listener(callback: Callable[[ConfigChange], None]):
    """添加配置变更监听器"""
    get_dynamic_config_engine().add_change_listener(callback)
