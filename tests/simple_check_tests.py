#!/usr/bin/env python3
"""
简单检查测试进程 - 不依赖特殊权限
改进版：检测所有Python进程，包括测试相关的
"""
import subprocess
import sys
import os

def check_tests():
    """检查测试进程"""
    print("🔍 检查测试进程...\n")
    
    # 扩展的关键词列表（包括所有可能的测试脚本）
    keywords = [
        "run_optimization_tests",
        "run_all_tests", 
        "run_tests_with_timeout",  # 用户正在使用的
        "run_single_test",
        "test_",
        "pytest",
        "unittest",
        "langgraph",
        "optimization",
        "workflow",
        "tests/run",  # 匹配 tests/run_*.py
        "tests.run"   # 匹配模块导入方式
    ]
    
    found = []
    seen_pids = set()
    
    # 方法1: 使用 pgrep 查找所有Python进程
    try:
        # 先查找所有Python进程
        result = subprocess.run(
            ["pgrep", "-f", "python"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            all_python_pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
            
            for pid in all_python_pids:
                if pid in seen_pids:
                    continue
                    
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
                            # 解析输出
                            parts = lines[1].split(None, 2)
                            if len(parts) >= 3:
                                cmdline = parts[2]
                                
                                # 检查是否包含测试关键词
                                cmd_lower = cmdline.lower()
                                is_test = any(keyword in cmd_lower for keyword in keywords)
                                
                                # 排除诊断工具本身
                                if is_test and 'test_diagnostic_tool' not in cmd_lower and 'simple_check_tests' not in cmd_lower:
                                    found.append({
                                        'pid': pid,
                                        'etime': parts[1] if len(parts) > 1 else '?',
                                        'cmd': cmdline[:120]
                                    })
                                    seen_pids.add(pid)
                except Exception as e:
                    continue
        
        # 方法2: 直接使用关键词搜索（备用）
        if not found:
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
                            if pid not in seen_pids:
                                try:
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
                                                if 'test_diagnostic_tool' not in cmdline.lower() and 'simple_check_tests' not in cmdline.lower():
                                                    found.append({
                                                        'pid': pid,
                                                        'etime': parts[1] if len(parts) > 1 else '?',
                                                        'cmd': cmdline[:120]
                                                    })
                                                    seen_pids.add(pid)
                                except:
                                    found.append({'pid': pid, 'etime': '?', 'cmd': f'python ... {keyword}'})
                                    seen_pids.add(pid)
                except FileNotFoundError:
                    break
                    
    except FileNotFoundError:
        print("⚠️ pgrep 不可用，无法检查进程")
        print("💡 请手动检查: ps aux | grep python | grep test")
        return
    
    if found:
        print(f"⚠️ 发现 {len(found)} 个测试相关进程:\n")
        for i, proc in enumerate(found, 1):
            print(f"{i}. PID: {proc['pid']}")
            print(f"   运行时间: {proc['etime']}")
            print(f"   命令: {proc['cmd']}")
            print()
        
        print("💡 操作建议:")
        print(f"   - 如果测试卡住，可以中断: kill {found[0]['pid']} 或按 Ctrl+C")
        print(f"   - 查看进程详情: ps -p {found[0]['pid']} -f")
        print(f"   - 如果测试正常，请等待完成（每个测试可能需要几分钟）")
    else:
        print("✅ 没有发现测试进程")
        print()
        print("💡 如果测试确实在运行:")
        print("   1. 测试可能在另一个终端窗口")
        print("   2. 请提供测试启动命令和输出")
        print("   3. 手动检查: ps aux | grep python | grep -E 'test|run'")

if __name__ == "__main__":
    check_tests()

