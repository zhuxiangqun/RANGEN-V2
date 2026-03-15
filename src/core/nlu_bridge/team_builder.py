#!/usr/bin/env python3
"""
团队构建器 (Team Builder)
=======================

功能:
- 根据需求分析结果，构建多Agent协作团队
- 复用现有的AgentBuilder和SkillFactory
- 自动创建缺失的Skills
- 自动创建Agent
- 自动创建Workflow
- 自动记录成本
- 注册到数据库，可在管理界面查看和测试

使用方式:
    from src.core.nlu_bridge.team_builder import TeamBuilder
    
    builder = TeamBuilder()
    team = await builder.build(requirement_analysis)
"""

import logging
import uuid
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# 成本常量
SKILL_CREATE_COST = 0.01      # 创建Skill的估计成本 (美元)
AGENT_CREATE_COST = 0.02       # 创建Agent的估计成本 (美元)
TEAM_CREATE_COST = 0.005       # 创建Team的估计成本 (美元)
TYPE_DETECTION_COST = 0.001    # 类型识别的估计成本
PARSE_COST = 0.002             # 需求解析的估计成本


@dataclass
class CostRecord:
    """成本记录"""
    item: str
    cost: float
    description: str


@dataclass
class TeamRole:
    """团队角色"""
    name: str
    display_name: str
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Team:
    """团队定义"""
    id: str
    name: str
    roles: List[TeamRole] = field(default_factory=list)
    workflow: List[str] = field(default_factory=list)
    collaboration_mode: str = "sequential"
    created_skills: List[str] = field(default_factory=list)
    created_agents: List[str] = field(default_factory=list)
    cost_records: List[CostRecord] = field(default_factory=list)
    total_cost: float = 0.0


class TeamBuilder:
    """
    团队构建器
    
    复用现有组件:
    - AgentBuilder: 创建Agent
    - SkillFactory: 创建缺失的Skill
    - CapabilityChecker: 检查能力
    - Database: 注册Team/Agent/Skill
    """
    
    # 中文到英文的Skill名称映射
    SKILL_NAME_MAP = {
        "项目管理": "project_management",
        "软件架构设计": "software_architecture",
        "编程开发": "software_development",
        "质量保证测试": "quality_assurance",
        "持续集成与部署": "ci_cd",
        "技术文档编写": "technical_documentation",
        "沟通协作": "team_collaboration",
        "需求分析": "requirement_analysis",
        "优先级排序": "priority_ranking",
        "用户故事": "user_story",
        "技术设计": "technical_design",
        "架构评审": "architecture_review",
        "代码生成": "code_generation",
        "代码审查": "code_review",
        "重构": "refactoring",
        "测试用例生成": "test_generation",
        "测试执行": "test_execution",
        "缺陷报告": "bug_reporting",
        "自动化部署": "deployment",
        "监控": "monitoring",
        "API文档": "api_documentation",
        "用户手册": "user_manual",
    }
    
    ROLE_TEMPLATES = {
        "product_manager": {
            "display_name": "产品经理",
            "skills": ["requirement_analysis", "priority_ranking", "user_story"],
            "tools": ["search", "file_manager"],
            "description": "负责需求分析和项目管理"
        },
        "architect": {
            "display_name": "系统架构师",
            "skills": ["technical_design", "architecture_review"],
            "tools": ["search", "file_manager"],
            "description": "负责技术方案设计"
        },
        "developer": {
            "display_name": "开发者",
            "skills": ["code_generation", "code_review", "refactoring"],
            "tools": ["code_executor", "file_manager", "search"],
            "description": "负责代码实现"
        },
        "qa": {
            "display_name": "测试工程师",
            "skills": ["test_generation", "test_execution", "bug_reporting"],
            "tools": ["code_executor", "file_manager"],
            "description": "负责质量保证"
        },
        "devops": {
            "display_name": "运维工程师",
            "skills": ["deployment", "ci_cd", "monitoring"],
            "tools": ["code_executor", "file_manager"],
            "description": "负责部署和运维"
        },
        "tech_writer": {
            "display_name": "技术文档工程师",
            "skills": ["api_documentation", "user_manual"],
            "tools": ["file_manager", "search"],
            "description": "负责技术文档"
        }
    }
    
    def __init__(self):
        self._capability_checker = None
        self._skill_factory = None
        self._agent_builder = None
        self._db = None
    
    def _get_db(self):
        if self._db is None:
            try:
                from src.services.database import get_database
                self._db = get_database()
            except Exception as e:
                logger.warning(f"Database init failed: {e}")
        return self._db
    
    def _get_capability_checker(self):
        if self._capability_checker is None:
            try:
                from src.services.capability_checker import CapabilityChecker
                self._capability_checker = CapabilityChecker()
            except Exception as e:
                logger.warning(f"CapabilityChecker init failed: {e}")
        return self._capability_checker
    
    def _get_skill_factory(self):
        if self._skill_factory is None:
            try:
                from src.agents.skills.skill_factory_integration import get_factory_integration
                self._skill_factory = get_factory_integration()
            except Exception as e:
                logger.warning(f"SkillFactory init failed: {e}")
        return self._skill_factory
    
    def _get_agent_builder(self):
        if self._agent_builder is None:
            try:
                from src.agents.agent_builder import AgentBuilder
                self._agent_builder = AgentBuilder()
            except Exception as e:
                logger.warning(f"AgentBuilder init failed: {e}")
        return self._agent_builder
    
    async def build(self, requirement_analysis) -> Team:
        """
        构建团队
        
        完整流程:
        1. 检查并创建缺失的Skills
        2. 创建Agent
        3. 创建Workflow
        4. 记录成本
        5. 注册Team到数据库
        """
        
        created_skills = []
        created_agents = []
        cost_records = []
        
        # 1. 检查并创建缺失的Skills
        missing_skills = await self._ensure_skills(requirement_analysis.required_skills)
        created_skills.extend(missing_skills)
        
        # 记录Skill创建成本
        for skill in missing_skills:
            cost_records.append(CostRecord(
                item=f"create_skill:{skill}",
                cost=SKILL_CREATE_COST,
                description=f"创建Skill: {skill}"
            ))
        
        # 2. 为每个角色创建Agent
        for role_name in requirement_analysis.roles:
            role_info = self.ROLE_TEMPLATES.get(role_name, {})
            agent_name = await self._create_agent(
                name=role_name,
                display_name=role_info.get("display_name", role_name),
                skills=role_info.get("skills", []),
                tools=role_info.get("tools", []),
                description=role_info.get("description", "")
            )
            if agent_name:
                created_agents.append(agent_name)
                cost_records.append(CostRecord(
                    item=f"create_agent:{agent_name}",
                    cost=AGENT_CREATE_COST,
                    description=f"创建Agent: {agent_name}"
                ))
        
        # 3. 创建团队
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        
        roles = []
        for role_name in requirement_analysis.roles:
            role_info = self.ROLE_TEMPLATES.get(role_name, {})
            
            role = TeamRole(
                name=role_name,
                display_name=role_info.get("display_name", role_name),
                skills=role_info.get("skills", []),
                tools=role_info.get("tools", []),
                description=role_info.get("description", "")
            )
            roles.append(role)
        
        # 计算总成本
        total_cost = sum(c.cost for c in cost_records)
        
        # 记录团队创建成本
        cost_records.append(CostRecord(
            item="create_team",
            cost=TEAM_CREATE_COST,
            description=f"创建团队: {requirement_analysis.team_name or '软件研发团队'}"
        ))
        total_cost += TEAM_CREATE_COST
        
        team = Team(
            id=team_id,
            name=requirement_analysis.team_name or "软件研发团队",
            roles=roles,
            workflow=requirement_analysis.workflow or ["需求分析", "开发", "测试", "交付"],
            collaboration_mode="sequential",
            created_skills=created_skills,
            created_agents=created_agents,
            cost_records=cost_records,
            total_cost=total_cost
        )
        
        # 4. 保存成本记录
        await self._save_cost_records(team)
        
        # 5. 注册到数据库
        await self._register_team(team)
        
        logger.info(f"Team built: {team.name} with {len(team.roles)} roles, {len(created_skills)} skills, {len(created_agents)} agents")
        
        return team
    
    async def _ensure_skills(self, required_skills: List[str]) -> List[str]:
        """检查并创建缺失的Skills"""
        
        checker = self._get_capability_checker()
        created_skills = []
        
        if not checker:
            logger.warning("CapabilityChecker not available, skipping skill check")
            return created_skills
        
        try:
            result = checker.check_skills(required_skills)
            
            if result.missing:
                logger.info(f"Missing skills detected: {result.missing}")
                
                factory = self._get_skill_factory()
                for skill_name in result.missing:
                    try:
                        success = await self._create_skill(skill_name)
                        if success:
                            created_skills.append(skill_name)
                    except Exception as e:
                        logger.warning(f"Failed to create skill {skill_name}: {e}")
        except Exception as e:
            logger.warning(f"Skill check failed: {e}")
        
        return created_skills
    
    async def _create_skill(self, skill_name: str) -> Optional[str]:
        """创建Skill并注册到系统"""
        logger.info(f"Creating skill: {skill_name}")
        
        # 转换为英文名称
        english_name = self.SKILL_NAME_MAP.get(skill_name, skill_name)
        
        # 尝试在数据库创建Skill记录 (降级方案)
        try:
            db = self._get_db()
            if db:
                import uuid
                skill_id = f"skill_{uuid.uuid4().hex[:8]}"
                
                skill_data = {
                    "id": skill_id,
                    "name": english_name,
                    "type": "auto_created",
                    "description": f"自动创建的技能: {skill_name}",
                    "status": "active",
                    "source": "auto_created"
                }
                
                db.create_skill(skill_data)
                logger.info(f"Skill created: {english_name}")
                return english_name
        except Exception as e:
            logger.warning(f"Failed to create skill {skill_name}: {e}")
        
        return None

    async def _create_agent(self, name: str, display_name: str, 
                          skills: List[str], tools: List[str],
                          description: str) -> Optional[str]:
        """创建Agent并注册到系统"""
        logger.info(f"Creating agent: {name}")
        
        db = self._get_db()
        if not db:
            logger.warning("Database not available")
            return None
        
        try:
            import uuid
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
            
            agent_data = {
                "id": agent_id,
                "name": name,
                "type": "auto_created",
                "description": description or f"自动创建的Agent: {display_name}",
                "config_path": "",
                "status": "active"
            }
            
            db.create_agent(agent_data)
            
            # 关联Skills到Agent - 模糊匹配
            all_skills = db.get_all_skills()
            for skill in all_skills:
                skill_name = skill.get('name', '')
                for required_skill in skills:
                    if (required_skill.lower() in skill_name.lower() or 
                        skill_name.lower() in required_skill.lower()):
                        try:
                            db.add_skill_to_agent(agent_id, skill['id'])
                            logger.info(f"Added skill '{skill_name}' to agent {name}")
                        except Exception as e:
                            pass
            
            # 关联Tools到Agent - 模糊匹配
            all_tools = db.get_all_tools()
            tool_keywords = {
                'search': ['search', 'Search', '检索', '搜索'],
                'file_manager': ['file', 'File', '文件'],
                'code_executor': ['code', 'Code', '代码', 'executor', 'Executor']
            }
            
            for tool in all_tools:
                tool_name = tool.get('name', '')
                for required_tool in tools:
                    keywords = tool_keywords.get(required_tool.lower(), [required_tool])
                    if any(kw.lower() in tool_name.lower() for kw in keywords):
                        try:
                            db.add_tool_to_agent(agent_id, tool['id'])
                            logger.info(f"Added tool '{tool_name}' to agent {name}")
                        except Exception as e:
                            pass
            
            logger.info(f"Agent created successfully: {name}")
            return name
            
        except Exception as e:
            logger.warning(f"Failed to create agent {name}: {e}")
            return None
    
    async def _save_cost_records(self, team: Team):
        """保存成本记录"""
        try:
            import os
            # 使用更可靠的方式获取项目根目录
            current = os.path.dirname(os.path.abspath(__file__))
            # src/core/nlu_bridge -> src/core -> src -> project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current)))
            cost_file = os.path.join(project_root, 'data', 'auto_costs.json')
            
            os.makedirs(os.path.dirname(cost_file), exist_ok=True)
            
            existing_costs = []
            if os.path.exists(cost_file):
                with open(cost_file, 'r', encoding='utf-8') as f:
                    existing_costs = json.load(f)
            
            cost_data = {
                "team_id": team.id,
                "team_name": team.name,
                "total_cost": team.total_cost,
                "records": [
                    {
                        "item": r.item,
                        "cost": r.cost,
                        "description": r.description
                    }
                    for r in team.cost_records
                ]
            }
            
            existing_costs.append(cost_data)
            
            with open(cost_file, 'w', encoding='utf-8') as f:
                json.dump(existing_costs, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cost records saved: ${team.total_cost:.4f}")
            
        except Exception as e:
            logger.warning(f"Failed to save cost records: {e}")
    
    async def _register_team(self, team: Team):
        """注册团队到数据库"""
        db = self._get_db()
        if not db:
            logger.warning("Database not available")
            return
        
        try:
            import json
            import os
            
            # 保存到teams.json文件
            current = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current)))
            teams_file = os.path.join(project_root, 'data', 'auto_teams.json')
            
            os.makedirs(os.path.dirname(teams_file), exist_ok=True)
            
            existing_teams = []
            if os.path.exists(teams_file):
                with open(teams_file, 'r', encoding='utf-8') as f:
                    existing_teams = json.load(f)
            
            team_data = {
                "id": team.id,
                "name": team.name,
                "description": f"自动创建的团队: {team.name}",
                "roles": [r.name for r in team.roles],
                "workflow": team.workflow,
                "collaboration_mode": team.collaboration_mode,
                "created_skills": team.created_skills,
                "created_agents": team.created_agents,
                "status": "active"
            }
            
            existing_teams.append(team_data)
            
            with open(teams_file, 'w', encoding='utf-8') as f:
                json.dump(existing_teams, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Team registered: {team.name}")
            
        except Exception as e:
            logger.warning(f"Failed to register team: {e}")


async def build_team(requirement_analysis) -> Team:
    """便捷函数: 构建团队"""
    builder = TeamBuilder()
    return await builder.build(requirement_analysis)
