"""
Unified Entity Creator Service
=============================

This service provides unified natural language entity creation for:
- Agent: From natural language descriptions
- Skill: From requirements
- Team: From team composition descriptions
- Tool: From tool specifications
- Workflow: From workflow definitions

Intent Detection:
- Keywords matching to determine entity type
- LLM-based analysis for complex descriptions
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities that can be created"""
    AGENT = "agent"
    SKILL = "skill"
    TEAM = "team"
    TOOL = "tool"
    WORKFLOW = "workflow"
    SERVICE = "service"
    UNKNOWN = "unknown"


@dataclass
class CreationResult:
    """Result of entity creation"""
    success: bool
    entity_type: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class IntentAnalysis:
    """Analysis result from intent detection"""
    entity_type: EntityType
    confidence: float
    description: str
    suggested_name: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None


class UnifiedCreator:
    """
    Unified Natural Language Entity Creator
    
    Detects entity type from natural language and dispatches to appropriate creator.
    """
    
    def __init__(self):
        self._agent_creator = None
        self._skill_factory = None
        self._team_service = None
        self._tool_service = None
    
    def _get_agent_creator(self):
        """Lazy load agent creator"""
        if self._agent_creator is None:
            try:
                from src.services.nlp_agent_creator import get_nlp_agent_creator
                self._agent_creator = get_nlp_agent_creator()
            except Exception as e:
                logger.warning(f"Agent creator not available: {e}")
        return self._agent_creator
    
    def _get_skill_factory(self):
        """Lazy load skill factory"""
        if self._skill_factory is None:
            try:
                from src.agents.skills.skill_factory_integration import SkillFactoryIntegration
                self._skill_factory = SkillFactoryIntegration()
            except Exception as e:
                logger.warning(f"Skill factory not available: {e}")
        return self._skill_factory
    
    def _get_team_service(self):
        """Lazy load team service"""
        if self._team_service is None:
            try:
                from src.services.team_service import get_team_service
                self._team_service = get_team_service()
            except Exception as e:
                logger.warning(f"Team service not available: {e}")
        return self._team_service
    
    def _get_tool_service(self):
        """Lazy load tool service"""
        if self._tool_service is None:
            try:
                from src.services.tool_registry import get_tool_registry
                self._tool_service = get_tool_registry()
            except Exception as e:
                logger.warning(f"Tool service not available: {e}")
        return self._tool_service
    
    # Keywords for entity type detection
    ENTITY_KEYWORDS = {
        EntityType.AGENT: [
            "agent", "助手", "机器人", "智能体", "assistant", "bot", "帮我创建",
            "做一个", "创建一个", "新建一个",
            "代理", "客服", "分析师", "工程师"
        ],
        EntityType.SKILL: [
            "skill", "技能", "能力", "功能",
            "帮我学会", "新增技能", "添加技能"
        ],
        EntityType.TEAM: [
            "team", "团队", "小组", "协作",
            "创建一个团队", "组成团队", "团队成员"
        ],
        EntityType.TOOL: [
            "tool", "工具", "帮我做一个工具", "创建工具"
        ],
        EntityType.WORKFLOW: [
            "workflow", "工作流", "流程", "自动化流程"
        ],
    }
    
    def analyze_intent(self, description: str) -> IntentAnalysis:
        """
        Analyze user intent from natural language description
        
        Args:
            description: User's natural language description
            
        Returns:
            IntentAnalysis with detected entity type and requirements
        """
        desc_lower = description.lower()
        
        # Priority keywords (more specific, should be checked first)
        PRIORITY_KEYWORDS = {
            EntityType.SKILL: ["skill", "技能", "能力", "功能"],
            EntityType.TOOL: ["tool", "工具"],
            EntityType.TEAM: ["team", "团队", "小组"],
            EntityType.WORKFLOW: ["workflow", "工作流", "流程自动化"],
            EntityType.AGENT: ["agent", "assistant", "bot"],
        }
        
        # Check priority keywords first
        for entity_type, keywords in PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    return IntentAnalysis(
                        entity_type=entity_type,
                        confidence=0.9,
                        description=description,
                        suggested_name=None,
                        requirements={"description": description}
                    )
        
        # Fallback to keyword scoring for other keywords
        scores = {et: 0 for et in EntityType}
        
        for entity_type, keywords in self.ENTITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    scores[entity_type] += 1
        
        # Find highest scoring entity type
        max_score = max(scores.values())
        if max_score > 0:
            detected_type = max(scores, key=scores.get)
            confidence = min(1.0, max_score / 3)
        else:
            # Default to agent if no keywords matched
            detected_type = EntityType.AGENT
            confidence = 0.5
        
        # Extract suggested name
        name_match = re.search(r'(?:叫做?|名为?|name[:\s]*)([\w\u4e00-\u9fa5]+)', desc_lower)
        suggested_name = name_match.group(1) if name_match else None
        
        return IntentAnalysis(
            entity_type=detected_type,
            confidence=confidence,
            description=description,
            suggested_name=suggested_name,
            requirements={"description": description}
        )
    
    async def create_from_natural_language(
        self, 
        description: str,
        entity_type: Optional[str] = None,
        name: Optional[str] = None,
        auto_register: bool = True
    ) -> CreationResult:
        """
        Create entity from natural language description
        
        Args:
            description: Natural language description of what to create
            entity_type: Optional explicit entity type (agent/skill/team/tool/workflow)
            name: Optional name for the entity
            auto_register: Whether to auto-register the entity
            
        Returns:
            CreationResult with creation status and details
        """
        try:
            # Analyze intent if entity type not specified
            if entity_type:
                try:
                    intent_type = EntityType(entity_type.lower())
                except ValueError:
                    return CreationResult(
                        success=False,
                        entity_type="unknown",
                        error=f"Invalid entity type: {entity_type}"
                    )
            else:
                intent = self.analyze_intent(description)
                intent_type = intent.entity_type
                if not name and intent.suggested_name:
                    name = intent.suggested_name
            
            # Dispatch to appropriate creator
            if intent_type == EntityType.AGENT:
                return await self._create_agent(description, name)
            elif intent_type == EntityType.SKILL:
                return await self._create_skill(description, name)
            elif intent_type == EntityType.TEAM:
                return await self._create_team(description, name)
            elif intent_type == EntityType.TOOL:
                return await self._create_tool(description, name)
            elif intent_type == EntityType.WORKFLOW:
                return await self._create_workflow(description, name)
            else:
                return CreationResult(
                    success=False,
                    entity_type="unknown",
                    message="无法识别要创建的实体类型"
                )
                
        except Exception as e:
            logger.error(f"Entity creation failed: {e}", exc_info=True)
            return CreationResult(
                success=False,
                entity_type="unknown",
                error=str(e)
            )
    
    async def _create_agent(self, description: str, name: Optional[str]) -> CreationResult:
        """Create an Agent"""
        creator = self._get_agent_creator()
        if not creator:
            return CreationResult(
                success=False,
                entity_type="agent",
                error="Agent creator service not available"
            )
        
        try:
            result = await creator.create_agent_from_natural_language(description)
            
            if result.success:
                return CreationResult(
                    success=True,
                    entity_type="agent",
                    entity_id=result.agent.get("id") if result.agent else None,
                    entity_name=result.agent.get("name") if result.agent else name,
                    message=f"Agent创建成功: {result.agent.get('name') if result.agent else name}",
                    details={"agent": result.agent, "preview": result.preview}
                )
            else:
                return CreationResult(
                    success=False,
                    entity_type="agent",
                    error=result.error
                )
        except Exception as e:
            return CreationResult(
                success=False,
                entity_type="agent",
                error=f"Agent creation failed: {str(e)}"
            )
    
    async def _create_skill(self, description: str, name: Optional[str]) -> CreationResult:
        """Create a Skill"""
        factory = self._get_skill_factory()
        if not factory:
            return CreationResult(
                success=False,
                entity_type="skill",
                error="Skill factory not available"
            )
        
        try:
            # Parse requirements from description
            requirements = {
                "name": name or self._extract_name_from_description(description),
                "description": description,
                "use_cases": [description],
                "target_users": ["general"],
                "complexity": "medium",
                "tools_needed": [],
                "integration_points": []
            }
            
            result = factory.create_and_register_skill(requirements, requirements["name"])
            
            if result.get("success"):
                return CreationResult(
                    success=True,
                    entity_type="skill",
                    entity_id=result.get("skill_id"),
                    entity_name=requirements["name"],
                    message=f"Skill创建成功: {requirements['name']}",
                    details=result
                )
            else:
                return CreationResult(
                    success=False,
                    entity_type="skill",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            return CreationResult(
                success=False,
                entity_type="skill",
                error=f"Skill creation failed: {str(e)}"
            )
    
    async def _create_team(self, description: str, name: Optional[str]) -> CreationResult:
        """Create a Team from natural language description"""
        import uuid
        import json
        from pathlib import Path
        
        try:
            team_id = f"team_{uuid.uuid4().hex[:8]}"
            team_name = name or self._extract_name_from_description(description) or f"team_{team_id}"
            
            parsed = _parse_team_requirements(description)
            
            members = []
            for role in parsed["roles"]:
                member = {
                    "role": role,
                    "description": f"Team member: {role}",
                    "capabilities": parsed["capabilities_by_role"].get(role, []),
                    "input_from": []
                }
                members.append(member)
            
            team_config = {
                "id": team_id,
                "name": team_name,
                "description": description,
                "roles": parsed["roles"],
                "members": members,
                "mode": parsed.get("mode", "sequential"),
                "created_at": str(uuid.uuid4()),
                "status": "active"
            }
            
            team_file = self._get_teams_file()
            teams = []
            if team_file.exists():
                with open(team_file, 'r', encoding='utf-8') as f:
                    teams = json.load(f)
            
            teams.append(team_config)
            
            team_file.parent.mkdir(parents=True, exist_ok=True)
            with open(team_file, 'w', encoding='utf-8') as f:
                json.dump(teams, f, ensure_ascii=False, indent=2)
            
            return CreationResult(
                success=True,
                entity_type="team",
                entity_id=team_id,
                entity_name=team_name,
                message=f"Team创建成功: {team_name}",
                details={
                    "team_id": team_id,
                    "team_name": team_name,
                    "roles": parsed["roles"],
                    "members": members,
                    "mode": parsed.get("mode", "sequential"),
                    "description": description
                }
            )
            
        except Exception as e:
            logger.error(f"Team creation failed: {e}", exc_info=True)
            return CreationResult(
                success=False,
                entity_type="team",
                error=f"Team creation failed: {str(e)}"
            )
    
    def _get_teams_file(self) -> Path:
        """获取团队文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'data' / 'teams.json'
    
    async def _create_tool(self, description: str, name: Optional[str]) -> CreationResult:
        """Create a Tool from natural language description"""
        import uuid
        import json
        from pathlib import Path
        
        try:
            tool_id = f"tool_{uuid.uuid4().hex[:8]}"
            tool_name = name or self._extract_name_from_description(description) or f"tool_{tool_id}"
            
            parsed = _parse_tool_requirements(description)
            
            tool_config = {
                "id": tool_id,
                "name": tool_name,
                "description": description,
                "category": parsed["category"],
                "capabilities": parsed["capabilities"],
                "parameters": parsed["parameters"],
                "code_template": parsed["code_template"],
                "created_at": str(uuid.uuid4()),
                "status": "active"
            }
            
            tool_file = self._get_tools_file()
            tools = []
            if tool_file.exists():
                with open(tool_file, 'r', encoding='utf-8') as f:
                    tools = json.load(f)
            
            tools.append(tool_config)
            
            tool_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tool_file, 'w', encoding='utf-8') as f:
                json.dump(tools, f, ensure_ascii=False, indent=2)
            
            return CreationResult(
                success=True,
                entity_type="tool",
                entity_id=tool_id,
                entity_name=tool_name,
                message=f"工具创建成功: {tool_name}",
                details={
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "category": parsed["category"],
                    "capabilities": parsed["capabilities"],
                    "parameters": parsed["parameters"],
                    "description": description
                }
            )
            
        except Exception as e:
            logger.error(f"Tool creation failed: {e}", exc_info=True)
            return CreationResult(
                success=False,
                entity_type="tool",
                error=f"工具创建失败: {str(e)}"
            )
    
    def _get_tools_file(self) -> Path:
        """获取工具文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'data' / 'tools.json'
    
    async def _create_workflow(self, description: str, name: Optional[str]) -> CreationResult:
        """Create a Workflow from natural language description with Agents"""
        import uuid
        import json
        from pathlib import Path
        
        try:
            parsed = _parse_workflow_requirements(description)
            
            workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
            workflow_name = name or f"工作流-{workflow_id}"
            
            role_map = {
                "product_manager": {
                    "name": "product_manager",
                    "role_type": "Product Manager",
                    "capabilities": ["需求分析", "优先级排序", "用户故事撰写"],
                    "tools": ["search", "file_manager"]
                },
                "architect": {
                    "name": "architect", 
                    "role_type": "System Architect",
                    "capabilities": ["技术方案设计", "架构评审", "技术选型"],
                    "tools": ["search", "file_manager"]
                },
                "developer": {
                    "name": "developer",
                    "role_type": "Developer", 
                    "capabilities": ["代码生成", "代码审查", "重构"],
                    "tools": ["code_executor", "file_manager", "search"]
                },
                "qa": {
                    "name": "qa",
                    "role_type": "QA Engineer",
                    "capabilities": ["测试用例生成", "测试执行", "缺陷报告"],
                    "tools": ["code_executor", "file_manager"]
                },
                "devops": {
                    "name": "devops",
                    "role_type": "DevOps Engineer",
                    "capabilities": ["自动化部署", "CI/CD", "监控"],
                    "tools": ["code_executor", "file_manager"]
                },
                "tech_writer": {
                    "name": "tech_writer",
                    "role_type": "Technical Writer",
                    "capabilities": ["API文档", "用户手册", "版本说明"],
                    "tools": ["file_manager", "search"]
                }
            }
            
            created_agents = []
            for role_name in parsed["roles"]:
                agent_config = role_map.get(role_name, {
                    "name": role_name,
                    "role_type": "Agent",
                    "capabilities": ["通用任务"],
                    "tools": ["search"]
                })
                
                agent_id = f"agent_{workflow_id}_{role_name}"
                agent_data = {
                    "id": agent_id,
                    "workflow_id": workflow_id,
                    "role": role_name,
                    "name": agent_config["name"],
                    "role_type": agent_config["role_type"],
                    "capabilities": agent_config["capabilities"],
                    "tools": agent_config["tools"],
                    "status": "active"
                }
                created_agents.append(agent_data)
            
            workflow_config = {
                "id": workflow_id,
                "name": workflow_name,
                "description": description,
                "roles": parsed["roles"],
                "steps": parsed["steps"],
                "created_at": str(uuid.uuid4()),
                "status": "active",
                "agents": created_agents
            }
            
            workflow_file = self._get_workflows_file()
            workflows = []
            if workflow_file.exists():
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflows = json.load(f)
            
            workflows.append(workflow_config)
            
            workflow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflows, f, ensure_ascii=False, indent=2)
            
            return CreationResult(
                success=True,
                entity_type="workflow",
                entity_id=workflow_id,
                entity_name=workflow_name,
                message=f"工作流创建成功: {workflow_name}",
                details={
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "roles": parsed["roles"],
                    "steps": parsed["steps"],
                    "agents": created_agents,
                    "description": description
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow creation failed: {e}", exc_info=True)
            return CreationResult(
                success=False,
                entity_type="workflow",
                error=f"工作流创建失败: {str(e)}"
            )
    
    def _get_workflows_file(self) -> Path:
        """获取工作流文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'data' / 'workflows.json'
    
    def _extract_name_from_description(self, description: str) -> str:
        """Extract entity name from description"""
        # Try to find name pattern like "叫做XXX" or "name: XXX"
        patterns = [
            r'(?:叫做?|名为?|name[:\s]*)([\w\u4e00-\u9fa5]+)',
            r'(?:创建|新建)(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return match.group(1)
        
        # Default name with timestamp
        import time
        return f"entity_{int(time.time())}"
    
    def _extract_agent_ids_from_description(self, description: str) -> List[str]:
        """Extract agent IDs from team description"""
        # This would need more sophisticated parsing
        # For now, return empty list
        return []


def _parse_workflow_requirements(description: str) -> Dict[str, Any]:
    """解析工作流需求，提取角色和步骤"""
    desc_lower = description.lower()
    
    ROLE_KEYWORDS = {
        "product_manager": ["产品经理", "需求", "用户故事", "PM"],
        "architect": ["架构师", "技术设计", "架构", "技术方案"],
        "developer": ["开发", "代码", "程序员", "工程师"],
        "qa": ["测试", "QA", "质检", "测试工程师"],
        "devops": ["运维", "部署", "DevOps"],
        "tech_writer": ["文档", "技术文档", "手册", "写文档"]
    }
    
    STEP_KEYWORDS = {
        "需求分析": ["需求", "分析"],
        "技术设计": ["设计", "架构", "技术方案"],
        "代码开发": ["开发", "代码", "写代码"],
        "代码审查": ["审查", "review", "检查"],
        "单元测试": ["测试", "单元测试", "UT"],
        "测试验证": ["验证", "质检"],
        "文档编写": ["文档", "手册", "说明"],
        "上线部署": ["上线", "部署", "发布"]
    }
    
    detected_roles = []
    for role_name, keywords in ROLE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_roles.append(role_name)
    
    detected_steps = []
    for step_name, keywords in STEP_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_steps.append(step_name)
    
    if not detected_roles:
        detected_roles = ["developer"]
    
    if not detected_steps:
        if "qa" in detected_roles:
            detected_steps = ["需求分析", "代码开发", "代码审查", "单元测试", "测试验证"]
        else:
            detected_steps = ["需求分析", "代码开发", "代码审查"]
    
    return {
        "roles": detected_roles,
        "steps": detected_steps,
        "original_description": description
    }


def _parse_tool_requirements(description: str) -> Dict[str, Any]:
    """解析工具需求，提取类别、功能、参数和代码模板"""
    desc_lower = description.lower()
    
    TOOL_CATEGORIES = {
        "性能测试": ["性能", "压力", "负载", "性能测试", "压测", "benchmark"],
        "安全测试": ["安全", "渗透", "漏洞", "安全测试", "黑客"],
        "接口测试": ["接口", "API", "接口测试", "rest", "http"],
        "单元测试": ["单元测试", "unit test", "UT"],
        "集成测试": ["集成测试", "integration"],
        "数据处理": ["数据", "分析", "处理", "ETL"],
        "监控": ["监控", "监控", "monitor"],
        "日志": ["日志", "log"],
        "通用": []
    }
    
    TOOL_TEMPLATES = {
        "性能测试": {
            "capabilities": ["压力测试", "性能指标采集", "结果分析"],
            "parameters": [
                {"name": "target_url", "type": "string", "required": True, "description": "目标URL"},
                {"name": "concurrency", "type": "integer", "required": False, "description": "并发数", "default": 10},
                {"name": "duration", "type": "integer", "required": False, "description": "持续时间(秒)", "default": 60}
            ],
            "code_template": '''"""
Performance Testing Tool
自动生成的性能测试工具
"""

import time
import threading
import requests
from typing import Dict, Any, List

class PerformanceTester:
    def __init__(self, target_url: str, concurrency: int = 10, duration: int = 60):
        self.target_url = target_url
        self.concurrency = concurrency
        self.duration = duration
        self.results = []
        
    def test(self) -> Dict[str, Any]:
        """执行性能测试"""
        # 实现性能测试逻辑
        pass
    
    def get_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return {
            "total_requests": len(self.results),
            "avg_response_time": sum(r['response_time'] for r in self.results) / len(self.results) if self.results else 0,
            "success_rate": sum(1 for r in self.results if r['success']) / len(self.results) if self.results else 0
        }

# 导出接口
def run_performance_test(config: Dict[str, Any]) -> Dict[str, Any]:
    tester = PerformanceTester(
        target_url=config['target_url'],
        concurrency=config.get('concurrency', 10),
        duration=config.get('duration', 60)
    )
    tester.test()
    return tester.get_report()
'''
        },
        "安全测试": {
            "capabilities": ["漏洞扫描", "SQL注入检测", "XSS检测"],
            "parameters": [
                {"name": "target_url", "type": "string", "required": True, "description": "目标URL"},
                {"name": "scan_type", "type": "string", "required": False, "description": "扫描类型", "default": "basic"}
            ],
            "code_template": '''"""
Security Testing Tool
自动生成的安全测试工具
"""

class SecurityTester:
    def __init__(self, target_url: str, scan_type: str = "basic"):
        self.target_url = target_url
        self.scan_type = scan_type
        
    def scan(self) -> dict:
        """执行安全扫描"""
        pass
    
    def get_vulnerabilities(self) -> List[dict]:
        """获取漏洞列表"""
        return []
'''
        },
        "接口测试": {
            "capabilities": ["HTTP请求", "响应验证", "断言"],
            "parameters": [
                {"name": "endpoint", "type": "string", "required": True, "description": "接口地址"},
                {"name": "method", "type": "string", "required": False, "description": "HTTP方法", "default": "GET"},
                {"name": "headers", "type": "object", "required": False, "description": "请求头"}
            ],
            "code_template": '''"""
API Testing Tool
自动生成的接口测试工具
"""

import requests

class APITester:
    def __init__(self, endpoint: str, method: str = "GET", headers: dict = None):
        self.endpoint = endpoint
        self.method = method
        self.headers = headers or {}
        
    def test(self, data: dict = None) -> dict:
        """执行API测试"""
        response = requests.request(
            method=self.method,
            url=self.endpoint,
            headers=self.headers,
            json=data
        )
        return {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
'''
        },
        "通用": {
            "capabilities": ["自定义功能"],
            "parameters": [
                {"name": "input", "type": "string", "required": True, "description": "输入数据"}
            ],
            "code_template": '''"""
Custom Tool
自动生成的自定义工具
"""

def execute(input_data: str) -> str:
    """执行自定义逻辑"""
    return f"Processed: {input_data}"
'''
        }
    }
    
    detected_category = "通用"
    for category, keywords in TOOL_CATEGORIES.items():
        if any(kw in desc_lower for kw in keywords):
            detected_category = category
            break
    
    template = TOOL_TEMPLATES.get(detected_category, TOOL_TEMPLATES["通用"])
    
    return {
        "category": detected_category,
        "capabilities": template["capabilities"],
        "parameters": template["parameters"],
        "code_template": template["code_template"]
    }


def _parse_team_requirements(description: str) -> Dict[str, Any]:
    """解析团队需求，提取角色和协作模式"""
    desc_lower = description.lower()
    
    ROLE_KEYWORDS = {
        "产品经理": ["产品经理", "PM", "需求"],
        "开发者": ["开发", "程序员", "工程师"],
        "设计师": ["设计", "UI", "UX"],
        "测试工程师": ["测试", "QA"],
        "运维": ["运维", "DevOps", "部署"],
        "数据分析师": ["数据分析", "数据"],
        "架构师": ["架构", "架构师"]
    }
    
    CAPABILITIES_BY_ROLE = {
        "产品经理": ["需求分析", "优先级排序", "用户故事"],
        "开发者": ["代码开发", "代码审查", "重构"],
        "设计师": ["UI设计", "UX设计", "原型设计"],
        "测试工程师": ["测试用例", "测试执行", "缺陷报告"],
        "运维": ["部署", "监控", "自动化"],
        "数据分析师": ["数据分析", "可视化", "报表"],
        "架构师": ["架构设计", "技术选型", "性能优化"]
    }
    
    MODE_KEYWORDS = {
        "sequential": ["顺序", "依次", "逐步"],
        "parallel": ["并行", "同时", "一起"],
        "hierarchical": ["层级", "分层", "领导"]
    }
    
    detected_roles = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_roles.append(role)
    
    if not detected_roles:
        detected_roles = ["开发者"]
    
    detected_mode = "sequential"
    for mode, keywords in MODE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_mode = mode
            break
    
    capabilities_by_role = {}
    for role in detected_roles:
        capabilities_by_role[role] = CAPABILITIES_BY_ROLE.get(role, ["通用任务"])
    
    return {
        "roles": detected_roles,
        "mode": detected_mode,
        "capabilities_by_role": capabilities_by_role,
        "original_description": description
    }


# Global instance
_unified_creator: Optional[UnifiedCreator] = None


def get_unified_creator() -> UnifiedCreator:
    """Get the global UnifiedCreator instance"""
    global _unified_creator
    if _unified_creator is None:
        _unified_creator = UnifiedCreator()
    return _unified_creator
