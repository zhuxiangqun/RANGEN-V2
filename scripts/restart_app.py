#!/usr/bin/env python3
"""
重启推理应用 - 修复端口占用问题的增强版脚本
"""

import os
import sys
import time
import subprocess
import signal

def get_pids_on_port(port):
    try:
        # lsof -i :port -t returns PIDs only
        result = subprocess.check_output(['lsof', '-i', f':{port}', '-t'], stderr=subprocess.DEVNULL)
        pids = [int(pid) for pid in result.decode().strip().split('\n') if pid]
        return pids
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        # 如果没有 lsof，回退到 pkill
        print("⚠️ 未找到 lsof 命令，将尝试使用 pkill")
        return []

def kill_process_on_port(port):
    pids = get_pids_on_port(port)
    
    # 如果没有找到 PID，但可能还是有进程（lsof 失败），尝试 pkill 作为保底
    if not pids:
        # print(f"ℹ️ lsof 未找到占用端口 {port} 的进程，尝试 pkill 清理残留...")
        subprocess.run(['pkill', '-f', 'streamlit'], check=False, stderr=subprocess.DEVNULL)
        # 再次检查
        time.sleep(1)
        # 这里的检查可能不准确如果 lsof 失败，但我们假设 lsof 是工作的
    else:
        print(f"⚠️ 发现端口 {port} 被占用，PIDs: {pids}")
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"🔪 已发送 SIGTERM 给进程 {pid}")
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"❌ 无法终止进程 {pid}: {e}")

    # 等待进程结束
    max_retries = 10
    for i in range(max_retries):
        current_pids = get_pids_on_port(port)
        if not current_pids:
            print(f"✅ 端口 {port} 已释放")
            return True
        
        if i == max_retries // 2:
             print("⚠️ 进程未响应，尝试强制终止 (SIGKILL)...")
             for pid in current_pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                    print(f"💀 已发送 SIGKILL 给进程 {pid}")
                except:
                    pass

        time.sleep(1)
        print(f"⏳ 等待端口释放... ({i+1}/{max_retries})")
    
    return False

def main():
    print("🔄 重启推理应用...")

    # 设置工作目录
    work_dir = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
    if os.getcwd() != work_dir:
        try:
            os.chdir(work_dir)
        except Exception as e:
            print(f"⚠️ 无法切换到工作目录: {e}")

    # 端口
    port = 8501

    # 清理缓存 (保留原有逻辑)
    cache_file = "data/learning/llm_cache.json"
    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
            print("✅ 缓存已清理")
        except Exception as e:
            print(f"⚠️ 清理缓存失败: {e}")

    # 终止现有进程并释放端口
    if not kill_process_on_port(port):
        print(f"❌ 无法释放端口 {port}，请手动清理进程后重试")
        # 尝试 netstat 查看情况
        os.system(f"netstat -an | grep {port}")
        return 1

    # 启动新应用
    print("🚀 启动新应用...")
    try:
        proc = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            'src/apps/knowledge_query_app.py',
            '--server.headless', 'true',
            '--server.port', str(port)
        ], cwd=work_dir)

        print(f"✅ 应用启动中，PID: {proc.pid}")
        print("💡 请等待几秒钟让应用完全启动")
        print(f"🔗 访问: http://localhost:{port}")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
