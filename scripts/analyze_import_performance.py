#!/usr/bin/env python3
"""
分析向量知识库导入程序的性能
检查优化是否生效，对比性能指标
"""

import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any

def analyze_performance():
    """分析导入性能"""
    print("=" * 80)
    print("🚀 向量知识库导入性能分析")
    print("=" * 80)
    
    log_file = Path("logs/knowledge_management.log")
    if not log_file.exists():
        print("\n⚠️  日志文件不存在: logs/knowledge_management.log")
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 1. 检查Wikipedia抓取性能
    print("\n📊 1. Wikipedia抓取性能")
    print("-" * 80)
    
    fetch_times = []
    fetch_counts = []
    concurrent_counts = []
    
    for line in lines:
        # 检查并发数
        concurrent_match = re.search(r'并发数:\s*(\d+)', line)
        if concurrent_match:
            concurrent_counts.append(int(concurrent_match.group(1)))
        
        # 检查抓取完成
        fetch_match = re.search(r'异步批量抓取完成:\s*(\d+)/(\d+)\s*成功', line)
        if fetch_match:
            success = int(fetch_match.group(1))
            total = int(fetch_match.group(2))
            fetch_counts.append((success, total))
            
            # 尝试提取时间戳
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if time_match:
                fetch_times.append(time_match.group(1))
    
    if concurrent_counts:
        max_concurrent = max(concurrent_counts)
        print(f"   ✅ 并发数: {max_concurrent} (优化后: 10)")
        if max_concurrent == 10:
            print(f"      ✅ 优化已生效（从5提升到10）")
        else:
            print(f"      ⚠️  实际并发数: {max_concurrent}，预期: 10")
    
    if fetch_counts:
        total_fetches = len(fetch_counts)
        total_success = sum(s for s, t in fetch_counts)
        total_attempts = sum(t for s, t in fetch_counts)
        success_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
        print(f"   📥 抓取统计: {total_fetches} 次批量抓取")
        print(f"   ✅ 成功率: {success_rate:.1f}% ({total_success}/{total_attempts})")
    
    # 2. 检查批量向量化性能
    print("\n📊 2. 批量向量化性能")
    print("-" * 80)
    
    batch_vectorization_stats = []
    long_text_batch_stats = []
    
    # 🚀 修复：只分析最近的数据（最后2000行），避免历史数据影响
    recent_lines = lines[-2000:] if len(lines) > 2000 else lines
    
    for line in recent_lines:
        # 批量向量化完成
        batch_match = re.search(r'批量向量化完成:\s*(\d+)\s*个条目.*总耗时:\s*([\d.]+)秒.*平均:\s*([\d.]+)秒/条', line)
        if batch_match:
            count = int(batch_match.group(1))
            total_time = float(batch_match.group(2))
            avg_time = float(batch_match.group(3))
            batch_vectorization_stats.append({
                'count': count,
                'total_time': total_time,
                'avg_time': avg_time
            })
        
        # 长文本批量向量化完成
        long_batch_match = re.search(r'批量向量化长文本完成:\s*(\d+)\s*个条目.*总耗时:\s*([\d.]+)秒.*平均:\s*([\d.]+)秒/条', line)
        if long_batch_match:
            count = int(long_batch_match.group(1))
            total_time = float(long_batch_match.group(2))
            avg_time = float(long_batch_match.group(3))
            long_text_batch_stats.append({
                'count': count,
                'total_time': total_time,
                'avg_time': avg_time
            })
    
    if batch_vectorization_stats:
        total_items = sum(s['count'] for s in batch_vectorization_stats)
        total_time = sum(s['total_time'] for s in batch_vectorization_stats)
        avg_time_per_item = sum(s['avg_time'] for s in batch_vectorization_stats) / len(batch_vectorization_stats)
        
        # 计算最近10个批次的平均（更准确反映当前性能）
        recent_10_avg = 0
        if len(batch_vectorization_stats) >= 10:
            recent_10_stats = batch_vectorization_stats[-10:]
            recent_10_avg = sum(s['avg_time'] for s in recent_10_stats) / len(recent_10_stats)
        
        print(f"   ✅ 批量向量化统计（最近数据）:")
        print(f"      批次数量: {len(batch_vectorization_stats)}")
        print(f"      总条目数: {total_items}")
        print(f"      总耗时: {total_time:.1f}秒")
        print(f"      平均耗时: {avg_time_per_item:.2f}秒/条")
        if recent_10_avg > 0:
            print(f"      最近10批次平均: {recent_10_avg:.2f}秒/条（更准确反映当前性能）")
        print(f"      处理速度: {total_items/total_time*3600:.1f}条目/小时" if total_time > 0 else "      处理速度: N/A")
        
        # 显示最近的几个批次
        print(f"\n      最近批次（前5个）:")
        for i, stat in enumerate(batch_vectorization_stats[-5:], 1):
            print(f"        {i}. {stat['count']}个条目, {stat['total_time']:.1f}秒, 平均{stat['avg_time']:.2f}秒/条")
    
    if long_text_batch_stats:
        total_items = sum(s['count'] for s in long_text_batch_stats)
        total_time = sum(s['total_time'] for s in long_text_batch_stats)
        avg_time_per_item = sum(s['avg_time'] for s in long_text_batch_stats) / len(long_text_batch_stats)
        
        print(f"\n   ✅ 长文本批量向量化统计:")
        print(f"      批次数量: {len(long_text_batch_stats)}")
        print(f"      总条目数: {total_items}")
        print(f"      总耗时: {total_time:.1f}秒")
        print(f"      平均耗时: {avg_time_per_item:.2f}秒/条")
    
    # 3. 检查优化配置
    print("\n📊 3. 优化配置检查")
    print("-" * 80)
    
    optimizations = {
        'batch_size': {'expected': 20, 'found': False},
        'max_concurrent': {'expected': 10, 'found': False},
        'max_text_length': {'expected': 20000, 'found': False},
        'chunk_max_length': {'expected': 12000, 'found': False}
    }
    
    for line in lines:
        # 检查batch_size
        if 'batch_size: int = 20' in line or 'batch_size = 20' in line:
            optimizations['batch_size']['found'] = True
        
        # 检查并发数
        if 'max_concurrent: int = 10' in line or 'max_concurrent=10' in line:
            optimizations['max_concurrent']['found'] = True
        
        # 检查MAX_TEXT_LENGTH_FOR_BATCH
        if 'MAX_TEXT_LENGTH_FOR_BATCH = 20000' in line:
            optimizations['max_text_length']['found'] = True
        
        # 检查chunk max_length
        if 'max_length = 12000' in line and '单块最大长度' in line:
            optimizations['chunk_max_length']['found'] = True
    
    print(f"   优化项检查:")
    for opt_name, opt_info in optimizations.items():
        status = "✅" if opt_info['found'] else "❌"
        print(f"     {status} {opt_name}: 预期={opt_info['expected']}, 状态={'已应用' if opt_info['found'] else '未找到'}")
    
    # 4. 性能对比（如果有历史数据）
    print("\n📊 4. 性能评估")
    print("-" * 80)
    
    if batch_vectorization_stats:
        # 使用最近10个批次的平均，更准确反映当前性能
        if len(batch_vectorization_stats) >= 10:
            recent_10_stats = batch_vectorization_stats[-10:]
            avg_time = sum(s['avg_time'] for s in recent_10_stats) / len(recent_10_stats)
            print(f"   📊 使用最近10批次数据评估（更准确）")
        else:
            avg_time = sum(s['avg_time'] for s in batch_vectorization_stats) / len(batch_vectorization_stats)
            print(f"   📊 使用全部{len(batch_vectorization_stats)}批次数据评估")
        
        # 预期性能（基于优化）
        # 优化前：约2-3秒/条（逐个处理）
        # 优化后：约0.5-1.5秒/条（批量处理）
        expected_avg_time = 1.0  # 秒/条
        
        print(f"   当前平均耗时: {avg_time:.2f}秒/条")
        print(f"   预期平均耗时: {expected_avg_time:.2f}秒/条（批量处理）")
        
        if avg_time <= expected_avg_time * 1.5:
            print(f"   ✅ 性能符合预期（在预期范围内）")
        elif avg_time <= expected_avg_time * 2:
            print(f"   ⚠️  性能略低于预期（可能是API响应慢）")
        else:
            print(f"   ❌ 性能低于预期，可能需要进一步优化")
        
        # 计算性能提升
        baseline_time = 2.5  # 优化前的基准（逐个处理）
        improvement = ((baseline_time - avg_time) / baseline_time) * 100
        print(f"\n   性能提升: {improvement:.1f}% (相对于优化前的{baseline_time}秒/条)")
        
        if improvement > 0:
            print(f"   ✅ 性能已提升")
        else:
            print(f"   ⚠️  性能未提升，可能需要检查优化是否生效")
    
    # 5. 检查是否使用了批量处理
    print("\n📊 5. 批量处理使用情况")
    print("-" * 80)
    
    batch_usage_count = len(batch_vectorization_stats) + len(long_text_batch_stats)
    # 只统计最近数据中的单个处理
    individual_count = len([l for l in recent_lines if '文本过长' in l and '分成' in l and '块进行向量化' in l])
    
    print(f"   批量处理批次: {batch_usage_count}（最近数据）")
    print(f"   单个处理次数: {individual_count}（最近数据）")
    
    if batch_usage_count > individual_count:
        print(f"   ✅ 批量处理使用较多，优化生效")
    elif batch_usage_count > 0:
        print(f"   ⚠️  批量处理已使用，但仍有较多单个处理")
        print(f"   💡 说明: 单个处理主要是长文本分块，这是正常的")
    else:
        print(f"   ❌ 未发现批量处理，可能优化未生效")
    
    # 6. 检查优化是否生效
    print("\n📊 6. 优化生效情况")
    print("-" * 80)
    
    optimizations_status = {
        'Wikipedia并发数': '✅ 已生效（10个并发）' if (concurrent_counts and max(concurrent_counts) == 10) else '❌ 未生效',
        '批量向量化': '✅ 已生效' if batch_usage_count > 0 else '❌ 未生效',
        '批量处理阈值': '✅ 已提高（20000字符）' if any('MAX_TEXT_LENGTH_FOR_BATCH = 20000' in l for l in lines) else '⚠️  需检查',
    }
    
    for opt_name, status in optimizations_status.items():
        print(f"   {status}: {opt_name}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_performance()

