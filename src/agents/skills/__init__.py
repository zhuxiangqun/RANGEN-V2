"""
Skills System
Pluggable skill system for RANGEN agents.
"""

import os
import json
import yaml
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from enum import Enum


class SkillScope(Enum):
    BUNDLED = "bundled"
    MANAGED = "managed"
    WORKSPACE = "workspace"


@dataclass
class SkillMetadata:
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    scope: SkillScope = SkillScope.BUNDLED
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self._tools: Dict[str, Callable] = {}
        self._prompt_template: str = ""
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def version(self) -> str:
        return self.metadata.version
    
    @property
    def tools(self) -> Dict[str, Callable]:
        return self._tools
    
    @property
    def prompt_template(self) -> str:
        return self._prompt_template
    
    def register_tool(self, name: str, func: Callable):
        self._tools[name] = func
    
    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def get_schemas(self) -> List[ToolSchema]:
        return []


class DynamicSkill(Skill):
    def __init__(self, metadata: SkillMetadata, config: Dict[str, Any]):
        super().__init__(metadata)
        self.config = config
        self._prompt_template = config.get("prompt_template", "")
        self._tool_handlers: Dict[str, str] = config.get("handlers", {})
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action = context.get("action", "")
        handler_name = self._tool_handlers.get(action)
        if handler_name:
            return {"success": True, "result": f"Handler: {handler_name}", "action": action}
        return {"success": True, "result": "Dynamic skill executed", "action": action}
    
    def get_schemas(self) -> List[ToolSchema]:
        schemas = []
        for tool in self.config.get("tools", []):
            schemas.append(ToolSchema(
                name=tool.get("name", ""),
                description=tool.get("description", ""),
                parameters=tool.get("params", {})
            ))
        return schemas


class PythonSkill(Skill):
    def __init__(self, metadata: SkillMetadata, module_path: str):
        super().__init__(metadata)
        self.module_path = module_path
        self._module = None
        self._load_module()
    
    def _load_module(self):
        try:
            spec = importlib.util.spec_from_file_location(self.name, self.module_path)
            if spec and spec.loader:
                self._module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self._module)
                
                if hasattr(self._module, 'tools'):
                    for name, func in self._module.tools.items():
                        self.register_tool(name, func)
                
                if hasattr(self._module, 'PROMPT_TEMPLATE'):
                    self._prompt_template = self._module.PROMPT_TEMPLATE
        except Exception as e:
            print(f"Failed to load skill module: {e}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if self._module and hasattr(self._module, 'execute'):
            try:
                result = await self._module.execute(context)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "No execute function found"}


class SkillRegistry:
    def __init__(self, base_paths: Optional[Dict[SkillScope, str]] = None):
        self._skills: Dict[SkillScope, Dict[str, Skill]] = {
            SkillScope.BUNDLED: {},
            SkillScope.MANAGED: {},
            SkillScope.WORKSPACE: {},
        }
        
        self._base_paths = base_paths or {
            SkillScope.BUNDLED: "./src/agents/skills/bundled",
            SkillScope.MANAGED: os.path.expanduser("~/.rangen/skills"),
            SkillScope.WORKSPACE: "./skills",
        }
        
        self._load_bundled_skills()
    
    def _load_bundled_skills(self):
        bundled_path = Path(self._base_paths[SkillScope.BUNDLED])
        if bundled_path.exists():
            for skill_dir in bundled_path.iterdir():
                if skill_dir.is_dir():
                    self._load_skill_from_dir(skill_dir, SkillScope.BUNDLED)
    
    def _load_skill_from_dir(self, skill_dir: Path, scope: SkillScope):
        config_file = skill_dir / "skill.yaml"
        if not config_file.exists():
            config_file = skill_dir / "skill.json"
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    if config_file.suffix == ".yaml":
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                
                metadata = SkillMetadata(
                    name=config.get("name", skill_dir.name),
                    version=config.get("version", "1.0.0"),
                    description=config.get("description", ""),
                    author=config.get("author", ""),
                    tags=config.get("tags", []),
                    scope=scope,
                    dependencies=config.get("dependencies", [])
                )
                
                skill = DynamicSkill(metadata, config)
                self.register_skill(skill, scope)
            except Exception as e:
                print(f"Failed to load skill from {skill_dir}: {e}")
    
    def register_skill(self, skill: Skill, scope: SkillScope = SkillScope.BUNDLED):
        self._skills[scope][skill.name] = skill
    
    def get_skill(self, name: str, scope: Optional[SkillScope] = None) -> Optional[Skill]:
        if scope:
            return self._skills[scope].get(name)
        
        for s in SkillScope:
            skill = self._skills[s].get(name)
            if skill:
                return skill
        return None
    
    def list_skills(self, scope: Optional[SkillScope] = None) -> List[SkillMetadata]:
        if scope:
            return [s.metadata for s in self._skills[scope].values()]
        
        result = []
        for skills in self._skills.values():
            result.extend([s.metadata for s in skills.values()])
        return result
    
    def load_skill_from_path(self, skill_path: str, scope: SkillScope = SkillScope.WORKSPACE) -> Optional[Skill]:
        path = Path(skill_path)
        
        if path.is_dir():
            self._load_skill_from_dir(path, scope)
            return self.get_skill(path.name, scope)
        elif path.suffix in [".yaml", ".json"]:
            with open(path) as f:
                config = yaml.safe_load(f) if path.suffix == ".yaml" else json.load(f)
            
            metadata = SkillMetadata(
                name=config.get("name", path.stem),
                version=config.get("version", "1.0.0"),
                description=config.get("description", ""),
                scope=scope
            )
            skill = DynamicSkill(metadata, config)
            self.register_skill(skill, scope)
            return skill
        elif path.suffix == ".py":
            metadata = SkillMetadata(name=path.stem, scope=scope)
            skill = PythonSkill(metadata, str(path))
            self.register_skill(skill, scope)
            return skill
        
        return None


_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
