#!/usr/bin/env python3
"""
显示所有Python进程 - 帮助找到测试进程
"""
import subprocess
import sys

def show_all_python():
    """显示所有Python进程"""
    print("🔍 查找所有Python进程...\n")
    
    try:
        # 查找所有Python进程
        result = subprocess.run(
            ["pgrep", "-f", "python"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            
            if not pids:
                print("✅ 没有发现Python进程")
                return
            
            print(f"发现 {len(pids)} 个Python进程:\n")
            
            test_processes = []
            other_processes = []
            
            for pid in pids:
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
                                cmdline = parts[2]
                                
                                # 判断是否是测试相关
                                cmd_lower = cmdline.lower()
                                is_test = any(kw in cmd_lower for kw in [
                                    'test', 'run_optimization', 'run_all', 'run_tests',
                                    'pytest', 'unittest', 'langgraph'
                                ])
                                
                                proc_info = {
                                    'pid': pid,
                                    'etime': parts[1] if len(parts) > 1 else '?',
                                    'cmd': cmdline
                                }
                                
                                if is_test and 'test_diagnostic' not in cmd_lower and 'show_all' not in cmd_lower:
                                    test_processes.append(proc_info)
                                elif 'test_diagnostic' not in cmd_lower and 'show_all' not in cmd_lower:
                                    other_processes.append(proc_info)
                except:
                    continue
            
            if test_processes:
                print("=" * 60)
                print("🧪 测试相关进程:")
                print("=" * 60)
                for proc in test_processes:
                    print(f"\n  PID: {proc['pid']}")
                    print(f"  运行时间: {proc['etime']}")
                    print(f"  命令: {proc['cmd'][:150]}")
            
            if other_processes:
                print("\n" + "=" * 60)
                print("🐍 其他Python进程:")
                print("=" * 60)
                for proc in other_processes[:10]:  # 只显示前10个
                    print(f"\n  PID: {proc['pid']}")
                    print(f"  运行时间: {proc['etime']}")
                    print(f"  命令: {proc['cmd'][:150]}")
            
            if not test_processes and not other_processes:
                print("⚠️ 无法获取进程详细信息")
                print("   可能是权限问题")
                
        else:
            print("✅ 没有发现Python进程")
            
    except FileNotFoundError:
        print("⚠️ pgrep 不可用")
        print("💡 请手动运行: ps aux | grep python")

if __name__ == "__main__":
    show_all_python()

