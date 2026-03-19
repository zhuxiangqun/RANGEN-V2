#!/usr/bin/env python3
"""
T20: 轻量模式测试
测试 LiteConfigurator, CLI入口
"""

import sys
sys.path.insert(0, '.')

import pytest
import tempfile
import os
import subprocess


class TestLiteConfigurator:
    """测试轻量配置器"""
    
    def test_import(self):
        """测试 LiteConfigurator 可以导入"""
        from src.core.lite_configurator import LiteConfigurator
        configurator = LiteConfigurator()
        assert configurator is not None
    
    def test_load_config(self):
        """测试加载配置"""
        from src.core.lite_configurator import LiteConfigurator
        configurator = LiteConfigurator()
        config = configurator.load_config()
        assert config is not None
    
    def test_configure(self):
        """测试配置功能"""
        from src.core.lite_configurator import LiteConfigurator
        configurator = LiteConfigurator()
        
        assert hasattr(configurator, 'configure')
        assert hasattr(configurator, 'config')
        assert hasattr(configurator, 'config_path')


class TestCLI:
    """测试 CLI 入口"""
    
    def test_cli_module_import(self):
        """测试 CLI 模块可以导入"""
        import src.cli
        assert src.cli is not None
    
    def test_cli_help(self):
        """测试 CLI 帮助"""
        result = subprocess.run(
            [sys.executable, '-m', 'src.cli', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert 'skills' in result.stdout.lower() or 'help' in result.stdout.lower()


class TestLiteConfigGeneration:
    """测试轻量配置生成"""
    
    def test_config_load(self):
        """测试配置加载"""
        from src.core.lite_configurator import LiteConfigurator
        configurator = LiteConfigurator()
        
        config = configurator.load_config()
        assert config is not None


class TestLiteModeIntegration:
    """测试轻量模式集成"""
    
    def test_configurator_importable(self):
        """测试配置器可导入"""
        from src.core.lite_configurator import LiteConfigurator
        assert LiteConfigurator is not None


class TestLiteModeCLI:
    """测试轻量模式 CLI 命令"""
    
    def test_lite_command(self):
        """测试 lite 子命令"""
        result = subprocess.run(
            [sys.executable, '-m', 'src.cli', 'lite', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # argparser 返回 0 表示成功
        assert result.returncode == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
