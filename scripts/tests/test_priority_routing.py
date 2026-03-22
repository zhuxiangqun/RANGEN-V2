#!/usr/bin/env python3
"""
测试智能优先级路由引擎

验证"先skill后MCP，先本地后外部"策略的正确性
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, MagicMock
from src.agents.priority_routing_engine import (
    PriorityRoutingEngine,
    SkillSource,
    ToolSource,
    PrioritizedSkill,
    PrioritizedTool
)


def test_skill_source_priority():
    """测试技能来源优先级"""
    print("测试技能来源优先级...")
    
    # 验证优先级分数
    assert SkillSource.LOCAL.priority_score == 100
    assert SkillSource.LOCAL_MCP.priority_score == 80
    assert SkillSource.EXTERNAL.priority_score == 60
    assert SkillSource.EXTERNAL_MCP.priority_score == 40
    
    # 验证优先级顺序
    sources = [SkillSource.LOCAL, SkillSource.LOCAL_MCP, SkillSource.EXTERNAL, SkillSource.EXTERNAL_MCP]
    for i in range(len(sources) - 1):
        assert sources[i].priority_score > sources[i + 1].priority_score
    
    print("✓ 技能来源优先级测试通过")


def test_tool_source_priority():
    """测试工具来源优先级"""
    print("测试工具来源优先级...")
    
    # 验证优先级分数
    assert ToolSource.LOCAL.priority_score == 100
    assert ToolSource.LOCAL_MCP.priority_score == 80
    assert ToolSource.CUSTOM_API.priority_score == 70
    assert ToolSource.EXTERNAL_MCP.priority_score == 50
    assert ToolSource.UNKNOWN.priority_score == 30
    
    # 验证优先级顺序
    sources = [ToolSource.LOCAL, ToolSource.LOCAL_MCP, ToolSource.CUSTOM_API, ToolSource.EXTERNAL_MCP, ToolSource.UNKNOWN]
    for i in range(len(sources) - 1):
        assert sources[i].priority_score > sources[i + 1].priority_score
    
    print("✓ 工具来源优先级测试通过")


def test_prioritized_skill_calculation():
    """测试优先级技能计算"""
    print("测试优先级技能计算...")
    
    # 创建本地技能（高优先级）
    local_skill = PrioritizedSkill(
        skill_id="skill_local_1",
        name="本地天气查询",
        description="查询本地天气信息",
        source=SkillSource.LOCAL,
        priority=100,
        semantic_score=0.8,
        performance_score=0.9,
        total_score=0.0
    )
    
    # 创建外部MCP技能（低优先级）
    external_mcp_skill = PrioritizedSkill(
        skill_id="skill_external_mcp_1",
        name="外部天气查询",
        description="查询外部天气信息",
        source=SkillSource.EXTERNAL_MCP,
        priority=40,
        semantic_score=0.9,  # 语义匹配更高
        performance_score=0.8,
        total_score=0.0
    )
    
    # 计算最终优先级
    local_final = local_skill.final_priority
    external_final = external_mcp_skill.final_priority
    
    print(f"本地技能最终优先级: {local_final:.2f}")
    print(f"外部MCP技能最终优先级: {external_final:.2f}")
    
    # 即使外部技能语义匹配更高，本地技能应该因为来源优先级而胜出
    assert local_final > external_final, "本地技能应具有更高优先级"
    
    print("✓ 优先级技能计算测试通过")


def test_prioritized_tool_calculation():
    """测试优先级工具计算"""
    print("测试优先级工具计算...")
    
    # 创建本地工具（高优先级）
    local_tool = PrioritizedTool(
        tool_id="tool_local_1",
        name="本地计算器",
        description="本地计算工具",
        source=ToolSource.LOCAL,
        priority=100,
        semantic_score=0.7,
        latency_score=1.0,
        reliability_score=1.0,
        total_score=0.0
    )
    
    # 创建外部MCP工具（低优先级）
    external_mcp_tool = PrioritizedTool(
        tool_id="tool_external_mcp_1",
        name="外部计算器",
        description="外部计算工具",
        source=ToolSource.EXTERNAL_MCP,
        priority=50,
        semantic_score=0.8,  # 语义匹配更高
        latency_score=0.7,
        reliability_score=0.8,
        total_score=0.0
    )
    
    # 计算最终优先级
    local_final = local_tool.final_priority
    external_final = external_mcp_tool.final_priority
    
    print(f"本地工具最终优先级: {local_final:.2f}")
    print(f"外部MCP工具最终优先级: {external_final:.2f}")
    
    # 即使外部工具语义匹配更高，本地工具应该因为来源优先级而胜出
    assert local_final > external_final, "本地工具应具有更高优先级"
    
    print("✓ 优先级工具计算测试通过")


def test_routing_engine_basic():
    """测试路由引擎基本功能"""
    print("测试路由引擎基本功能...")
    
    # 创建模拟的技能注册表
    mock_skill_registry = Mock()
    
    # 模拟discover方法返回技能
    mock_skill = Mock()
    mock_skill.skill_id = "skill_test_1"
    mock_skill.name = "测试技能"
    mock_skill.description = "测试技能描述"
    mock_skill.source = "local"  # 本地技能
    mock_skill.priority = 100
    
    mock_skill_registry.discover.return_value = [
        {
            "skill": mock_skill,
            "score": 8.5,
            "skill_id": "skill_test_1"
        }
    ]
    
    # 创建模拟的工具注册表
    mock_tool_registry = Mock()
    
    # 模拟get_all_tools方法返回工具
    mock_tool_registry.get_all_tools.return_value = [
        {
            "id": "tool_test_1",
            "name": "测试工具",
            "description": "测试工具描述",
            "type": "builtin",
            "source": "local",
            "priority": 100
        }
    ]
    
    # 创建路由引擎
    engine = PriorityRoutingEngine(mock_skill_registry, mock_tool_registry)
    
    # 测试路由请求
    result = engine.route_request("测试查询")
    
    print(f"路由结果: {result}")
    
    # 验证结果结构
    assert "query" in result
    assert "recommended_skills" in result
    assert "recommended_tools" in result
    assert "strategy" in result
    assert result["strategy"] == "先skill后MCP，先本地后外部"
    
    # 验证应该优先推荐技能
    assert result["recommended_action"] == "use_skill"
    assert result["primary_recommendation"]["type"] == "skill"
    
    print("✓ 路由引擎基本功能测试通过")


def test_skill_source_detection():
    """测试技能来源检测"""
    print("测试技能来源检测...")
    
    # 创建模拟对象
    mock_skill_registry = Mock()
    mock_tool_registry = Mock()
    engine = PriorityRoutingEngine(mock_skill_registry, mock_tool_registry)
    
    # 测试本地技能检测
    local_skill = Mock()
    local_skill.skill_id = "builtin_weather"
    local_skill.source = "local"
    
    source = engine._determine_skill_source(local_skill)
    assert source == SkillSource.LOCAL
    
    # 测试本地MCP技能检测
    local_mcp_skill = Mock()
    local_mcp_skill.skill_id = "mcp_local_weather"
    local_mcp_skill.source = "local_mcp"
    
    source = engine._determine_skill_source(local_mcp_skill)
    assert source == SkillSource.LOCAL_MCP
    
    # 测试外部MCP技能检测
    external_mcp_skill = Mock()
    external_mcp_skill.skill_id = "mcp_external_weather"
    external_mcp_skill.source = "external_mcp"
    
    source = engine._determine_skill_source(external_mcp_skill)
    assert source == SkillSource.EXTERNAL_MCP
    
    print("✓ 技能来源检测测试通过")


def test_tool_source_detection():
    """测试工具来源检测"""
    print("测试工具来源检测...")
    
    # 创建模拟对象
    mock_skill_registry = Mock()
    mock_tool_registry = Mock()
    engine = PriorityRoutingEngine(mock_skill_registry, mock_tool_registry)
    
    # 测试本地工具检测
    local_tool = {
        "id": "builtin_calculator",
        "name": "计算器",
        "type": "builtin",
        "source": "local"
    }
    
    source = engine._determine_tool_source(local_tool)
    assert source == ToolSource.LOCAL
    
    # 测试本地MCP工具检测
    local_mcp_tool = {
        "id": "mcp_local_weather_get_weather",
        "name": "本地天气",
        "type": "mcp",
        "source": "local_mcp",
        "server_type": "local"
    }
    
    source = engine._determine_tool_source(local_mcp_tool)
    assert source == ToolSource.LOCAL_MCP
    
    # 测试外部MCP工具检测
    external_mcp_tool = {
        "id": "mcp_external_weather_get_weather",
        "name": "外部天气",
        "type": "mcp",
        "source": "external_mcp"
    }
    
    source = engine._determine_tool_source(external_mcp_tool)
    assert source == ToolSource.EXTERNAL_MCP
    
    print("✓ 工具来源检测测试通过")


def test_performance_tracking():
    """测试性能追踪功能"""
    print("测试性能追踪功能...")
    
    mock_skill_registry = Mock()
    mock_tool_registry = Mock()
    engine = PriorityRoutingEngine(mock_skill_registry, mock_tool_registry)
    
    # 记录技能性能
    engine.record_skill_performance("skill_1", True, 2.5)
    engine.record_skill_performance("skill_1", False, 1.0)
    
    # 检查性能数据
    assert "skill_1" in engine.skill_performance
    perf = engine.skill_performance["skill_1"]
    assert perf["total_calls"] == 2
    assert perf["success_count"] == 1
    assert perf["success_rate"] == 0.5
    assert perf["avg_execution_time"] == 1.75
    
    # 记录工具性能
    engine.record_tool_performance("tool_1", True, 0.5)
    engine.record_tool_performance("tool_1", True, 0.7)
    
    # 检查性能数据
    assert "tool_1" in engine.tool_performance
    perf = engine.tool_performance["tool_1"]
    assert perf["total_calls"] == 2
    assert perf["success_count"] == 2
    assert perf["success_rate"] == 1.0
    assert perf["avg_latency"] == 0.6
    
    print("✓ 性能追踪测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试智能优先级路由引擎")
    print("=" * 60)
    
    try:
        test_skill_source_priority()
        test_tool_source_priority()
        test_prioritized_skill_calculation()
        test_prioritized_tool_calculation()
        test_skill_source_detection()
        test_tool_source_detection()
        test_performance_tracking()
        test_routing_engine_basic()
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())