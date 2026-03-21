"""
Skill 市场 - 能力市场的 Skill 部分

功能:
- Skill 注册与管理
- Skill 组合
- Skill 质量评估
- Skill 版本管理

纯新增，不影响现有 Skill 实现
"""

import uuid
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SkillStatus(Enum):
    """Skill 状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


@dataclass
class SkillInfo:
    """Skill 信息"""
    skill_id: str
    name: str
    description: str
    status: SkillStatus = SkillStatus.ACTIVE
    
    # 组成
    tools: List[str] = field(default_factory=list)  # tool_ids
    agents: List[str] = field(default_factory=list)  # agent_ids
    prompts: List[str] = field(default_factory=list)  # prompt 模板
    
    # 配置
    config: Dict = field(default_factory=dict)
    
    # 版本
    version: str = "1.0.0"
    version_history: List[Dict] = field(default_factory=list)
    
    # 质量
    quality_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0
    
    # 元数据
    author: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SkillDefinition:
    """Skill 定义"""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    prompts: List[str] = field(default_factory=list)
    config: Optional[Dict] = None
    tags: List[str] = field(default_factory=list)
    category: str = "general"


class SkillMarketplace:
    """
    Skill 市场 - 单例模式
    
    功能:
    - Skill 注册
    - Skill 组合
    - Skill 发现
    - Skill 质量追踪
    """
    
    _instance: Optional['SkillMarketplace'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Skill 存储
        self._skills: Dict[str, SkillInfo] = {}  # skill_id -> SkillInfo
        self._skills_by_name: Dict[str, str] = {}  # name -> skill_id
        self._skills_by_category: Dict[str, List[str]] = {}  # category -> [skill_id]
        
        # 组合关系
        self._composed_skills: Dict[str, Set[str]] = {}  # skill_id -> set of composed skill_ids
        
        # 内置 Skill 初始化
        self._register_builtin_skills()
        
        self._initialized = True
    
    def _register_builtin_skills(self):
        """注册内置 Skill"""
        builtin_skills = [
            SkillDefinition(
                name="ResearchAssistant",
                description="研究助手 Skill，提供深度研究和分析能力",
                tools=["web_search", "document_reader"],
                agents=["ReasoningAgent", "RetrievalAgent"],
                prompts=["research_template"],
                tags=["research", "analysis"],
                category="research"
            ),
            SkillDefinition(
                name="CodeAssistant",
                description="代码助手 Skill，提供代码生成和调试能力",
                tools=["code_generator", "code_executor"],
                agents=["ReasoningAgent"],
                prompts=["code_template"],
                tags=["coding", "development"],
                category="development"
            ),
            SkillDefinition(
                name="KnowledgeQA",
                description="知识问答 Skill，基于知识库的问答",
                tools=["retrieval_tool", "citation_tool"],
                agents=["RAGAgent", "ValidationAgent"],
                prompts=["qa_template"],
                tags=["qa", "knowledge"],
                category="knowledge"
            ),
        ]
        
        for definition in builtin_skills:
            self.register(definition)
    
    def register(self, definition: SkillDefinition) -> SkillInfo:
        """
        注册 Skill
        
        Args:
            definition: Skill 定义
            
        Returns:
            SkillInfo: Skill 信息
        """
        # 检查名称是否已存在
        if definition.name in self._skills_by_name:
            raise ValueError(f"Skill 名称已存在: {definition.name}")
        
        skill_id = f"skill_{uuid.uuid4().hex[:12]}"
        
        skill = SkillInfo(
            skill_id=skill_id,
            name=definition.name,
            description=definition.description,
            tools=definition.tools,
            agents=definition.agents,
            prompts=definition.prompts,
            config=definition.config or {},
            tags=definition.tags,
            category=definition.category
        )
        
        # 存储
        self._skills[skill_id] = skill
        self._skills_by_name[definition.name] = skill_id
        
        if definition.category not in self._skills_by_category:
            self._skills_by_category[definition.category] = []
        self._skills_by_category[definition.category].append(skill_id)
        
        return skill
    
    def compose(
        self,
        name: str,
        description: str,
        skill_ids: List[str],
        tags: Optional[List[str]] = None
    ) -> SkillInfo:
        """
        组合多个 Skill
        
        Args:
            name: 组合 Skill 名称
            description: 描述
            skill_ids: 要组合的 Skill ID 列表
            tags: 标签
            
        Returns:
            SkillInfo: 组合后的 Skill
        """
        # 验证所有 Skill 存在
        for sid in skill_ids:
            if sid not in self._skills:
                raise ValueError(f"Skill 不存在: {sid}")
        
        # 合并工具和 Agent
        tools = []
        agents = []
        prompts = []
        
        for sid in skill_ids:
            skill = self._skills[sid]
            tools.extend(skill.tools)
            agents.extend(skill.agents)
            prompts.extend(skill.prompts)
        
        # 去重
        tools = list(set(tools))
        agents = list(set(agents))
        prompts = list(set(prompts))
        
        # 创建组合 Skill
        definition = SkillDefinition(
            name=name,
            description=description,
            tools=tools,
            agents=agents,
            prompts=prompts,
            tags=tags or []
        )
        
        composed_skill = self.register(definition)
        
        # 记录组合关系
        self._composed_skills[composed_skill.skill_id] = set(skill_ids)
        
        return composed_skill
    
    def get_by_id(self, skill_id: str) -> Optional[SkillInfo]:
        """通过 ID 获取 Skill"""
        return self._skills.get(skill_id)
    
    def get_by_name(self, name: str) -> Optional[SkillInfo]:
        """通过名称获取 Skill"""
        skill_id = self._skills_by_name.get(name)
        if not skill_id:
            return None
        return self._skills.get(skill_id)
    
    def list_all(self, status: Optional[SkillStatus] = None) -> List[SkillInfo]:
        """列出所有 Skill"""
        skills = list(self._skills.values())
        
        if status:
            skills = [s for s in skills if s.status == status]
        
        return skills
    
    def list_by_category(self, category: str) -> List[SkillInfo]:
        """按类别列出 Skill"""
        skill_ids = self._skills_by_category.get(category, [])
        return [self._skills[sid] for sid in skill_ids if sid in self._skills]
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[SkillStatus] = None
    ) -> List[SkillInfo]:
        """
        搜索 Skill
        
        Args:
            query: 搜索关键词
            category: 按类别过滤
            tags: 按标签过滤
            status: 按状态过滤
            
        Returns:
            List[SkillInfo]: 匹配的 Skill
        """
        results = list(self._skills.values())
        
        if status:
            results = [s for s in results if s.status == status]
        
        if category:
            results = [s for s in results if s.category == category]
        
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in s.name.lower() or query_lower in s.description.lower()
            ]
        
        if tags:
            results = [
                s for s in results
                if any(tag.lower() in [t.lower() for t in s.tags] for tag in tags)
            ]
        
        return results
    
    def update_quality(self, skill_id: str, success: bool, quality_score: float) -> bool:
        """更新 Skill 质量"""
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        
        # 更新使用统计
        skill.usage_count += 1
        
        # 更新成功率
        if success:
            skill.success_rate = skill.success_rate * 0.9 + 0.1
        else:
            skill.success_rate = skill.success_rate * 0.9
        
        # 更新质量分数
        skill.quality_score = skill.quality_score * 0.8 + quality_score * 0.2
        
        return True
    
    def get_categories(self) -> List[str]:
        """获取所有类别"""
        return list(self._skills_by_category.keys())
    
    def get_stats(self) -> Dict:
        """获取市场统计"""
        return {
            "total_skills": len(self._skills),
            "active_skills": len([s for s in self._skills.values() if s.status == SkillStatus.ACTIVE]),
            "by_category": {
                cat: len(sids)
                for cat, sids in self._skills_by_category.items()
            },
            "avg_quality": sum(s.quality_score for s in self._skills.values()) / max(len(self._skills), 1)
        }
    
    def __len__(self) -> int:
        return len(self._skills)


# 全局单例
_skill_marketplace: Optional[SkillMarketplace] = None


def get_skill_marketplace() -> SkillMarketplace:
    """获取 Skill 市场实例"""
    global _skill_marketplace
    if _skill_marketplace is None:
        _skill_marketplace = SkillMarketplace()
    return _skill_marketplace
