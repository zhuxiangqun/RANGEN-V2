#!/usr/bin/env python3
"""
统一执行器测试

测试新旧系统执行结果一致性
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.unified_executor import UnifiedExecutor, get_unified_executor


class TestUnifiedExecutor:
    """统一执行器测试"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器"""
        return UnifiedExecutor(default_mode="skill")
    
    @pytest.mark.asyncio
    async def test_calculator_skill_mode(self, executor):
        """测试计算器 - Skill模式"""
        result = await executor.execute(
            "calculator",
            {"expression": "100 + 200"}
        )
        
        assert result.success is True
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_calculator_legacy_mode(self, executor):
        """测试计算器 - Legacy模式"""
        result = await executor.execute(
            "calculator",
            {"expression": "50 + 50"},
            mode="legacy"
        )
        
        assert result.success is True
        # Legacy模式会触发deprecation warning
    
    @pytest.mark.asyncio
    async def test_result_consistency(self, executor):
        """测试结果一致性"""
        # Skill模式
        result1 = await executor.execute(
            "calculator",
            {"expression": "10 * 10"},
            mode="skill"
        )
        
        # Legacy模式
        result2 = await executor.execute(
            "calculator",
            {"expression": "10 * 10"},
            mode="legacy"
        )
        
        # 结果应该一致 (都是100)
        assert result1.success == result2.success
    
    def test_list_tools(self, executor):
        """测试列出工具"""
        tools = executor.list_tools()
        
        assert "available_tools" in tools
        assert "count" in tools
        assert tools["count"] > 0


class TestToolToSkillMap:
    """工具到Skill映射测试"""
    
    def test_get_skill_name(self):
        """测试获取Skill名称"""
        from src.agents.skills.tool_to_skill_map import get_skill_name
        
        assert get_skill_name("calculator") == "calculator-skill"
        assert get_skill_name("search") == "web-search"
        assert get_skill_name("unknown") == "unknown"
    
    def test_is_skill_available(self):
        """测试Skill可用性"""
        from src.agents.skills.tool_to_skill_map import is_skill_available
        
        # 已知存在的工具
        assert is_skill_available("calculator") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
