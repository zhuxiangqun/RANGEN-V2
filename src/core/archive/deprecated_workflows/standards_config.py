"""
标准配置加载器

从 config/standards.json 加载标准定义
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class StandardsConfig:
    """标准配置加载器"""
    
    _instance: Optional['StandardsConfig'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载标准配置"""
        config_path = Path(__file__).parent.parent.parent / "config" / "standards.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            self._config = {}
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    @property
    def agent_capabilities(self) -> List[str]:
        """获取 Agent 能力列表"""
        return self._config.get("agent", {}).get("capabilities", [])
    
    @property
    def agent_default_timeout(self) -> float:
        """获取 Agent 默认超时"""
        return self._config.get("agent", {}).get("default_timeout", 30.0)
    
    @property
    def skill_scopes(self) -> List[str]:
        """获取 Skill 作用域"""
        return self._config.get("skill", {}).get("scopes", [])
    
    @property
    def skill_categories(self) -> List[str]:
        """获取 Skill 类别"""
        return self._config.get("skill", {}).get("categories", [])
    
    @property
    def tool_categories(self) -> List[str]:
        """获取 Tool 类别"""
        return self._config.get("tool", {}).get("categories", [])
    
    @property
    def workflow_nodes(self) -> List[str]:
        """获取 Workflow 节点"""
        return self._config.get("workflow", {}).get("nodes", [])
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)


def get_standards_config() -> StandardsConfig:
    """获取标准配置实例"""
    return StandardsConfig()
