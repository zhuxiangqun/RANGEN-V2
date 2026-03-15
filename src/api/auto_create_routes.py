"""
Auto Create Workflow API Routes
==============================

API endpoints for automatic workflow creation from natural language.
Supports one-click creation of development workflows with multiple roles.

Enhanced with NLU Bridge:
- Capability type detection (Tool/Skill/Agent/Team)
- LLM-powered requirement understanding
- Auto-building missing capabilities
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/api/v1/auto", tags=["auto-create"])


class WorkflowTemplate(str, Enum):
    """预置工作流模板"""
    SIMPLE_DEV = "simple_dev"           # 简单研发
    STANDARD_DEV = "standard_dev"       # 标准研发
    COMPLETE_DEV = "complete_dev"       # 完整研发


class RoleDefinition(BaseModel):
    """角色定义"""
    name: str
    role_type: str
    capabilities: List[str]
    tools: List[str]


class AutoCreateWorkflowRequest(BaseModel):
    """自动创建工作流请求"""
    description: str = Field(..., description="自然语言描述")
    template: Optional[WorkflowTemplate] = Field(None, description="使用预置模板")
    auto_execute: bool = Field(True, description="创建后自动执行")
    use_nlu: bool = Field(True, description="使用NLU桥接进行智能理解")


class AutoCreateWorkflowResponse(BaseModel):
    """自动创建工作流响应"""
    success: bool
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    agents: List[Dict[str, Any]] = []
    workflow_steps: List[str] = []
    message: str
    execution_id: Optional[str] = None
    nlu_analysis: Optional[Dict[str, Any]] = None


# ============================================================
# 预置研发模板
# ============================================================

DEVELOPMENT_TEMPLATES = {
    WorkflowTemplate.SIMPLE_DEV: {
        "name": "简单研发流程",
        "description": "开发 → 测试",
        "roles": [
            {
                "name": "developer",
                "role_type": "Developer",
                "capabilities": ["代码生成", "代码审查", "重构"],
                "tools": ["code_executor", "file_manager", "search"]
            },
            {
                "name": "qa",
                "role_type": "QA Engineer",
                "capabilities": ["测试用例生成", "测试执行", "缺陷报告"],
                "tools": ["code_executor", "file_manager"]
            }
        ],
        "steps": ["需求分析", "代码开发", "测试验证", "交付"]
    },
    WorkflowTemplate.STANDARD_DEV: {
        "name": "标准研发流程",
        "description": "需求 → 开发 → 测试 → 上线",
        "roles": [
            {
                "name": "product_manager",
                "role_type": "Product Manager",
                "capabilities": ["需求分析", "优先级排序", "用户故事撰写"],
                "tools": ["search", "file_manager"]
            },
            {
                "name": "developer",
                "role_type": "Developer",
                "capabilities": ["代码生成", "代码审查", "重构"],
                "tools": ["code_executor", "file_manager", "search"]
            },
            {
                "name": "qa",
                "role_type": "QA Engineer",
                "capabilities": ["测试用例生成", "测试执行", "缺陷报告"],
                "tools": ["code_executor", "file_manager"]
            }
        ],
        "steps": ["需求分析", "技术设计", "代码开发", "测试验证", "上线准备"]
    },
    WorkflowTemplate.COMPLETE_DEV: {
        "name": "完整研发流程",
        "description": "需求 → 设计 → 开发 → 测试 → 文档 → 上线",
        "roles": [
            {
                "name": "product_manager",
                "role_type": "Product Manager",
                "capabilities": ["需求分析", "优先级排序", "用户故事撰写"],
                "tools": ["search", "file_manager"]
            },
            {
                "name": "architect",
                "role_type": "System Architect",
                "capabilities": ["技术方案设计", "架构评审", "技术选型"],
                "tools": ["search", "file_manager"]
            },
            {
                "name": "developer",
                "role_type": "Developer",
                "capabilities": ["代码生成", "代码审查", "重构"],
                "tools": ["code_executor", "file_manager", "search"]
            },
            {
                "name": "qa",
                "role_type": "QA Engineer",
                "capabilities": ["测试用例生成", "测试执行", "缺陷报告"],
                "tools": ["code_executor", "file_manager"]
            },
            {
                "name": "tech_writer",
                "role_type": "Technical Writer",
                "capabilities": ["API文档", "用户手册", "版本说明"],
                "tools": ["file_manager", "search"]
            }
        ],
        "steps": ["需求分析", "技术设计", "代码开发", "测试验证", "文档编写", "上线部署"]
    }
}


# ============================================================
# 需求解析逻辑
# ============================================================

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
    "测试验证": ["测试", "验证", "质检"],
    "文档编写": ["文档", "手册", "说明"],
    "上线部署": ["上线", "部署", "发布"]
}


def parse_requirements(description: str) -> Dict[str, Any]:
    """解析需求，提取角色和流程"""
    desc_lower = description.lower()
    
    # 检测角色
    detected_roles = []
    for role_name, keywords in ROLE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_roles.append(role_name)
    
    # 检测流程步骤
    detected_steps = []
    for step_name, keywords in STEP_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            detected_steps.append(step_name)
    
    # 如果没有检测到角色，提供默认
    if not detected_roles:
        detected_roles = ["developer"]
    
    # 如果没有检测到步骤，生成默认步骤
    if not detected_steps:
        if "qa" in detected_roles:
            detected_steps = ["需求分析", "代码开发", "测试验证"]
        else:
            detected_steps = ["需求分析", "代码开发"]
    
    return {
        "roles": detected_roles,
        "steps": detected_steps,
        "original_description": description
    }


# ============================================================
# API 端点
# ============================================================

@router.post("/create-workflow", response_model=AutoCreateWorkflowResponse)
async def auto_create_workflow(request: AutoCreateWorkflowRequest):
    """
    一句话自动创建研发工作流
    
    根据自然语言描述自动：
    1. 解析需求，识别所需角色
    2. 创建对应的 Agent
    3. 生成工作流
    4. 可选：自动执行
    
    示例:
    - "帮我创建一个研发流程，包含产品经理、开发者、测试工程师"
    - "做一个完整的需求到上线的流程"
    """
    try:
        # 1. 解析需求
        if request.template:
            # 使用预置模板
            template = DEVELOPMENT_TEMPLATES.get(request.template)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown template: {request.template}"
                )
            parsed = {
                "roles": [r["name"] for r in template["roles"]],
                "steps": template["steps"],
                "template_used": request.template.value
            }
            roles = template["roles"]
            workflow_steps = template["steps"]
        else:
            # 解析自然语言需求
            parsed = parse_requirements(request.description)
            roles = parsed["roles"]
            workflow_steps = parsed["steps"]
        
        # 2. 生成工作流 ID
        import uuid
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        workflow_name = f"研发流程-{workflow_id}"
        
        # 3. 准备 Agent 定义
        agents = []
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
        
        for role_name in roles:
            agent_def = role_map.get(role_name, {
                "name": role_name,
                "role_type": "Agent",
                "capabilities": ["通用任务"],
                "tools": ["search"]
            })
            agents.append(agent_def)
        
        # 4. 构建响应
        response = AutoCreateWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            agents=agents,
            workflow_steps=workflow_steps,
            message=f"✅ 已创建工作流 '{workflow_name}'，包含 {len(agents)} 个角色: {', '.join(roles)}"
        )
        
        # 5. 如果需要自动执行
        if request.auto_execute:
            response.execution_id = f"exec_{uuid.uuid4().hex[:8]}"
            response.message += f"\n⏳ 正在自动执行..."
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow creation failed: {str(e)}"
        )


@router.get("/templates")
async def get_workflow_templates():
    """获取可用的工作流模板"""
    return {
        "templates": [
            {
                "id": "simple_dev",
                "name": "简单研发",
                "description": "开发 → 测试",
                "roles": ["developer", "qa"],
                "steps": 2
            },
            {
                "id": "standard_dev", 
                "name": "标准研发",
                "description": "需求 → 开发 → 测试 → 上线",
                "roles": ["product_manager", "developer", "qa"],
                "steps": 4
            },
            {
                "id": "complete_dev",
                "name": "完整研发",
                "description": "需求 → 设计 → 开发 → 测试 → 文档 → 上线",
                "roles": ["product_manager", "architect", "developer", "qa", "tech_writer"],
                "steps": 6
            }
        ]
    }


@router.get("/parse-description")
async def parse_description(description: str):
    """解析需求描述，返回识别的角色和步骤"""
    parsed = parse_requirements(description)
    return {
        "description": description,
        "detected_roles": parsed["roles"],
        "detected_steps": parsed["steps"],
        "message": f"检测到角色: {', '.join(parsed['roles'])}\n检测到步骤: {', '.join(parsed['steps'])}"
    }


# ============================================================
# NLU Bridge 集成端点
# ============================================================

class DetectTypeRequest(BaseModel):
    """能力类型识别请求"""
    query: str = Field(..., description="用户输入的自然语言")


class DetectTypeResponse(BaseModel):
    """能力类型识别响应"""
    success: bool
    detection: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UnderstandRequest(BaseModel):
    """需求理解请求"""
    query: str = Field(..., description="用户输入的自然语言")
    include_team_build: bool = Field(False, description="是否同时构建团队")


class UnderstandResponse(BaseModel):
    """需求理解响应"""
    success: bool
    type_detection: Optional[Dict[str, Any]] = None
    requirement_analysis: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/detect-type", response_model=DetectTypeResponse)
async def detect_capability_type(request: DetectTypeRequest):
    """
    能力类型识别
    
    识别用户需求需要什么层次的能力: Tool / Skill / Agent / Team
    
    示例:
    - "搜索今天天气" -> tool
    - "查RAG原理" -> skill  
    - "当我技术顾问" -> agent
    - "建立研发团队" -> team
    """
    try:
        from src.core.nlu_bridge import CapabilityTypeDetector
        
        detector = CapabilityTypeDetector()
        result = await detector.detect(request.query)
        
        return DetectTypeResponse(
            success=True,
            detection={
                "primary_type": result.primary_type.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "suggested_actions": result.suggested_actions
            }
        )
    except Exception as e:
        return DetectTypeResponse(
            success=False,
            error=str(e)
        )


@router.post("/understand", response_model=UnderstandResponse)
async def understand_requirement(request: UnderstandRequest):
    """
    完整需求理解
    
    1. 识别能力类型 (Tool/Skill/Agent/Team)
    2. 解析具体需求
    3. (可选) 构建团队
    
    这是整个NLU Bridge的统一入口！
    """
    try:
        from src.core.nlu_bridge import (
            CapabilityTypeDetector,
            RequirementParser,
            TeamBuilder
        )
        
        detector = CapabilityTypeDetector()
        parser = RequirementParser()
        
        # Step 1: 类型识别
        type_result = await detector.detect(request.query)
        
        # Step 2: 需求解析
        analysis = await parser.parse(request.query, type_result.primary_type)
        
        # Step 3: 构建团队 (如果需要)
        team_info = None
        if request.include_team_build and type_result.primary_type.value == "team":
            builder = TeamBuilder()
            team = await builder.build(analysis)
            team_info = {
                "id": team.id,
                "name": team.name,
                "roles": [
                    {
                        "name": r.name,
                        "display_name": r.display_name,
                        "skills": r.skills,
                        "tools": r.tools
                    }
                    for r in team.roles
                ],
                "workflow": team.workflow
            }
        
        return UnderstandResponse(
            success=True,
            type_detection={
                "primary_type": type_result.primary_type.value,
                "confidence": type_result.confidence,
                "reasoning": type_result.reasoning
            },
            requirement_analysis={
                "team_name": analysis.team_name,
                "roles": analysis.roles,
                "workflow": analysis.workflow,
                "required_skills": analysis.required_skills,
                "complexity": analysis.complexity
            },
            team=team_info
        )
        
    except Exception as e:
        return UnderstandResponse(
            success=False,
            error=str(e)
        )


# ============================================================
# 工作流管理端点
# ============================================================

import json
import uuid
from pathlib import Path
from pydantic import BaseModel


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    task: str = Field(..., description="用户任务描述")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")


class WorkflowExecuteResponse(BaseModel):
    """执行工作流响应"""
    success: bool
    workflow_id: str
    workflow_name: str
    task: str
    result: Any
    steps: List[Dict[str, Any]]
    error: Optional[str] = None
    cost: Optional[Dict[str, Any]] = None


def _estimate_cost(task: str, result: Any = None) -> Dict[str, Any]:
    """估算执行成本"""
    input_tokens = len(task) // 4
    output_tokens = len(str(result)) // 4 if result else input_tokens * 2
    
    input_cost = input_tokens / 1_000_000 * 0.1
    output_cost = output_tokens / 1_000_000 * 0.3
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total_cost": round(input_cost + output_cost, 4),
        "currency": "USD",
        "provider": "deepseek"
    }


def _get_workflows_file() -> Path:
    """获取工作流文件路径"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / 'data' / 'workflows.json'


@router.get("/workflows")
async def list_workflows():
    """
    获取所有已创建的工作流
    """
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        return {"workflows": [], "count": 0}
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    return {
        "workflows": workflows,
        "count": len(workflows)
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """
    获取指定工作流的详情
    """
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="No workflows found")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    for wf in workflows:
        if wf.get('id') == workflow_id:
            return wf
    
    raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    status: Optional[str] = None


class WorkflowUpdateResponse(BaseModel):
    """更新工作流响应"""
    success: bool
    workflow_id: str
    workflow: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.put("/workflows/{workflow_id}", response_model=WorkflowUpdateResponse)
async def update_workflow(workflow_id: str, request: WorkflowUpdateRequest):
    """
    更新指定的工作流
    
    用户可以更新:
    - name: 工作流名称
    - description: 描述
    - roles: 角色列表
    - steps: 步骤列表
    - status: 状态 (active/inactive)
    """
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="No workflows found")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    workflow_index = None
    for i, wf in enumerate(workflows):
        if wf.get('id') == workflow_id:
            workflow_index = i
            break
    
    if workflow_index is None:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    workflow = workflows[workflow_index]
    
    if request.name is not None:
        workflow['name'] = request.name
    if request.description is not None:
        workflow['description'] = request.description
    if request.roles is not None:
        workflow['roles'] = request.roles
    if request.steps is not None:
        workflow['steps'] = request.steps
    if request.status is not None:
        workflow['status'] = request.status
    
    workflows[workflow_index] = workflow
    
    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(workflows, f, ensure_ascii=False, indent=2)
    
    return WorkflowUpdateResponse(
        success=True,
        workflow_id=workflow_id,
        workflow=workflow
    )


@router.delete("/workflows/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str):
    """
    删除指定的工作流
    """
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="No workflows found")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    original_count = len(workflows)
    workflows = [wf for wf in workflows if wf.get('id') != workflow_id]
    
    if len(workflows) == original_count:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(workflows, f, ensure_ascii=False, indent=2)
    
    return None


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """
    执行指定的工作流
    
    用户提供:
    - workflow_id: 工作流ID
    - task: 任务描述
    - context: 可选的上下文
    
    返回:
    - 执行结果
    - 每个步骤的执行情况
    """
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="No workflows found")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    workflow = None
    for wf in workflows:
        if wf.get('id') == workflow_id:
            workflow = wf
            break
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    steps = []
    roles = workflow.get('roles', [])
    workflow_steps = workflow.get('steps', [])
    
    # 执行每个步骤
    try:
        from src.core.production_workflow import ProductionWorkflow
        
        wf = ProductionWorkflow()
        
        for i, step in enumerate(workflow_steps):
            step_result = {
                "step": i + 1,
                "name": step,
                "status": "pending"
            }
            steps.append(step_result)
        
        # 使用 ProductionWorkflow 执行任务
        result = await wf.execute(request.task, {
            **request.context,
            "workflow": workflow,
            "steps": workflow_steps,
            "roles": roles
        })
        
        # 更新步骤状态
        for step in steps:
            step["status"] = "completed"
        
        estimated_result = result.get('final_answer') or result.get('answer')
        cost_info = _estimate_cost(request.task, estimated_result)
        
        return WorkflowExecuteResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_name=workflow.get('name', ''),
            task=request.task,
            result=estimated_result,
            steps=steps,
            cost=cost_info
        )
        
    except Exception as e:
        for step in steps:
            step["status"] = "error"
            step["error"] = str(e)
        
        cost_info = _estimate_cost(request.task)
        
        return WorkflowExecuteResponse(
            success=False,
            workflow_id=workflow_id,
            workflow_name=workflow.get('name', ''),
            task=request.task,
            result=None,
            steps=steps,
            error=str(e)
        )


@router.get("/workflows/{workflow_id}/export")
async def export_workflow(workflow_id: str):
    """
    导出工作流完整包 (工作流 + Agents + Skills + Tools)
    
    返回一个完整的交付包，包含:
    - workflow.json: 工作流配置
    - agents/: 所有 Agent 定义
    - skills/: 所需技能列表
    - tools/: 所需工具列表
    """
    import zipfile
    import io
    from fastapi.responses import Response
    
    workflow_file = _get_workflows_file()
    
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="No workflows found")
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    workflow = None
    for wf in workflows:
        if wf.get('id') == workflow_id:
            workflow = wf
            break
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('workflow.json', json.dumps(workflow, ensure_ascii=False, indent=2))
        
        agents = workflow.get('agents', [])
        for agent in agents:
            agent_file_name = f"agents/{agent['role']}.json"
            zf.writestr(agent_file_name, json.dumps(agent, ensure_ascii=False, indent=2))
        
        skills_manifest = []
        tools_manifest = []
        
        for agent in agents:
            for cap in agent.get('capabilities', []):
                if cap not in [s['name'] for s in skills_manifest]:
                    skills_manifest.append({
                        "name": cap,
                        "agent_role": agent['role'],
                        "description": f"Skill for {agent['role_type']}: {cap}"
                    })
            
            for tool in agent.get('tools', []):
                if tool not in [t['name'] for t in tools_manifest]:
                    tools_manifest.append({
                        "name": tool,
                        "agent_role": agent['role'],
                        "description": f"Tool required by {agent['role']}"
                    })
        
        zf.writestr('skills.json', json.dumps(skills_manifest, ensure_ascii=False, indent=2))
        zf.writestr('tools.json', json.dumps(tools_manifest, ensure_ascii=False, indent=2))
        
        readme = f"""# {workflow['name']}

## 工作流描述
{workflow.get('description', '')}

## 包含的角色
{', '.join(workflow.get('roles', []))}

## 执行步骤
{chr(10).join(['- ' + s for s in workflow.get('steps', [])])}

## 成本估算

### 每次执行预估成本
- 输入Token: ~{len(workflow.get('description', '')) // 4} tokens
- 输出Token: ~1000 tokens (平均)
- **预估费用: ~$0.003/次**

### 定价说明
- DeepSeek: $0.1/1M input, $0.3/1M output
- 实际费用根据实际Token使用量计算

### 成本控制建议
- 使用简单查询减少Token使用
- 启用上下文压缩减少费用
- 设置预算上限避免超额

## 使用方法

### 1. 安装依赖
确保已部署 RANGEN 基座

### 2. 加载工作流
```bash
# 通过 API 加载
curl -X GET http://localhost:8000/api/v1/auto/workflows/{workflow_id}
```

### 3. 执行任务
```bash
curl -X POST http://localhost:8000/api/v1/auto/workflows/{workflow_id}/execute \\
  -H "Content-Type: application/json" \\
  -d '{{"task": "你的任务描述"}}'
```

### 4. 查看成本
执行返回的响应中包含 cost 字段，显示本次执行的Token使用量和费用

## 交付物清单
- workflow.json: 工作流配置
- agents/: Agent 定义 ({len(agents)} 个)
- skills.json: 技能清单
- tools.json: 工具清单
"""
        zf.writestr('README.md', readme)
    
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename={workflow_id}.zip'}
    )


def _get_tools_file() -> Path:
    """获取工具文件路径"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / 'data' / 'tools.json'


class ToolExecuteRequest(BaseModel):
    """执行工具请求"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolExecuteResponse(BaseModel):
    """执行工具响应"""
    success: bool
    tool_id: str
    tool_name: str
    result: Any = None
    error: Optional[str] = None


@router.get("/tools")
async def list_tools():
    """
    获取所有已创建的工具
    """
    tool_file = _get_tools_file()
    
    if not tool_file.exists():
        return {"tools": [], "count": 0}
    
    with open(tool_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    return {
        "tools": tools,
        "count": len(tools)
    }


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """
    获取指定工具的详情
    """
    tool_file = _get_tools_file()
    
    if not tool_file.exists():
        raise HTTPException(status_code=404, detail="No tools found")
    
    with open(tool_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    for tool in tools:
        if tool.get('id') == tool_id:
            return tool
    
    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")


@router.post("/tools/{tool_id}/execute", response_model=ToolExecuteResponse)
async def execute_tool(tool_id: str, request: ToolExecuteRequest):
    """
    执行指定的工具
    """
    tool_file = _get_tools_file()
    
    if not tool_file.exists():
        raise HTTPException(status_code=404, detail="No tools found")
    
    with open(tool_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    tool = None
    for t in tools:
        if t.get('id') == tool_id:
            tool = t
            break
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    try:
        code_template = tool.get('code_template', '')
        
        result = {
            "message": "Tool code generated successfully",
            "code": code_template,
            "parameters": request.parameters,
            "note": "This tool is a template. Execute the generated code locally."
        }
        
        return ToolExecuteResponse(
            success=True,
            tool_id=tool_id,
            tool_name=tool.get('name', ''),
            result=result
        )
        
    except Exception as e:
        return ToolExecuteResponse(
            success=False,
            tool_id=tool_id,
            tool_name=tool.get('name', ''),
            error=str(e)
        )


@router.get("/tools/{tool_id}/export")
async def export_tool(tool_id: str):
    """
    导出指定工具的完整包
    """
    import zipfile
    import io
    from fastapi.responses import Response
    
    tool_file = _get_tools_file()
    
    if not tool_file.exists():
        raise HTTPException(status_code=404, detail="No tools found")
    
    with open(tool_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    tool = None
    for t in tools:
        if t.get('id') == tool_id:
            tool = t
            break
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('tool.json', json.dumps(tool, ensure_ascii=False, indent=2))
        zf.writestr('tool.py', tool.get('code_template', '# No code template'))
        
        readme = f"""# {tool['name']}

## 工具描述
{tool.get('description', '')}

## 类别
{tool.get('category', '通用')}

## 功能
{chr(10).join(['- ' + cap for cap in tool.get('capabilities', [])])}

## 参数
{chr(10).join(['- ' + p['name'] + ': ' + p.get('description', '') for p in tool.get('parameters', [])])}

## 成本说明

此工具为本地执行工具，不消耗 API Token。

如需集成到基座工作流中执行，每次工作流执行会消耗 Token:
- DeepSeek: $0.1/1M input, $0.3/1M output

## 使用方法

```python
# 导入工具代码
from tool import run_performance_test

# 执行工具
result = run_performance_test({{
    "target_url": "https://example.com",
    "concurrency": 10,
    "duration": 60
}})
print(result)
```
"""
        zf.writestr('README.md', readme)
    
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename={tool_id}.zip'}
    )
