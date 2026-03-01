"""
LLM管理器
统一管理LLM调用，支持多种接口和错误处理
"""
import logging
import time
import inspect
from typing import Any, Dict, Optional, Callable, Union, Protocol

logger = logging.getLogger(__name__)


class UnifiedLLMInterface(Protocol):
    """统一LLM接口协议"""

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """主要LLM调用接口（无下划线）"""
        ...

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """内部LLM调用接口（有下划线）"""
        ...

    def _call_deepseek(self, prompt: str, enable_thinking_mode: bool = True, **kwargs) -> Optional[str]:
        """DeepSeek专用接口（可选）"""
        ...


class LLMManager(UnifiedLLMInterface):
    """LLM管理器 - 统一LLM调用接口"""

    def __init__(self, primary_llm=None, fallback_llm=None, cache_manager=None):
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        self.cache_manager = cache_manager

        # 调用统计
        self.call_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_used': 0,
            'avg_response_time': 0.0
        }

        logger.info("✅ LLM管理器初始化完成")

    def call_with_cache(self,
                       operation_name: str,
                       prompt: str,
                       cache_key: Optional[str] = None,
                       use_cache: bool = True,
                       **kwargs) -> Optional[str]:
        """
        带缓存的LLM调用

        Args:
            operation_name: 操作名称（用于日志和缓存）
            prompt: 提示词
            cache_key: 缓存键，如果为None则自动生成
            use_cache: 是否使用缓存
            **kwargs: 传递给LLM的其他参数

        Returns:
            LLM响应文本，如果失败返回None
        """
        self.call_stats['total_calls'] += 1
        start_time = time.time()

        try:
            # 生成缓存键
            if cache_key is None:
                cache_key = self._generate_cache_key(operation_name, prompt, kwargs)

            # 检查缓存
            if use_cache and self.cache_manager:
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    self.call_stats['cache_hits'] += 1
                    logger.debug(f"✅ 缓存命中: {operation_name}")
                    return cached_result

            self.call_stats['cache_misses'] += 1

            # 调用LLM
            response = self._call_llm(prompt, **kwargs)

            # 缓存结果
            if use_cache and self.cache_manager and response:
                self.cache_manager.set(cache_key, response)

            # 更新统计
            self.call_stats['successful_calls'] += 1
            response_time = time.time() - start_time
            self._update_avg_response_time(response_time)

            return response

        except Exception as e:
            self.call_stats['failed_calls'] += 1
            logger.error(f"LLM调用失败 ({operation_name}): {e}")

            # 尝试fallback
            if self.fallback_llm:
                try:
                    self.call_stats['fallback_used'] += 1
                    logger.info(f"🔄 尝试fallback LLM调用: {operation_name}")
                    response = self._call_llm_fallback(prompt, **kwargs)
                    if response:
                        self.call_stats['successful_calls'] += 1
                        return response
                except Exception as fallback_error:
                    logger.error(f"Fallback LLM调用也失败: {fallback_error}")

            return None

    def call_without_cache(self, prompt: str, **kwargs) -> Optional[str]:
        """不使用缓存的LLM调用"""
        return self.call_with_cache(
            operation_name="direct_call",
            prompt=prompt,
            use_cache=False,
            **kwargs
        )

    def _call_llm(self, prompt: str, **kwargs) -> Optional[str]:
        """统一的LLM调用方法"""
        if not self.primary_llm:
            raise RuntimeError("Primary LLM 未设置")

        # 支持的LLM方法列表（按优先级）
        llm_methods = [
            ('generate', {'temperature': 0.1, 'max_tokens': 2000, **kwargs}),
            ('_call_llm', {'temperature': 0.1, 'max_tokens': 2000, **kwargs}),
            ('call', {'temperature': 0.1, 'max_tokens': 2000, **kwargs}),
            ('_call_deepseek', {'enable_thinking_mode': kwargs.get('enable_thinking_mode', False),
                               'dynamic_complexity': kwargs.get('dynamic_complexity', 'general')}),
        ]

        for method_name, call_kwargs in llm_methods:
            if hasattr(self.primary_llm, method_name):
                try:
                    method = getattr(self.primary_llm, method_name)
                    sig = inspect.signature(method)

                    # 动态构建调用参数
                    final_kwargs = self._build_call_kwargs(prompt, call_kwargs, sig)

                    # 调用方法
                    if 'prompt' in final_kwargs:
                        response = method(**final_kwargs)
                    else:
                        # 假设第一个参数是prompt
                        response = method(prompt, **{k: v for k, v in final_kwargs.items() if k != 'prompt'})

                    # 处理响应
                    if isinstance(response, str):
                        return response
                    elif hasattr(response, 'text'):
                        return response.text
                    elif response:
                        return str(response)

                except Exception as method_error:
                    logger.debug(f"LLM方法 {method_name} 调用失败: {method_error}")
                    continue

        raise RuntimeError("所有LLM调用方法都失败了")

    def call_llm(self, prompt: str, **kwargs) -> Optional[str]:
        """Alias for _call_llm for compatibility with external code"""
        return self._call_llm(prompt, **kwargs)

    def _call_deepseek(self, prompt: str, enable_thinking_mode: bool = True, **kwargs) -> Optional[str]:
        """DeepSeek专用接口 - 委托给_call_llm"""
        kwargs['enable_thinking_mode'] = enable_thinking_mode
        return self._call_llm(prompt, **kwargs)

    def _call_llm_fallback(self, prompt: str, **kwargs) -> Optional[str]:
        """Fallback LLM调用"""
        if not self.fallback_llm:
            return None

        try:
            # 简化版的调用，只使用最基本的方法
            if hasattr(self.fallback_llm, '_call_llm'):
                return self.fallback_llm._call_llm(prompt, **kwargs)
            elif hasattr(self.fallback_llm, 'generate'):
                return self.fallback_llm.generate(prompt=prompt, **kwargs)
            else:
                logger.warning("Fallback LLM没有兼容的调用方法")
                return None
        except Exception as e:
            logger.error(f"Fallback LLM调用失败: {e}")
            return None

    def _build_call_kwargs(self, prompt: str, call_kwargs: Dict[str, Any],
                          method_sig: inspect.Signature) -> Dict[str, Any]:
        """根据方法签名构建调用参数"""
        final_kwargs = {}

        # 检查方法参数
        for param_name, param in method_sig.parameters.items():
            if param_name == 'self':
                continue

            # 按优先级设置参数值
            if param_name == 'prompt' or param_name == 'message' or param_name == 'input':
                final_kwargs[param_name] = prompt
            elif param_name in call_kwargs:
                final_kwargs[param_name] = call_kwargs[param_name]

        return final_kwargs

    def _generate_cache_key(self, operation_name: str, prompt: str, kwargs: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib

        # 包含操作名、提示词和关键参数
        key_components = [
            operation_name,
            hashlib.md5(prompt.encode()).hexdigest()[:8],
        ]

        # 添加重要的kwargs
        important_params = ['temperature', 'max_tokens', 'enable_thinking_mode', 'dynamic_complexity']
        for param in important_params:
            if param in kwargs:
                key_components.append(f"{param}:{kwargs[param]}")

        return "|".join(key_components)

    def _update_avg_response_time(self, response_time: float):
        """更新平均响应时间"""
        total_calls = self.call_stats['successful_calls']
        current_avg = self.call_stats['avg_response_time']
        self.call_stats['avg_response_time'] = (current_avg * (total_calls - 1) + response_time) / total_calls

    def get_stats(self) -> Dict[str, Any]:
        """获取调用统计"""
        stats = self.call_stats.copy()
        stats['success_rate'] = (
            stats['successful_calls'] / stats['total_calls'] * 100
            if stats['total_calls'] > 0 else 0
        )
        stats['cache_hit_rate'] = (
            stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100
            if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        )
        return stats

    def reset_stats(self):
        """重置统计信息"""
        self.call_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_used': 0,
            'avg_response_time': 0.0
        }

    def set_primary_llm(self, llm):
        """设置主LLM"""
        self.primary_llm = llm
        logger.info("✅ 主LLM已更新")

    def set_fallback_llm(self, llm):
        """设置备用LLM"""
        self.fallback_llm = llm
        logger.info("✅ 备用LLM已更新")

    def set_cache_manager(self, cache_manager):
        """设置缓存管理器"""
        self.cache_manager = cache_manager
        logger.info("✅ 缓存管理器已更新")
