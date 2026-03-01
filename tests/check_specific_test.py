#!/usr/bin/env python3
"""
检查特定测试进程 - run_tests_with_timeout.py
"""
import subprocess
import sys

def check_run_tests_with_timeout():
    """检查 run_tests_with_timeout.py 进程"""
    print("🔍 检查 run_tests_with_timeout.py 进程...\n")
    
    keywords = [
        "run_tests_with_timeout",
        "run_tests_with_timeout.py",
        "tests/run_tests_with_timeout",
        "tests.run_tests_with_timeout"
    ]
    
    found = []
    
    for keyword in keywords:
        try:
            result = subprocess.run(
                ["pgrep", "-f", keyword],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
                
                for pid in pids:
                    if pid not in [f['pid'] for f in found]:
                        try:
                            # 获取进程详细信息
                            ps_result = subprocess.run(
                                ["ps", "-p", pid, "-o", "pid,etime,command"],
                                capture_output=True,
                                text=True
                            )
                            
                            if ps_result.returncode == 0:
                                lines = ps_result.stdout.strip().split('\n')
                                if len(lines) > 1:
                                    parts = lines[1].split(None, 2)
                                    if len(parts) >= 3:
                                        found.append({
                                            'pid': pid,
                                            'etime': parts[1] if len(parts) > 1 else '?',
                                            'cmd': parts[2]
                                        })
                        except Exception as e:
                            found.append({
                                'pid': pid,
                                'etime': '?',
                                'cmd': f'python ... {keyword}'
                            })
        except FileNotFoundError:
            print("⚠️ pgrep 不可用")
            break
    
    if found:
        print(f"✅ 发现 {len(found)} 个 run_tests_with_timeout.py 进程:\n")
        for proc in found:
            print(f"  PID: {proc['pid']}")
            print(f"  运行时间: {proc['etime']}")
            print(f"  命令: {proc['cmd'][:150]}")
            print()
        
        print("💡 测试状态:")
        print("  - 如果测试正在输出，说明测试正常运行中")
        print("  - 每个测试可能需要2-5分钟（涉及LLM API调用）")
        print("  - 如果超过超时时间（默认5分钟），测试会自动超时")
        print()
        print("💡 如果测试卡住:")
        print(f"  - 中断: kill {found[0]['pid']} 或按 Ctrl+C")
        print("  - 查看测试输出了解当前进度")
    else:
        print("❌ 没有发现 run_tests_with_timeout.py 进程")
        print()
        print("💡 可能的原因:")
        print("  1. 测试已经完成")
        print("  2. 测试在另一个终端窗口运行")
        print("  3. 测试进程名称不匹配")
        print()
        print("💡 请检查:")
        print("  - 测试是否在另一个终端窗口运行？")
        print("  - 测试输出显示什么？")
        print("  - 手动检查: ps aux | grep run_tests_with_timeout")

if __name__ == "__main__":
    check_run_tests_with_timeout()

