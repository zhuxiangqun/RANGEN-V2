#!/usr/bin/env python3
"""
自动化系统验证器

定期验证系统各组件的健康状态和功能完整性
支持定时执行和报告生成
"""

import asyncio
import logging
import time
import json
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入系统组件
from src.core.enhanced_simplified_workflow import get_enhanced_simplified_workflow
from src.core.langgraph_monitoring_adapter import get_unified_monitoring_dashboard
from src.core.unified_test_orchestrator import get_unified_test_orchestrator


class ValidationResult:
    """验证结果"""

    def __init__(self, component: str, status: str, details: Dict[str, Any]):
        self.component = component
        self.status = status  # "healthy", "warning", "error"
        self.details = details
        self.timestamp = time.time()


class AutomatedSystemValidator:
    """自动化系统验证器"""

    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 加载配置
        self.config = self._load_config(config_file)

        # 初始化组件
        self.workflow = get_enhanced_simplified_workflow()
        self.monitoring = get_unified_monitoring_dashboard()
        self.test_orchestrator = get_unified_test_orchestrator()

        # 验证历史
        self.validation_history: List[ValidationResult] = []
        self.last_validation_time = 0

        # 告警配置
        self.alert_thresholds = {
            "error_count": 2,  # 错误数量阈值
            "response_time": 10.0,  # 响应时间阈值（秒）
            "success_rate": 0.8  # 成功率阈值
        }

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "validation_interval": 3600,  # 1小时
            "enable_email_alerts": False,
            "email_config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": []
            },
            "report_directory": "reports/validation",
            "log_level": "INFO"
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"无法加载配置文件 {config_file}: {e}")

        return default_config

    async def run_full_validation(self) -> Dict[str, Any]:
        """运行完整验证"""

        self.logger.info("🚀 开始系统完整验证")
        start_time = time.time()

        validation_results = []

        try:
            # 1. 工作流组件验证
            workflow_result = await self._validate_workflow_component()
            validation_results.append(workflow_result)

            # 2. 监控系统验证
            monitoring_result = await self._validate_monitoring_component()
            validation_results.append(monitoring_result)

            # 3. 测试系统验证
            test_result = await self._validate_test_component()
            validation_results.append(test_result)

            # 4. 端到端集成验证
            integration_result = await self._validate_integration()
            validation_results.append(integration_result)

            # 5. 性能验证
            performance_result = await self._validate_performance()
            validation_results.append(performance_result)

            # 计算总体状态
            overall_status = self._calculate_overall_status(validation_results)

            # 生成报告
            report = self._generate_validation_report(
                validation_results, overall_status, time.time() - start_time
            )

            # 保存验证历史
            for result in validation_results:
                self.validation_history.append(result)

            # 限制历史记录数量
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]

            self.last_validation_time = time.time()

            # 发送告警（如果需要）
            await self._send_alerts_if_needed(report)

            # 保存报告
            self._save_report(report)

            self.logger.info(f"✅ 系统验证完成，状态: {overall_status}")

            return report

        except Exception as e:
            error_report = {
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "duration": time.time() - start_time
            }
            self.logger.error(f"❌ 系统验证失败: {e}")
            return error_report

    async def _validate_workflow_component(self) -> ValidationResult:
        """验证工作流组件"""

        try:
            # 测试基本查询处理
            test_queries = ["验证查询1", "验证查询2", "验证查询3"]
            results = []

            for query in test_queries:
                start_time = time.time()
                result = await self.workflow.process_query(query)
                execution_time = time.time() - start_time

                results.append({
                    "query": query,
                    "status": result.get("status"),
                    "execution_time": execution_time,
                    "success": result.get("status") == "success"
                })

            # 分析结果
            success_count = sum(1 for r in results if r["success"])
            avg_execution_time = sum(r["execution_time"] for r in results) / len(results)
            max_execution_time = max(r["execution_time"] for r in results)

            success_rate = success_count / len(results)

            # 确定状态
            if success_rate >= 0.9 and avg_execution_time < 5.0:
                status = "healthy"
            elif success_rate >= 0.7 or avg_execution_time < 10.0:
                status = "warning"
            else:
                status = "error"

            details = {
                "total_queries": len(test_queries),
                "successful_queries": success_count,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "max_execution_time": max_execution_time,
                "results": results
            }

            return ValidationResult("workflow", status, details)

        except Exception as e:
            return ValidationResult("workflow", "error", {"error": str(e)})

    async def _validate_monitoring_component(self) -> ValidationResult:
        """验证监控组件"""

        try:
            # 获取监控指标
            metrics = await self.monitoring.get_comprehensive_metrics()
            alerts = await self.monitoring.get_unified_alerts()

            # 检查指标完整性
            required_metrics = ["fused_metrics", "source_breakdown", "health_status"]
            metrics_complete = all(key in metrics for key in required_metrics)

            # 检查告警数量
            alert_count = len(alerts)
            critical_alerts = len([a for a in alerts if a.get("severity") == "critical"])

            # 确定状态
            if metrics_complete and critical_alerts == 0 and alert_count < 5:
                status = "healthy"
            elif metrics_complete and critical_alerts <= 1:
                status = "warning"
            else:
                status = "error"

            details = {
                "metrics_available": metrics_complete,
                "total_alerts": alert_count,
                "critical_alerts": critical_alerts,
                "health_status": metrics.get("health_status", "unknown"),
                "fused_metrics_count": len(metrics.get("fused_metrics", {}))
            }

            return ValidationResult("monitoring", status, details)

        except Exception as e:
            return ValidationResult("monitoring", "error", {"error": str(e)})

    async def _validate_test_component(self) -> ValidationResult:
        """验证测试组件"""

        try:
            # 运行简化的测试套件
            mini_suite = self.test_orchestrator.create_comprehensive_test_suite()
            mini_suite.test_cases = mini_suite.test_cases[:2]  # 只运行前2个测试

            execution_report = await self.test_orchestrator.execute_test_suite(mini_suite)

            # 分析测试结果
            test_results = execution_report.test_results
            successful_tests = len([r for r in test_results if r.status.name == "PASSED"])
            total_tests = len(test_results)

            success_rate = successful_tests / total_tests if total_tests > 0 else 0

            # 检查质量门禁
            quality_gates = execution_report.quality_gate_results
            gates_passed = sum(1 for gate in quality_gates if gate.get("passed", False))
            total_gates = len(quality_gates)

            # 确定状态
            if success_rate >= 0.8 and gates_passed == total_gates:
                status = "healthy"
            elif success_rate >= 0.5 or gates_passed >= total_gates * 0.5:
                status = "warning"
            else:
                status = "error"

            details = {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "quality_gates_passed": gates_passed,
                "total_quality_gates": total_gates,
                "execution_time": execution_report.total_duration
            }

            return ValidationResult("test_system", status, details)

        except Exception as e:
            return ValidationResult("test_system", "error", {"error": str(e)})

    async def _validate_integration(self) -> ValidationResult:
        """验证集成"""

        try:
            # 执行端到端流程测试
            query = "集成验证查询"
            workflow_result = await self.workflow.process_query(query)

            if workflow_result.get("status") != "success":
                return ValidationResult("integration", "error", {
                    "error": "工作流执行失败",
                    "workflow_status": workflow_result.get("status")
                })

            # 检查监控数据更新
            metrics_before = await self.monitoring.get_comprehensive_metrics()
            await asyncio.sleep(0.1)
            metrics_after = await self.monitoring.get_comprehensive_metrics()

            monitoring_updated = (
                metrics_after.get("timestamp", 0) > metrics_before.get("timestamp", 0)
            )

            # 确定状态
            if workflow_result.get("status") == "success" and monitoring_updated:
                status = "healthy"
            elif workflow_result.get("status") == "success":
                status = "warning"
            else:
                status = "error"

            details = {
                "workflow_success": workflow_result.get("status") == "success",
                "monitoring_updated": monitoring_updated,
                "execution_time": workflow_result.get("execution_time", 0),
                "quality_score": workflow_result.get("quality_score", 0)
            }

            return ValidationResult("integration", status, details)

        except Exception as e:
            return ValidationResult("integration", "error", {"error": str(e)})

    async def _validate_performance(self) -> ValidationResult:
        """验证性能"""

        try:
            # 执行性能测试
            queries = ["性能查询1", "性能查询2", "性能查询3"]
            execution_times = []

            for query in queries:
                start_time = time.time()
                result = await self.workflow.process_query(query)
                execution_time = time.time() - start_time
                execution_times.append(execution_time)

            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)

            # 检查性能阈值
            within_threshold = avg_time < self.alert_thresholds["response_time"]

            # 确定状态
            if within_threshold and max_time < self.alert_thresholds["response_time"] * 1.5:
                status = "healthy"
            elif within_threshold:
                status = "warning"
            else:
                status = "error"

            details = {
                "avg_response_time": avg_time,
                "max_response_time": max_time,
                "min_response_time": min_time,
                "within_threshold": within_threshold,
                "threshold": self.alert_thresholds["response_time"],
                "queries_tested": len(queries)
            }

            return ValidationResult("performance", status, details)

        except Exception as e:
            return ValidationResult("performance", "error", {"error": str(e)})

    def _calculate_overall_status(self, results: List[ValidationResult]) -> str:
        """计算总体状态"""

        if not results:
            return "unknown"

        status_counts = {"healthy": 0, "warning": 0, "error": 0}

        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        if status_counts["error"] > 0:
            return "error"
        elif status_counts["warning"] > len(results) * 0.3:  # 30%以上是警告
            return "warning"
        else:
            return "healthy"

    def _generate_validation_report(
        self, results: List[ValidationResult], overall_status: str, duration: float
    ) -> Dict[str, Any]:
        """生成验证报告"""

        report = {
            "timestamp": time.time(),
            "duration": duration,
            "overall_status": overall_status,
            "components": {}
        }

        for result in results:
            report["components"][result.component] = {
                "status": result.status,
                "details": result.details
            }

        # 添加统计信息
        status_summary = {}
        for result in results:
            status_summary[result.status] = status_summary.get(result.status, 0) + 1

        report["summary"] = {
            "total_components": len(results),
            "status_distribution": status_summary,
            "healthy_components": status_summary.get("healthy", 0),
            "warning_components": status_summary.get("warning", 0),
            "error_components": status_summary.get("error", 0)
        }

        # 添加建议
        report["recommendations"] = self._generate_recommendations(results, overall_status)

        return report

    def _generate_recommendations(self, results: List[ValidationResult], overall_status: str) -> List[str]:
        """生成建议"""

        recommendations = []

        if overall_status == "error":
            recommendations.append("🚨 系统存在严重问题，建议立即调查并修复")
        elif overall_status == "warning":
            recommendations.append("⚠️ 系统存在潜在问题，建议关注并监控")

        # 针对各组件的建议
        for result in results:
            if result.status == "error":
                if result.component == "workflow":
                    recommendations.append("修复工作流组件问题，检查查询处理逻辑")
                elif result.component == "monitoring":
                    recommendations.append("修复监控系统问题，检查指标收集和告警")
                elif result.component == "test_system":
                    recommendations.append("修复测试系统问题，检查测试用例和运行器")
                elif result.component == "integration":
                    recommendations.append("修复集成问题，检查组件间通信")
                elif result.component == "performance":
                    recommendations.append("修复性能问题，优化响应时间")

        if not recommendations:
            recommendations.append("✅ 系统运行正常，继续保持监控")

        return recommendations

    async def _send_alerts_if_needed(self, report: Dict[str, Any]):
        """发送告警（如果需要）"""

        if not self.config.get("enable_email_alerts", False):
            return

        overall_status = report.get("overall_status", "unknown")

        # 只在错误或警告状态下发送告警
        if overall_status not in ["error", "warning"]:
            return

        try:
            await self._send_email_alert(report)
        except Exception as e:
            self.logger.error(f"发送告警邮件失败: {e}")

    async def _send_email_alert(self, report: Dict[str, Any]):
        """发送邮件告警"""

        email_config = self.config.get("email_config", {})
        if not email_config.get("sender_email") or not email_config.get("recipient_emails"):
            return

        # 创建邮件内容
        subject = f"系统验证告警 - {report.get('overall_status', 'unknown').upper()}"

        body = f"""
系统自动化验证报告

状态: {report.get('overall_status', 'unknown').upper()}
时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.get('timestamp', 0)))}
验证耗时: {report.get('duration', 0):.2f}秒

组件状态:
"""

        for component, data in report.get("components", {}).items():
            body += f"- {component}: {data.get('status', 'unknown').upper()}\n"

        body += f"\n建议:\n"
        for rec in report.get("recommendations", []):
            body += f"- {rec}\n"

        # 发送邮件
        msg = MIMEMultipart()
        msg['From'] = email_config["sender_email"]
        msg['To'] = ", ".join(email_config["recipient_emails"])
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        text = msg.as_string()
        server.sendmail(email_config["sender_email"], email_config["recipient_emails"], text)
        server.quit()

        self.logger.info("✅ 告警邮件已发送")

    def _save_report(self, report: Dict[str, Any]):
        """保存报告"""

        report_dir = Path(self.config.get("report_directory", "reports/validation"))
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(report.get("timestamp", time.time())))
        report_file = report_dir / f"validation_report_{timestamp}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ 验证报告已保存: {report_file}")

            # 清理旧报告（保留最近10个）
            self._cleanup_old_reports(report_dir, 10)

        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

    def _cleanup_old_reports(self, report_dir: Path, keep_count: int):
        """清理旧报告"""

        try:
            report_files = list(report_dir.glob("validation_report_*.json"))
            report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            if len(report_files) > keep_count:
                for old_file in report_files[keep_count:]:
                    old_file.unlink()
                    self.logger.debug(f"清理旧报告: {old_file.name}")

        except Exception as e:
            self.logger.debug(f"清理旧报告失败: {e}")

    def start_periodic_validation(self):
        """启动定期验证"""

        interval_seconds = self.config.get("validation_interval", 3600)

        def validation_job():
            asyncio.run(self.run_full_validation())

        def periodic_task():
            while True:
                validation_job()
                time.sleep(interval_seconds)

        # 启动后台线程执行定期验证
        validation_thread = threading.Thread(target=periodic_task, daemon=True)
        validation_thread.start()

        self.logger.info(f"✅ 已启动定期验证，每 {interval_seconds} 秒执行一次")

        # 保持主线程运行
        try:
            while True:
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("🛑 收到中断信号，停止定期验证")

    def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取验证历史"""

        recent_results = self.validation_history[-limit:] if self.validation_history else []

        return [
            {
                "component": result.component,
                "status": result.status,
                "timestamp": result.timestamp,
                "details": result.details
            }
            for result in recent_results
        ]

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""

        if not self.validation_history:
            return {"status": "no_data", "message": "暂无验证数据"}

        # 计算最近5次验证的平均状态
        recent_results = self.validation_history[-5:] if len(self.validation_history) >= 5 else self.validation_history

        status_counts = {"healthy": 0, "warning": 0, "error": 0}

        for result in recent_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        # 确定整体健康状态
        total_results = len(recent_results)
        if status_counts["error"] > 0:
            overall_status = "unhealthy"
        elif status_counts["warning"] > total_results * 0.4:  # 40%以上是警告
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "last_validation": self.last_validation_time,
            "recent_validations": len(recent_results),
            "status_distribution": status_counts,
            "health_score": (status_counts["healthy"] * 1.0 + status_counts["warning"] * 0.5) / total_results
        }


# 全局验证器实例
_validator_instance = None

def get_system_validator(config_file: Optional[str] = None) -> AutomatedSystemValidator:
    """获取系统验证器实例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = AutomatedSystemValidator(config_file)
    return _validator_instance

async def run_validation_check():
    """运行验证检查（用于命令行调用）"""
    validator = get_system_validator()
    report = await validator.run_full_validation()

    print("\n" + "="*60)
    print("📊 系统验证报告")
    print("="*60)

    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "error": "❌",
        "unknown": "❓"
    }

    overall_status = report.get("overall_status", "unknown")
    print(f"总体状态: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
    print(".2f")

    # 组件状态
    components = report.get("components", {})
    print(f"\n组件状态:")
    for component, data in components.items():
        comp_status = data.get("status", "unknown")
        emoji = status_emoji.get(comp_status, "❓")
        print(f"  {component}: {emoji} {comp_status.upper()}")

    # 统计信息
    summary = report.get("summary", {})
    print(f"\n统计信息:")
    print(f"  总组件数: {summary.get('total_components', 0)}")
    print(f"  健康组件: {summary.get('healthy_components', 0)}")
    print(f"  警告组件: {summary.get('warning_components', 0)}")
    print(f"  错误组件: {summary.get('error_components', 0)}")

    # 建议
    recommendations = report.get("recommendations", [])
    if recommendations:
        print(f"\n💡 建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    return report

if __name__ == "__main__":
    # 命令行运行验证
    import argparse

    parser = argparse.ArgumentParser(description="自动化系统验证器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--periodic", action="store_true", help="启动定期验证")
    parser.add_argument("--once", action="store_true", help="执行一次性验证")

    args = parser.parse_args()

    if args.periodic:
        print("🚀 启动定期系统验证...")
        validator = get_system_validator(args.config)
        validator.start_periodic_validation()
    elif args.once or len(sys.argv) == 1:
        print("🔍 执行一次性系统验证...")
        asyncio.run(run_validation_check())
    else:
        parser.print_help()
