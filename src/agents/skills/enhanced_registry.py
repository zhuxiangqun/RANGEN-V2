"""
增强版 SkillRegistry - 支持 Claude Code 风格

新增功能：
1. 自动加载 SKILL.md 作为文档
2. 支持 triggers 关键词触发
3. Skill 知识查询接口
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from src.agents.skills import Skill, SkillScope, SkillMetadata, DynamicSkill


@dataclass
class TriggerConfig:
    """触发器配置"""
    keywords: List[str]
    case_sensitive: bool = False


@dataclass  
class ToolConfig:
    """工具配置"""
    name: str
    description: str
    class_name: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedSkillMetadata(SkillMetadata):
    """增强版 Skill 元数据"""
    triggers: List[str] = field(default_factory=list)
    tools: List[ToolConfig] = field(default_factory=list)
    prompt_template: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    documentation_path: Optional[str] = None


class EnhancedSkillRegistry:
    """
    增强版 Skill 注册表
    
    特性:
    - 支持从 SKILL.md 加载文档
    - 支持 triggers 关键词匹配
    - 提供 Skill 知识查询接口
    """
    
    def __init__(self, base_path: str = "./src/agents/skills/bundled"):
        self._skills: Dict[str, Skill] = {}
        self._metadata: Dict[str, EnhancedSkillMetadata] = {}
        self._triggers: Dict[str, List[str]] = {}  # keyword -> [skill_names]
        self._base_path = Path(base_path)
        
        # 加载所有 Skills
        self._load_all_skills()
    
    def _load_all_skills(self):
        """加载所有 Skills"""
        if not self._base_path.exists():
            return
            
        for skill_dir in self._base_path.iterdir():
            if skill_dir.is_dir():
                self._load_skill(skill_dir)
    
    def _load_skill(self, skill_dir: Path):
        """加载单个 Skill"""
        skill_name = skill_dir.name
        
        # 1. 加载 YAML 配置
        config = {}
        yaml_path = skill_dir / "skill.yaml"
        json_path = skill_dir / "skill.json"
        
        if yaml_path.exists():
            with open(yaml_path) as f:
                config = yaml.safe_load(f) or {}
        elif json_path.exists():
            with open(json_path) as f:
                config = json.load(f)
        
        # 2. 构建元数据
        metadata = EnhancedSkillMetadata(
            name=config.get("name", skill_name),
            version=config.get("version", "1.0.0"),
            description=config.get("description", ""),
            author=config.get("author", ""),
            tags=config.get("tags", []),
            scope=SkillScope.BUNDLED,
            triggers=config.get("triggers", []),
            tools=[
                ToolConfig(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    class_name=t.get("class", ""),
                    config=t.get("config", {})
                )
                for t in config.get("tools", [])
            ],
            prompt_template=config.get("prompt_template", ""),
            config=config.get("config", {}),
            documentation_path=str(skill_dir / "SKILL.md") if (skill_dir / "SKILL.md").exists() else None
        )
        
        # 3. 创建 Skill 实例
        skill = DynamicSkill(
            metadata=SkillMetadata(
                name=metadata.name,
                version=metadata.version,
                description=metadata.description,
                author=metadata.author,
                tags=metadata.tags,
                scope=metadata.scope
            ),
            config=config
        )
        
        # 4. 注册
        self._skills[skill_name] = skill
        self._metadata[skill_name] = metadata
        
        # 5. 建立触发词索引
        for trigger in metadata.triggers:
            trigger_lower = trigger.lower()
            if trigger_lower not in self._triggers:
                self._triggers[trigger_lower] = []
            self._triggers[trigger_lower].append(skill_name)
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取 Skill 实例"""
        return self._skills.get(name)
    
    def get_metadata(self, name: str) -> Optional[EnhancedSkillMetadata]:
        """获取 Skill 元数据"""
        return self._metadata.get(name)
    
    def find_skills_by_trigger(self, query: str) -> List[str]:
        """根据触发词查找 Skill"""
        query_lower = query.lower()
        
        # 精确匹配
        if query_lower in self._triggers:
            return self._triggers[query_lower]
        
        # 模糊匹配
        results = []
        for trigger, skill_names in self._triggers.items():
            if query_lower in trigger or trigger in query_lower:
                results.extend(skill_names)
        
        return list(set(results))
    
    def get_skill_documentation(self, name: str) -> Optional[str]:
        """获取 Skill 文档"""
        metadata = self._metadata.get(name)
        if not metadata or not metadata.documentation_path:
            return None
        
        doc_path = Path(metadata.documentation_path)
        if doc_path.exists():
            with open(doc_path) as f:
                return f.read()
        return None
    
    def list_skills(self) -> List[EnhancedSkillMetadata]:
        """列出所有 Skills"""
        return list(self._metadata.values())
    
    def search_skills(self, query: str) -> List[EnhancedSkillMetadata]:
        """搜索 Skills"""
        query_lower = query.lower()
        results = []
        
        for metadata in self._metadata.values():
            # 搜索名称、描述、标签
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append(metadata)
        
        return results


# 全局单例
_enhanced_registry: Optional[EnhancedSkillRegistry] = None


def get_enhanced_skill_registry() -> EnhancedSkillRegistry:
    """获取增强版 Skill 注册表"""
    global _enhanced_registry
    if _enhanced_registry is None:
        _enhanced_registry = EnhancedSkillRegistry()
    return _enhanced_registry
