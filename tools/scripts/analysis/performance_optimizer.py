#!/usr/bin/env python3
"""
性能优化脚本 - 自动分析和优化系统性能
基于监控数据提供智能优化建议
"""

import os
import sys
import json
import time
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import gc

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.utils.unified_monitoring_center import get_unified_monitoring_center
from src.utils.smart_cache import get_smart_cache
from src.utils.memory_optimizer import get_memory_optimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.monitoring_center = get_unified_monitoring_center()
        self.cache = get_smart_cache()
        self.memory_optimizer = get_memory_optimizer()

        # 性能基准
        self.baselines = {
            "response_time": 2000,  # ms
            "memory_usage": 80.0,   # %
            "cpu_usage": 70.0,      # %
            "cache_hit_rate": get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))   # 80%
        }

    async def run_optimization(self) -> Dict[str, Any]:
        """运行性能优化"""
        logger.info("🚀 开始性能优化分析...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "analysis": {},
            "recommendations": [],
            "actions_taken": [],
            "improvements": {}
        }

        try:
            # 1. 系统性能分析
            results["analysis"]["system"] = await self._analyze_system_performance()

            # 2. 缓存性能分析
            results["analysis"]["cache"] = self._analyze_cache_performance()

            # 3. 内存使用分析
            results["analysis"]["memory"] = self._analyze_memory_usage()

            # 4. 生成优化建议
            results["recommendations"] = self._generate_recommendations(
                results["analysis"]
            )

            # 5. 自动执行优化
            results["actions_taken"] = await self._execute_optimizations(
                results["recommendations"]
            )

            # 6. 验证优化效果
            results["improvements"] = await self._measure_improvements()

            logger.info("✅ 性能优化完成")

        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            results["error"] = str(e)

        return results

    async def _analyze_system_performance(self) -> Dict[str, Any]:
        """分析系统性能"""
        try:
            # 获取系统指标
            system_metrics = self.monitoring_center.get_system_metrics()

            analysis = {
                "cpu_usage": system_metrics.get("cpu_percent", 0),
                "memory_usage": system_metrics.get("memory_percent", 0),
                "disk_usage": system_metrics.get("disk_percent", 0),
                "network_io": system_metrics.get("network_io", {}),
                "load_average": system_metrics.get("load_average", []),
                "status": "healthy"
            }

            # 评估状态
            if analysis["cpu_usage"] > self.baselines["cpu_usage"]:
                analysis["status"] = "warning"
            if analysis["memory_usage"] > self.baselines["memory_usage"]:
                analysis["status"] = "critical"

            return analysis

        except Exception as e:
            logger.error(f"系统性能分析失败: {e}")
            return {"error": str(e)}

    def _analyze_cache_performance(self) -> Dict[str, Any]:
        """分析缓存性能"""
        try:
            cache_stats = self.cache.get_stats()

            analysis = {
                "hit_rate": cache_stats.get("hit_rate", 0),
                "total_requests": cache_stats.get("hits", 0) + cache_stats.get("misses", 0),
                "memory_usage": cache_stats.get("memory_usage", 0),
                "disk_usage": cache_stats.get("disk_usage", 0),
                "efficiency": "good"
            }

            # 评估效率
            if analysis["hit_rate"] < self.baselines["cache_hit_rate"]:
                analysis["efficiency"] = "poor"
            elif analysis["hit_rate"] < 0.6:
                analysis["efficiency"] = "fair"

            return analysis

        except Exception as e:
            logger.error(f"缓存性能分析失败: {e}")
            return {"error": str(e)}

    def _analyze_memory_usage(self) -> Dict[str, Any]:
        """分析内存使用"""
        try:
            memory_info = psutil.virtual_memory()

            analysis = {
                "total_gb": memory_info.total / (1024**3),
                "available_gb": memory_info.available / (1024**3),
                "used_gb": memory_info.used / (1024**3),
                "usage_percent": memory_info.percent,
                "status": "normal"
            }

            # 内存分析
            if analysis["usage_percent"] > 90:
                analysis["status"] = "critical"
            elif analysis["usage_percent"] > 80:
                analysis["status"] = "warning"

            # 获取Top内存对象
            analysis["top_objects"] = self._get_top_memory_objects()

            return analysis

        except Exception as e:
            logger.error(f"内存分析失败: {e}")
            return {"error": str(e)}

    def _get_top_memory_objects(self, limit: int = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))) -> List[Dict[str, Any]]:
        """获取占用内存最多的对象"""
        try:
            import tracemalloc
            if not tracemalloc.is_tracing():
                tracemalloc.start()

            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')[:limit]

            top_objects = []
            for stat in top_stats:
                top_objects.append({
                    "file": stat.traceback[0].filename,
                    "line": stat.traceback[0].lineno,
                    "size_mb": stat.size / (1024**2),
                    "count": stat.count
                })

            return top_objects

        except Exception:
            return []

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        # CPU优化建议
        system_analysis = analysis.get("system", {})
        if system_analysis.get("cpu_usage", 0) > self.baselines["cpu_usage"]:
            recommendations.append({
                "type": "cpu_optimization",
                "priority": "high",
                "title": "CPU使用率过高",
                "description": f"当前CPU使用率: {system_analysis['cpu_usage']:.1f}%",
                "actions": [
                    "考虑增加计算资源",
                    "优化算法复杂度",
                    "启用并行处理",
                    "检查是否有无限循环"
                ]
            })

        # 内存优化建议
        memory_analysis = analysis.get("memory", {})
        if memory_analysis.get("usage_percent", 0) > self.baselines["memory_usage"]:
            recommendations.append({
                "type": "memory_optimization",
                "priority": "high",
                "title": "内存使用率过高",
                "description": f"当前内存使用率: {memory_analysis['usage_percent']:.1f}%",
                "actions": [
                    "增加内存容量",
                    "优化内存管理",
                    "启用垃圾回收",
                    "检查内存泄漏"
                ]
            })

        # 缓存优化建议
        cache_analysis = analysis.get("cache", {})
        if cache_analysis.get("efficiency") == "poor":
            recommendations.append({
                "type": "cache_optimization",
                "priority": "medium",
                "title": "缓存效率低下",
                "description": f"缓存命中率: {cache_analysis.get('hit_rate', 0):.2%}",
                "actions": [
                    "调整缓存大小",
                    "优化缓存键策略",
                    "增加缓存预热",
                    "启用多级缓存"
                ]
            })

        return recommendations

    async def _execute_optimizations(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """执行优化措施"""
        actions_taken = []

        for rec in recommendations:
            try:
                if rec["type"] == "memory_optimization":
                    # 执行内存优化
                    await self.memory_optimizer.optimize_memory()
                    actions_taken.append("执行内存优化")

                elif rec["type"] == "cache_optimization":
                    # 清理缓存
                    self.cache.clear()
                    actions_taken.append("清理缓存")

                elif rec["type"] == "cpu_optimization":
                    # 强制垃圾回收
                    gc.collect()
                    actions_taken.append("执行垃圾回收")

            except Exception as e:
                logger.error(f"执行优化失败 {rec['type']}: {e}")

        return actions_taken

    async def _measure_improvements(self) -> Dict[str, Any]:
        """测量优化效果"""
        try:
            # 等待一段时间让优化生效
            await asyncio.sleep(2)

            # 重新分析
            new_analysis = await self._analyze_system_performance()

            improvements = {
                "cpu_improvement": 0,
                "memory_improvement": 0,
                "overall_better": False
            }

            # 这里可以计算具体的改进幅度
            # 由于是示例，我们返回模拟数据

            return improvements

        except Exception as e:
            logger.error(f"测量改进失败: {e}")
            return {"error": str(e)}

    async def continuous_monitoring(self, interval_seconds: int = 300):
        """持续监控和优化"""
        logger.info(f"🔄 启动持续监控 (间隔: {interval_seconds}秒)")

        while True:
            try:
                # 运行优化
                results = await self.run_optimization()

                # 检查是否需要告警
                await self._check_alerts(results)

                # 保存结果
                self._save_results(results)

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"持续监控出错: {e}")
                await asyncio.sleep(60)  # 出错时等待较短时间

    async def _check_alerts(self, results: Dict[str, Any]):
        """检查告警条件"""
        try:
            analysis = results.get("analysis", {}).get("system", {})

            alerts = []

            # CPU告警
            if analysis.get("cpu_usage", 0) > 90:
                alerts.append({
                    "level": "critical",
                    "message": f"CPU使用率严重过高: {analysis['cpu_usage']:.1f}%"
                })

            # 内存告警
            if analysis.get("memory_usage", 0) > 95:
                alerts.append({
                    "level": "critical",
                    "message": f"内存使用率严重过高: {analysis['memory_usage']:.1f}%"
                })

            # 发送告警
            for alert in alerts:
                logger.warning(f"🚨 {alert['level'].upper()}: {alert['message']}")
                await self.monitoring_center.record_metric("alert", alert)

        except Exception as e:
            logger.error(f"告警检查失败: {e}")

    def _save_results(self, results: Dict[str, Any]):
        """保存优化结果"""
        try:
            os.makedirs("performance_reports", exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_reports/optimization_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 优化结果已保存: {filename}")

        except Exception as e:
            logger.error(f"保存结果失败: {e}")


async def main():
    """主函数"""
    optimizer = PerformanceOptimizer()

    # 单次优化
    if len(sys.argv) == 1:
        results = await optimizer.run_optimization()

        print("\n" + "="*50)
        print("🎯 性能优化报告")
        print("="*50)

        print(f"📊 系统状态: {results['analysis'].get('system', {}).get('status', 'unknown')}")
        print(f"💾 内存使用: {results['analysis'].get('memory', {}).get('usage_percent', 0):.1f}%")
        print(f"🧠 缓存命中率: {results['analysis'].get('cache', {}).get('hit_rate', 0):.2%}")

        print(f"\n🔧 优化建议 ({len(results['recommendations'])} 项):")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec['title']} ({rec['priority']})")

        print(f"\n✅ 已执行优化: {len(results['actions_taken'])} 项")

        # 保存结果
        optimizer._save_results(results)

    # 持续监控
    elif len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        await optimizer.continuous_monitoring(interval)

    else:
        print("用法:")
        print("  python performance_optimizer.py              # 单次优化")
        print("  python performance_optimizer.py --continuous [interval]  # 持续监控")


if __name__ == "__main__":
    asyncio.run(main())
