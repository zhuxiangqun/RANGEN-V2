"""
Team Service Tests
Based on actual code: src/services/team_service.py
"""
import pytest
from src.services.team_service import (
    TeamService, CollaborationMode, RoleType,
    TeamMember, TeamConfig
)


class TestTeamService:
    @pytest.fixture
    def team_service(self):
        return TeamService()
    
    def test_can_be_instantiated(self, team_service):
        assert team_service is not None
    
    def test_has_create_team_method(self, team_service):
        assert hasattr(team_service, 'create_team')


class TestTeamEnums:
    def test_collaboration_mode_enum(self):
        assert CollaborationMode.SEQUENTIAL.value == "sequential"
        assert CollaborationMode.PARALLEL.value == "parallel"
        assert CollaborationMode.HIERARCHICAL.value == "hierarchical"
    
    def test_role_type_enum(self):
        assert RoleType.COORDINATOR.value == "coordinator"
        assert RoleType.EXECUTOR.value == "executor"


class TestTeamMember:
    def test_can_create_member(self):
        member = TeamMember(
            agent_id="agent_1",
            role="executor",
            description="Test member"
        )
        assert member.agent_id == "agent_1"
        assert member.role == "executor"


class TestTeamConfig:
    def test_can_create_config(self):
        member = TeamMember(
            agent_id="agent_1",
            role="executor",
            description="Test"
        )
        config = TeamConfig(
            id="team_1",
            name="Test Team",
            description="Test team",
            members=[member],
            mode=CollaborationMode.PARALLEL
        )
        assert config.name == "Test Team"
        assert config.mode == CollaborationMode.PARALLEL
