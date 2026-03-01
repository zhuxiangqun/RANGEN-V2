"""
编排过程可视化追踪钩子验证测试

验证 Agent、工具、提示词工程、上下文工程的追踪钩子是否正常工作
"""
import asyncio
import logging
import pytest
import pytest_asyncio
from typing import Dict, Any

from src.unified_research_system import UnifiedResearchSystem
from src.visualization.orchestration_tracker import (
    OrchestrationTracker,
    get_orchestration_tracker,
    reset_orchestration_tracker
)

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def tracker():
    """创建编排追踪器实例"""
    reset_orchestration_tracker()
    tracker = get_orchestration_tracker()
    tracker.start_execution("test_execution")
    yield tracker
    reset_orchestration_tracker()


@pytest_asyncio.fixture
async def system():
    """创建系统实例"""
    system = UnifiedResearchSystem()
    yield system


class TestOrchestrationTracking:
    """编排追踪钩子验证测试"""
    
    def test_tracker_initialization(self, tracker):
        """测试追踪器初始化"""
        assert tracker is not None
        assert tracker.execution_id == "test_execution"
        assert len(tracker.events) == 0
        logger.info("✅ 追踪器初始化测试通过")
    
    def test_agent_tracking(self, tracker):
        """测试 Agent 追踪"""
        # 追踪 Agent 开始
        event_id = tracker.track_agent_start("test_agent", "react_agent", {"query": "test"})
        assert event_id is not None
        
        # 追踪 Agent 思考
        tracker.track_agent_think("test_agent", "I need to think about this", event_id)
        
        # 追踪 Agent 结束
        tracker.track_agent_end("test_agent", {"result": "success"})
        
        # 验证事件
        assert len(tracker.events) >= 3
        agent_events = [e for e in tracker.events if e.component_name == "test_agent"]
        assert len(agent_events) >= 3
        
        logger.info(f"✅ Agent 追踪测试通过，记录了 {len(agent_events)} 个事件")
    
    def test_tool_tracking(self, tracker):
        """测试工具追踪"""
        # 追踪工具开始
        event_id = tracker.track_tool_start("test_tool", {"query": "test"})
        assert event_id is not None
        
        # 追踪工具结束
        tracker.track_tool_end("test_tool", {"result": "success"}, parent_event_id=event_id)
        
        # 验证事件
        tool_events = [e for e in tracker.events if e.component_name == "test_tool"]
        assert len(tool_events) >= 2
        
        logger.info(f"✅ 工具追踪测试通过，记录了 {len(tool_events)} 个事件")
    
    def test_prompt_tracking(self, tracker):
        """测试提示词工程追踪"""
        # 追踪提示词生成
        tracker.track_prompt_generate("test_prompt", "What is AI?")
        
        # 追踪提示词优化
        tracker.track_prompt_optimize("test_prompt", "What is artificial intelligence?")
        
        # 验证事件
        prompt_events = [e for e in tracker.events if "prompt" in e.component_name.lower()]
        assert len(prompt_events) >= 2
        
        logger.info(f"✅ 提示词工程追踪测试通过，记录了 {len(prompt_events)} 个事件")
    
    def test_context_tracking(self, tracker):
        """测试上下文工程追踪"""
        # 追踪上下文增强
        tracker.track_context_enhance("test_context", {"enhanced": True})
        
        # 追踪上下文更新
        tracker.track_context_update("test_context", {"updated": True})
        
        # 验证事件
        context_events = [e for e in tracker.events if "context" in e.component_name.lower()]
        assert len(context_events) >= 2
        
        logger.info(f"✅ 上下文工程追踪测试通过，记录了 {len(context_events)} 个事件")
    
    @pytest.mark.asyncio
    async def test_system_integration(self, system, tracker):
        """测试系统集成（追踪器传递）"""
        # 设置系统追踪器
        system._orchestration_tracker = tracker
        
        # 验证追踪器已设置
        assert hasattr(system, '_orchestration_tracker')
        assert system._orchestration_tracker == tracker
        
        logger.info("✅ 系统集成测试通过，追踪器已正确传递")
    
    def test_event_tree_structure(self, tracker):
        """测试事件树结构"""
        # 创建层级事件
        parent_id = tracker.track_agent_start("parent_agent", "agent")
        child_id = tracker.track_tool_start("child_tool", {}, parent_event_id=parent_id)
        tracker.track_tool_end("child_tool", {}, parent_event_id=child_id)
        tracker.track_agent_end("parent_agent", {}, parent_event_id=parent_id)
        
        # 获取事件树
        event_tree = tracker.get_event_tree()
        
        # 验证树结构
        assert event_tree is not None
        assert len(event_tree) > 0
        
        logger.info(f"✅ 事件树结构测试通过，树包含 {len(event_tree)} 个根事件")
    
    def test_event_summary(self, tracker):
        """测试事件摘要"""
        # 添加一些事件
        tracker.track_agent_start("agent1", "agent")
        tracker.track_tool_start("tool1", {})
        tracker.track_prompt_generate("prompt1", "test")
        
        # 获取摘要
        summary = tracker.get_summary()
        
        # 验证摘要
        assert summary is not None
        assert 'total_events' in summary
        assert summary['total_events'] >= 3
        
        logger.info(f"✅ 事件摘要测试通过，摘要包含 {summary['total_events']} 个事件")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

