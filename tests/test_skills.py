"""
Skills Service Tests
Based on actual code: src/services/skills.py
"""
import pytest
from src.services.skills import (
    SkillsService, SkillCategory, SkillStatus, TriggerType,
    Skill, SkillResult, SkillBenchmark, Skill
)


class TestSkillsService:
    @pytest.fixture
    def skills_service(self):
        return SkillsService()
    
    def test_can_be_instantiated(self, skills_service):
        assert skills_service is not None
    
    def test_has_register_skill_method(self, skills_service):
        assert hasattr(skills_service, 'register_skill')


class TestSkillsEnums:
    def test_skill_category_enum(self):
        assert SkillCategory.RETRIEVAL == "retrieval"
        assert SkillCategory.REASONING == "reasoning"
        assert SkillCategory.CODE == "code"
    
    def test_skill_status_enum(self):
        assert SkillStatus.ACTIVE == "active"
        assert SkillStatus.INACTIVE == "inactive"
    
    def test_trigger_type_enum(self):
        assert TriggerType.AUTO == "auto"
        assert TriggerType.MANUAL == "manual"


class TestSkill:
    def test_can_create_skill(self):
        def handler(x): return x
        skill = Skill(
            name="test_skill",
            category=SkillCategory.UTILITY,
            description="Test skill",
            trigger_type=TriggerType.AUTO,
            handler=handler,
            keywords=["test"],
            metadata={},
            status=SkillStatus.ACTIVE,
            version="1.0",
            created_at=1234567890.0
        )
        assert skill.name == "test_skill"
        assert skill.status == SkillStatus.ACTIVE


class TestSkillResult:
    def test_can_create_skill_result(self):
        result = SkillResult(
            skill_name="test",
            success=True,
            result="output",
            execution_time=1.5
        )
        assert result.success == True
        assert result.execution_time == 1.5
