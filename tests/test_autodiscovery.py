"""
自动发现服务测试
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAutoDiscoveryService:
    """测试自动发现服务"""

    def setup_method(self):
        """每个测试前设置"""
        try:
            from src.services.autodiscovery_service import AutoDiscoveryService
            self.service = AutoDiscoveryService()
        except ImportError as e:
            pytest.skip(f"Cannot import AutoDiscoveryService: {e}")

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service is not None
        assert len(self.service.discovery_targets) > 0

    def test_default_targets_loaded(self):
        """测试默认发现目标已加载"""
        assert len(self.service.discovery_targets) >= 3
        
        target_names = [t.name for t in self.service.discovery_targets]
        assert 'localhost_mcp' in target_names

    def test_discovery_status(self):
        """测试发现状态"""
        status = self.service.get_discovery_status()
        
        assert status['status'] == 'active'
        assert 'target_count' in status
        assert 'discovered_count' in status

    def test_is_mcp_service(self):
        """测试MCP服务检测"""
        assert self.service._is_mcp_service('mcp', '') is True
        assert self.service._is_mcp_service('openai', '') is True
        assert self.service._is_mcp_service('unknown', '') is False

    @pytest.mark.asyncio
    async def test_discover_resources(self):
        """测试资源发现"""
        resources = await self.service.discover_resources()
        
        assert isinstance(resources, list)
        assert len(resources) >= 0

    @pytest.mark.asyncio
    async def test_discover_predefined(self):
        """测试预定义发现"""
        from src.services.autodiscovery_service import DiscoveryTarget
        
        target = DiscoveryTarget(
            name='test_predefined',
            target_type='predefined',
            value='mcp_ports',
            description='Test predefined discovery'
        )
        
        resources = await self.service._discover_predefined(target)
        assert isinstance(resources, list)

    @pytest.mark.asyncio
    async def test_deduplicate_resources(self):
        """测试资源去重"""
        from src.services.autodiscovery_service import DiscoveredResource
        from datetime import datetime
        
        resources = [
            DiscoveredResource(
                resource_id='res1',
                name='Resource 1',
                resource_type='mcp_server',
                endpoint='http://localhost:8000',
                discovered_at=datetime.now()
            ),
            DiscoveredResource(
                resource_id='res2',
                name='Resource 2',
                resource_type='mcp_server',
                endpoint='http://localhost:8000',
                discovered_at=datetime.now()
            )
        ]
        
        unique = self.service._deduplicate_resources(resources)
        assert len(unique) == 1


class TestDiscoveryTarget:
    """测试发现目标"""

    def test_target_creation(self):
        """测试目标创建"""
        from src.services.autodiscovery_service import DiscoveryTarget
        
        target = DiscoveryTarget(
            name='test',
            target_type='network',
            value='192.168.1.1',
            priority=5
        )
        
        assert target.name == 'test'
        assert target.priority == 5

    def test_target_priorities(self):
        """测试目标优先级"""
        from src.services.autodiscovery_service import DiscoveryTarget
        
        targets = [
            DiscoveryTarget(name='low', target_type='network', value='1', priority=1),
            DiscoveryTarget(name='high', target_type='network', value='2', priority=5)
        ]
        
        high_priority = [t for t in targets if t.priority >= 4]
        assert len(high_priority) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
