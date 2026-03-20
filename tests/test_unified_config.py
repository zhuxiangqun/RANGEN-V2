#!/usr/bin/env python3
"""
Unified Config Tests
==================

测试统一配置加载器
"""
import pytest
import os


class TestUnifiedConfig:
    """测试统一配置"""
    
    def test_load_development_config(self):
        """测试加载开发环境配置"""
        from src.config.unified_config import get_config
        
        config = get_config('development')
        
        assert config.system['name'] == 'RANGEN V2'
        assert config.system['environment'] == 'development'
        assert config.system['debug'] is True
        assert config.llm['provider'] == 'deepseek'
    
    def test_load_production_config(self):
        """测试加载生产环境配置"""
        from src.config.unified_config import get_config
        
        config = get_config('production')
        
        assert config.system['name'] == 'RANGEN V2'
        assert config.system['environment'] == 'production'
        assert config.system['debug'] is False
        assert config.llm['provider'] == 'deepseek'
    
    def test_load_default_env(self):
        """测试从环境变量加载"""
        os.environ['ENVIRONMENT'] = 'development'
        
        from src.config.unified_config import get_config
        config = get_config()
        
        assert config.system['environment'] == 'development'
        
        # 清理
        del os.environ['ENVIRONMENT']
    
    def test_config_sections_exist(self):
        """测试配置各部分存在"""
        from src.config.unified_config import get_config
        
        config = get_config('development')
        
        # 验证关键配置部分
        assert 'system' in config.raw
        assert 'llm' in config.raw
        assert 'kms' in config.raw
        assert 'agents' in config.raw
    
    def test_agent_configs(self):
        """测试 Agent 配置"""
        from src.config.unified_config import get_config
        
        config = get_config('development')
        
        agents = config.agents
        assert 'reasoning_agent' in agents
        assert 'validation_agent' in agents
        assert 'citation_agent' in agents
    
    def test_llm_config(self):
        """测试 LLM 配置"""
        from src.config.unified_config import get_config
        
        config = get_config('development')
        
        llm = config.llm
        assert 'provider' in llm
        assert llm['provider'] == 'deepseek'
        assert 'deepseek' in llm
    
    def test_kms_config(self):
        """测试 KMS 配置"""
        from src.config.unified_config import get_config
        
        config = get_config('development')
        
        kms = config.kms
        assert kms.get('enabled') is not None
        assert 'features' in kms
        assert 'performance' in kms


class TestUnifiedConfigClass:
    """测试 UnifiedConfig 数据类"""
    
    def test_from_dict(self):
        """测试从字典创建"""
        from src.config.unified_config import UnifiedConfig
        
        data = {
            'system': {'name': 'Test', 'version': '1.0'},
            'llm': {'provider': 'test'}
        }
        
        config = UnifiedConfig.from_dict(data)
        
        assert config.system['name'] == 'Test'
        assert config.llm['provider'] == 'test'
    
    def test_get_method(self):
        """测试 get 方法"""
        from src.config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        config.raw = {'key': 'value'}
        
        assert config.get('key') == 'value'
        assert config.get('missing', 'default') == 'default'


class TestBaseConfig:
    """测试基础配置"""
    
    def test_base_config_parsing(self):
        """测试基础配置解析"""
        import yaml
        
        with open('config/base.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        assert config is not None
        assert 'system' in config
        assert config['system']['name'] == 'RANGEN V2'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
