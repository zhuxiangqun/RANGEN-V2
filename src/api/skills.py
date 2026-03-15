"""
Skill API Routes - REST API for Skill CRUD operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from src.api.models_skill import (
    SkillCreate, 
    SkillResponse, 
    SkillListResponse
)
from src.services.skill_service import get_skill_service

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(skill: SkillCreate):
    """
    创建新Skill
    """
    service = get_skill_service()
    
    try:
        result = service.create_skill(skill.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Skill失败: {str(e)}"
        )


@router.get("", response_model=SkillListResponse)
async def list_skills(status: Optional[str] = None):
    """
    获取Skill列表
    """
    service = get_skill_service()
    
    try:
        skills = service.list_skills(status)
        return {
            "skills": skills,
            "total": len(skills)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Skill列表失败: {str(e)}"
        )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: str):
    """
    获取单个Skill详情
    """
    service = get_skill_service()
    
    skill = service.get_skill(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill不存在: {skill_id}"
        )
    
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(skill_id: str):
    """
    删除Skill
    """
    service = get_skill_service()
    
    if not service.check_skill_exists(skill_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill不存在: {skill_id}"
        )
    
    try:
        service.delete_skill(skill_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Skill失败: {str(e)}"
        )


@router.post("/combine", response_model=SkillResponse)
async def combine_tools_to_skill(
    name: str,
    description: str,
    tool_ids: List[str]
):
    """
    从现有Tools组合新Skill
    """
    service = get_skill_service()
    
    try:
        result = service.combine_tools_to_skill(name, description, tool_ids)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"组合Skill失败: {str(e)}"
        )



# ============== 触发优化相关 ==============


@router.post("/trigger-analyze")
async def analyze_trigger_effectiveness(
    test_cases: List[dict]
):
    """
    分析触发词效果
    
    检测过度触发（false positives）和触发不足（false negatives）
    返回精确率、召回率、F1分数和优化建议
    """
    from src.agents.skills.skill_trigger import get_skill_trigger, TriggerTestCase
    
    # 转换输入
    cases = []
    for tc in test_cases:
        cases.append(TriggerTestCase(
            prompt=tc.get("prompt", ""),
            should_trigger=tc.get("should_trigger", False),
            category=tc.get("category", "manual"),
            metadata=tc.get("metadata", {})
        ))
    
    trigger = get_skill_trigger()
    analysis = trigger.analyze_trigger_effectiveness(cases)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="触发优化器不可用"
        )
    
    # 转换为字典返回
    return {
        "skill_name": analysis.skill_name,
        "total_tests": analysis.total_tests,
        "passed_tests": analysis.passed_tests,
        "failed_tests": analysis.failed_tests,
        "false_positives": analysis.false_positives,
        "false_negatives": analysis.false_negatives,
        "precision": analysis.precision,
        "recall": analysis.recall,
        "f1_score": analysis.f1_score,
        "suggestions": analysis.suggestions,
        "analyzed_at": analysis.analyzed_at.isoformat()
    }


@router.post("/trigger-optimize")
async def optimize_triggers(
    skill_name: str,
    test_cases: List[dict]
):
    """
    优化触发词
    
    根据测试用例自动生成优化的触发词配置
    """
    from src.agents.skills.skill_trigger import get_skill_trigger, TriggerTestCase
    
    # 转换输入
    cases = []
    for tc in test_cases:
        cases.append(TriggerTestCase(
            prompt=tc.get("prompt", ""),
            should_trigger=tc.get("should_trigger", False),
            category=tc.get("category", "manual"),
            metadata=tc.get("metadata", {})
        ))
    
    trigger = get_skill_trigger()
    optimized = trigger.optimize_triggers(skill_name, cases)
    
    if not optimized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="触发优化器不可用"
        )
    
    # 转换为字典返回
    return {
        "skill_name": optimized.skill_name,
        "current_triggers": optimized.current_triggers,
        "recommended_triggers": optimized.recommended_triggers,
        "added_triggers": optimized.added_triggers,
        "removed_triggers": optimized.removed_triggers,
        "confidence": optimized.confidence,
        "reasoning": optimized.reasoning
    }


@router.get("/trigger-stats")
async def get_trigger_stats():
    """
    获取触发器统计信息
    """
    from src.agents.skills.skill_trigger import get_skill_trigger
    
    trigger = get_skill_trigger()
    return trigger.get_trigger_stats()
