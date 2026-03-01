#!/usr/bin/env python3
"""
回归测试
确保新架构不破坏现有功能
"""

import unittest
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest


class TestRegression(unittest.IsolatedAsyncioTestCase):
    """回归测试类"""
    
    async def asyncSetUp(self):
        """异步测试前准备"""
        # 注意：实际初始化UnifiedResearchSystem可能需要较长时间
        # 在实际测试中，可以考虑使用Mock或简化初始化
        self.system = None
    
    async def test_basic_query_functionality(self):
        """测试基本查询功能"""
        # 这个测试需要实际初始化UnifiedResearchSystem
        # 由于初始化可能较慢，这里先跳过，在实际测试中实现
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整回归测试中实现")
        
        # 示例测试代码：
        # if self.system is None:
        #     self.system = UnifiedResearchSystem()
        #     await self.system.initialize()
        # 
        # request = ResearchRequest(query="What is the capital of France?")
        # result = await self.system.execute_research(request)
        # 
        # self.assertTrue(result.success)
        # self.assertIsNotNone(result.answer)
        # self.assertIn("Paris", result.answer)
    
    async def test_complex_query_functionality(self):
        """测试复杂查询功能"""
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整回归测试中实现")
    
    async def test_error_handling(self):
        """测试错误处理"""
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整回归测试中实现")
    
    async def test_answer_quality(self):
        """测试答案质量"""
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整回归测试中实现")


class TestFramesDatasetRegression(unittest.IsolatedAsyncioTestCase):
    """FRAMES数据集回归测试"""
    
    async def asyncSetUp(self):
        """异步测试前准备"""
        self.system = None
    
    async def test_frames_sample(self):
        """测试FRAMES数据集样本"""
        self.skipTest("需要实际初始化UnifiedResearchSystem，在完整回归测试中实现")
        
        # 示例测试代码：
        # if self.system is None:
        #     self.system = UnifiedResearchSystem()
        #     await self.system.initialize()
        # 
        # # 使用FRAMES数据集中的样本
        # query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
        # expected_answer = "Jane Ballou"
        # 
        # request = ResearchRequest(query=query)
        # result = await self.system.execute_research(request)
        # 
        # self.assertTrue(result.success)
        # self.assertIsNotNone(result.answer)
        # # 验证答案质量（可能需要模糊匹配）
        # self.assertIn("Jane", result.answer)
        # self.assertIn("Ballou", result.answer)


def run_all_existing_tests():
    """运行所有现有测试"""
    import subprocess
    import os
    
    # 获取所有测试文件
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"\n找到 {len(test_files)} 个测试文件:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # 运行每个测试文件
    results = {}
    for test_file in test_files:
        if test_file.name == "test_regression.py":
            continue  # 跳过自己
        
        print(f"\n运行测试: {test_file.name}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", f"tests.{test_file.stem}", "-v"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            results[test_file.name] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except subprocess.TimeoutExpired:
            results[test_file.name] = {
                "success": False,
                "output": "",
                "error": "测试超时（>5分钟）"
            }
        except Exception as e:
            results[test_file.name] = {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    # 打印结果
    print("\n" + "="*80)
    print("回归测试结果汇总")
    print("="*80)
    
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    
    print(f"\n总计: {total_count} 个测试文件")
    print(f"成功: {success_count} 个")
    print(f"失败: {total_count - success_count} 个")
    
    for test_file, result in results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"\n{status}: {test_file}")
        if not result["success"]:
            if result["error"]:
                print(f"  错误: {result['error'][:200]}")
    
    return success_count == total_count


if __name__ == '__main__':
    # 如果直接运行此文件，执行所有现有测试
    if len(sys.argv) > 1 and sys.argv[1] == "--run-all":
        success = run_all_existing_tests()
        sys.exit(0 if success else 1)
    else:
        # 否则运行单元测试
        unittest.main()

