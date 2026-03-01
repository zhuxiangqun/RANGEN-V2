#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN测试框架
提供统一的测试基础设施和工具
"""

import os
import sys
import unittest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RANGENTestCase(unittest.TestCase):
    """RANGEN测试基类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(self.temp_dir, "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """创建测试文件"""
        file_path = os.path.join(self.test_data_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def create_test_config(self, config_data: Dict[str, Any]) -> str:
        """创建测试配置文件"""
        config_path = os.path.join(self.test_data_dir, "test_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return config_path
    
    def assert_file_exists(self, file_path: str):
        """断言文件存在"""
        self.assertTrue(os.path.exists(file_path), f"文件不存在: {file_path}")
    
    def assert_file_content_contains(self, file_path: str, content: str):
        """断言文件内容包含指定文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertIn(content, file_content, f"文件内容不包含: {content}")
    
    def assert_json_valid(self, file_path: str):
        """断言JSON文件有效"""
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)  # 如果JSON无效会抛出异常

class AsyncTestCase(RANGENTestCase):
    """异步测试基类"""
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
    
    def run_async(self, coro):
        """运行异步函数"""
        return self.loop.run_until_complete(coro)

class MockTestCase(RANGENTestCase):
    """模拟测试基类"""
    
    def setUp(self):
        super().setUp()
        self.mocks = {}
    
    def tearDown(self):
        for mock in self.mocks.values():
            if hasattr(mock, 'stop'):
                mock.stop()
        super().tearDown()
    
    def create_mock(self, name: str, **kwargs) -> Mock:
        """创建模拟对象"""
        mock = Mock(**kwargs)
        self.mocks[name] = mock
        return mock
    
    def patch_module(self, module_path: str, **kwargs):
        """补丁模块"""
        patcher = patch(module_path, **kwargs)
        mock = patcher.start()
        self.mocks[module_path] = patcher
        return mock

class TestRunner:
    """测试运行器"""
    
    def __init__(self, test_dir: str = "tests"):
        self.test_dir = test_dir
        self.results = {}
    
    def discover_tests(self) -> List[str]:
        """发现测试文件"""
        test_files = []
        for root, dirs, files in os.walk(self.test_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))
        return test_files
    
    def run_tests(self, pattern: str = "test_*.py") -> Dict[str, Any]:
        """运行测试"""
        loader = unittest.TestLoader()
        suite = loader.discover(self.test_dir, pattern=pattern)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
        }
        
        return self.results
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """生成覆盖率报告"""
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
            
            # 运行测试
            self.run_tests()
            
            cov.stop()
            cov.save()
            
            # 生成报告
            report = {
                'coverage_percentage': cov.report(),
                'missing_lines': cov.analysis2('src/').missing_lines if hasattr(cov, 'analysis2') else [],
                'covered_files': len(cov.get_data().measured_files()) if hasattr(cov, 'get_data') else 0
            }
            
            return report
        except ImportError:
            return {'error': 'coverage模块未安装'}
    
    def generate_test_report(self) -> str:
        """生成测试报告"""
        report = f"""
# RANGEN测试报告

## 测试统计
- 总测试数: {self.results.get('tests_run', 0)}
- 失败数: {self.results.get('failures', 0)}
- 错误数: {self.results.get('errors', 0)}
- 跳过数: {self.results.get('skipped', 0)}
- 成功率: {self.results.get('success_rate', 0):.2%}

## 测试文件
"""
        test_files = self.discover_tests()
        for test_file in test_files:
            report += f"- {test_file}\n"
        
        return report

# 测试工具函数
def create_mock_agent():
    """创建模拟智能体"""
    agent = Mock()
    agent.name = "TestAgent"
    agent.process.return_value = {"result": "test_result"}
    agent.analyze.return_value = {"analysis": "test_analysis"}
    return agent

def create_mock_config():
    """创建模拟配置"""
    return {
        "test_mode": True,
        "debug": True,
        "timeout": 30,
        "max_retries": 3
    }

def create_test_data():
    """创建测试数据"""
    return {
        "query": "test query",
        "context": "test context",
        "expected_result": "expected result"
    }

if __name__ == "__main__":
    # 运行测试
    runner = TestRunner()
    results = runner.run_tests()
    print(f"测试结果: {results}")
    
    # 生成报告
    report = runner.generate_test_report()
    print(report)
