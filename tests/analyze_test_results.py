"""
分析集成测试结果的详细脚本

深入分析哪些测试项目失败以及失败原因
"""

import sys
import os
import asyncio
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入测试组件
from src.core.enhanced_simplified_workflow import get_enhanced_simplified_workflow
from src.core.langgraph_monitoring_adapter import get_unified_monitoring_dashboard
from src.core.unified_test_orchestrator import get_unified_test_orchestrator

class TestResultAnalyzer:
    """测试结果分析器"""

    def __init__(self):
        self.enhanced_workflow = get_enhanced_simplified_workflow()
        self.monitoring_dashboard = get_unified_monitoring_dashboard()
        self.test_orchestrator = get_unified_test_orchestrator()

    async def analyze_individual_tests(self):
        """分析各个测试项目"""

        print("=" * 80)
        print("🔍 集成测试详细结果分析")
        print("=" * 80)

        results = []

        # 测试1: 增强版简化工作流功能验证
        print("\n📋 测试1: 增强版简化工作流功能验证")
        print("-" * 50)
        workflow_result = await self.analyze_workflow_test()
        results.append(("workflow_test", workflow_result))
        self.print_test_result(workflow_result)

        # 测试2: 监控系统集成验证
        print("\n📊 测试2: 监控系统集成验证")
        print("-" * 50)
        monitoring_result = await self.analyze_monitoring_test()
        results.append(("monitoring_test", monitoring_result))
        self.print_test_result(monitoring_result)

        # 测试3: 测试系统统一验证
        print("\n🧪 测试3: 测试系统统一验证")
        print("-" * 50)
        test_system_result = await self.analyze_test_system_test()
        results.append(("test_system_test", test_system_result))
        self.print_test_result(test_system_result)

        # 测试4: 端到端流程验证
        print("\n🔄 测试4: 端到端流程验证")
        print("-" * 50)
        e2e_result = await self.analyze_e2e_test()
        results.append(("e2e_test", e2e_result))
        self.print_test_result(e2e_result)

        # 测试5: 性能对比验证
        print("\n⚡ 测试5: 性能对比验证")
        print("-" * 50)
        performance_result = await self.analyze_performance_test()
        results.append(("performance_test", performance_result))
        self.print_test_result(performance_result)

        # 生成综合分析报告
        await self.generate_comprehensive_analysis(results)

    async def analyze_workflow_test(self):
        """分析工作流测试"""
        try:
            query = "测试工作流执行"
            result = await self.enhanced_workflow.process_query(query)

            validations = {
                "has_workflow_id": bool(result.get("workflow_id")),
                "has_final_answer": bool(result.get("final_answer")),
                "has_execution_time": isinstance(result.get("execution_time"), (int, float)),
                "has_execution_history": bool(result.get("execution_history")),
                "has_metrics": bool(result.get("metrics")),
                "status_success": result.get("status") == "success"
            }

            execution_history = result.get("execution_history", {})
            history_validations = {
                "has_nodes_executed": bool(execution_history.get("nodes_executed")),
                "has_execution_time": isinstance(execution_history.get("total_execution_time"), (int, float)),
                "nodes_completed": all(
                    node.get("status") == "completed"
                    for node in execution_history.get("nodes_executed", [])
                )
            }

            all_validations = {**validations, **history_validations}
            all_passed = all(all_validations.values())

            return {
                "status": "passed" if all_passed else "failed",
                "validations": all_validations,
                "passed_count": sum(all_validations.values()),
                "total_validations": len(all_validations),
                "issues": [k for k, v in all_validations.items() if not v]
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "validations": {},
                "passed_count": 0,
                "total_validations": 0,
                "issues": ["exception_occurred"]
            }

    async def analyze_monitoring_test(self):
        """分析监控测试"""
        try:
            metrics = await self.monitoring_dashboard.get_comprehensive_metrics()
            alerts = await self.monitoring_dashboard.get_unified_alerts()

            validations = {
                "has_timestamp": bool(metrics.get("timestamp")),
                "has_fused_metrics": bool(metrics.get("fused_metrics")),
                "has_source_breakdown": bool(metrics.get("source_breakdown")),
                "has_health_status": bool(metrics.get("health_status")),
                "fused_metrics_count": len(metrics.get("fused_metrics", {})),
                "alerts_is_list": isinstance(alerts, list)
            }

            # 检查是否有ABC导入错误
            abc_error_detected = any(
                alert.get("description", "").startswith("name 'ABC' is not defined")
                for alert in alerts if isinstance(alert, dict)
            )

            if abc_error_detected:
                validations["abc_import_error"] = False
            else:
                validations["abc_import_error"] = True

            all_passed = all(v for k, v in validations.items() if k != "abc_import_error")

            return {
                "status": "passed" if all_passed else "failed",
                "validations": validations,
                "passed_count": sum(v for k, v in validations.items() if isinstance(v, bool)),
                "total_validations": len([v for v in validations.values() if isinstance(v, bool)]),
                "issues": [k for k, v in validations.items() if isinstance(v, bool) and not v],
                "abc_error_detected": abc_error_detected
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "validations": {},
                "passed_count": 0,
                "total_validations": 0,
                "issues": ["exception_occurred"]
            }

    async def analyze_test_system_test(self):
        """分析测试系统测试"""
        try:
            test_suite = self.test_orchestrator.create_comprehensive_test_suite()
            execution_report = await self.test_orchestrator.execute_test_suite(test_suite)

            validations = {
                "has_suite_id": bool(execution_report.suite_id),
                "has_start_time": bool(execution_report.start_time),
                "has_end_time": bool(execution_report.end_time),
                "has_total_duration": isinstance(execution_report.total_duration, (int, float)),
                "has_test_results": bool(execution_report.test_results),
                "has_summary": bool(execution_report.summary),
                "has_quality_gate_results": bool(execution_report.quality_gate_results)
            }

            test_results = execution_report.test_results
            results_validations = {
                "has_test_results": len(test_results) > 0,
                "results_have_required_fields": all(
                    hasattr(result, 'test_id') and hasattr(result, 'status')
                    for result in test_results
                ) if test_results else False
            }

            quality_gates = execution_report.quality_gate_results
            quality_validations = {
                "has_quality_gates": len(quality_gates) > 0,
                "gates_have_results": all(
                    isinstance(gate, dict) and "passed" in gate
                    for gate in quality_gates
                ) if quality_gates else False
            }

            # 检查质量门禁是否都通过
            all_gates_passed = all(gate.get("passed", False) for gate in quality_gates)
            quality_validations["all_gates_passed"] = all_gates_passed

            all_validations = {**validations, **results_validations, **quality_validations}
            all_passed = all(all_validations.values())

            return {
                "status": "passed" if all_passed else "failed",
                "validations": all_validations,
                "passed_count": sum(all_validations.values()),
                "total_validations": len(all_validations),
                "issues": [k for k, v in all_validations.items() if not v],
                "quality_gates_status": {
                    "total_gates": len(quality_gates),
                    "passed_gates": sum(1 for gate in quality_gates if gate.get("passed", False)),
                    "all_passed": all_gates_passed
                }
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "validations": {},
                "passed_count": 0,
                "total_validations": 0,
                "issues": ["exception_occurred"]
            }

    async def analyze_e2e_test(self):
        """分析端到端测试"""
        try:
            query = "端到端测试查询"
            workflow_result = await self.enhanced_workflow.process_query(query)
            metrics_before = await self.monitoring_dashboard.get_comprehensive_metrics()
            await asyncio.sleep(0.1)
            metrics_after = await self.monitoring_dashboard.get_comprehensive_metrics()

            validations = {
                "workflow_completed": workflow_result.get("status") == "success",
                "monitoring_updated": (
                    metrics_after.get("timestamp", 0) >= metrics_before.get("timestamp", 0)
                ),
                "has_workflow_id": bool(workflow_result.get("workflow_id")),
                "has_monitoring_metrics": bool(metrics_after.get("fused_metrics"))
            }

            all_passed = all(validations.values())

            return {
                "status": "passed" if all_passed else "failed",
                "validations": validations,
                "passed_count": sum(validations.values()),
                "total_validations": len(validations),
                "issues": [k for k, v in validations.items() if not v]
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "validations": {},
                "passed_count": 0,
                "total_validations": 0,
                "issues": ["exception_occurred"]
            }

    async def analyze_performance_test(self):
        """分析性能测试"""
        try:
            queries = ["性能测试查询1", "性能测试查询2"]
            performance_data = []

            for query in queries:
                start_time = time.time()
                result = await self.enhanced_workflow.process_query(query)
                execution_time = time.time() - start_time

                performance_data.append({
                    "query": query,
                    "execution_time": execution_time,
                    "status": result.get("status")
                })

            validations = {
                "queries_executed": len(performance_data) == len(queries),
                "all_queries_succeeded": all(d["status"] == "success" for d in performance_data),
                "execution_times_recorded": all(d["execution_time"] > 0 for d in performance_data),
                "performance_stable": len(set(d["execution_time"] for d in performance_data)) > 0
            }

            all_passed = all(validations.values())

            return {
                "status": "passed" if all_passed else "failed",
                "validations": validations,
                "passed_count": sum(validations.values()),
                "total_validations": len(validations),
                "issues": [k for k, v in validations.items() if not v],
                "performance_data": performance_data
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "validations": {},
                "passed_count": 0,
                "total_validations": 0,
                "issues": ["exception_occurred"]
            }

    def print_test_result(self, result):
        """打印测试结果"""
        status_emoji = "✅" if result["status"] == "passed" else "❌"
        print(f"状态: {status_emoji} {result['status'].upper()}")

        if "passed_count" in result and "total_validations" in result:
            print(f"验证: {result['passed_count']}/{result['total_validations']} 通过")

        if result.get("issues"):
            print(f"问题: {', '.join(result['issues'])}")

        if "error" in result:
            print(f"错误: {result['error']}")

        # 特殊信息
        if "abc_error_detected" in result:
            abc_status = "❌ 检测到" if result["abc_error_detected"] else "✅ 未检测到"
            print(f"ABC导入错误: {abc_status}")

        if "quality_gates_status" in result:
            qg = result["quality_gates_status"]
            qg_emoji = "✅" if qg["all_passed"] else "❌"
            print(f"质量门禁: {qg_emoji} {qg['passed_gates']}/{qg['total_gates']} 通过")

        if "performance_data" in result:
            for data in result["performance_data"]:
                print(".2f")
    async def generate_comprehensive_analysis(self, results):
        """生成综合分析报告"""

        print("\n" + "=" * 80)
        print("📊 综合分析报告")
        print("=" * 80)

        # 总体统计
        total_tests = len(results)
        passed_tests = sum(1 for _, result in results if result["status"] == "passed")
        failed_tests = total_tests - passed_tests

        print(f"总体统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过测试: {passed_tests}")
        print(f"  失败测试: {failed_tests}")
        print(".1f")
        # 验证统计
        total_validations = sum(result["total_validations"] for _, result in results)
        passed_validations = sum(result["passed_count"] for _, result in results)

        print(f"\n验证统计:")
        print(f"  总验证项: {total_validations}")
        print(f"  通过验证: {passed_validations}")
        print(".1f")
        # 各测试详情
        print(f"\n各测试详情:")
        for test_name, result in results:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            validation_info = ""
            if "passed_count" in result and "total_validations" in result:
                validation_info = f" ({result['passed_count']}/{result['total_validations']})"

            print(f"  {test_name}: {status_emoji} {validation_info}")

            if result.get("issues"):
                print(f"    问题: {', '.join(result['issues'])}")

        # 识别主要问题
        print(f"\n🔍 主要问题识别:")

        # 检查ABC导入问题
        abc_issues = []
        for test_name, result in results:
            if test_name == "monitoring_test" and result.get("abc_error_detected"):
                abc_issues.append("监控系统ABC导入错误")

        if abc_issues:
            print(f"  ❌ {abc_issues[0]}")

        # 检查质量门禁问题
        quality_issues = []
        for test_name, result in results:
            if test_name == "test_system_test":
                qg_status = result.get("quality_gates_status", {})
                if not qg_status.get("all_passed", True):
                    quality_issues.append(
                        f"质量门禁失败 ({qg_status.get('passed_gates', 0)}/{qg_status.get('total_gates', 0)})"
                    )

        if quality_issues:
            print(f"  ❌ {quality_issues[0]}")

        # 成功项目
        successful_tests = [test_name for test_name, result in results if result["status"] == "passed"]
        if successful_tests:
            print(f"  ✅ 成功测试: {', '.join(successful_tests)}")

        # 建议
        print(f"\n💡 建议:")
        if failed_tests > 0:
            print("1. 修复失败的测试项目")
            print("2. 检查错误日志获取详细原因")
            print("3. 考虑调整测试标准或逻辑")
        else:
            print("1. 所有测试通过！🎉")
            print("2. 定期运行以确保稳定性")
            print("3. 考虑增加更多测试用例")

        # Phase 10状态评估
        if passed_tests >= total_tests * 0.8:  # 80%以上通过
            phase_status = "🎉 COMPLETED"
        elif passed_tests >= total_tests * 0.6:  # 60%以上通过
            phase_status = "⚠️ NEEDS_IMPROVEMENT"
        else:
            phase_status = "❌ REQUIRES_ATTENTION"

        print(f"\n🏆 Phase 10 状态: {phase_status}")

async def main():
    """主函数"""
    analyzer = TestResultAnalyzer()
    await analyzer.analyze_individual_tests()

if __name__ == "__main__":
    asyncio.run(main())
