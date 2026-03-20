#!/usr/bin/env python3
"""
Unified Agent Interface Tests
============================

测试统一接口的功能和向后兼容性
"""
import pytest
import asyncio
import warnings
from typing import Dict, Any, Optional


class TestUnifiedAgentConfig:
    """测试 UnifiedAgentConfig"""
    
    def test_create_minimal_config(self):
        """测试最小配置创建"""
        from src.interfaces.unified_agent import UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='test-agent',
            name='Test Agent',
            description='A test agent'
        )
        
        assert config.agent_id == 'test-agent'
        assert config.name == 'Test Agent'
        assert config.description == 'A test agent'
        assert config.version == '1.0.0'  # 默认值
        assert config.category == 'general'  # 默认值
        assert config.enabled is True  # 默认值
    
    def test_create_full_config(self):
        """测试完整配置创建"""
        from src.interfaces.unified_agent import UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='full-agent',
            name='Full Agent',
            description='A fully configured agent',
            version='2.0.0',
            category='reasoning',
            capabilities=['tool_use', 'reasoning'],
            max_retries=5,
            timeout=600,
            enabled=False,
            metadata={'key': 'value'}
        )
        
        assert config.version == '2.0.0'
        assert config.category == 'reasoning'
        assert 'tool_use' in config.capabilities
        assert config.max_retries == 5
        assert config.timeout == 600
        assert config.enabled is False
        assert config.metadata['key'] == 'value'


class TestUnifiedAgentResult:
    """测试 UnifiedAgentResult"""
    
    def test_create_successful_result(self):
        """测试成功结果创建"""
        from src.interfaces.unified_agent import UnifiedAgentResult, ExecutionStatus
        
        result = UnifiedAgentResult(
            agent_id='test-agent',
            agent_name='Test Agent',
            status=ExecutionStatus.COMPLETED,
            output='test output',
            execution_time=1.5
        )
        
        assert result.agent_id == 'test-agent'
        assert result.status == 'completed'
        assert result.output == 'test output'
        assert result.execution_time == 1.5
        assert result.error is None
        assert result.success is True
    
    def test_create_failed_result(self):
        """测试失败结果创建"""
        from src.interfaces.unified_agent import UnifiedAgentResult, ExecutionStatus
        
        result = UnifiedAgentResult(
            agent_id='test-agent',
            agent_name='Test Agent',
            status=ExecutionStatus.FAILED,
            output=None,
            execution_time=0.5,
            error='Something went wrong'
        )
        
        assert result.status == 'failed'
        assert result.error == 'Something went wrong'
        assert result.success is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        from src.interfaces.unified_agent import UnifiedAgentResult, ExecutionStatus
        
        result = UnifiedAgentResult(
            agent_id='test-agent',
            agent_name='Test Agent',
            status=ExecutionStatus.COMPLETED,
            output='test'
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['agent_id'] == 'test-agent'
        assert result_dict['status'] == 'completed'
        assert result_dict['output'] == 'test'


class TestIAgentInterface:
    """测试 IAgent 接口"""
    
    def test_agent_execute_sync(self):
        """测试 Agent 执行（同步包装）"""
        from src.interfaces.unified_agent import (
            IAgent, UnifiedAgentConfig, UnifiedAgentResult, ExecutionStatus
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None) -> UnifiedAgentResult:
                return UnifiedAgentResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    status=ExecutionStatus.COMPLETED,
                    output=f'executed: {query}',
                    execution_time=0.1
                )
        
        config = UnifiedAgentConfig(
            agent_id='exec-agent',
            name='Execute Agent',
            description='Test execution'
        )
        agent = TestAgent(config)
        
        # 同步测试
        result = asyncio.get_event_loop().run_until_complete(agent.execute('test query'))
        
        assert result.output == 'executed: test query'
        assert result.success is True
    
    def test_agent_process_alias_sync(self):
        """测试 process 别名（同步包装）"""
        from src.interfaces.unified_agent import (
            IAgent, UnifiedAgentConfig, UnifiedAgentResult, ExecutionStatus
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None) -> UnifiedAgentResult:
                return UnifiedAgentResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    status=ExecutionStatus.COMPLETED,
                    output=f'processed: {query}'
                )
        
        config = UnifiedAgentConfig(
            agent_id='alias-agent',
            name='Alias Agent',
            description='Test alias'
        )
        agent = TestAgent(config)
        
        # 同步测试
        result = asyncio.get_event_loop().run_until_complete(agent.process('alias test'))
        
        assert result.output == 'processed: alias test'
    
    def test_agent_properties(self):
        """测试 Agent 属性"""
        from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='prop-agent',
            name='Property Agent',
            description='Test properties',
            capabilities=['reasoning', 'tool_use']
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None):
                pass
        
        agent = TestAgent(config)
        
        assert agent.agent_id == 'prop-agent'
        assert agent.name == 'Property Agent'
        assert agent.description == 'Test properties'
        assert 'reasoning' in agent.capabilities
    
    def test_agent_enable_disable(self):
        """测试启用/禁用"""
        from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='toggle-agent',
            name='Toggle Agent',
            description='Test toggle',
            enabled=True
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None):
                pass
        
        agent = TestAgent(config)
        
        assert agent.is_enabled() is True
        
        agent.disable()
        assert agent.is_enabled() is False
        
        agent.enable()
        assert agent.is_enabled() is True
    
    def test_agent_capability_check(self):
        """测试能力检查"""
        from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='cap-agent',
            name='Capability Agent',
            description='Test capabilities',
            capabilities=['reasoning', 'tool_use']
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None):
                pass
        
        agent = TestAgent(config)
        
        assert agent.has_capability('reasoning') is True
        assert agent.has_capability('tool_use') is True
        assert agent.has_capability('rag') is False
    
    def test_agent_repr(self):
        """测试字符串表示"""
        from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig
        
        config = UnifiedAgentConfig(
            agent_id='repr-agent',
            name='Repr Agent',
            description='Test repr'
        )
        
        class TestAgent(IAgent):
            async def execute(self, query: str, context: Optional[Dict] = None):
                pass
        
        agent = TestAgent(config)
        repr_str = repr(agent)
        
        assert 'TestAgent' in repr_str
        assert 'repr-agent' in repr_str
        assert 'enabled=True' in repr_str


class TestBackwardCompatibility:
    """测试向后兼容性"""
    
    def test_alias_exports(self):
        """测试别名导出"""
        from src.interfaces.unified_agent import (
            AgentConfig, AgentResult,  # 别名
            UnifiedAgentConfig, UnifiedAgentResult  # 原始
        )
        
        # 验证别名指向正确的类型
        assert AgentConfig == UnifiedAgentConfig
        assert AgentResult == UnifiedAgentResult
    
    def test_import_from_interfaces(self):
        """测试从 interfaces 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            
            from src.interfaces import IAgent, UnifiedAgentConfig
            from src.interfaces.unified_agent import IAgent as DirectIAgent
            
            # 验证导入的是统一接口
            assert IAgent == DirectIAgent


class TestExecutionStatus:
    """测试 ExecutionStatus 枚举"""
    
    def test_status_values(self):
        """测试状态值"""
        from src.interfaces.unified_agent import ExecutionStatus
        
        assert ExecutionStatus.PENDING.value == 'pending'
        assert ExecutionStatus.RUNNING.value == 'running'
        assert ExecutionStatus.COMPLETED.value == 'completed'
        assert ExecutionStatus.FAILED.value == 'failed'
        assert ExecutionStatus.CANCELLED.value == 'cancelled'
    
    def test_status_in_result(self):
        """测试状态在结果中的使用"""
        from src.interfaces.unified_agent import ExecutionStatus, UnifiedAgentResult
        
        for status in ExecutionStatus:
            result = UnifiedAgentResult(
                agent_id='test',
                agent_name='Test',
                status=status,
                output='test'
            )
            assert result.status == status.value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
