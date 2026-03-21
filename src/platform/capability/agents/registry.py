"""
Agent 注册表 - 能力市场的 Agent 部分

功能:
- Agent 注册与发现
- Agent 目录管理
- Agent 启用/禁用

纯新增，不影响现有 Agent 实现
"""

import uuid
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """Agent 状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class AgentCategory(Enum):
    """Agent 类别"""
    REASONING = "reasoning"  # 推理类
    RAG = "rag"              # 检索增强类
    RETRIEVAL = "retrieval"   # 检索类
    QUALITY = "quality"       # 质量控制类
    COORDINATION = "coordination"  # 协调类
    SPECIALIZED = "specialized"  # 专业领域类
    CUSTOM = "custom"           # 自定义类


@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    name: str
    description: str
    category: AgentCategory
    status: AgentStatus = AgentStatus.ACTIVE
    
    # 能力描述
    capabilities: List[str] = field(default_factory=list)
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    
    # 配置
    config: Dict = field(default_factory=dict)
    
    # 元数据
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 统计
    usage_count: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentRegistration:
    """Agent 注册配置"""
    name: str
    description: str
    category: AgentCategory
    capabilities: List[str]
    input_types: List[str] = field(default_factory=lambda: ["text"])
    output_types: List[str] = field(default_factory=lambda: ["text"])
    config: Optional[Dict] = None
    tags: List[str] = field(default_factory=list)


class AgentRegistry:
    """
    Agent 注册表 - 单例模式
    
    功能:
    - 注册 Agent
    - 发现 Agent
    - 管理 Agent 状态
    - 按类别、能力搜索
    """
    
    _instance: Optional['AgentRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Agent 存储
        self._agents: Dict[str, AgentInfo] = {}  # agent_id -> AgentInfo
        self._agents_by_name: Dict[str, str] = {}  # name -> agent_id
        self._agents_by_category: Dict[AgentCategory, List[str]] = {}  # category -> [agent_id]
        
        # 内置 Agent 初始化
        self._register_builtin_agents()
        
        self._initialized = True
    
    def _register_builtin_agents(self):
        """注册内置 Agent"""
        builtin_agents = [
            AgentRegistration(
                name="ChiefAgent",
                description="首席 Agent，负责整体协调和任务分解",
                category=AgentCategory.COORDINATION,
                capabilities=["task_planning", "coordination", "result_aggregation"],
                input_types=["text", "json"],
                output_types=["text", "json"],
                tags=["coordinator", "orchestration"]
            ),
            AgentRegistration(
                name="RAGAgent",
                description="检索增强生成 Agent，提供基于知识库的答案",
                category=AgentCategory.RAG,
                capabilities=["retrieval", "generation", "citation"],
                input_types=["text"],
                output_types=["text", "json"],
                tags=["rag", "knowledge"]
            ),
            AgentRegistration(
                name="ReasoningAgent",
                description="推理 Agent，提供深度推理和分析",
                category=AgentCategory.REASONING,
                capabilities=["reasoning", "analysis", "step_by_step"],
                input_types=["text"],
                output_types=["text", "json"],
                tags=["reasoning", "analysis"]
            ),
            AgentRegistration(
                name="RetrievalAgent",
                description="检索 Agent，从多种来源检索信息",
                category=AgentCategory.RETRIEVAL,
                capabilities=["search", "retrieval", "filtering"],
                input_types=["text"],
                output_types=["json", "text"],
                tags=["retrieval", "search"]
            ),
            AgentRegistration(
                name="ValidationAgent",
                description="验证 Agent，检查答案质量和准确性",
                category=AgentCategory.QUALITY,
                capabilities=["validation", "fact_check", "quality_assessment"],
                input_types=["text", "json"],
                output_types=["json"],
                tags=["quality", "validation"]
            ),
        ]
        
        for reg in builtin_agents:
            self.register(reg)
    
    def register(self, registration: AgentRegistration) -> AgentInfo:
        """
        注册 Agent
        
        Args:
            registration: 注册配置
            
        Returns:
            AgentInfo: Agent 信息
        """
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        
        agent = AgentInfo(
            agent_id=agent_id,
            name=registration.name,
            description=registration.description,
            category=registration.category,
            capabilities=registration.capabilities,
            input_types=registration.input_types,
            output_types=registration.output_types,
            config=registration.config or {},
            tags=registration.tags
        )
        
        # 存储
        self._agents[agent_id] = agent
        self._agents_by_name[registration.name] = agent_id
        
        if registration.category not in self._agents_by_category:
            self._agents_by_category[registration.category] = []
        self._agents_by_category[registration.category].append(agent_id)
        
        return agent
    
    def get_by_id(self, agent_id: str) -> Optional[AgentInfo]:
        """通过 ID 获取 Agent"""
        return self._agents.get(agent_id)
    
    def get_by_name(self, name: str) -> Optional[AgentInfo]:
        """通过名称获取 Agent"""
        agent_id = self._agents_by_name.get(name)
        if not agent_id:
            return None
        return self._agents.get(agent_id)
    
    def list_all(self, status: Optional[AgentStatus] = None) -> List[AgentInfo]:
        """列出所有 Agent"""
        agents = list(self._agents.values())
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        return agents
    
    def list_by_category(self, category: AgentCategory) -> List[AgentInfo]:
        """按类别列出 Agent"""
        agent_ids = self._agents_by_category.get(category, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[AgentCategory] = None,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        status: Optional[AgentStatus] = None
    ) -> List[AgentInfo]:
        """
        搜索 Agent
        
        Args:
            query: 搜索关键词 (匹配名称和描述)
            category: 按类别过滤
            tags: 按标签过滤
            capabilities: 按能力过滤
            status: 按状态过滤
            
        Returns:
            List[AgentInfo]: 匹配的 Agent 列表
        """
        results = list(self._agents.values())
        
        # 按状态过滤
        if status:
            results = [a for a in results if a.status == status]
        
        # 按类别过滤
        if category:
            results = [a for a in results if a.category == category]
        
        # 按关键词过滤
        if query:
            query_lower = query.lower()
            results = [
                a for a in results
                if query_lower in a.name.lower() or query_lower in a.description.lower()
            ]
        
        # 按标签过滤
        if tags:
            results = [
                a for a in results
                if any(tag.lower() in [t.lower() for t in a.tags] for tag in tags)
            ]
        
        # 按能力过滤
        if capabilities:
            results = [
                a for a in results
                if all(cap.lower() in [c.lower() for c in a.capabilities] for cap in capabilities)
            ]
        
        return results
    
    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """更新 Agent 状态"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        agent.status = status
        agent.updated_at = datetime.now()
        return True
    
    def update_stats(
        self,
        agent_id: str,
        success: bool,
        latency: float
    ) -> bool:
        """更新 Agent 统计"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # 更新使用次数
        agent.usage_count += 1
        
        # 更新成功率 (指数移动平均)
        if success:
            agent.success_rate = agent.success_rate * 0.9 + 0.1
        else:
            agent.success_rate = agent.success_rate * 0.9
        
        # 更新平均延迟
        agent.avg_latency = agent.avg_latency * 0.9 + latency * 0.1
        
        return True
    
    def get_categories(self) -> List[AgentCategory]:
        """获取所有类别"""
        return list(self._agents_by_category.keys())
    
    def get_stats(self) -> Dict:
        """获取注册表统计"""
        return {
            "total_agents": len(self._agents),
            "active_agents": len([a for a in self._agents.values() if a.status == AgentStatus.ACTIVE]),
            "by_category": {
                cat.value: len(agent_ids)
                for cat, agent_ids in self._agents_by_category.items()
            }
        }
    
    def __len__(self) -> int:
        return len(self._agents)


# 全局单例
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """获取 Agent 注册表实例"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
