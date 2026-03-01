#!/usr/bin/env python3
"""
快速检查正在运行的测试进程
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_running_tests():
    """检查正在运行的测试进程"""
    print("🔍 检查正在运行的测试进程...\n")
    
    # 测试关键词
    test_keywords = [
        "run_optimization_tests",
        "run_all_tests",
        "run_tests_with_timeout",
        "run_single_test",
        "test_",
        "pytest",
        "unittest"
    ]
    
    found_processes = []
    
    # 方法1: 使用 psutil（如果可用）
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # 检查是否包含测试关键词
                if any(keyword in cmdline.lower() for keyword in test_keywords):
                    # 排除诊断工具本身
                    if 'test_diagnostic_tool' not in cmdline and 'check_running_tests' not in cmdline:
                        import time
                        runtime = time.time() - proc.info['create_time']
                        found_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'runtime': runtime
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except ImportError:
        # psutil 不可用，使用 pgrep
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
                                found_processes.append({
                                    'pid': pid_int,
                                    'name': 'python',
                                    'cmdline': f'python ... {keyword}',
                                    'runtime': None
                                })
                            except ValueError:
                                continue
        except FileNotFoundError:
            print("⚠️ 无法检查进程（需要 psutil 或 pgrep）")
            print("   安装: pip install psutil")
            return
    
    if found_processes:
        print(f"⚠️ 发现 {len(found_processes)} 个测试相关进程:\n")
        for proc in found_processes:
            runtime_str = f"运行时间: {proc['runtime']:.1f}秒" if proc['runtime'] else "运行时间: 未知"
            print(f"  PID: {proc['pid']}")
            print(f"  命令: {proc['cmdline'][:120]}")
            print(f"  {runtime_str}")
            print()
        
        print("💡 操作建议:")
        print("  1. 如果测试卡住，可以中断: kill <PID> 或按 Ctrl+C")
        print("  2. 查看测试输出: 检查终端或日志文件")
        print("  3. 运行诊断工具: python tests/test_diagnostic_tool.py")
    else:
        print("✅ 没有发现正在运行的测试进程")

if __name__ == "__main__":
    check_running_tests()

