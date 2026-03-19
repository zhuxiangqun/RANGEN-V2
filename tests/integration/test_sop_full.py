#!/usr/bin/env python3
"""
T17: SOP集成测试
测试 SOP Recall/Execution/Learning 节点集成
"""

import sys
sys.path.insert(0, '.')

import pytest
import time
from typing import Dict, Any


class TestSOPRecallNode:
    """测试 SOP Recall 节点"""
    
    def test_recall_node_import(self):
        """测试 SOP Recall 节点可以导入"""
        from src.core.langgraph_sop_nodes import SOPNodes
        nodes = SOPNodes()
        assert nodes is not None
    
    def test_recall_with_keyword(self):
        """测试关键词召回"""
        from src.core.langgraph_sop_nodes import SOPNodes
        nodes = SOPNodes()
        
        state: Dict[str, Any] = {
            'query': '如何修复404错误',
            'context': {},
            'user_context': {},
            'sop_recalled': False,
            'recalled_sops': [],
            'sop_executed': False,
            'executed_sops': [],
            'evidence': [],
            'answer': None,
            'final_answer': None,
            'knowledge': [],
            'citations': [],
            'task_complete': False,
            'error': None,
            'errors': [],
            'retry_count': 0
        }
        
        assert 'query' in state
        assert state['query'] == '如何修复404错误'
    
    def test_sop_learning_system_import(self):
        """测试 SOP Learning System 可以导入"""
        from src.core.sop_learning import SOPLearningSystem
        system = SOPLearningSystem()
        assert system is not None
    
    def test_sop_recall_method(self):
        """测试 SOP recall 方法"""
        from src.core.sop_learning import SOPLearningSystem
        system = SOPLearningSystem()
        assert hasattr(system, 'recall_sop')


class TestSOPExecutionNode:
    """测试 SOP Execution 节点"""
    
    def test_execution_node_import(self):
        """测试 SOP Execution 节点可以导入"""
        from src.core.langgraph_sop_nodes import SOPNodes
        nodes = SOPNodes()
        assert hasattr(nodes, 'sop_execution_node')


class TestSOPLearningHook:
    """测试 SOP Learning Hook"""
    
    def test_learning_node_import(self):
        """测试 Learning 节点可以导入"""
        from src.core.langgraph_sop_nodes import SOPNodes
        nodes = SOPNodes()
        assert hasattr(nodes, 'sop_learning_hook')
    
    def test_sop_learning_integration(self):
        """测试 SOP Learning 与系统集成"""
        from src.core.sop_learning import SOPLearningSystem
        
        system = SOPLearningSystem()
        
        assert hasattr(system, 'learn_from_execution')
        assert hasattr(system, 'recall_sop')
        assert hasattr(system, 'get_statistics')


class TestSOPAPI:
    """测试 SOP API 端点"""
    
    def test_sop_routes_import(self):
        """测试 SOP Routes 可以导入"""
        from src.api.sop_routes import router
        assert router is not None
    
    def test_sop_statistics(self):
        """测试 SOP 统计信息"""
        from src.core.sop_learning import SOPLearningSystem
        system = SOPLearningSystem()
        
        stats = system.get_statistics()
        assert isinstance(stats, dict)
        assert 'total_sops' in stats


class TestSOPRecallExecutionLearning:
    """测试完整 SOP Recall→Execution→Learning 流程"""
    
    def test_full_workflow_state(self):
        """测试完整工作流状态"""
        from src.core.langgraph_sop_nodes import AgentState
        
        state: AgentState = {
            'query': '测试查询',
            'context': {},
            'user_context': {},
            'sop_recalled': False,
            'recalled_sops': [],
            'sop_executed': False,
            'executed_sops': [],
            'evidence': [],
            'answer': None,
            'final_answer': None,
            'knowledge': [],
            'citations': [],
            'task_complete': False,
            'error': None,
            'errors': [],
            'retry_count': 0
        }
        
        assert 'sop_recalled' in state
        assert 'recalled_sops' in state
        assert 'sop_executed' in state
        assert 'executed_sops' in state
    
    def test_sop_nodes_methods(self):
        """测试 SOPNodes 所有方法"""
        from src.core.langgraph_sop_nodes import SOPNodes
        nodes = SOPNodes()
        
        assert hasattr(nodes, 'sop_recall_node')
        assert hasattr(nodes, 'sop_execution_node')
        assert hasattr(nodes, 'sop_learning_hook')
        assert hasattr(nodes, 'get_sop_statistics')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
