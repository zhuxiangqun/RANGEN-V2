#!/usr/bin/env python3
"""
缓存健康检查与清理工具
功能：
1. 扫描缓存文件，识别无效或污染条目
2. 验证缓存键的合理性
3. 提供清理和修复选项
"""

import json
import os
import sys
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List

# 配置
CACHE_FILE = Path("data/learning/llm_cache.json")
BACKUP_FILE = Path("data/learning/llm_cache.json.bak")

def load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        print(f"❌ 缓存文件不存在: {CACHE_FILE}")
        return {}
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载缓存失败: {e}")
        return {}

def save_cache(cache: Dict[str, Any], backup: bool = True):
    if backup and CACHE_FILE.exists():
        import shutil
        shutil.copy2(CACHE_FILE, BACKUP_FILE)
        print(f"✅ 已备份缓存到: {BACKUP_FILE}")
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"✅ 已保存 {len(cache)} 条缓存记录")

def is_corrupted(key: str, entry: Dict[str, Any]) -> bool:
    """检查缓存条目是否污染"""
    if not isinstance(entry, dict):
        return True
        
    response = entry.get('response', '')
    if not response:
        return True
        
    response_lower = str(response).lower().strip()
    
    # 1. 基础无效响应
    invalid_responses = [
        "no question provided",
        "查询为空",
        "query is empty",
        "[error]",
        "error:",
        "reasoning task failed",
        "failed due to api timeout",
        "api call failed"
    ]
    
    if any(inv in response_lower for inv in invalid_responses):
        return True
        
    # 2. 幻觉检测 (针对已知问题)
    # 如果响应包含"Chinese Academy of Sciences"但看起来不像是一个关于它的查询
    # 这里只能做简单的启发式检查，因为我们没有原始查询
    if "chinese academy of sciences" in response_lower:
        # 如果缓存键中包含 united states 等词，或者是 generate_reasoning_steps 函数
        if "united states" in key.lower() or "president" in key.lower():
            return True
            
    return False

def analyze_cache():
    """分析缓存健康状况"""
    cache = load_cache()
    if not cache:
        return
    
    print(f"\n🔍 开始分析缓存 (共 {len(cache)} 条)...")
    
    corrupted_keys = []
    expired_keys = []
    valid_keys = []
    
    current_time = time.time()
    ttl = 86400 # 24小时
    
    for key, entry in cache.items():
        # 检查过期
        timestamp = entry.get('timestamp', 0)
        age = current_time - timestamp
        
        if age > ttl:
            expired_keys.append(key)
            continue
            
        # 检查污染
        if is_corrupted(key, entry):
            corrupted_keys.append(key)
            continue
            
        valid_keys.append(key)
    
    print(f"\n📊 分析结果:")
    print(f"   ✅ 有效条目: {len(valid_keys)}")
    print(f"   ⏳ 过期条目: {len(expired_keys)}")
    print(f"   ☣️  污染条目: {len(corrupted_keys)}")
    
    if corrupted_keys:
        print("\n⚠️ 发现以下污染条目示例:")
        for k in corrupted_keys[:3]:
            resp = cache[k].get('response', '')[:50].replace('\n', ' ')
            print(f"   - Key: {k[:20]}... | Resp: {resp}...")
            
    return cache, corrupted_keys, expired_keys

def clean_cache(dry_run: bool = True):
    """清理缓存"""
    cache, corrupted, expired = analyze_cache()
    
    to_delete = corrupted + expired
    
    if not to_delete:
        print("\n✨ 缓存健康，无需清理")
        return
        
    if dry_run:
        print(f"\n📢 [预演] 将清理 {len(to_delete)} 条记录")
        print("   (使用 --run 参数执行实际清理)")
    else:
        for k in to_delete:
            del cache[k]
        save_cache(cache)
        print(f"\n🧹 已清理 {len(to_delete)} 条记录")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        clean_cache(dry_run=False)
    else:
        clean_cache(dry_run=True)
