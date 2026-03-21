#!/usr/bin/env python3
"""
文档文件清理脚本
将根目录下的文档文件按类型分类并移动到相应目录
"""

import os
import shutil
import re
from pathlib import Path

def analyze_doc_type(filename):
    """分析文档类型"""
    filename_lower = filename.lower()
    
    # 报告类文档
    if any(keyword in filename_lower for keyword in ['report', 'summary', 'analysis', 'status']):
        return 'reports'
    
    # 指南类文档
    if any(keyword in filename_lower for keyword in ['guide', 'manual', 'tutorial', 'reference']):
        return 'guides'
    
    # 架构相关文档
    if any(keyword in filename_lower for keyword in ['architecture', 'refactor', 'structure']):
        return 'architecture'
    
    # 优化相关文档
    if any(keyword in filename_lower for keyword in ['optimization', 'improvement', 'fix', 'hardcode']):
        return 'optimization'
    
    # 安全相关文档
    if any(keyword in filename_lower for keyword in ['security', 'anti_cheat', 'vulnerability']):
        return 'security'
    
    # 配置相关文档
    if any(keyword in filename_lower for keyword in ['config', 'migration', 'setup']):
        return 'config'
    
    # 质量相关文档
    if any(keyword in filename_lower for keyword in ['quality', 'intelligence', 'intelligent']):
        return 'quality'
    
    # 评测相关文档
    if any(keyword in filename_lower for keyword in ['evaluation', 'test', 'benchmark']):
        return 'evaluation'
    
    return 'misc'

def create_doc_directories():
    """创建文档目录"""
    base_dir = Path(__file__).parent.parent.parent
    directories = [
        'docs/reports',
        'docs/guides', 
        'docs/architecture',
        'docs/optimization',
        'docs/security',
        'docs/config',
        'docs/quality',
        'docs/evaluation',
        'docs/misc'
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {full_path}")

def move_doc_files():
    """移动文档文件到相应目录"""
    base_dir = Path(__file__).parent.parent.parent
    root_dir = base_dir
    moved_count = 0
    skipped_count = 0
    
    # 获取根目录下的所有文档文件
    doc_extensions = ['.md', '.txt', '.json']
    doc_files = []
    for ext in doc_extensions:
        doc_files.extend([f for f in root_dir.glob(f"*{ext}") if f.is_file()])
    
    print(f"📋 发现 {len(doc_files)} 个文档文件需要分类")
    
    for file_path in doc_files:
        filename = file_path.name
        doc_type = analyze_doc_type(filename)
        
        # 确定目标目录
        if doc_type == 'reports':
            target_dir = root_dir / 'docs' / 'reports'
        elif doc_type == 'guides':
            target_dir = root_dir / 'docs' / 'guides'
        elif doc_type == 'architecture':
            target_dir = root_dir / 'docs' / 'architecture'
        elif doc_type == 'optimization':
            target_dir = root_dir / 'docs' / 'optimization'
        elif doc_type == 'security':
            target_dir = root_dir / 'docs' / 'security'
        elif doc_type == 'config':
            target_dir = root_dir / 'docs' / 'config'
        elif doc_type == 'quality':
            target_dir = root_dir / 'docs' / 'quality'
        elif doc_type == 'evaluation':
            target_dir = root_dir / 'docs' / 'evaluation'
        else:
            target_dir = root_dir / 'docs' / 'misc'
        
        # 移动文件
        target_path = target_dir / filename
        try:
            shutil.move(str(file_path), str(target_path))
            print(f"✅ 移动: {filename} -> {target_path.relative_to(root_dir)}")
            moved_count += 1
        except Exception as e:
            print(f"❌ 移动失败: {filename} - {e}")
            skipped_count += 1
    
    print(f"\n📊 移动完成:")
    print(f"  - 成功移动: {moved_count} 个文件")
    print(f"  - 跳过: {skipped_count} 个文件")

def main():
    """主函数"""
    print("📚 开始清理根目录文档文件...")
    print("=" * 50)
    
    # 创建目标目录
    create_doc_directories()
    
    # 移动文件
    move_doc_files()
    
    print("\n🎉 根目录文档文件清理完成！")

if __name__ == "__main__":
    main()
