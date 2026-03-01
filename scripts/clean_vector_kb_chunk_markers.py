#!/usr/bin/env python3
"""
清理向量知识库中的分块标记残留
移除内容中的 [第X级: ...] 标记，统一内容格式

使用方式:
  python scripts/clean_vector_kb_chunk_markers.py
  python scripts/clean_vector_kb_chunk_markers.py --dry-run  # 仅检查，不修改
  python scripts/clean_vector_kb_chunk_markers.py --backup  # 清理前创建备份
"""

import json
import sys
import re
import argparse
import shutil
from pathlib import Path
from datetime import datetime

def clean_chunk_markers(content: str) -> str:
    """
    清理内容中的分块标记
    
    Args:
        content: 原始内容
        
    Returns:
        清理后的内容
    """
    if not isinstance(content, str):
        return content
    
    # 移除 [第X级: ...] 标记
    cleaned = re.sub(r'\[第\d+级:[^\]]+\]\s*', '', content)
    
    # 移除可能的重复标题（如果标记后面紧跟着重复的标题）
    # 例如: [第2级: Title] Title -> Title
    cleaned = re.sub(r'^([^\n]+)\1\s*', r'\1', cleaned, flags=re.MULTILINE)
    
    return cleaned.strip()

def clean_vector_kb_chunk_markers(
    metadata_path: str = "data/knowledge_management/metadata.json",
    dry_run: bool = False,
    backup: bool = True
) -> dict:
    """
    清理向量知识库中的分块标记
    
    Args:
        metadata_path: 元数据文件路径
        dry_run: 是否仅检查不修改
        backup: 是否创建备份
        
    Returns:
        清理统计信息
    """
    metadata_file = Path(metadata_path)
    
    if not metadata_file.exists():
        print(f"❌ 元数据文件不存在: {metadata_path}")
        sys.exit(1)
    
    # 加载元数据
    print("📖 正在加载元数据文件...")
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    entries = metadata.get('entries', {})
    print(f"✅ 已加载 {len(entries)} 个条目\n")
    
    # 统计信息
    stats = {
        'total': len(entries),
        'cleaned': 0,
        'unchanged': 0,
        'errors': 0
    }
    
    # 检查并清理
    print("=" * 70)
    print("🔍 检查分块标记...")
    print("=" * 70)
    
    cleaned_entries = []
    
    for kid, entry in entries.items():
        meta = entry.get('metadata', {})
        content = meta.get('content', '')
        
        if not isinstance(content, str):
            stats['unchanged'] += 1
            continue
        
        # 检查是否有分块标记
        has_marker = '[第' in content and '级:' in content
        
        if has_marker:
            # 清理内容
            cleaned_content = clean_chunk_markers(content)
            
            if cleaned_content != content:
                cleaned_entries.append({
                    'id': kid,
                    'title': meta.get('title', '')[:60],
                    'original_length': len(content),
                    'cleaned_length': len(cleaned_content),
                    'original_preview': content[:100],
                    'cleaned_preview': cleaned_content[:100]
                })
                
                if not dry_run:
                    # 更新内容
                    meta['content'] = cleaned_content
                    # 更新 content_preview
                    entry['content_preview'] = cleaned_content[:200] if isinstance(cleaned_content, str) else str(cleaned_content)[:200]
                
                stats['cleaned'] += 1
            else:
                stats['unchanged'] += 1
        else:
            stats['unchanged'] += 1
    
    # 显示结果
    print(f"\n📊 清理统计:")
    print(f"   总条目数: {stats['total']}")
    print(f"   需要清理: {stats['cleaned']}")
    print(f"   无需清理: {stats['unchanged']}")
    print(f"   错误: {stats['errors']}")
    
    if cleaned_entries:
        print(f"\n📋 清理示例（前5个）:")
        for i, item in enumerate(cleaned_entries[:5]):
            print(f"\n   示例 {i+1}:")
            print(f"   标题: {item['title']}")
            print(f"   原始长度: {item['original_length']} 字符")
            print(f"   清理后长度: {item['cleaned_length']} 字符")
            print(f"   原始预览: {item['original_preview']}...")
            print(f"   清理后预览: {item['cleaned_preview']}...")
    
    # 如果不是dry-run，保存修改
    if not dry_run and stats['cleaned'] > 0:
        # 创建备份
        if backup:
            backup_path = metadata_file.parent / f"metadata_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            print(f"\n💾 创建备份: {backup_path}")
            shutil.copy2(metadata_file, backup_path)
            print(f"   ✅ 备份完成")
        
        # 保存修改后的元数据（使用原子性写入）
        print(f"\n💾 保存清理后的元数据...")
        temp_file = metadata_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            # 原子性重命名
            temp_file.replace(metadata_file)
            print(f"   ✅ 已保存 {stats['cleaned']} 个条目的清理结果")
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
            if temp_file.exists():
                temp_file.unlink()
            sys.exit(1)
    elif dry_run:
        print(f"\n💡 这是预览模式（--dry-run），未实际修改文件")
        print(f"   如需实际清理，请移除 --dry-run 参数")
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="清理向量知识库中的分块标记残留",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--metadata-path",
        type=str,
        default="data/knowledge_management/metadata.json",
        help="元数据文件路径（默认: data/knowledge_management/metadata.json）"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅检查不修改（预览模式）"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不创建备份（默认会创建备份）"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧹 向量知识库分块标记清理工具")
    print("=" * 70)
    print()
    
    if args.dry_run:
        print("⚠️  预览模式：仅检查，不会修改文件")
    else:
        if not args.no_backup:
            print("💾 将自动创建备份")
        else:
            print("⚠️  不会创建备份（使用 --no-backup）")
    
    print()
    
    stats = clean_vector_kb_chunk_markers(
        metadata_path=args.metadata_path,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    
    print("\n" + "=" * 70)
    if stats['cleaned'] > 0:
        if args.dry_run:
            print("✅ 检查完成！发现需要清理的条目")
        else:
            print("✅ 清理完成！")
    else:
        print("✅ 未发现需要清理的条目")
    print("=" * 70)
    
    return 0 if stats['errors'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

