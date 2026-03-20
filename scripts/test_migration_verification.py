#!/usr/bin/env python3
"""
验证ReActAgent到ReasoningExpert迁移效果的综合测试
"""

import sys
import time
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

class MigrationVerifier:
    """迁移验证器"""

    def __init__(self):
        self.results = []
        self.errors = []

    def log_result(self, test_name: str, success: bool, message: str = "", details: Dict[str, Any] = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")

    async def test_import_systems(self):
        """测试主要系统的导入"""
        print("\n🔍 测试1: 系统导入验证")
        print("-" * 40)

        test_cases = [
            ("UnifiedResearchSystem", "src.unified_research_system", "UnifiedResearchSystem"),
            ("IntelligentOrchestrator", "src.core.intelligent_orchestrator", "IntelligentOrchestrator"),
            ("LangGraphAgentNodes", "src.core.langgraph_agent_nodes", "LangGraphAgentNodes"),
            ("ReasoningExpert", "src.agents.reasoning_expert", "ReasoningExpert"),
        ]

        for test_name, module_path, class_name in test_cases:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.log_result(f"导入{test_name}", True, f"成功导入{class_name}")
            except Exception as e:
                self.log_result(f"导入{test_name}", False, f"导入失败: {e}")
                self.errors.append(f"Import error in {test_name}: {e}")

    async def test_instantiation(self):
        """测试实例化"""
        print("\n🔍 测试2: 实例化验证")
        print("-" * 40)

        try:
            # 测试UnifiedResearchSystem
            from src.unified_research_system import UnifiedResearchSystem
            system = UnifiedResearchSystem()
            agent_type = type(system._react_agent).__name__
            self.log_result("UnifiedResearchSystem实例化", True,
                          f"成功实例化，内部Agent类型: {agent_type}")

            if agent_type == "ReasoningExpert":
                self.log_result("Agent类型验证", True, "正确使用ReasoningExpert")
            else:
                self.log_result("Agent类型验证", False, f"仍在使用: {agent_type}")

        except Exception as e:
            self.log_result("UnifiedResearchSystem实例化", False, f"实例化失败: {e}")
            self.errors.append(f"Instantiation error: {e}")

    async def test_basic_functionality(self):
        """测试基本功能"""
        print("\n🔍 测试3: 基本功能验证")
        print("-" * 40)

        try:
            from src.agents.reasoning_expert import ReasoningExpert

            # 创建ReasoningExpert实例
            expert = ReasoningExpert()
            self.log_result("ReasoningExpert实例化", True, "成功创建实例")

            # 测试简单的推理任务
            test_context = {
                "query": "What are the main benefits of artificial intelligence?",
                "reasoning_type": "deductive",
                "complexity": "moderate",
                "max_parallel_paths": 2,  # 减少并行度以加快测试
                "timeout_seconds": 60     # 1分钟超时
            }

            print("   🔄 执行推理任务（可能需要一些时间）...")

            start_time = time.time()
            try:
                # 设置较短的超时时间进行测试
                result = await asyncio.wait_for(
                    expert.execute(test_context),
                    timeout=30  # 30秒超时
                )

                execution_time = time.time() - start_time

                self.log_result("推理执行", True,
                              ".2f"
                              f"成功: {result.success}")

                if result.success:
                    self.log_result("结果验证", True, "推理任务成功完成")
                else:
                    self.log_result("结果验证", False, f"推理失败: {result.error}")

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                self.log_result("推理执行", False, ".2f"            except Exception as e:
                execution_time = time.time() - start_time
                self.log_result("推理执行", False, f"执行异常: {e}")
                self.errors.append(f"Execution error: {e}")

        except Exception as e:
            self.log_result("基本功能测试", False, f"测试失败: {e}")
            self.errors.append(f"Basic functionality error: {e}")

    async def test_error_handling(self):
        """测试错误处理"""
        print("\n🔍 测试4: 错误处理验证")
        print("-" * 40)

        try:
            from src.agents.reasoning_expert import ReasoningExpert

            expert = ReasoningExpert()

            # 测试空查询
            empty_context = {"query": ""}
            result = await expert.execute(empty_context)

            if not result.success and result.error:
                self.log_result("错误处理", True, "正确处理空查询")
            else:
                self.log_result("错误处理", False, "空查询处理异常")

            # 测试无效上下文
            invalid_context = {"invalid": "data"}
            result = await expert.execute(invalid_context)

            if not result.success:
                self.log_result("无效输入处理", True, "正确处理无效输入")
            else:
                self.log_result("无效输入处理", False, "无效输入处理异常")

        except Exception as e:
            self.log_result("错误处理测试", False, f"测试失败: {e}")
            self.errors.append(f"Error handling test error: {e}")

    async def test_performance_baseline(self):
        """测试性能基线"""
        print("\n🔍 测试5: 性能基线测试")
        print("-" * 40)

        try:
            from src.agents.reasoning_expert import ReasoningExpert

            expert = ReasoningExpert()

            # 测试不同复杂度的查询
            test_queries = [
                ("Simple", {"query": "What is 2+2?", "complexity": "simple"}),
                ("Moderate", {"query": "Explain photosynthesis", "complexity": "moderate"}),
            ]

            for test_name, context in test_queries:
                try:
                    start_time = time.time()
                    result = await asyncio.wait_for(
                        expert.execute(context),
                        timeout=45  # 45秒超时
                    )
                    execution_time = time.time() - start_time

                    if result.success:
                        self.log_result(f"{test_name}性能测试", True,
                                      ".2f"                    else:
                        self.log_result(f"{test_name}性能测试", False,
                                      ".2f"
                except asyncio.TimeoutError:
                    self.log_result(f"{test_name}性能测试", False, "执行超时")
                except Exception as e:
                    self.log_result(f"{test_name}性能测试", False, f"执行异常: {e}")

        except Exception as e:
            self.log_result("性能测试", False, f"测试失败: {e}")
            self.errors.append(f"Performance test error: {e}")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 迁移验证测试总结")
        print("=" * 60)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"   • {error}")

        print("
✅ 通过的测试:"        for result in self.results:
            if result["success"]:
                print(f"   • {result['test']}: {result['message']}")

        if failed_tests > 0:
            print("
❌ 失败的测试:"            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")

        # 总体评估
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"\n🎯 迁移成功率: {success_rate:.1%}")

        if success_rate >= 0.8:
            print("🎉 迁移成功！ReasoningExpert正常工作")
        elif success_rate >= 0.6:
            print("⚠️ 迁移部分成功，需要进一步调试")
        else:
            print("❌ 迁移失败，需要回滚或修复")

async def main():
    """主测试函数"""
    print("🚀 ReActAgent → ReasoningExpert 迁移效果验证")
    print("=" * 60)
    print("此测试将验证迁移是否成功，以及新Agent是否正常工作")
    print("测试包括：导入验证、实例化、功能测试、错误处理、性能测试")
    print("=" * 60)

    verifier = MigrationVerifier()

    # 运行所有测试
    await verifier.test_import_systems()
    await verifier.test_instantiation()
    await verifier.test_basic_functionality()
    await verifier.test_error_handling()
    await verifier.test_performance_baseline()

    # 打印总结
    verifier.print_summary()

    print("\n💡 后续建议:")
    if verifier.errors:
        print("- 检查上述错误并修复")
        print("- 考虑回滚到ReActAgent如果问题严重")
    else:
        print("- 监控生产环境的使用情况")
        print("- 收集用户反馈")
        print("- 准备进行其他Agent的迁移")

    print("\n🔄 如需重新运行测试，请执行:")
    print("python3 test_migration_verification.py")

if __name__ == "__main__":
    asyncio.run(main())
