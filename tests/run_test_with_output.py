#!/usr/bin/env python3
"""
运行测试并显示详细输出
"""
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_with_output(test_name=None, verbose=True, capture_output=False):
    """运行测试并显示输出"""
    
    # 构建 pytest 命令
    cmd = ["python3", "-m", "pytest", "tests/test_langgraph_integration.py"]
    
    if test_name:
        cmd.append(f"::{test_name}")
    
    if verbose:
        cmd.append("-v")
        cmd.append("-s")  # 显示 print 输出
    
    if capture_output:
        cmd.append("--capture=no")
    
    print("=" * 80)
    print("🚀 运行测试命令:")
    print("   " + " ".join(cmd))
    print("=" * 80)
    print()
    
    # 运行测试
    start_time = time.time()
    
    try:
        # 实时输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时打印输出
        for line in process.stdout:
            print(line, end='', flush=True)
        
        process.wait()
        exit_code = process.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断 (Ctrl-C)")
        if process:
            process.terminate()
            process.wait()
        exit_code = 130
    except Exception as e:
        print(f"\n❌ 运行测试时出错: {e}")
        exit_code = 1
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print(f"⏱️  测试执行时间: {elapsed:.2f} 秒")
    print(f"📊 退出代码: {exit_code}")
    print("=" * 80)
    
    return exit_code

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行测试并显示详细输出")
    parser.add_argument(
        "-t", "--test",
        help="运行特定测试 (例如: TestLangGraphIntegration::test_simple_query_path)",
        default=None
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="安静模式（不显示详细输出）"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="运行所有测试"
    )
    
    args = parser.parse_args()
    
    if args.all:
        test_name = None
    else:
        test_name = args.test or "TestLangGraphIntegration::test_state_consistency"
    
    verbose = not args.quiet
    
    exit_code = run_test_with_output(
        test_name=test_name,
        verbose=verbose,
        capture_output=False
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

