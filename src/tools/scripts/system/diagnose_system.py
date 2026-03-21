#!/usr/bin/env python3
"""
系统诊断脚本 - 检查系统卡住的原因
"""
import asyncio
import time
import psutil
import os
from src.memory.enhanced_faiss_memory import EnhancedFAISSMemory

async def diagnose_system():
    """诊断系统状态"""
    try:
        print("🔍 开始系统诊断...")
        
        # 1. 检查系统资源
        print("\n📊 系统资源状态:")
        print(f"  CPU使用率: {psutil.cpu_percent(interval=1)}%")
        print(f"  内存使用率: {psutil.virtual_memory().percent}%")
        print(f"  磁盘使用率: {psutil.disk_usage('/').percent}%")
        
        # 2. 检查Python进程
        print("\n🐍 Python进程状态:")
        current_process = psutil.Process()
        print(f"  进程ID: {current_process.pid}")
        print(f"  进程状态: {current_process.status()}")
        print(f"  CPU时间: {current_process.cpu_times()}")
        print(f"  内存使用: {current_process.memory_info().rss / 1024 / 1024:.2f} MB")
        
        # 3. 检查FAISS状态
        print("\n🔍 FAISS系统状态:")
        try:
            faiss = EnhancedFAISSMemory()
            print(f"  FAISS实例创建成功")
            print(f"  索引已加载: {faiss._index_loaded}")
            print(f"  初始化任务: {faiss._initialization_task}")
            print(f"  初始化锁状态: {faiss._initialization_lock.locked() if hasattr(faiss._initialization_lock, 'locked') else '无锁'}")
            
            # 检查异步初始化
            print("\n⏳ 测试异步初始化...")
            start_time = time.time()
            success = await faiss.ensure_index_ready()
            end_time = time.time()
            print(f"  异步初始化结果: {success}")
            print(f"  耗时: {end_time - start_time:.3f}秒")
            
        except Exception as e:
            print(f"  FAISS检查失败: {e}")
        
        # 4. 检查文件系统
        print("\n📁 文件系统状态:")
        faiss_path = "data/faiss_memory/faiss_index.bin"
        knowledge_path = "data/faiss_memory/knowledge_entries.json"
        
        if os.path.exists(faiss_path):
            size = os.path.getsize(faiss_path)
            mtime = os.path.getmtime(faiss_path)
            print(f"  FAISS索引文件: 存在, 大小: {size} bytes, 修改时间: {time.ctime(mtime)}")
        else:
            print(f"  FAISS索引文件: 不存在")
            
        if os.path.exists(knowledge_path):
            size = os.path.getsize(knowledge_path)
            mtime = os.path.getmtime(knowledge_path)
            print(f"  知识条目文件: 存在, 大小: {size} bytes, 修改时间: {time.ctime(mtime)}")
        else:
            print(f"  知识条目文件: 不存在")
        
        print("\n✅ 系统诊断完成")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_system())
