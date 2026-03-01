#!/usr/bin/env python3
"""
启动Agent迁移稳定性监控
"""

import asyncio
import sys
import time
import signal
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.agent_migration_monitoring import (
    start_migration_monitoring,
    stop_migration_monitoring,
    generate_stability_report,
    get_monitoring_summary
)


async def main():
    """主函数"""
    print("🚀 启动Agent迁移稳定性监控")
    print("=" * 60)

    # 启动监控
    print("📊 正在启动监控系统...")
    await start_migration_monitoring()

    # 设置信号处理器
    def signal_handler(signum, frame):
        print("\n🛑 收到停止信号，正在关闭监控...")
        stop_migration_monitoring()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ 监控系统已启动")
    print("📋 监控项目:")
    print("   • 逐步替换Agent的性能表现")
    print("   • 替换率变化趋势")
    print("   • 系统资源使用情况")
    print("   • 错误率和异常检测")
    print("   • 稳定性评分计算")
    print("\n🎯 按 Ctrl+C 停止监控并生成报告")

    try:
        while True:
            # 每小时生成一次稳定性报告
            await asyncio.sleep(3600)  # 1小时

            print("\n📊 生成稳定性报告...")
            report = await generate_stability_report()

            if report:
                print(".1f")
                print(f"   🔍 监控Agent数量: {report.total_agents_monitored}")
                print(f"   ⚠️  有问题的Agent: {report.agents_with_issues}")

                if report.agents_with_issues > 0:
                    print("   📋 建议:")
                    for rec in report.recommendations[:3]:  # 只显示前3条建议
                        print(f"      • {rec}")

                print(f"   📁 报告已保存: reports/migration_monitoring/stability_report_{report.report_id}.json")
            else:
                print("   ❌ 生成报告失败")

    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在生成最终报告...")

    # 生成最终报告
    print("📊 生成最终稳定性报告...")
    final_report = await generate_stability_report()

    if final_report:
        print("🎉 最终报告生成完成！")
        print(f"📁 报告文件: reports/migration_monitoring/stability_report_{final_report.report_id}.json")

        # 显示摘要
        print("\n📋 监控摘要:")
        summary = get_monitoring_summary()
        print(f"   监控Agent: {len(summary['agents_monitored'])}")
        print(f"   生成报告: {summary['total_reports']}")
        print(f"   数据目录: {summary['data_directory']}")

    # 停止监控
    stop_migration_monitoring()
    print("✅ 监控系统已安全关闭")


if __name__ == "__main__":
    asyncio.run(main())
