"""
批处理优化器 - 实现真正的批量处理
"""
import asyncio
import logging
from typing import Any, Dict, List, Dict, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)


class BatchProcessorOptimizer:
    """批处理优化器 - 实现真正的批量处理"""

    def __init__(self,
                 batch_size: Optional[int] = None,
                 max_workers: Optional[int] = None,
                 use_process_pool: bool = False):
        self.batch_size = batch_size or self._get_intelligent_batch_param("default_batch_size")
        self.max_workers = max_workers or self._get_intelligent_batch_param("default_max_workers")
        self.use_process_pool = use_process_pool
        self.executor = None
        self._setup_executor()

        self.performance_history = []
        self.optimal_batch_size = self.batch_size
        self.adaptive_threshold = self._get_intelligent_batch_param("adaptive_threshold")  # 性能阈值

    def _setup_executor(self):
        """设置执行器"""
        if self.use_process_pool:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    async def process_batch(self,
                           items: List[Any],
                           processor_func: Callable[[Any], Any],
                           is_async: bool = False) -> List[Optional[Any]]:
        """处理批量数据 - 真正的批处理"""
        if not items:
            return []

        if len(items) <= self.batch_size:
            if is_async:
                return await self._process_async_batch(items, processor_func)
            return self._process_sync_batch(items, processor_func)

        batches = [items[i:i + self.batch_size]
                  for i in range(0, len(items), self.batch_size)]

        all_results = []

        for batch in batches:
            if is_async:
                batch_results = await self._process_async_batch(batch, processor_func)
            else:
                batch_results = self._process_sync_batch(batch, processor_func)

            all_results.extend(batch_results)

        return all_results

    def _optimize_batch_size(self, execution_time: float, batch_size: int):
        """智能优化批处理大小"""
        try:
            self.performance_history.append({
                'batch_size': batch_size,
                'execution_time': execution_time,
                'timestamp': asyncio.get_event_loop().time()
            })

            max_history_size = self._get_intelligent_batch_param("max_history_size")
            if len(self.performance_history) > max_history_size:
                self.performance_history = self.performance_history[-max_history_size:]

            min_trend_samples = self._get_intelligent_batch_param("min_trend_samples")
            if len(self.performance_history) >= min_trend_samples:
                recent_performance = self.performance_history[-min_trend_samples:]
                avg_time = sum(p['execution_time'] for p in recent_performance) / len(recent_performance)

                performance_decline_threshold = self._get_intelligent_batch_param("performance_decline_threshold")
                if execution_time > avg_time * performance_decline_threshold:
                    min_batch_size = self._get_intelligent_batch_param("min_batch_size")
                    batch_reduction_factor = self._get_intelligent_batch_param("batch_reduction_factor")
                    self.optimal_batch_size = max(min_batch_size, int(batch_size * batch_reduction_factor))
                    logger.info(f"性能下降，调整批处理大小为: {self.optimal_batch_size}")
                elif execution_time < avg_time * self._get_intelligent_batch_param("performance_improvement_threshold"):
                    max_batch_size = self._get_intelligent_batch_param("max_batch_size")
                    batch_increase_factor = self._get_intelligent_batch_param("batch_increase_factor")
                    self.optimal_batch_size = min(max_batch_size, int(batch_size * batch_increase_factor))
                    logger.info(f"性能提升，调整批处理大小为: {self.optimal_batch_size}")

                self.batch_size = self.optimal_batch_size

        except Exception as e:
            logger.warning("批处理大小优化失败: {e}")

    def _get_intelligent_batch_param(self, param_name: str) -> Any:
        """获取智能批处理参数"""
        try:
            return _get_intelligent_batch_param_global(param_name)
        except Exception:
            param_configs = {
                "default_batch_size": 3config.DEFAULT_TWO_VALUE,
                "default_max_workers": 4,
                "adaptive_threshold": config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE,
                "max_history_size": config.DEFAULT_LIMIT,
                "min_trend_samples": 5,
                "performance_decline_threshold": config.DEFAULT_ONE_VALUE.config.DEFAULT_ONE_VALUE,
                "performance_improvement_threshold": config.DEFAULT_NEAR_MAX_THRESHOLD,
                "min_batch_size": 8,
                "max_batch_size": config.DEFAULT_ONE_VALUEconfig.DEFAULT_TWO_VALUE8,
                "batch_reduction_factor": config.DEFAULT_HIGH_THRESHOLD,
                "batch_increase_factor": 1.2
            }
            return param_configs.get(param_name, 32)

    def get_optimal_batch_size(self) -> int:
        """获取最优批处理大小"""
        return self.optimal_batch_size

    async def _process_async_batch(self,
                                  batch: List[Any],
                                  processor_func: Callable[[Any], Any]) -> List[Optional[Any]]:
        """异步批处理"""
        try:
            tasks = [processor_func(item) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("批处理项目 %d 失败: %s", i, result)
                    processed_results.append(None)
                else:
                    processed_results.append(result)

            return processed_results

        except (RuntimeError, ValueError, TypeError) as e:
            logger.error("异步批处理失败: %s", e)
            return [None] * len(batch)

    def _process_sync_batch(self,
                           batch: List[Any],
                           processor_func: Callable[[Any], Any]) -> List[Optional[Any]]:
        """同步批处理 - 在线程池中并行执行"""
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                batch_results = list(executor.map(processor_func, batch))

            processed_results = []
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error("批处理项目 %d 失败: %s", i, result)
                    processed_results.append(None)
                else:
                    processed_results.append(result)

            return processed_results

        except (RuntimeError, ValueError, TypeError) as e:
            logger.error("同步批处理失败: %s", e)
            return [None] * len(batch)

    def process_batch_sync(self,
                          items: List[Any],
                          processor_func: Callable[[Any], Any]) -> List[Optional[Any]]:
        """同步批处理（非异步版本）"""
        if not items:
            return []

        batches = [items[i:i + self.batch_size]
                  for i in range(0, len(items), self.batch_size)]

        all_results = []

        for batch in batches:
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    batch_results = list(executor.map(processor_func, batch))
                all_results.extend(batch_results)
            except (RuntimeError, ValueError, TypeError) as e:
                logger.error("同步批处理失败: %s", e)
                all_results.extend([None] * len(batch))

        return all_results

    async def vector_batch_processing(self,
                                    texts: List[str],
                                    embedding_func: Callable[[str], List[float]]) -> List[Optional[List[float]]]:
        """向量嵌入批处理优化"""
        try:
            if hasattr(embedding_func, '__self__'):
                try:
                    model = embedding_func.__self__  # type: ignore
                    if hasattr(model, 'encode'):
                        embeddings = model.encode(texts, batch_size=len(texts))
                        return embeddings.tolist()
                except (AttributeError, TypeError):
                    pass
            results = await self.process_batch(texts, embedding_func, is_async=False)
            return results

        except (RuntimeError, ValueError, TypeError) as e:
            logger.error("向量批处理失败: %s", e)
            return [None] * len(texts)

    async def query_batch_processing(self,
                                   queries: List[str],
                                   query_processor: Callable[[str], Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """查询批处理优化"""
        try:
            results = await self.process_batch(queries, query_processor, is_async=False)
            return results
        except (RuntimeError, ValueError, TypeError) as e:
            logger.error("查询批处理失败: %s", e)
            return [None] * len(queries)

    def close(self):
        """关闭执行器"""
        if self.executor:
            self.executor.shutdown(wait=True)


_BATCH_PROCESSOR = None


def get_batch_processor(batch_size: Optional[int] = None,
                       max_workers: Optional[int] = None,
                       use_process_pool: bool = False) -> BatchProcessorOptimizer:
    """获取批处理优化器实例"""
    if globals().get('_BATCH_PROCESSOR') is None:
        globals()['_BATCH_PROCESSOR'] = BatchProcessorOptimizer(batch_size, max_workers, use_process_pool)
    return globals()['_BATCH_PROCESSOR']


async def process_batch_async(items: List[Any],
                             processor_func: Callable[[Any], Any],
                             batch_size: Optional[int] = None) -> List[Optional[Any]]:
    """异步批处理便捷函数"""
    processor = get_batch_processor(batch_size)
    return await processor.process_batch(items, processor_func, is_async=True)


def process_batch_sync(items: List[Any],
                      processor_func: Callable[[Any], Any],
                      batch_size: Optional[int] = None) -> List[Optional[Any]]:
    """同步批处理便捷函数"""
    processor = get_batch_processor(batch_size)
    return processor.process_batch_sync(items, processor_func)


async def vector_batch_embedding(texts: List[str],
                                embedding_func: Callable[[str], List[float]]) -> List[Optional[List[float]]]:
    """向量批处理嵌入便捷函数"""
    processor = get_batch_processor()
    return await processor.vector_batch_processing(texts, embedding_func)


async def query_batch_processing(queries: List[str],
                                query_processor: Callable[[str], Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
    """查询批处理便捷函数"""
    processor = get_batch_processor()
    return await processor.query_batch_processing(queries, query_processor)



def _get_intelligent_batch_param_global(param_type: str) -> Any:
    """获取智能批处理参数（全局版本）"""
    return _get_default_batch_param(param_type)


def _get_default_batch_param(param_type: str) -> Any:
    """获取默认批处理参数（回退值）"""
    default_params = {
        "default_batch_size": 64,
        "default_max_workers": 4,
        "adaptive_threshold": config.DEFAULT_HIGH_THRESHOLD,
        "max_history_size": config.DEFAULT_LIMIT,
        "min_trend_samples": config.DEFAULT_TOP_K,
        "performance_decline_threshold": config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE,
        "performance_improvement_threshold": config.DEFAULT_HIGH_THRESHOLD,
        "min_batch_size": 8,
        "max_batch_size": config.DEFAULT_TWO_VALUE56,
        "batch_reduction_factor": config.DEFAULT_HIGH_THRESHOLD,
        "batch_increase_factor": 1.2
    }
    return default_params.get(param_type, 64)


def _get_current_batch_context() -> Dict[str, Any]:
    """获取当前批处理上下文"""
    return {
        "processor_type": "batch_processor_optimizer",
        "current_batch_size": getattr(globals().get('_BATCH_PROCESSOR'), 'batch_size', 64),
        "current_max_workers": getattr(globals().get('_BATCH_PROCESSOR'), 'max_workers', 4)
    }
