#!/usr/bin/env python3
"""
监控向量知识库构建进度
实时显示构建状态、进度和统计信息

使用方式：
  python scripts/monitor_vector_build.py
  python scripts/monitor_vector_build.py --watch  # 持续监控模式
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def format_duration(seconds):
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

def check_build_status():
    """检查构建状态"""
    metadata_path = Path("data/knowledge_management/metadata.json")
    progress_path = Path("data/knowledge_management/vector_import_progress.json")
    vector_index_path = Path("data/knowledge_management/vector_index.bin")
    log_path = Path("logs/vector_kb_build.log")
    
    status = {
        'metadata_exists': metadata_path.exists(),
        'metadata_entry_count': 0,
        'metadata_size': 0,
        'progress_exists': progress_path.exists(),
        'progress_total': 0,
        'progress_processed': 0,
        'progress_failed': 0,
        'progress_last_update': None,
        'progress_start_time': None,
        'vector_index_exists': vector_index_path.exists(),
        'vector_index_size': 0,
        'log_exists': log_path.exists(),
        'log_size': 0
    }
    
    # 检查元数据
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            status['metadata_entry_count'] = len(metadata.get('entries', {}))
            status['metadata_size'] = metadata_path.stat().st_size
        except Exception:
            pass
    
    # 检查进度文件
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            status['progress_total'] = progress.get('total_items', 0)
            status['progress_processed'] = len(progress.get('processed_item_indices', []))
            status['progress_failed'] = len(progress.get('failed_item_indices', []))
            status['progress_last_update'] = progress.get('last_update')
            status['progress_start_time'] = progress.get('start_time')
        except Exception:
            pass
    
    # 检查向量索引
    if vector_index_path.exists():
        status['vector_index_size'] = vector_index_path.stat().st_size
    
    # 检查日志
    if log_path.exists():
        status['log_size'] = log_path.stat().st_size
    
    return status

def print_status(status, watch_mode=False):
    """打印状态信息"""
    print("\033[2J\033[H" if watch_mode else "")  # 清屏（仅在watch模式）
    print("=" * 70)
    print("📊 向量知识库构建监控")
    print("=" * 70)
    print()
    
    # 元数据状态
    if status['metadata_exists']:
        print(f"✅ 元数据文件: {status['metadata_entry_count']} 条条目")
        print(f"   文件大小: {format_size(status['metadata_size'])}")
    else:
        print("⚠️ 元数据文件: 不存在")
    
    print()
    
    # 进度状态
    if status['progress_exists']:
        total = status['progress_total']
        processed = status['progress_processed']
        failed = status['progress_failed']
        remaining = total - processed
        
        if total > 0:
            progress_pct = (processed / total) * 100
            print(f"📋 构建进度: {processed}/{total} ({progress_pct:.1f}%)")
            print(f"   剩余: {remaining} 条")
            print(f"   失败: {failed} 条")
            
            # 计算预计剩余时间
            if status['progress_start_time'] and processed > 0:
                try:
                    start_time = datetime.fromisoformat(status['progress_start_time'])
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if processed > 0:
                        avg_time_per_item = elapsed / processed
                        estimated_remaining = avg_time_per_item * remaining
                        print(f"   已用时间: {format_duration(elapsed)}")
                        print(f"   预计剩余: {format_duration(estimated_remaining)}")
                except Exception:
                    pass
        else:
            print(f"📋 构建进度: {processed} 条已处理")
        
        if status['progress_last_update']:
            try:
                last_update = datetime.fromisoformat(status['progress_last_update'])
                time_since_update = (datetime.now() - last_update).total_seconds()
                if time_since_update < 60:
                    print(f"   最后更新: {int(time_since_update)}秒前")
                elif time_since_update < 3600:
                    print(f"   最后更新: {int(time_since_update/60)}分钟前")
                else:
                    print(f"   最后更新: {int(time_since_update/3600)}小时前")
            except Exception:
                print(f"   最后更新: {status['progress_last_update']}")
    else:
        print("⚠️ 进度文件: 不存在")
    
    print()
    
    # 向量索引状态
    if status['vector_index_exists']:
        print(f"✅ 向量索引: 存在 ({format_size(status['vector_index_size'])})")
    else:
        print("⚠️ 向量索引: 不存在")
    
    print()
    
    # 日志状态
    if status['log_exists']:
        print(f"📝 日志文件: {format_size(status['log_size'])}")
        print(f"   路径: logs/vector_kb_build.log")
    else:
        print("⚠️ 日志文件: 不存在")
    
    print()
    print("=" * 70)
    
    if watch_mode:
        print("💡 提示: 按 Ctrl+C 退出监控")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description="监控向量知识库构建进度",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--watch",
        action="store_true",
        help="持续监控模式（每5秒刷新一次）"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="监控刷新间隔（秒，默认: 5）"
    )
    
    args = parser.parse_args()
    
    if args.watch:
        try:
            while True:
                status = check_build_status()
                print_status(status, watch_mode=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n✅ 监控已停止")
    else:
        status = check_build_status()
        print_status(status, watch_mode=False)

if __name__ == "__main__":
    main()

