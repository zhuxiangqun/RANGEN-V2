#!/usr/bin/env python3
"""
T18: 原子框架测试
测试 7 个原子工具
"""

import sys
sys.path.insert(0, '.')

import pytest
import tempfile
import os


class TestAtomicToolRegistry:
    """测试原子工具注册表"""
    
    def test_registry_import(self):
        """测试注册表可以导入"""
        from src.tools.atomic import AtomicToolRegistry
        registry = AtomicToolRegistry()
        assert registry is not None
    
    def test_list_tools(self):
        """测试列出所有工具"""
        from src.tools.atomic import AtomicToolRegistry
        registry = AtomicToolRegistry()
        tools = registry.list_tools()
        
        # 验证 7 个原子工具
        expected_tools = ['code_run', 'file_read', 'file_write', 'file_patch', 
                         'web_scan', 'web_execute_js', 'ask_user']
        for tool in expected_tools:
            assert tool in tools, f"Missing tool: {tool}"
    
    def test_get_tool(self):
        """测试获取指定工具"""
        from src.tools.atomic import AtomicToolRegistry
        registry = AtomicToolRegistry()
        
        code_runner = registry.get_tool('code_run')
        assert code_runner is not None


class TestCodeRunTool:
    """测试 code_run 工具"""
    
    def test_code_runner_import(self):
        """测试 CodeRunner 可以导入"""
        from src.tools.atomic import AtomicCodeRunner
        runner = AtomicCodeRunner()
        assert runner is not None


class TestFileReadTool:
    """测试 file_read 工具"""
    
    def test_file_tool_import(self):
        """测试 FileTool 可以导入"""
        from src.tools.atomic import AtomicFileTool
        tool = AtomicFileTool()
        assert tool is not None
    
    def test_file_read(self):
        """测试文件读取"""
        from src.tools.atomic import AtomicFileTool
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('test content')
            temp_path = f.name
        
        try:
            tool = AtomicFileTool()
            result = tool.read(temp_path)
            assert result.success is True
            assert 'test content' in result.output
        finally:
            os.unlink(temp_path)


class TestFileWriteTool:
    """测试 file_write 工具"""
    
    def test_file_write(self):
        """测试文件写入"""
        from src.tools.atomic import AtomicFileTool
        
        temp_path = tempfile.mktemp(suffix='.txt')
        
        try:
            tool = AtomicFileTool()
            result = tool.write(temp_path, 'new content')
            assert result.success is True
            
            with open(temp_path, 'r') as f:
                assert f.read() == 'new content'
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestFilePatchTool:
    """测试 file_patch 工具"""
    
    def test_file_patch(self):
        """测试文件修补"""
        from src.tools.atomic import AtomicFileTool
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write('def hello():\n    return "old"\n')
            temp_path = f.name
        
        try:
            tool = AtomicFileTool()
            result = tool.patch(temp_path, 'return "old"', 'return "new"')
            assert result.success is True
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert 'return "new"' in content
        finally:
            os.unlink(temp_path)


class TestWebScanTool:
    """测试 web_scan 工具"""
    
    def test_web_tool_import(self):
        """测试 WebTool 可以导入"""
        from src.tools.atomic import AtomicWebTool
        tool = AtomicWebTool()
        assert tool is not None


class TestAskUserTool:
    """测试 ask_user 工具"""
    
    def test_user_tool_import(self):
        """测试 UserTool 可以导入"""
        from src.tools.atomic import AtomicUserTool
        tool = AtomicUserTool()
        assert tool is not None


class TestHandsBuilder:
    """测试 HandsBuilder"""
    
    def test_builder_import(self):
        """测试 HandsBuilder 可以导入"""
        from src.hands.builder import HandsBuilder
        builder = HandsBuilder()
        assert builder is not None
    
    def test_list_hands(self):
        """测试列出所有 Hands"""
        from src.hands.builder import HandsBuilder
        builder = HandsBuilder()
        hands = builder.list_hands()
        assert isinstance(hands, list)
    
    def test_get_hand(self):
        """测试获取 Hand"""
        from src.hands.builder import HandsBuilder
        builder = HandsBuilder()
        hand = builder.get_hand('test_hand')
        # 可能返回 None 如果不存在，这是正常的


class TestAtomicToolSchema:
    """测试原子工具 Schema"""
    
    def test_tool_schemas(self):
        """测试工具 Schema 定义"""
        from src.tools.atomic import AtomicToolRegistry
        
        registry = AtomicToolRegistry()
        tools = registry.list_tools()
        assert len(tools) == 7


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
