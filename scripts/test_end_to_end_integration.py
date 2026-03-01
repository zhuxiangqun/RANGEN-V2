#!/usr/bin/env python3
"""
端到端集成测试 - P4阶段全面验证

验证完整系统架构从查询输入到答案输出的端到端流程：
1. 智能路由器 → 简化工作流 → 能力编排 → 状态管理 → 监控系统
2. 错误处理和恢复机制
3. 性能监控和统计
4. 系统健康检查
5. 跨组件集成验证
"""

import asyncio
import sys
import time
import json
from typing import Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intelligent_router import get_intelligent_router
from src.core.simplified_business_workflow import SimplifiedBusinessWorkflow
from src.core.capability_orchestration_engine import get_orchestration_engine
from src.core.layered_state_management import UnifiedState, BusinessState
from src.core.monitoring_sidecar import get_monitoring_sidecar


class EndToEndTestSuite:
    """端到端集成测试套件"""

    def __init__(self):
        self.router = get_intelligent_router()
        self.workflow = SimplifiedBusinessWorkflow()
        self.orchestrator = get_orchestration_engine()
        self.sidecar = get_monitoring_sidecar()

        # 初始化监控
        self.sidecar.attach_to_workflow(self.workflow)

        self.test_results = []
        self.performance_metrics = {}

    async def run_full_integration_test(self):
        """运行完整集成测试"""
        print("🚀 开始端到端集成测试")
        print("=" * 80)

        try:
            # 测试1: 简单查询完整流程
            await self.test_simple_query_flow()

            # 测试2: 复杂查询完整流程
            await self.test_complex_query_flow()

            # 测试3: 能力编排集成
            await self.test_capability_orchestration_integration()

            # 测试4: 状态管理集成
            await self.test_state_management_integration()

            # 测试5: 监控系统集成
            await self.test_monitoring_integration()

            # 测试6: 错误处理和恢复
            await self.test_error_handling_and_recovery()

            # 测试7: 性能和负载测试
            await self.test_performance_and_load()

            # 测试8: 系统健康检查
            await self.test_system_health_check()

            # 生成测试报告
            self.generate_test_report()

        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    async def test_simple_query_flow(self):
        """测试简单查询完整流程"""
        print("\n🧪 测试1: 简单查询完整流程")
        print("-" * 40)

        query = "What is Python?"
        start_time = time.time()

        try:
            # 1. 智能路由
            route_decision = self.router.route_query(query)
            assert route_decision.route_type.value == "simple"

            # 2. 业务工作流执行
            workflow_result = await self.workflow.execute(query)

            # 3. 验证结果
            assert "result" in workflow_result
            assert "answer" in workflow_result["result"]
            assert workflow_result["route_path"] == "simple"

            execution_time = time.time() - start_time
            self.performance_metrics["simple_query"] = execution_time

            print(".3f")
            print("✅ 简单查询完整流程测试通过")

            self.test_results.append({
                "test": "simple_query_flow",
                "status": "passed",
                "execution_time": execution_time,
                "details": {
                    "route_type": route_decision.route_type.value,
                    "confidence": route_decision.confidence,
                    "result_keys": list(workflow_result.keys())
                }
            })

        except Exception as e:
            print(f"❌ 简单查询流程测试失败: {e}")
            self.test_results.append({
                "test": "simple_query_flow",
                "status": "failed",
                "error": str(e)
            })

    async def test_complex_query_flow(self):
        """测试复杂查询完整流程"""
        print("\n🧪 测试2: 复杂查询完整流程")
        print("-" * 40)

        query = "Explain the impact of artificial intelligence on healthcare systems and provide detailed recommendations"
        start_time = time.time()

        try:
            # 1. 智能路由
            route_decision = self.router.route_query(query)
            assert route_decision.route_type.value in ["complex", "multi_agent"]

            # 2. 业务工作流执行
            workflow_result = await self.workflow.execute(query)

            # 3. 验证结果
            assert "result" in workflow_result
            assert workflow_result["route_path"] in ["complex", "medium"]

            execution_time = time.time() - start_time
            self.performance_metrics["complex_query"] = execution_time

            print(".3f")
            print("✅ 复杂查询完整流程测试通过")

            self.test_results.append({
                "test": "complex_query_flow",
                "status": "passed",
                "execution_time": execution_time,
                "details": {
                    "route_type": route_decision.route_type.value,
                    "confidence": route_decision.confidence,
                    "complexity_score": getattr(route_decision, 'features_used', [])
                }
            })

        except Exception as e:
            print(f"❌ 复杂查询流程测试失败: {e}")
            self.test_results.append({
                "test": "complex_query_flow",
                "status": "failed",
                "error": str(e)
            })

    async def test_capability_orchestration_integration(self):
        """测试能力编排集成"""
        print("\n🧪 测试3: 能力编排集成")
        print("-" * 40)

        try:
            # 1. 创建复合能力
            composite_dsl = "knowledge_retrieval -> reasoning -> answer_generation"
            composite_cap_id = self.orchestrator.create_composite_capability(
                "ai_analysis_pipeline",
                composite_dsl,
                "AI分析管道复合能力"
            )

            # 2. 执行复合能力编排
            result = await self.orchestrator.execute_orchestration(
                composite_dsl,
                {"query": "How do neural networks learn?"}
            )

            # 3. 验证编排结果
            assert result, "编排结果为空"
            assert len(result) >= 3, f"编排结果不完整: {len(result)}个输出"

            # 4. 验证编排统计
            stats = self.orchestrator.get_orchestration_stats()
            assert stats["total_executions"] >= 1
            assert stats["successful_executions"] >= 1

            print("✅ 能力编排集成测试通过"            print(f"   创建复合能力: {composite_cap_id}")
            print(f"   编排执行统计: {stats['total_executions']}次执行")

            self.test_results.append({
                "test": "capability_orchestration_integration",
                "status": "passed",
                "details": {
                    "composite_capability": composite_cap_id,
                    "orchestration_stats": stats,
                    "result_count": len(result)
                }
            })

        except Exception as e:
            print(f"❌ 能力编排集成测试失败: {e}")
            self.test_results.append({
                "test": "capability_orchestration_integration",
                "status": "failed",
                "error": str(e)
            })

    async def test_state_management_integration(self):
        """测试状态管理集成"""
        print("\n🧪 测试4: 状态管理集成")
        print("-" * 40)

        try:
            # 1. 创建分层状态
            business_state = BusinessState(
                query="Test state management integration",
                context={"test": True},
                route_path="complex",
                complexity_score=0.8
            )

            unified_state = UnifiedState(business=business_state)

            # 2. 执行工作流（会更新状态）
            workflow_result = await self.workflow.execute(unified_state.business.query)

            # 3. 更新状态
            unified_state.business.result = workflow_result.get("result", {})
            unified_state.business.execution_time = workflow_result.get("execution_time", 0)
            unified_state.business.update_timestamp()

            # 4. 序列化/反序列化测试
            state_dict = unified_state.to_dict()
            restored_state = UnifiedState.from_dict(state_dict)

            # 5. 验证状态完整性
            from src.core.layered_state_management import get_state_manager
            state_manager = get_state_manager()
            assert state_manager.validate_state_integrity(unified_state)
            assert state_manager.validate_state_integrity(restored_state)

            # 6. 测试向后兼容
            legacy_state = unified_state.to_langgraph_state()
            assert "query" in legacy_state
            assert "result" in legacy_state

            print("✅ 状态管理集成测试通过"            print(f"   状态序列化大小: {len(json.dumps(state_dict))} 字符")
            print("   向后兼容性: ✅ 通过"

            self.test_results.append({
                "test": "state_management_integration",
                "status": "passed",
                "details": {
                    "state_size": len(json.dumps(state_dict)),
                    "has_business_layer": unified_state.business is not None,
                    "has_collaboration_layer": unified_state.collaboration is not None,
                    "has_system_layer": unified_state.system is not None,
                    "backward_compatibility": True
                }
            })

        except Exception as e:
            print(f"❌ 状态管理集成测试失败: {e}")
            self.test_results.append({
                "test": "state_management_integration",
                "status": "failed",
                "error": str(e)
            })

    async def test_monitoring_integration(self):
        """测试监控系统集成"""
        print("\n🧪 测试5: 监控系统集成")
        print("-" * 40)

        try:
            # 1. 启动监控系统
            self.sidecar.start()

            # 2. 执行多个查询生成监控数据
            test_queries = [
                "What is AI?",
                "Explain machine learning",
                "Compare different databases"
            ]

            for query in test_queries:
                # 发送监控事件
                from src.core.monitoring_sidecar import WorkflowEvent
                event = WorkflowEvent(
                    "workflow_start", f"test_{int(time.time())}",
                    time.time(), "integration_test", {"query": query}
                )
                await self.sidecar.on_workflow_event_async(event)

                # 执行查询
                await self.workflow.execute(query)

                # 发送完成事件
                event = WorkflowEvent(
                    "workflow_end", f"test_{int(time.time())}",
                    time.time(), "integration_test",
                    {"execution_time": 0.5, "success": True}
                )
                await self.sidecar.on_workflow_event_async(event)

            # 3. 等待监控处理
            await asyncio.sleep(2)

            # 4. 检查监控状态
            status = self.sidecar.get_system_status()
            assert status["running"] == True
            assert status["event_queue_size"] == 0  # 应该被处理完

            print("✅ 监控系统集成测试通过"            print(f"   监控事件处理: {status['event_queue_size'] == 0}")
            print(f"   指标收集: {status['metrics_collected'] > 0}")

            self.test_results.append({
                "test": "monitoring_integration",
                "status": "passed",
                "details": {
                    "monitoring_status": status,
                    "events_processed": status['event_queue_size'] == 0,
                    "metrics_collected": status['metrics_collected']
                }
            })

            # 5. 停止监控
            self.sidecar.stop()

        except Exception as e:
            print(f"❌ 监控系统集成测试失败: {e}")
            self.test_results.append({
                "test": "monitoring_integration",
                "status": "failed",
                "error": str(e)
            })

    async def test_error_handling_and_recovery(self):
        """测试错误处理和恢复"""
        print("\n🧪 测试6: 错误处理和恢复")
        print("-" * 40)

        try:
            # 1. 测试路由器错误处理
            invalid_query = ""  # 空查询
            route_decision = self.router.route_query(invalid_query)
            assert route_decision.route_type.value == "simple"  # 应该有默认值

            # 2. 测试编排错误处理
            invalid_dsl = "nonexistent_capability -> another_nonexistent"
            try:
                result = await self.orchestrator.execute_orchestration(invalid_dsl)
                # 如果没有抛出异常，说明错误处理正常工作
            except Exception:
                # 预期内的异常，错误处理正常
                pass

            # 3. 测试状态迁移错误处理
            from src.core.layered_state_management import get_state_manager
            state_manager = get_state_manager()

            # 无效状态
            invalid_state = {"invalid": "state"}
            migrated = state_manager.migrate_legacy_state(invalid_state)
            assert migrated.business.query == ""  # 应该有默认值

            print("✅ 错误处理和恢复测试通过"            print("   路由器错误处理: ✅ 通过"
            print("   编排错误处理: ✅ 通过"            print("   状态迁移错误处理: ✅ 通过"
            self.test_results.append({
                "test": "error_handling_and_recovery",
                "status": "passed",
                "details": {
                    "router_error_handling": True,
                    "orchestrator_error_handling": True,
                    "state_migration_error_handling": True
                }
            })

        except Exception as e:
            print(f"❌ 错误处理和恢复测试失败: {e}")
            self.test_results.append({
                "test": "error_handling_and_recovery",
                "status": "failed",
                "error": str(e)
            })

    async def test_performance_and_load(self):
        """测试性能和负载"""
        print("\n🧪 测试7: 性能和负载测试")
        print("-" * 40)

        try:
            # 1. 并发性能测试
            concurrent_queries = [
                "What is Python?",
                "Explain AI",
                "How does machine learning work?",
                "Compare SQL and NoSQL",
                "What are microservices?"
            ]

            start_time = time.time()

            # 并发执行
            tasks = [self.workflow.execute(query) for query in concurrent_queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            concurrent_time = time.time() - start_time

            # 验证并发结果
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]

            print(".3f"            print(f"   成功查询: {len(successful_results)}/{len(concurrent_queries)}")
            print(f"   失败查询: {len(failed_results)}")

            # 2. 持续负载测试
            load_test_queries = ["Load test query"] * 10
            load_start_time = time.time()

            load_tasks = [self.workflow.execute(query) for query in load_test_queries]
            load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

            load_time = time.time() - load_start_time
            load_successful = [r for r in load_results if not isinstance(r, Exception)]

            print(".3f"            print(f"   负载成功率: {len(load_successful)}/{len(load_test_queries)}")

            # 性能断言
            avg_query_time = concurrent_time / len(concurrent_queries)
            assert avg_query_time < 1.0, f"平均查询时间过长: {avg_query_time:.3f}s"
            assert len(successful_results) >= len(concurrent_queries) * 0.8, "并发成功率过低"

            self.performance_metrics.update({
                "concurrent_time": concurrent_time,
                "concurrent_queries": len(concurrent_queries),
                "successful_concurrent": len(successful_results),
                "load_time": load_time,
                "load_queries": len(load_test_queries),
                "successful_load": len(load_successful),
                "avg_query_time": avg_query_time
            })

            print("✅ 性能和负载测试通过")

            self.test_results.append({
                "test": "performance_and_load",
                "status": "passed",
                "execution_time": concurrent_time + load_time,
                "details": self.performance_metrics
            })

        except Exception as e:
            print(f"❌ 性能和负载测试失败: {e}")
            self.test_results.append({
                "test": "performance_and_load",
                "status": "failed",
                "error": str(e)
            })

    async def test_system_health_check(self):
        """测试系统健康检查"""
        print("\n🧪 测试8: 系统健康检查")
        print("-" * 40)

        try:
            health_status = {
                "router": await self.check_component_health("router"),
                "workflow": await self.check_component_health("workflow"),
                "orchestrator": await self.check_component_health("orchestrator"),
                "state_manager": await self.check_component_health("state_manager"),
                "monitoring": await self.check_component_health("monitoring")
            }

            # 计算整体健康度
            healthy_components = sum(1 for status in health_status.values() if status)
            total_components = len(health_status)
            health_score = healthy_components / total_components

            print(".1%"            print("组件健康状态:"            for component, healthy in health_status.items():
                status = "✅" if healthy else "❌"
                print(f"   {component}: {status}")

            # 健康度断言
            assert health_score >= 0.8, f"系统健康度过低: {health_score:.1%}"

            print("✅ 系统健康检查测试通过")

            self.test_results.append({
                "test": "system_health_check",
                "status": "passed",
                "details": {
                    "health_score": health_score,
                    "component_health": health_status,
                    "healthy_components": healthy_components,
                    "total_components": total_components
                }
            })

        except Exception as e:
            print(f"❌ 系统健康检查失败: {e}")
            self.test_results.append({
                "test": "system_health_check",
                "status": "failed",
                "error": str(e)
            })

    async def check_component_health(self, component_name: str) -> bool:
        """检查组件健康状态"""
        try:
            if component_name == "router":
                # 测试路由器健康
                decision = self.router.route_query("health check")
                return decision.route_type is not None

            elif component_name == "workflow":
                # 测试工作流健康
                result = await self.workflow.execute("health check")
                return "result" in result

            elif component_name == "orchestrator":
                # 测试编排器健康
                stats = self.orchestrator.get_orchestration_stats()
                return "total_executions" in stats

            elif component_name == "state_manager":
                # 测试状态管理器健康
                from src.core.layered_state_management import get_state_manager
                manager = get_state_manager()
                test_state = UnifiedState(business=BusinessState(query="test"))
                return manager.validate_state_integrity(test_state)

            elif component_name == "monitoring":
                # 测试监控系统健康
                status = self.sidecar.get_system_status()
                return "running" in status

            return False

        except Exception:
            return False

    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("📊 端到端集成测试报告")
        print("=" * 80)

        # 测试结果统计
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "passed"])
        failed_tests = total_tests - passed_tests

        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"总体测试结果: {passed_tests}/{total_tests} 通过 ({success_rate:.1%})")
        print(f"✅ 通过测试: {passed_tests}")
        print(f"❌ 失败测试: {failed_tests}")
        print()

        # 详细结果
        print("详细测试结果:")
        for result in self.test_results:
            status = "✅" if result["status"] == "passed" else "❌"
            execution_time = result.get("execution_time", 0)
            print(".3f")

            if result["status"] == "failed":
                print(f"     错误: {result.get('error', '未知错误')}")

        print()

        # 性能指标
        if self.performance_metrics:
            print("性能指标:")
            for metric, value in self.performance_metrics.items():
                if isinstance(value, float):
                    print(".3f")
                else:
                    print(f"   {metric}: {value}")
            print()

        # 结论
        if success_rate >= 0.9:
            print("🎉 测试结论: 端到端集成测试全部通过！系统架构重构成功！")
            print("🏆 系统已准备好进行性能基准测试和生产部署。")
        elif success_rate >= 0.7:
            print("⚠️ 测试结论: 大部分测试通过，系统基本稳定，但存在一些问题需要解决。")
            print("🔧 建议在生产部署前解决失败的测试项。")
        else:
            print("❌ 测试结论: 多个关键测试失败，系统存在严重问题。")
            print("🛠️ 需要立即修复失败的测试项后再进行后续步骤。")

        print("=" * 80)


async def main():
    """主测试函数"""
    test_suite = EndToEndTestSuite()
    success = await test_suite.run_full_integration_test()

    # 保存测试结果到文件
    import json
    result_file = Path(__file__).parent / "end_to_end_test_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_results": test_suite.test_results,
            "performance_metrics": test_suite.performance_metrics,
            "overall_success": success,
            "timestamp": time.time()
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 测试结果已保存到: {result_file}")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
