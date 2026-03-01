#!/usr/bin/env python3
"""
测试诊断工具 - 诊断测试问题并提供修复建议
"""
import sys
import os
import signal
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入 psutil，如果不可用则使用备用方法
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def check_test_status():
    """检查测试状态"""
    print("🔍 检查测试状态...")
    
    # 检查是否有测试进程在运行
    import subprocess
    import psutil
    
    test_keywords = [
        "run_optimization_tests",
        "run_all_tests",
        "run_tests_with_timeout",
        "run_single_test",
        "test_",
        "pytest",
        "unittest",
        "langgraph",
        "optimization",
        "workflow",
        "tests/",  # 测试目录
        "test.py"  # 测试文件
    ]
    
    running_tests = []
    
    if PSUTIL_AVAILABLE:
        # 方法1: 使用 psutil（更可靠）
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline.lower() for keyword in test_keywords):
                        # 排除诊断工具本身
                        if 'test_diagnostic_tool' not in cmdline:
                            running_tests.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline[:100]  # 只显示前100个字符
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"⚠️ 使用 psutil 检查进程时出错: {e}")
    
    # 方法2: 使用 pgrep（备用方法）
    if not running_tests:
        try:
            for keyword in test_keywords:
                result = subprocess.run(
                    ["pgrep", "-f", keyword],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid and pid.strip():
                            try:
                                pid_int = int(pid.strip())
                                if PSUTIL_AVAILABLE:
                                    try:
                                        proc = psutil.Process(pid_int)
                                        cmdline = ' '.join(proc.cmdline() or [])
                                        if 'test_diagnostic_tool' not in cmdline:
                                            running_tests.append({
                                                'pid': pid_int,
                                                'name': proc.name(),
                                                'cmdline': cmdline[:100]
                                            })
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        continue
                                else:
                                    # 没有 psutil，只显示 PID
                                    running_tests.append({
                                        'pid': pid_int,
                                        'name': 'python',
                                        'cmdline': f'python ... {keyword}'
                                    })
                            except ValueError:
                                continue
        except FileNotFoundError:
            # pgrep 不可用
            if not PSUTIL_AVAILABLE:
                print("ℹ️ 无法检查进程状态（需要 psutil 或 pgrep）")
                print("   安装: pip install psutil")
                return None
    
    if running_tests:
        print(f"⚠️ 发现 {len(running_tests)} 个测试相关进程正在运行:")
        for test in running_tests:
            print(f"  - PID: {test['pid']}, 命令: {test['cmdline'][:80]}...")
        return True
    else:
        print("✅ 没有发现正在运行的测试进程")
        return False

def analyze_common_issues():
    """分析常见问题"""
    print("\n📋 常见问题分析:")
    
    issues = [
        {
            "问题": "测试卡在LLM API调用",
            "原因": "API超时、网络问题、API限流",
            "解决方案": [
                "1. 检查网络连接",
                "2. 检查API密钥是否有效",
                "3. 检查API限流状态",
                "4. 增加API超时时间"
            ]
        },
        {
            "问题": "测试无限等待",
            "原因": "缺少超时机制、死循环、资源竞争",
            "解决方案": [
                "1. 添加测试超时机制",
                "2. 检查是否有无限重试逻辑",
                "3. 检查资源锁是否释放"
            ]
        },
        {
            "问题": "测试内存泄漏",
            "原因": "未释放资源、缓存过大、循环引用",
            "解决方案": [
                "1. 检查资源是否正确释放",
                "2. 限制缓存大小",
                "3. 使用内存分析工具"
            ]
        },
        {
            "问题": "测试数据库锁定",
            "原因": "SQLite数据库被锁定、连接未关闭",
            "解决方案": [
                "1. 检查数据库连接是否正确关闭",
                "2. 使用临时数据库文件",
                "3. 增加数据库超时时间"
            ]
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['问题']}")
        print(f"   原因: {issue['原因']}")
        print(f"   解决方案:")
        for solution in issue['解决方案']:
            print(f"     {solution}")

def create_timeout_wrapper():
    """创建带超时的测试包装器"""
    wrapper_code = '''
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
'''
    
    wrapper_path = project_root / "tests" / "timeout_wrapper.py"
    wrapper_path.write_text(wrapper_code)
    print(f"✅ 已创建超时包装器: {wrapper_path}")

def provide_fix_suggestions():
    """提供修复建议"""
    print("\n🔧 修复建议:")
    
    suggestions = [
        "1. 立即中断测试: 按 Ctrl+C 或运行 'pkill -f run_optimization_tests'",
        "2. 添加超时机制: 使用 timeout_wrapper.py 包装测试",
        "3. 减少测试范围: 只运行单个测试而不是全部",
        "4. 使用模拟数据: 避免实际调用LLM API",
        "5. 检查日志: 查看最近的错误日志",
        "6. 清理临时文件: 删除测试生成的临时数据库文件"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")

def create_quick_test_script():
    """创建快速测试脚本（只测试核心功能）"""
    quick_test_code = '''#!/usr/bin/env python3
"""
快速测试脚本 - 只测试核心功能，避免长时间运行
"""
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def quick_test():
    """快速测试"""
    print("🚀 快速测试模式（跳过耗时测试）")
    
    # 只测试工作流构建，不执行实际查询
    from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
    
    try:
        # 创建简化系统对象
        class MockSystem:
            pass
        
        system = MockSystem()
        
        # 测试工作流构建
        print("📋 测试工作流构建...")
        workflow = UnifiedResearchWorkflow(system=system)
        
        if workflow.workflow is not None:
            print("✅ 工作流构建成功")
            return True
        else:
            print("❌ 工作流构建失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(quick_test())
    sys.exit(0 if result else 1)
'''
    
    quick_test_path = project_root / "tests" / "quick_test.py"
    quick_test_path.write_text(quick_test_code)
    quick_test_path.chmod(0o755)  # 添加执行权限
    print(f"✅ 已创建快速测试脚本: {quick_test_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 测试诊断工具")
    print("=" * 60)
    
    # 检查测试状态
    has_running_tests = check_test_status()
    
    # 分析常见问题
    analyze_common_issues()
    
    # 提供修复建议
    provide_fix_suggestions()
    
    # 创建工具
    print("\n🛠️ 创建诊断工具...")
    create_timeout_wrapper()
    create_quick_test_script()
    
    print("\n" + "=" * 60)
    print("📝 下一步操作:")
    print("=" * 60)
    print("1. 如果测试卡住，按 Ctrl+C 中断")
    print("2. 运行快速测试: python tests/quick_test.py")
    print("3. 检查错误日志: 查看最近的日志文件")
    print("4. 清理临时文件: rm -rf /tmp/langgraph_test_*")
    print("=" * 60)

if __name__ == "__main__":
    main()

