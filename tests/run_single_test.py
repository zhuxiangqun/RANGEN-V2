#!/usr/bin/env python3
"""
运行单个测试 - 避免运行全部测试导致长时间等待
"""
import asyncio
import sys
import os
import signal
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.run_optimization_tests import TestRunner

# 全局中断标志
interrupted = False
force_exit = False

def signal_handler(signum, frame):
    """处理 Ctrl-C 信号
    
    🚀 优化：不在信号处理器中直接调用sys.exit()，避免threading shutdown异常
    而是设置标志，让主循环处理退出逻辑
    """
    global interrupted, force_exit
    if not interrupted:
        interrupted = True
        print("\n⚠️  收到中断信号 (Ctrl-C)，正在退出...", flush=True)
        print("   如果 3 秒内未退出，请再次按 Ctrl-C 强制退出", flush=True)
    else:
        force_exit = True
        print("\n⚠️  强制退出...", flush=True)
        # 🚀 优化：使用os._exit()而不是sys.exit()，避免threading shutdown异常
        # os._exit()会立即退出，跳过所有清理（包括threading shutdown）
        import os
        os._exit(1)

async def run_single_test(test_number: int):
    """运行单个测试"""
    global interrupted
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    runner = TestRunner()
    runner.interrupted = False  # 将中断标志传递给 runner
    
    await runner.setup()
    
    try:
        tests = [
            ("测试1：持久化检查点", runner.test_1_persistent_checkpoint),
            ("测试2：检查点恢复", runner.test_2_checkpoint_recovery),
            ("测试3：子图封装", runner.test_3_subgraph_encapsulation),
            ("测试4：错误恢复", runner.test_4_error_recovery),
            ("测试5：增强错误恢复", runner.test_5_enhanced_error_recovery),
            ("测试6：并行执行", runner.test_6_parallel_execution),
            ("测试7：状态版本管理", runner.test_7_state_version_management),
            ("测试8：动态工作流", runner.test_8_dynamic_workflow),
            ("测试9：性能优化", runner.test_9_performance_optimization),
        ]
        
        if test_number < 1 or test_number > len(tests):
            print(f"❌ 无效的测试编号: {test_number}")
            print(f"   有效范围: 1-{len(tests)}")
            return
        
        test_name, test_func = tests[test_number - 1]
        print(f"🚀 运行: {test_name}")
        
        # 🚀 优化：创建后台任务，定期检查中断标志（更频繁的检查）
        async def check_interrupt():
            """定期检查中断标志，更快响应"""
            while not interrupted and not runner.interrupted and not force_exit:
                await asyncio.sleep(0.05)  # 🚀 优化：每 50ms 检查一次（更快响应）
                if interrupted:
                    runner.interrupted = True
                    # 🚀 新增：立即尝试取消所有待处理任务
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            all_tasks = asyncio.all_tasks(loop)
                            current_task = asyncio.current_task()
                            pending_tasks = [t for t in all_tasks 
                                           if not t.done() and t != current_task and t != interrupt_checker]
                            if pending_tasks:
                                print(f"🔄 正在取消 {len(pending_tasks)} 个待处理任务...", flush=True)
                                for task in pending_tasks:
                                    try:
                                        task.cancel()
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                if force_exit:
                    # 如果强制退出，立即退出循环
                    break
        
        interrupt_checker = asyncio.create_task(check_interrupt())
        
        try:
            # 🚀 优化：使用 800 秒超时（约13.3分钟）
            # 工作流内部超时是 600 秒，测试超时需要大于工作流超时，以允许：
            # 1. 工作流执行时间（最多600秒）
            # 2. 超时检测和取消操作的额外时间（约200秒缓冲）
            # 3. 考虑到性能分析显示第一次查询需要456.64秒，恢复需要246.51秒，总计703.15秒
            await runner.run_test(test_name, test_func, timeout_seconds=800)
        except asyncio.CancelledError:
            # 任务被取消（可能是中断）
            if interrupted:
                print("\n⚠️  测试任务被取消（中断）", flush=True)
            raise
        finally:
            # 取消中断检查任务
            interrupt_checker.cancel()
            try:
                await interrupt_checker
            except asyncio.CancelledError:
                pass
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被中断", flush=True)
        interrupted = True
        runner.interrupted = True
    except asyncio.CancelledError:
        # 任务被取消（可能是中断）
        if interrupted:
            print("\n⚠️  测试任务被取消（中断）", flush=True)
        raise
    finally:
        # 如果收到中断信号，快速清理
        if interrupted or force_exit:
            runner.interrupted = True
            print("🧹 快速清理资源...", flush=True)
            # 使用较短的超时进行快速清理
            try:
                await asyncio.wait_for(runner.cleanup(), timeout=2.0)
            except asyncio.TimeoutError:
                print("⚠️  清理超时，强制退出", flush=True)
            except Exception as e:
                print(f"⚠️  清理时出错: {e}", flush=True)
        else:
            try:
                await runner.cleanup()  # 🚀 修复：cleanup 是异步方法，需要 await
            except Exception as e:
                print(f"⚠️  清理时出错: {e}", flush=True)
        
        if not interrupted:
            print("\n" + "=" * 60)
            print("📊 测试结果")
            print("=" * 60)
            print(f"✅ 通过: {runner.passed}")
            print(f"❌ 失败: {runner.failed}")
            print(f"⏭️ 跳过: {runner.skipped}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tests/run_single_test.py <测试编号>")
        print("示例: python tests/run_single_test.py 1")
        print("\n可用测试:")
        print("  1. 持久化检查点")
        print("  2. 检查点恢复")
        print("  3. 子图封装")
        print("  4. 错误恢复")
        print("  5. 增强错误恢复")
        print("  6. 并行执行")
        print("  7. 状态版本管理")
        print("  8. 动态工作流")
        print("  9. 性能优化")
        sys.exit(1)
    
    test_number = int(sys.argv[1])
    try:
        asyncio.run(run_single_test(test_number))
    except KeyboardInterrupt:
        print("\n⚠️  程序被中断")
        sys.exit(130)  # 130 是标准的 Ctrl-C 退出码

