"""
测试文件 - Agent Service
基于实际代码结构: src/services/agent_service.py
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.agent_service import AgentService


class TestAgentService:
    """Agent服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        with patch('src.services.agent_service.get_database') as mock:
            db = MagicMock()
            mock.return_value = db
            yield db
    
    def test_agent_service_can_be_instantiated(self, mock_db):
        """测试AgentService可以被实例化"""
        service = AgentService()
        assert service is not None
        assert hasattr(service, 'db')
    
    def test_generate_id(self, mock_db):
        """测试ID生成"""
        service = AgentService()
        agent_id = service._generate_id()
        assert agent_id.startswith('agent_')
        assert len(agent_id) > 6
    
    def test_create_agent(self, mock_db):
        """测试创建Agent"""
        service = AgentService()
        mock_db.create_agent.return_value = {'id': 'test_123', 'name': 'TestAgent'}
        
        result = service.create_agent({
            'name': 'TestAgent',
            'type': 'agent',
            'description': 'Test description'
        })
        
        assert result is not None
        mock_db.create_agent.assert_called_once()
    
    def test_get_agent(self, mock_db):
        """测试获取Agent"""
        service = AgentService()
        # 模拟数据库返回完整字段
        mock_db.get_agent.return_value = {
            'id': 'test_123', 
            'name': 'TestAgent',
            'type': 'agent',
            'description': 'Test description',
            'status': 'active',
            'created_at': '2024-01-01',
            'updated_at': '2024-01-01',
            'reference_count': 0
        }
        mock_db.get_agent_skills.return_value = []
        mock_db.get_agent_tools.return_value = []
        
        result = service.get_agent('test_123')
        
        assert result is not None
        assert result['name'] == 'TestAgent'
        mock_db.get_agent.assert_called_once_with('test_123')
