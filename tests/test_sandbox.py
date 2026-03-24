"""
Sandbox Service Tests
Based on actual code: src/services/sandbox_service.py
"""
import pytest
from src.services.sandbox_service import (
    SandboxService, SandboxType, SandboxStatus,
    SandboxConfig, SandboxResult
)


class TestSandboxService:
    def test_has_execute_in_sandbox_method(self):
        service = SandboxService.__new__(SandboxService)
        assert hasattr(service, 'execute_in_sandbox')


class TestSandboxEnums:
    def test_sandbox_type_enum(self):
        assert SandboxType.TOOL.value == "tool"
        assert SandboxType.AGENT.value == "agent"
        assert SandboxType.API.value == "api"
        assert SandboxType.CODE.value == "code"
    
    def test_sandbox_status_enum(self):
        assert SandboxStatus.PENDING.value == "pending"
        assert SandboxStatus.RUNNING.value == "running"
        assert SandboxStatus.COMPLETED.value == "completed"


class TestSandboxConfig:
    def test_can_create_config(self):
        config = SandboxConfig(
            sandbox_type=SandboxType.TOOL,
            timeout=30,
            max_memory_mb=256
        )
        assert config.sandbox_type == SandboxType.TOOL
        assert config.timeout == 30
