"""
Requirement Analyzer Agent - 需求分析智能体

职责：
1. 理解用户需求
2. 检查现有能力是否满足
3. 判断是否需要新建 Agent/Skill/Tool
4. 与用户确认后执行或创建
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import time
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class CapabilityMatch(Enum):
    """能力匹配结果"""
    EXACT_MATCH = "exact_match"        # 完全匹配
    PARTIAL_MATCH = "partial_match"    # 部分匹配
    NO_MATCH = "no_match"            # 不匹配
    NEED_CREATION = "need_creation"   # 需要创建新能力


@dataclass
class CapabilityInfo:
    """能力信息"""
    type: str  # agent, skill, tool
    name: str
    description: str
    id: str
    match_score: float = 0.0
    can_handle: bool = False
    limitations: List[str] = field(default_factory=list)


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    requirement: str
    understood_requirement: str
    capabilities_needed: List[str]
    existing_capabilities: List[CapabilityInfo] = field(default_factory=list)
    match_result: CapabilityMatch = CapabilityMatch.NO_MATCH
    recommended_action: str = ""
    suggested_creation: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    requires_confirmation: bool = False
    confirmation_message: str = ""


class RequirementAnalyzerAgent(IAgent):
    """
    需求分析Agent - 智能理解需求并匹配合适的能力
    
    工作流程：
    1. 理解需求 - 解析用户想要什么
    2. 能力盘点 - 检查现有的Agent/Skill/Tool
    3. 匹配分析 - 判断是否能满足需求
    4. 决策建议 - 是否需要创建新能力
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="requirement_analyzer_agent",
                description="需求分析Agent，智能理解需求并匹配合适的能力",
                version="1.0.0"
            )
        super().__init__(config)
        
        self._capabilities_cache = None
        self._last_cache_time = 0
        self._cache_ttl = 60  # 缓存60秒
        
        logger.info("RequirementAnalyzerAgent initialized")
    
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            requirement = inputs.get("query", inputs.get("requirement", ""))
            if not requirement:
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=0.0,
                    error="Requirement is required"
                )
            
            context = context or {}
            auto_match = context.get("auto_match", True)
            require_confirmation = context.get("require_confirmation", True)
            
            result = await self.analyze_requirement(
                requirement=requirement,
                auto_match=auto_match,
                require_confirmation=require_confirmation
            )
            
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.SUCCESS,
                output=result.__dict__,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"RequirementAnalyzer execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def analyze_requirement(
        self,
        requirement: str,
        auto_match: bool = True,
        require_confirmation: bool = True
    ) -> RequirementAnalysis:
        """分析需求并匹配合适的能力"""
        
        # 1. 理解需求
        understood = self._understand_requirement(requirement)
        needed = self._extract_needed_capabilities(requirement)
        
        # 2. 获取现有能力
        existing = await self._get_all_capabilities()
        
        # 3. 匹配分析
        matched = self._match_capabilities(needed, existing)
        
        # 4. 生成建议
        analysis = RequirementAnalysis(
            requirement=requirement,
            understood_requirement=understood,
            capabilities_needed=needed,
            existing_capabilities=matched,
            match_result=self._determine_match_result(matched),
            confidence=self._calculate_confidence(matched, needed)
        )
        
        # 5. 生成推荐动作
        self._generate_recommendation(analysis, auto_match, require_confirmation)
        
        return analysis
    
    def _understand_requirement(self, requirement: str) -> str:
        """理解用户需求"""
        req_lower = requirement.lower()
        
        # 运维相关
        if any(k in req_lower for k in ["诊断", "修复", "重启", "监控", "检查", "health", "diagnosis", "fix"]):
            return "系统运维诊断和修复"
        
        # 数据处理
        if any(k in req_lower for k in ["分析", "统计", "报表", "data", "analytics"]):
            return "数据分析与报表生成"
        
        # 对话交互
        if any(k in req_lower for k in ["聊天", "对话", "回答", "chat", "qa"]):
            return "对话问答"
        
        # 内容生成
        if any(k in req_lower for k in ["生成", "创建", "编写", "create", "generate"]):
            return "内容创建"
        
        # 搜索检索
        if any(k in req_lower for k in ["搜索", "查找", "检索", "search", "find"]):
            return "搜索检索"
        
        return "通用任务处理"
    
    def _extract_needed_capabilities(self, requirement: str) -> List[str]:
        """提取需求需要的能力类型"""
        needed = []
        req_lower = requirement.lower()
        
        capability_keywords = {
            "系统诊断": ["诊断", "修复", "健康检查", "diagnosis", "fix", "health", "重启"],
            "指标监控": ["监控", "指标", "metric", "monitor", "性能"],
            "日志分析": ["日志", "log", "trace", "追踪"],
            "数据处理": ["数据", "处理", "清洗", "data", "process"],
            "对话生成": ["对话", "聊天", "chat", "qa", "问答"],
            "搜索检索": ["搜索", "查找", "search", "find"],
            "API调用": ["调用", "集成", "api", "集成"],
            "定时任务": ["定时", "调度", "schedule", "cron"],
        }
        
        for cap, keywords in capability_keywords.items():
            if any(k in req_lower for k in keywords):
                needed.append(cap)
        
        if not needed:
            needed.append("通用任务")
        
        return needed
    
    async def _get_all_capabilities(self) -> List[CapabilityInfo]:
        """获取所有现有能力"""
        current_time = time.time()
        
        # 使用缓存
        if self._capabilities_cache and (current_time - self._last_cache_time) < self._cache_ttl:
            return self._capabilities_cache
        
        capabilities = []
        
        # 1. 获取 Agents
        agents = await self._get_agents()
        for agent in agents:
            capabilities.append(CapabilityInfo(
                type="agent",
                name=agent.get("name", "unknown"),
                description=agent.get("description", ""),
                id=agent.get("id", "")
            ))
        
        # 2. 获取 Skills
        skills = await self._get_skills()
        for skill in skills:
            capabilities.append(CapabilityInfo(
                type="skill",
                name=skill.get("name", "unknown"),
                description=skill.get("description", ""),
                id=skill.get("id", "")
            ))
        
        # 3. 获取 Tools
        tools = await self._get_tools()
        for tool in tools:
            capabilities.append(CapabilityInfo(
                type="tool",
                name=tool.get("name", "unknown"),
                description=tool.get("description", ""),
                id=tool.get("id", "")
            ))
        
        self._capabilities_cache = capabilities
        self._last_cache_time = current_time
        
        return capabilities
    
    async def _get_agents(self) -> List[Dict]:
        """获取Agent列表"""
        try:
            import requests
            resp = requests.get(
                "http://localhost:8000/api/v1/agents",
                headers={"Authorization": "Bearer test"},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("agents", [])
        except:
            pass
        return []
    
    async def _get_skills(self) -> List[Dict]:
        """获取Skill列表"""
        try:
            import requests
            resp = requests.get(
                "http://localhost:8000/api/v1/skills",
                headers={"Authorization": "Bearer test"},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("skills", [])
        except:
            pass
        return []
    
    async def _get_tools(self) -> List[Dict]:
        """获取Tool列表"""
        try:
            import requests
            resp = requests.get(
                "http://localhost:8000/api/v1/tools",
                headers={"Authorization": "Bearer test"},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("tools", [])
        except:
            pass
        return []
    
    def _match_capabilities(self, needed: List[str], existing: List[CapabilityInfo]) -> List[CapabilityInfo]:
        """匹配能力"""
        matched = []
        
        # 简单的关键词匹配
        needed_text = " ".join(needed).lower()
        
        for cap in existing:
            score = 0
            desc_lower = (cap.description + " " + cap.name).lower()
            
            for need in needed:
                need_lower = need.lower()
                if need_lower in desc_lower:
                    score += 1
            
            if score > 0:
                cap.match_score = score / len(needed)
                cap.can_handle = cap.match_score >= 0.5
                matched.append(cap)
        
        # 按匹配度排序
        matched.sort(key=lambda x: x.match_score, reverse=True)
        
        return matched
    
    def _determine_match_result(self, matched: List[CapabilityInfo]) -> CapabilityMatch:
        """判断匹配结果"""
        if not matched:
            return CapabilityMatch.NEED_CREATION
        
        exact_matches = [m for m in matched if m.match_score >= 0.8]
        partial_matches = [m for m in matched if 0.3 <= m.match_score < 0.8]
        
        if exact_matches:
            return CapabilityMatch.EXACT_MATCH
        elif partial_matches:
            return CapabilityMatch.PARTIAL_MATCH
        else:
            return CapabilityMatch.NEED_CREATION
    
    def _calculate_confidence(self, matched: List[CapabilityInfo], needed: List[str]) -> float:
        """计算置信度"""
        if not matched:
            return 0.0
        
        best_score = matched[0].match_score if matched else 0.0
        
        coverage = len([m for m in matched if m.can_handle]) / max(len(needed), 1)
        
        return (best_score + coverage) / 2
    
    def _generate_recommendation(
        self,
        analysis: RequirementAnalysis,
        auto_match: bool,
        require_confirmation: bool
    ):
        """生成推荐动作"""
        
        if analysis.match_result == CapabilityMatch.EXACT_MATCH:
            analysis.recommended_action = "execute"
            analysis.requires_confirmation = False
            
        elif analysis.match_result == CapabilityMatch.PARTIAL_MATCH:
            analysis.recommended_action = "enhance_or_create"
            analysis.requires_confirmation = True
            analysis.confirmation_message = (
                f"现有能力部分满足需求，建议增强现有能力或创建新的{analysis.capabilities_needed[0] if analysis.capabilities_needed else '能力'}。"
                f"是否需要创建新能力？"
            )
            
        else:  # NO_MATCH or NEED_CREATION
            analysis.recommended_action = "create"
            analysis.requires_confirmation = True
            
            entity_type = self._infer_entity_type(analysis.capabilities_needed)
            analysis.suggested_creation = {
                "type": entity_type,
                "name": f"{analysis.capabilities_needed[0] if analysis.capabilities_needed else 'Custom'}Capability",
                "description": analysis.understood_requirement,
                "capabilities_needed": analysis.capabilities_needed
            }
            
            analysis.confirmation_message = (
                f"未找到匹配的能力，建议创建新的 {entity_type}。"
                f"是否创建？"
            )
    
    def _infer_entity_type(self, capabilities_needed: List[str]) -> str:
        """推断需要创建的实体类型"""
        capability_to_entity = {
            "系统诊断": "agent",
            "指标监控": "tool",
            "日志分析": "tool",
            "数据处理": "skill",
            "对话生成": "agent",
            "搜索检索": "tool",
            "API调用": "tool",
            "定时任务": "tool",
            "通用任务": "agent",
        }
        
        for cap in capabilities_needed:
            if cap in capability_to_entity:
                return capability_to_entity[cap]
        
        return "agent"  # 默认创建Agent


# 单例
_requirement_analyzer: Optional[RequirementAnalyzerAgent] = None

def get_requirement_analyzer() -> RequirementAnalyzerAgent:
    global _requirement_analyzer
    if _requirement_analyzer is None:
        _requirement_analyzer = RequirementAnalyzerAgent()
    return _requirement_analyzer
