#!/usr/bin/env python3
"""
带超时的测试运行器 - 改进版
为每个测试添加超时机制，避免无限等待
"""
import asyncio
import sys
import os
import signal
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.run_optimization_tests import TestRunner

# 全局关闭标志
_shutdown_flag = False

class TimeoutTestRunner(TestRunner):
    """带超时的测试运行器"""
    
    def __init__(self, default_timeout=300):
        super().__init__()
        self.default_timeout = default_timeout
        self.test_timeouts = {
            # 🚀 优化：所有测试超时时间设置为 800 秒（约13.3分钟）
            # 工作流内部超时是 600 秒，测试超时需要大于工作流超时，以允许：
            # 1. 工作流执行时间（最多600秒）
            # 2. 超时检测和取消操作的额外时间（约200秒缓冲）
            # 3. 考虑到性能分析显示第一次查询需要456.64秒，恢复需要246.51秒，总计703.15秒
            "测试1：持久化检查点": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试2：检查点恢复": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试3：子图封装": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试4：错误恢复": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试5：增强错误恢复": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试6：并行执行": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试7：状态版本管理": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试8：动态工作流": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
            "测试9：性能优化": 800,  # 约13.3分钟（修复：从700秒增加到800秒）
        }
    
    async def cleanup(self):
        """清理资源（调用父类的清理方法）"""
        await super().cleanup()
    
    async def run_test(self, test_name: str, test_func, timeout_seconds: int = None):
        """运行单个测试（带超时）"""
        if timeout_seconds is None:
            timeout_seconds = self.test_timeouts.get(test_name, self.default_timeout)
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🧪 运行测试: {test_name}")
        logger.info(f"⏱️  超时限制: {timeout_seconds}秒")
        logger.info(f"🕐 开始时间: {time.strftime('%H:%M:%S')}")
        
        start_time = time.time()
        test_task = None
        try:
            # 创建测试任务
            test_task = asyncio.create_task(test_func())
            # 使用 asyncio.wait_for 添加超时
            await asyncio.wait_for(test_task, timeout=timeout_seconds)
            elapsed = time.time() - start_time
            self.passed += 1
            logger.info("")
            logger.info(f"✅ {test_name} - 通过")
            logger.info(f"⏱️  耗时: {elapsed:.2f}秒")
            logger.info(f"🕐 结束时间: {time.strftime('%H:%M:%S')}")
            return True
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            # 取消测试任务
            if test_task and not test_task.done():
                test_task.cancel()
                try:
                    await asyncio.wait_for(test_task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            self.failed += 1
            logger.error("")
            logger.error(f"⏱️ {test_name} - 超时")
            logger.error(f"⏱️  实际耗时: {elapsed:.2f}秒")
            logger.error(f"⏱️  超时限制: {timeout_seconds}秒")
            logger.error("💡 建议:")
            logger.error("   1. 检查是否有无限等待或API调用卡住")
            logger.error("   2. 检查网络连接和API服务状态")
            logger.error(f"   3. 增加超时时间: python tests/run_tests_with_timeout.py {timeout_seconds + 60}")
            logger.error("   4. 尝试单独运行此测试: python tests/run_single_test.py <测试编号>")
            return False
        except asyncio.CancelledError:
            # 任务被取消（通常是由于 KeyboardInterrupt）
            elapsed = time.time() - start_time
            logger.warning("")
            logger.warning(f"⚠️ {test_name} - 任务被取消")
            logger.warning(f"⏱️  已运行: {elapsed:.2f}秒")
            raise  # 重新抛出，让上层处理
        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            logger.warning("")
            logger.warning(f"⚠️ {test_name} - 被用户中断")
            logger.warning(f"⏱️  已运行: {elapsed:.2f}秒")
            
            # 设置全局关闭标志
            global _shutdown_flag
            _shutdown_flag = True
            
            # 只取消当前测试任务，不取消所有任务（避免递归）
            try:
                if test_task and not test_task.done():
                    test_task.cancel()
                    try:
                        await asyncio.wait_for(test_task, timeout=0.1)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
            except Exception:
                pass
            
            # 直接退出，不等待其他任务
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            self.failed += 1
            logger.error("")
            logger.error(f"❌ {test_name} - 失败")
            logger.error(f"⏱️  耗时: {elapsed:.2f}秒")
            logger.error(f"❌ 错误: {type(e).__name__}: {e}")
            import traceback
            logger.error("📋 详细堆栈:")
            logger.error(traceback.format_exc())
            logger.error("💡 建议:")
            logger.error("   1. 查看上方错误堆栈信息")
            logger.error("   2. 尝试单独运行此测试: python tests/run_single_test.py <测试编号>")
            logger.error("   3. 检查相关配置和依赖")
            return False

async def main():
    """主函数"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    default_timeout = 300
    skip_tests = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.isdigit():
                default_timeout = int(arg)
            elif arg.startswith('--skip='):
                skip_tests = arg.split('=')[1].split(',')
            elif arg == '--help' or arg == '-h':
                print("""
用法: python tests/run_tests_with_timeout.py [超时秒数] [--skip=测试编号列表]

参数:
  超时秒数          每个测试的默认超时时间（默认: 300秒）
  --skip=1,2,3     跳过指定的测试编号（用逗号分隔）
  --help, -h       显示此帮助信息

示例:
  python tests/run_tests_with_timeout.py              # 使用默认超时
  python tests/run_tests_with_timeout.py 600          # 设置超时为600秒
  python tests/run_tests_with_timeout.py --skip=7,9   # 跳过测试7和测试9
  python tests/run_tests_with_timeout.py 600 --skip=7 # 组合使用

提示:
  - 按 Ctrl+C 可以中断当前测试
  - 测试涉及LLM API调用，可能需要较长时间
  - 建议先运行单个测试验证: python tests/run_single_test.py <编号>
                """)
                # 直接退出，不执行任何清理（因为还没有运行测试）
                os._exit(0)
    
    logger.info("🚀 启动带超时的测试运行器")
    logger.info(f"📋 默认超时: {default_timeout}秒")
    if skip_tests:
        logger.info(f"⏭️  跳过测试: {', '.join(skip_tests)}")
    logger.info("💡 提示: 按 Ctrl+C 可以中断测试")
    logger.info("💡 提示: 使用 --help 查看完整帮助信息")
    
    runner = TimeoutTestRunner(default_timeout=default_timeout)
    
    try:
        await runner.setup()
        
        # 运行所有测试
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
        
        total_tests = len(tests)
        skipped_count = 0
        completed_tests = []  # 已完成的测试列表
        failed_tests = []  # 失败的测试列表
        
        # 显示测试计划
        logger.info("")
        logger.info("=" * 80)
        logger.info("📋 测试计划")
        logger.info("=" * 80)
        for idx, (test_name, _) in enumerate(tests, 1):
            if str(idx) in skip_tests or test_name.split('：')[0] in skip_tests:
                logger.info(f"  ⏭️  [{idx}/{total_tests}] {test_name} (将跳过)")
            else:
                logger.info(f"  ⏳ [{idx}/{total_tests}] {test_name}")
        logger.info("=" * 80)
        logger.info("")
        
        for idx, (test_name, test_func) in enumerate(tests, 1):
            # 检查是否跳过此测试
            if str(idx) in skip_tests or test_name.split('：')[0] in skip_tests:
                logger.info(f"⏭️  跳过 {test_name} (测试编号: {idx})")
                runner.skipped += 1
                skipped_count += 1
                completed_tests.append((test_name, "跳过"))
                continue
            
            # 显示当前进度和已完成测试
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"📊 当前进度: [{idx}/{total_tests}]")
            logger.info(f"🔄 正在运行: {test_name}")
            logger.info("=" * 80)
            
            # 显示已完成的测试
            if completed_tests:
                logger.info("✅ 已完成的测试:")
                for name, status in completed_tests:
                    status_icon = "✅" if status == "通过" else "❌" if status == "失败" else "⏭️"
                    logger.info(f"   {status_icon} {name} ({status})")
                logger.info("")
            
            # 显示待测试列表
            remaining = total_tests - idx
            if remaining > 0:
                logger.info(f"⏳ 待测试 ({remaining} 个):")
                for i in range(idx, min(idx + 3, total_tests)):  # 只显示接下来3个
                    next_test_name = tests[i][0]
                    logger.info(f"   • {next_test_name}")
                if remaining > 3:
                    logger.info(f"   ... 还有 {remaining - 3} 个测试")
                logger.info("")
            
            logger.info("=" * 80)
            
            try:
                test_result = await runner.run_test(test_name, test_func)
                # 立即更新完成状态
                if test_result:
                    completed_tests.append((test_name, "通过"))
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info(f"✅ 测试完成: {test_name} - 通过")
                    logger.info(f"📊 进度更新: [{idx}/{total_tests}] - 已完成 {len(completed_tests)} 个测试")
                    logger.info("=" * 80)
                else:
                    completed_tests.append((test_name, "失败"))
                    failed_tests.append(test_name)
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info(f"❌ 测试完成: {test_name} - 失败")
                    logger.info(f"📊 进度更新: [{idx}/{total_tests}] - 已完成 {len(completed_tests)} 个测试")
                    logger.info("=" * 80)
                await asyncio.sleep(0.5)  # 短暂延迟，避免资源竞争
            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.warning("⚠️ 测试被用户中断")
                logger.info("")
                logger.info("📊 中断时的测试状态:")
                logger.info(f"   ✅ 已完成: {len([t for t in completed_tests if t[1] == '通过'])} 个")
                logger.info(f"   ❌ 已失败: {len([t for t in completed_tests if t[1] == '失败'])} 个")
                logger.info(f"   ⏭️  已跳过: {len([t for t in completed_tests if t[1] == '跳过'])} 个")
                logger.info(f"   ⏳ 当前测试: {test_name} (未完成)")
                logger.info("")
                
                # 设置全局关闭标志
                global _shutdown_flag
                _shutdown_flag = True
                
                logger.info("💡 提示: 可以使用 --skip 参数跳过已通过的测试")
                
                # 直接退出，不等待清理（避免递归错误）
                os._exit(130)  # 130 是 Ctrl+C 的标准退出码
        
    finally:
        # 确保资源被清理
        try:
            await runner.cleanup()
        except Exception as e:
            logger.warning(f"⚠️ 最终清理时出错: {e}")
        
        # 输出测试结果
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 测试结果汇总")
        logger.info("=" * 80)
        logger.info(f"✅ 通过: {runner.passed}")
        logger.info(f"❌ 失败: {runner.failed}")
        logger.info(f"⏭️ 跳过: {runner.skipped}")
        logger.info(f"📈 总计: {runner.passed + runner.failed + runner.skipped}")
        logger.info("")
        
        # 显示详细的测试结果列表
        if completed_tests:
            logger.info("📋 详细测试结果:")
            for name, status in completed_tests:
                if status == "通过":
                    logger.info(f"   ✅ {name}")
                elif status == "失败":
                    logger.info(f"   ❌ {name}")
                elif status == "跳过":
                    logger.info(f"   ⏭️  {name}")
            logger.info("")
        
        if runner.failed == 0 and runner.passed > 0:
            logger.info("🎉 所有测试通过！")
        elif runner.failed > 0:
            logger.warning(f"⚠️ 有 {runner.failed} 个测试失败")
            if failed_tests:
                logger.warning("失败的测试:")
                for test_name in failed_tests:
                    logger.warning(f"   ❌ {test_name}")
            logger.info("")
            logger.info("💡 查看上方错误信息了解详情")
            logger.info("💡 提示: 可以使用 python tests/run_single_test.py <编号> 单独运行失败的测试")
        else:
            logger.info("ℹ️ 没有执行任何测试")

def signal_handler(signum, frame):
    """信号处理器，用于立即退出"""
    global _shutdown_flag
    _shutdown_flag = True
    print("\n⚠️ 收到中断信号，正在退出...")
    
    # 尝试快速清理资源（不等待）
    try:
        import gc
        # 强制垃圾回收
        gc.collect()
        
        # 尝试清理 multiprocessing 资源
        try:
            import multiprocessing
            # 清理所有进程池
            for pool in multiprocessing.active_children():
                try:
                    pool.terminate()
                    pool.join(timeout=0.1)
                except Exception:
                    pass
        except Exception:
            pass
        
        # 尝试清理 joblib 资源
        try:
            import joblib
            # joblib 使用 loky 时可能会有后台进程
            # 这里尝试清理，但不等待
            pass
        except Exception:
            pass
    except Exception:
        pass
    
    # 强制退出，不等待清理
    os._exit(130)

async def safe_main():
    """安全的主函数，确保资源清理"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await main()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("\n⚠️ 测试被用户中断")
        # 直接退出，不等待清理
        os._exit(130)  # 130 是 Ctrl+C 的标准退出码
    except Exception as e:
        logger.error(f"❌ 测试运行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        os._exit(1)

if __name__ == "__main__":
    # 设置信号处理器（在主线程中）
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(safe_main())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        os._exit(130)  # 130 是 Ctrl+C 的标准退出码
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        os._exit(1)

