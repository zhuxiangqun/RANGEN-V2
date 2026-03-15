#!/usr/bin/env python3
"""
系统卡顿诊断工具
专门用于诊断和找出系统卡顿的真正原因
"""

import asyncio
import time
import logging
import threading
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import sys

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.system_performance_optimizer import get_global_optimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    active_threads: int
    active_processes: int

@dataclass
class BottleneckInfo:
    """瓶颈信息"""
    type: str
    severity: str
    description: str
    recommendation: str
    metrics: Dict[str, Any]

class SystemPerformanceDiagnostic:
    """系统性能诊断器"""

    def __init__(self):
        self.optimizer = get_global_optimizer()
        self.snapshots: List[PerformanceSnapshot] = []
        self.bottlenecks: List[BottleneckInfo] = []
        self.monitoring = False
        self._monitor_thread = None

    async def start_monitoring(self, duration: int = 60, interval: float = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))):
        """开始性能监控"""
        logger.info(f"🚀 开始性能监控，持续{duration}秒，间隔{interval}秒")
        self.monitoring = True

        start_time = time.time()
        while self.monitoring and (time.time() - start_time) < duration:
            snapshot = await self._take_performance_snapshot()
            self.snapshots.append(snapshot)

            # 实时分析瓶颈
            await self._analyze_bottlenecks(snapshot)

            await asyncio.sleep(interval)

        self.monitoring = False
        logger.info("✅ 性能监控完成")

    async def _take_performance_snapshot(self) -> PerformanceSnapshot:
        """获取性能快照"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘I/O
            disk_io = psutil.disk_io_counters()
            disk_io_dict = {
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            }

            # 网络I/O
            network_io = psutil.net_io_counters()
            network_io_dict = {
                'bytes_sent': network_io.bytes_sent if network_io else 0,
                'bytes_recv': network_io.bytes_recv if network_io else 0,
                'packets_sent': network_io.packets_sent if network_io else 0,
                'packets_recv': network_io.packets_recv if network_io else 0
            }

            # 线程和进程数
            current_process = psutil.Process()
            active_threads = current_process.num_threads()
            active_processes = len(psutil.pids())

            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io=disk_io_dict,
                network_io=network_io_dict,
                active_threads=active_threads,
                active_processes=active_processes
            )

        except Exception as e:
            logger.error(f"获取性能快照失败: {e}")
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                memory_percent=get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                disk_io={},
                network_io={},
                active_threads=0,
                active_processes=0
            )

    async def _analyze_bottlenecks(self, snapshot: PerformanceSnapshot):
        """分析性能瓶颈"""
        bottlenecks = []

        # CPU瓶颈检测
        if snapshot.cpu_percent > 80:
            bottlenecks.append(BottleneckInfo(
                type="CPU",
                severity="HIGH" if snapshot.cpu_percent > 90 else "MEDIUM",
                description=f"CPU使用率过高: {snapshot.cpu_percent:.1f}%",
                recommendation="检查是否有CPU密集型任务或死循环",
                metrics={"cpu_percent": snapshot.cpu_percent}
            ))

        # 内存瓶颈检测
        if snapshot.memory_percent > 85:
            bottlenecks.append(BottleneckInfo(
                type="MEMORY",
                severity="HIGH" if snapshot.memory_percent > 95 else "MEDIUM",
                description=f"内存使用率过高: {snapshot.memory_percent:.1f}%",
                recommendation="检查内存泄漏或优化内存使用",
                metrics={"memory_percent": snapshot.memory_percent}
            ))

        # 线程瓶颈检测
        if snapshot.active_threads > get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")):
            bottlenecks.append(BottleneckInfo(
                type="THREADS",
                severity="MEDIUM",
                description=f"活跃线程数过多: {snapshot.active_threads}",
                recommendation="检查线程池配置和线程泄漏",
                metrics={"active_threads": snapshot.active_threads}
            ))

        # 磁盘I/O瓶颈检测
        if snapshot.disk_io.get('read_count', 0) > 1000 or snapshot.disk_io.get('write_count', 0) > 1000:
            bottlenecks.append(BottleneckInfo(
                type="DISK_IO",
                severity="MEDIUM",
                description="磁盘I/O操作频繁",
                recommendation="检查文件操作和数据库查询",
                metrics=snapshot.disk_io
            ))

        # 添加到瓶颈列表
        self.bottlenecks.extend(bottlenecks)

        # 实时报告严重瓶颈
        for bottleneck in bottlenecks:
            if bottleneck.severity == "HIGH":
                logger.warning(f"🚨 检测到严重瓶颈: {bottleneck.description}")

    async def diagnose_specific_operations(self):
        """诊断特定操作的性能"""
        logger.info("🔍 开始诊断特定操作性能...")

        # 诊断FAISS操作
        await self._diagnose_faiss_operations()

        # 诊断智能体操作
        await self._diagnose_agent_operations()

        # 诊断异步操作
        await self._diagnose_async_operations()

    async def _diagnose_faiss_operations(self):
        """诊断FAISS操作性能"""
        logger.info("📚 诊断FAISS操作...")

        try:
            from memory.enhanced_faiss_memory import EnhancedFAISSMemory

            # 创建测试实例
            faiss_memory = EnhancedFAISSMemory(dimension=384)

            # 测试初始化性能
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    faiss_memory.ensure_index_ready(),
                    timeout=10.0
                )
                init_time = time.time() - start_time
                logger.info(f"✅ FAISS初始化耗时: {init_time:.2f}秒")

                if init_time > 5.0:
                    self.bottlenecks.append(BottleneckInfo(
                        type="FAISS_INIT",
                        severity="MEDIUM",
                        description=f"FAISS初始化过慢: {init_time:.2f}秒",
                        recommendation="优化FAISS索引构建，考虑异步初始化",
                        metrics={"init_time": init_time}
                    ))

            except asyncio.TimeoutError:
                self.bottlenecks.append(BottleneckInfo(
                    type="FAISS_INIT",
                    severity="HIGH",
                    description="FAISS初始化超时",
                    recommendation="检查FAISS配置和索引文件",
                    metrics={"init_time": "timeout"}
                ))

        except Exception as e:
            logger.error(f"FAISS诊断失败: {e}")

    async def _diagnose_agent_operations(self):
        """诊断智能体操作性能"""
        logger.info("🤖 诊断智能体操作...")

        try:
            from agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent

            # 创建测试实例
            agent = EnhancedKnowledgeRetrievalAgent()

            # 测试执行性能
            test_context = {"query": "test query", "type": "knowledge_retrieval"}

            start_time = time.time()
            try:
                result = await asyncio.wait_for(
                    agent.execute(test_context),
                    timeout=15.0
                )
                exec_time = time.time() - start_time
                logger.info(f"✅ 知识检索智能体执行耗时: {exec_time:.2f}秒")

                if exec_time > 10.0:
                    self.bottlenecks.append(BottleneckInfo(
                        type="AGENT_EXECUTION",
                        severity="MEDIUM",
                        description=f"智能体执行过慢: {exec_time:.2f}秒",
                        recommendation="优化智能体逻辑，减少不必要的计算",
                        metrics={"execution_time": exec_time}
                    ))

            except asyncio.TimeoutError:
                self.bottlenecks.append(BottleneckInfo(
                    type="AGENT_EXECUTION",
                    severity="HIGH",
                    description="智能体执行超时",
                    recommendation="检查智能体逻辑和依赖",
                    metrics={"execution_time": "timeout"}
                ))

        except Exception as e:
            logger.error(f"智能体诊断失败: {e}")

    async def _diagnose_async_operations(self):
        """诊断异步操作性能"""
        logger.info("⚡ 诊断异步操作...")

        # 测试异步任务调度性能
        async def test_task():
            await asyncio.sleep(0.1)
            return "test"

        # 测试并发性能
        start_time = time.time()
        tasks = [test_task() for _ in range(get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")))]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        logger.info(f"✅ 100个并发任务耗时: {concurrent_time:.2f}秒")

        if concurrent_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")):
            self.bottlenecks.append(BottleneckInfo(
                type="ASYNC_SCHEDULING",
                severity="MEDIUM",
                description=f"异步调度性能较差: {concurrent_time:.2f}秒",
                recommendation="检查事件循环配置和任务调度",
                metrics={"concurrent_time": concurrent_time}
            ))

    def generate_diagnosis_report(self) -> str:
        """生成诊断报告"""
        report = []
        report.append("# 🚨 系统性能诊断报告")
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"快照数量: {len(self.snapshots)}")
        report.append(f"检测到的瓶颈: {len(self.bottlenecks)}")
        report.append("")

        # 性能快照摘要
        if self.snapshots:
            report.append("## 📊 性能快照摘要")
            cpu_values = [s.cpu_percent for s in self.snapshots]
            memory_values = [s.memory_percent for s in self.snapshots]

            report.append(f"- CPU使用率: 平均 {sum(cpu_values)/len(cpu_values):.1f}%, 最高 {max(cpu_values):.1f}%")
            report.append(f"- 内存使用率: 平均 {sum(memory_values)/len(memory_values):.1f}%, 最高 {max(memory_values):.1f}%")
            report.append("")

        # 瓶颈详情
        if self.bottlenecks:
            report.append("## 🚨 检测到的瓶颈")

            # 按类型分组
            bottlenecks_by_type = {}
            for bottleneck in self.bottlenecks:
                if bottleneck.type not in bottlenecks_by_type:
                    bottlenecks_by_type[bottleneck.type] = []
                bottlenecks_by_type[bottleneck.type].append(bottleneck)

            for bottleneck_type, bottlenecks in bottlenecks_by_type.items():
                report.append(f"### {bottleneck_type}")
                for bottleneck in bottlenecks:
                    severity_emoji = "🔴" if bottleneck.severity == "HIGH" else "🟡"
                    report.append(f"{severity_emoji} **{bottleneck.severity}**: {bottleneck.description}")
                    report.append(f"   💡 建议: {bottleneck.recommendation}")
                    report.append("")

        # 优化建议
        report.append("## 💡 总体优化建议")
        report.append("1. **避免同步等待**: 将同步操作包装在线程池中执行")
        report.append("2. **超时控制**: 为所有异步操作设置合理的超时时间")
        report.append("3. **资源管理**: 及时释放不再使用的资源")
        report.append("4. **异步优化**: 使用异步I/O和并发执行")
        report.append("5. **监控告警**: 建立实时性能监控和告警机制")

        return "\n".join(report)

    async def run_comprehensive_diagnosis(self, duration: int = 60):
        """运行全面诊断"""
        logger.info("🔍 开始全面性能诊断...")

        # 1. 启动性能监控
        monitor_task = asyncio.create_task(self.start_monitoring(duration))

        # 2. 运行特定操作诊断
        diagnosis_task = asyncio.create_task(self.diagnose_specific_operations())

        # 3. 等待所有任务完成
        await asyncio.gather(monitor_task, diagnosis_task)

        # 4. 生成报告
        report = self.generate_diagnosis_report()

        # 5. 保存报告
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_diagnosis_report_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 诊断完成，报告已保存到: {report_file}")

        # 6. 打印摘要
        print("\n" + "="*50)
        print("🚨 性能诊断摘要")
        print("="*50)
        print(f"检测到的瓶颈数量: {len(self.bottlenecks)}")

        high_severity = len([b for b in self.bottlenecks if b.severity == "HIGH"])
        if high_severity > 0:
            print(f"🔴 严重瓶颈: {high_severity}")

        medium_severity = len([b for b in self.bottlenecks if b.severity == "MEDIUM"])
        if medium_severity > 0:
            print(f"🟡 中等瓶颈: {medium_severity}")

        print(f"详细报告: {report_file}")
        print("="*50)

        return report

async def main():
    """主函数"""
    logger.info("🚀 启动系统性能诊断工具")

    # 创建诊断器
    diagnostic = SystemPerformanceDiagnostic()

    try:
        # 运行全面诊断
        await diagnostic.run_comprehensive_diagnosis(duration=30)  # 30秒诊断

    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断诊断")
    except Exception as e:
        logger.error(f"❌ 诊断过程中出现错误: {e}")
    finally:
        logger.info("✅ 诊断工具退出")

if __name__ == "__main__":
    asyncio.run(main())
