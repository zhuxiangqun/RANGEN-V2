"""
LangGraph 工作流性能测试
测试工作流执行时间、资源使用和节点性能
"""
import asyncio
import logging
import time
import psutil
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'node_times': {},
            'memory_usage': [],
            'cpu_usage': [],
            'errors': []
        }
    
    def record_execution(
        self,
        success: bool,
        execution_time: float,
        node_times: Optional[Dict[str, float]] = None,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        error: Optional[str] = None
    ):
        """记录执行指标"""
        self.metrics['total_executions'] += 1
        if success:
            self.metrics['successful_executions'] += 1
        else:
            self.metrics['failed_executions'] += 1
            if error:
                self.metrics['errors'].append(error)
        
        self.metrics['total_execution_time'] += execution_time
        
        if node_times:
            for node_name, node_time in node_times.items():
                if node_name not in self.metrics['node_times']:
                    self.metrics['node_times'][node_name] = []
                self.metrics['node_times'][node_name].append(node_time)
        
        if memory_mb is not None:
            self.metrics['memory_usage'].append(memory_mb)
        
        if cpu_percent is not None:
            self.metrics['cpu_usage'].append(cpu_percent)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total = self.metrics['total_executions']
        if total == 0:
            return {"error": "No executions recorded"}
        
        avg_execution_time = self.metrics['total_execution_time'] / total
        success_rate = self.metrics['successful_executions'] / total
        
        # 计算节点平均时间
        avg_node_times = {}
        for node_name, times in self.metrics['node_times'].items():
            if times:
                avg_node_times[node_name] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        
        # 计算内存和CPU统计
        memory_stats = {}
        if self.metrics['memory_usage']:
            memory_stats = {
                'avg': sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']),
                'min': min(self.metrics['memory_usage']),
                'max': max(self.metrics['memory_usage'])
            }
        
        cpu_stats = {}
        if self.metrics['cpu_usage']:
            cpu_stats = {
                'avg': sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage']),
                'min': min(self.metrics['cpu_usage']),
                'max': max(self.metrics['cpu_usage'])
            }
        
        return {
            'total_executions': total,
            'successful_executions': self.metrics['successful_executions'],
            'failed_executions': self.metrics['failed_executions'],
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'total_execution_time': self.metrics['total_execution_time'],
            'avg_node_times': avg_node_times,
            'memory_stats': memory_stats,
            'cpu_stats': cpu_stats,
            'errors': self.metrics['errors'][:10]  # 只显示前10个错误
        }


def get_memory_usage_mb() -> float:
    """获取当前内存使用（MB）"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_cpu_usage() -> float:
    """获取当前CPU使用率（%）"""
    process = psutil.Process(os.getpid())
    return process.cpu_percent(interval=0.1)


async def test_workflow_performance(
    system: UnifiedResearchSystem,
    queries: List[str],
    use_unified_workflow: bool = True
) -> PerformanceMetrics:
    """测试工作流性能
    
    Args:
        system: 统一研究系统实例
        queries: 测试查询列表
        use_unified_workflow: 是否使用统一工作流
    
    Returns:
        性能指标
    """
    metrics = PerformanceMetrics()
    
    logger.info(f"🚀 开始性能测试，查询数量: {len(queries)}")
    
    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"测试 {i}/{len(queries)}: {query[:50]}...")
        logger.info(f"{'='*60}")
        
        # 记录初始资源使用
        initial_memory = get_memory_usage_mb()
        initial_cpu = get_cpu_usage()
        
        start_time = time.time()
        success = False
        error = None
        node_times = {}
        
        try:
            if use_unified_workflow and hasattr(system, '_unified_workflow') and system._unified_workflow:
                # 使用统一工作流
                workflow = system._unified_workflow
                initial_state = {
                    'query': query,
                    'context': {},
                    'route_path': 'simple',  # 将由路由节点决定
                    'complexity_score': 0.0,
                    'evidence': [],
                    'answer': None,
                    'confidence': 0.0,
                    'final_answer': None,
                    'knowledge': [],
                    'citations': [],
                    'task_complete': False,
                    'error': None,
                    'errors': [],  # 新增：错误列表
                    'execution_time': 0.0
                }
                
                result = await workflow.execute(query, initial_state.get('context', {}))
                
                if result and result.get('success', False):
                    success = True
                    # 从结果中提取节点时间（如果存在）
                    node_times = {}
                    if 'node_times' in result:
                        node_times = result['node_times']
                    elif isinstance(result, dict) and 'node_times' in result:
                        node_times = result.get('node_times', {})
                    logger.info(f"✅ 工作流执行成功，置信度: {result.get('confidence', 0.0):.2f}")
                    # 记录错误信息（如果有）
                    if 'errors' in result and result['errors']:
                        logger.warning(f"⚠️ 工作流执行中有 {len(result['errors'])} 个错误")
                else:
                    error = result.get('error', 'Unknown error') if result else 'No result returned'
                    # 记录详细错误信息
                    if result and 'errors' in result and result['errors']:
                        error_details = [e.get('message', str(e)) for e in result['errors']]
                        error = f"{error} | 详细错误: {', '.join(error_details[:3])}"
                    logger.warning(f"⚠️ 工作流执行失败: {error}")
            else:
                # 使用传统流程
                request = ResearchRequest(query=query)
                result = await system.execute_research(request)
                
                if result.success:
                    success = True
                    logger.info(f"✅ 传统流程执行成功，置信度: {result.confidence:.2f}")
                else:
                    error = result.error
                    logger.warning(f"⚠️ 传统流程执行失败: {error}")
        
        except Exception as e:
            error = str(e)
            logger.error(f"❌ 执行异常: {e}")
            import traceback
            traceback.print_exc()
        
        execution_time = time.time() - start_time
        
        # 记录最终资源使用
        final_memory = get_memory_usage_mb()
        final_cpu = get_cpu_usage()
        memory_delta = final_memory - initial_memory
        cpu_avg = (initial_cpu + final_cpu) / 2
        
        # 记录指标
        metrics.record_execution(
            success=success,
            execution_time=execution_time,
            node_times=node_times,
            memory_mb=memory_delta,
            cpu_percent=cpu_avg,
            error=error if error else None
        )
        
        logger.info(f"⏱️ 执行时间: {execution_time:.2f}秒")
        if node_times:
            logger.info(f"📊 节点执行时间:")
            for node_name, node_time in node_times.items():
                logger.info(f"   - {node_name}: {node_time:.2f}秒")
        logger.info(f"💾 内存增量: {memory_delta:.2f}MB")
        logger.info(f"🖥️ CPU使用: {cpu_avg:.2f}%")
        
        # 短暂休息，避免资源竞争
        await asyncio.sleep(0.5)
    
    return metrics


async def main():
    """主测试函数"""
    logger.info("="*60)
    logger.info("LangGraph 工作流性能测试")
    logger.info("="*60)
    
    # 测试查询
    test_queries = [
        "What is the capital of France?",
        "Who was the 15th first lady of the United States?",
        "What is the population of Tokyo?",
    ]
    
    # 初始化系统
    logger.info("\n🔧 初始化系统...")
    system = UnifiedResearchSystem()
    
    # 确保启用统一工作流
    os.environ.setdefault('ENABLE_UNIFIED_WORKFLOW', 'true')
    
    # 等待系统初始化
    await asyncio.sleep(2)
    
    # 测试统一工作流性能
    logger.info("\n" + "="*60)
    logger.info("测试1: 统一工作流性能")
    logger.info("="*60)
    
    metrics = await test_workflow_performance(
        system=system,
        queries=test_queries,
        use_unified_workflow=True
    )
    
    # 打印性能摘要
    logger.info("\n" + "="*60)
    logger.info("性能测试摘要")
    logger.info("="*60)
    
    summary = metrics.get_summary()
    logger.info(f"总执行次数: {summary['total_executions']}")
    logger.info(f"成功次数: {summary['successful_executions']}")
    logger.info(f"失败次数: {summary['failed_executions']}")
    logger.info(f"成功率: {summary['success_rate']:.2%}")
    logger.info(f"平均执行时间: {summary['avg_execution_time']:.2f}秒")
    logger.info(f"总执行时间: {summary['total_execution_time']:.2f}秒")
    
    if summary['avg_node_times']:
        logger.info("\n节点平均执行时间:")
        for node_name, stats in summary['avg_node_times'].items():
            logger.info(f"  {node_name}:")
            logger.info(f"    平均: {stats['avg']:.2f}秒")
            logger.info(f"    最小: {stats['min']:.2f}秒")
            logger.info(f"    最大: {stats['max']:.2f}秒")
            logger.info(f"    次数: {stats['count']}")
    
    if summary['memory_stats']:
        logger.info(f"\n内存统计:")
        logger.info(f"  平均增量: {summary['memory_stats']['avg']:.2f}MB")
        logger.info(f"  最小增量: {summary['memory_stats']['min']:.2f}MB")
        logger.info(f"  最大增量: {summary['memory_stats']['max']:.2f}MB")
    
    if summary['cpu_stats']:
        logger.info(f"\nCPU统计:")
        logger.info(f"  平均使用率: {summary['cpu_stats']['avg']:.2f}%")
        logger.info(f"  最小使用率: {summary['cpu_stats']['min']:.2f}%")
        logger.info(f"  最大使用率: {summary['cpu_stats']['max']:.2f}%")
    
    if summary['errors']:
        logger.info(f"\n错误列表 (前10个):")
        for error in summary['errors']:
            logger.info(f"  - {error}")
    
    logger.info("\n" + "="*60)
    logger.info("性能测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())


