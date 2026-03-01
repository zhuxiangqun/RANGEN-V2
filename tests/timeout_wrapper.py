
import asyncio
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    """超时上下文管理器"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超时 ({seconds}秒)")
    
    # 设置信号处理器（仅Unix系统）
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows系统使用asyncio超时
        yield

async def run_with_timeout(coro, timeout_seconds=300):
    """运行异步函数并设置超时"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"测试超时 ({timeout_seconds}秒)")
