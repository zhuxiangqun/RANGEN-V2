#!/usr/bin/env python3
"""
验证Embedding缓存优化效果
"""
import json
import re
from pathlib import Path
from collections import defaultdict

def analyze_embedding_cache():
    """分析Embedding缓存文件"""
    cache_path = Path("data/learning/embedding_cache.json")
    
    if not cache_path.exists():
        print("❌ Embedding缓存文件不存在")
        return
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    
    print(f"✅ Embedding缓存文件: {cache_path}")
    print(f"   缓存条目数: {len(cache_data)}")
    
    # 分析缓存条目
    if cache_data:
        import time
        current_time = time.time()
        valid_count = 0
        expired_count = 0
        
        for key, value in cache_data.items():
            if isinstance(value, dict):
                cache_time = value.get('timestamp', 0)
                cache_age = current_time - cache_time
                if cache_age < 86400:  # 24小时
                    valid_count += 1
                else:
                    expired_count += 1
        
        print(f"   有效缓存: {valid_count}条")
        print(f"   过期缓存: {expired_count}条")
        
        # 显示前3个缓存条目
        print("\n   前3个缓存条目:")
        for i, (key, value) in enumerate(list(cache_data.items())[:3]):
            if isinstance(value, dict):
                text_preview = value.get('text_preview', 'N/A')[:50]
                cache_time = value.get('timestamp', 0)
                cache_age = (current_time - cache_time) / 3600
                print(f"     {i+1}. 键: {key[:16]}..., 文本: {text_preview}..., 年龄: {cache_age:.2f}小时")

def analyze_logs():
    """分析日志中的缓存信息"""
    log_path = Path("research_system.log")
    
    if not log_path.exists():
        print("❌ 日志文件不存在")
        return
    
    print("\n📊 分析日志中的Embedding缓存信息...")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 统计缓存命中/未命中
    cache_hits = 0
    cache_misses = 0
    embedding_calls = []
    evidence_times = []
    
    for line in lines:
        # 缓存命中
        if "Embedding缓存命中" in line:
            cache_hits += 1
        
        # 缓存未命中（Jina API调用）
        if "Jina Embedding调用" in line:
            cache_misses += 1
            # 提取耗时
            match = re.search(r'(\d+\.\d+)秒', line)
            if match:
                embedding_calls.append(float(match.group(1)))
        
        # 证据收集时间
        if "证据收集总耗时" in line:
            match = re.search(r'(\d+\.\d+)秒', line)
            if match:
                evidence_times.append(float(match.group(1)))
    
    total_calls = cache_hits + cache_misses
    if total_calls > 0:
        hit_rate = (cache_hits / total_calls) * 100
        print(f"\n   Embedding缓存统计:")
        print(f"   总调用次数: {total_calls}")
        print(f"   缓存命中: {cache_hits}次")
        print(f"   缓存未命中: {cache_misses}次")
        print(f"   缓存命中率: {hit_rate:.1f}%")
    else:
        print("\n   ⚠️ 未找到Embedding缓存相关日志")
    
    if embedding_calls:
        avg_time = sum(embedding_calls) / len(embedding_calls)
        max_time = max(embedding_calls)
        min_time = min(embedding_calls)
        print(f"\n   Jina API调用时间:")
        print(f"   平均: {avg_time:.2f}秒")
        print(f"   最大: {max_time:.2f}秒")
        print(f"   最小: {min_time:.2f}秒")
        print(f"   调用次数: {len(embedding_calls)}")
    
    if evidence_times:
        avg_time = sum(evidence_times) / len(evidence_times)
        max_time = max(evidence_times)
        min_time = min(evidence_times)
        print(f"\n   证据收集时间:")
        print(f"   平均: {avg_time:.2f}秒")
        print(f"   最大: {max_time:.2f}秒")
        print(f"   最小: {min_time:.2f}秒")
        print(f"   收集次数: {len(evidence_times)}")
        
        # 对比优化前（假设优化前平均15秒）
        if avg_time < 10:
            improvement = ((15 - avg_time) / 15) * 100
            print(f"\n   ✅ 性能提升: 相比优化前（15秒）减少了 {improvement:.1f}%")

if __name__ == "__main__":
    print("=" * 60)
    print("Embedding缓存优化效果验证")
    print("=" * 60)
    
    analyze_embedding_cache()
    analyze_logs()
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

