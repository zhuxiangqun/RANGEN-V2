#!/usr/bin/env python3
"""
快速检查测试状态
"""
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_test_status():
    """检查测试状态"""
    print("=" * 60)
    print("🔍 测试状态检查")
    print("=" * 60)
    
    # 检查是否有测试日志文件
    log_files = [
        "tests/test_output.log",
        "tests/test_errors.log",
        ".pytest_cache/v/cache/lastfailed"
    ]
    
    print("\n📋 检查测试日志文件:")
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            size = log_path.stat().st_size
            mtime = time.ctime(log_path.stat().st_mtime)
            print(f"  ✅ {log_file} (大小: {size} 字节, 修改时间: {mtime})")
        else:
            print(f"  ❌ {log_file} (不存在)")
    
    # 检查 pytest 缓存
    cache_dir = Path(".pytest_cache")
    if cache_dir.exists():
        print(f"\n📋 Pytest 缓存目录存在")
        cache_files = list(cache_dir.rglob("*"))
        if cache_files:
            print(f"  找到 {len(cache_files)} 个缓存文件")
        else:
            print(f"  缓存目录为空")
    else:
        print(f"\n📋 Pytest 缓存目录不存在")
    
    # 检查临时文件
    temp_dirs = [
        "tests/temp",
        "tests/checkpoints"
    ]
    
    print("\n📋 检查临时目录:")
    for temp_dir in temp_dirs:
        temp_path = Path(temp_dir)
        if temp_path.exists():
            files = list(temp_path.glob("*"))
            print(f"  ✅ {temp_dir} (包含 {len(files)} 个文件)")
            if files:
                # 显示最新的文件
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                mtime = time.ctime(latest_file.stat().st_mtime)
                print(f"    最新文件: {latest_file.name} (修改时间: {mtime})")
        else:
            print(f"  ❌ {temp_dir} (不存在)")
    
    print("\n" + "=" * 60)
    print("💡 诊断建议:")
    print("=" * 60)
    print("1. 如果测试卡在某个查询，可能是:")
    print("   - LLM API 调用超时（网络问题或API限流）")
    print("   - 工作流内部超时（600秒）")
    print("   - 测试超时（5-10分钟）")
    print("\n2. 检查方法:")
    print("   - 查看终端输出，看卡在哪个测试")
    print("   - 按 Ctrl-C 中断测试（支持优雅退出）")
    print("   - 检查网络连接和 API 服务状态")
    print("\n3. 如果测试确实卡住:")
    print("   - 按 Ctrl-C 一次：优雅退出（3秒内）")
    print("   - 按 Ctrl-C 两次：强制退出")
    print("   - 然后运行单个测试: python tests/run_single_test.py <测试编号>")
    print("\n4. 测试超时设置:")
    print("   - 简单查询: 5分钟 (300秒)")
    print("   - 复杂查询: 10分钟 (600秒)")
    print("   - 多查询: 每个查询5分钟")
    print("   - 并发查询: 总共10分钟")
    print("=" * 60)

if __name__ == "__main__":
    check_test_status()
