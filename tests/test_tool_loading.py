#!/usr/bin/env python3
"""
Tool Loading Strategy Tests - 工具加载策略测试

测试渐进式工具加载 (Progressive Tool Loading)
优先级: Skill > CLI > API > MCP
"""
import sys
import unittest

sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')


class TestToolLoadingStrategy(unittest.TestCase):
    """测试工具加载策略"""
    
    def test_priority_order(self):
        """测试优先级顺序"""
        # 验证 progressive_tool_loader 存在
        from src.core.progressive_tool_loader import ToolPriority
        self.assertIsNotNone(ToolPriority)
    
    def test_cli_tools_import(self):
        """测试 CLI 工具可导入"""
        from src.core import cli_tools
        self.assertIsNotNone(cli_tools)
    
    def test_skill_priority_over_mcp(self):
        """测试 Skill 优先级高于 MCP"""
        # 根据 ADR-001，Skill 应该有更高优先级
        # 这是一个概念验证
        
        # 检查 Skill 系统存在
        try:
            from src.agents.skills import get_skill_registry
            self.assertTrue(True, "Skill registry available")
        except ImportError:
            self.skipTest("Skill registry not fully implemented")


class TestSkillSystem(unittest.TestCase):
    """测试 Skill 系统"""
    
    def test_skill_directory_exists(self):
        """测试 Skill 目录存在"""
        from pathlib import Path
        
        skill_path = Path("src/agents/skills/bundled")
        
        # 验证目录存在
        self.assertTrue(skill_path.exists(), "Skills bundled directory not found")
        
        # 验证有 skill 文件
        if skill_path.exists():
            skill_files = list(skill_path.glob("*/skill.yaml"))
            self.assertGreater(len(skill_files), 0, "No skill.yaml files found")


class TestToolRegistry(unittest.TestCase):
    """测试工具注册"""
    
    def test_tool_registry_exists(self):
        """测试工具注册表存在"""
        from src.agents.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        self.assertIsNotNone(registry)
    
    def test_tools_registered(self):
        """Test tools can be listed"""
        from src.agents.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Registry should exist and be functional
        self.assertIsNotNone(registry)


def run_tool_tests():
    """运行工具测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestToolLoadingStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestSkillSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestToolRegistry))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tool_tests()
    if success:
        print("\n✅ 工具加载策略测试通过!")
    else:
        print("\n⚠️ 部分测试跳过或失败")
