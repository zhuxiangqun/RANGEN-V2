#!/usr/bin/env python3
"""
根目录文件清理脚本
将根目录下的Python文件按功能分类并移动到相应目录
"""

import os
import shutil
import re
from pathlib import Path

def analyze_file_type(filename):
    """分析文件类型"""
    filename_lower = filename.lower()
    
    # 测试相关
    if any(keyword in filename_lower for keyword in ['test', 'eval', 'benchmark']):
        return 'testing'
    
    # 分析相关
    if any(keyword in filename_lower for keyword in ['analysis', 'quality', 'performance', 'intelligent']):
        return 'analysis'
    
    # 修复/优化相关
    if any(keyword in filename_lower for keyword in ['fix', 'optimize', 'debug', 'repair', 'correct']):
        return 'maintenance'
    
    # 评测相关
    if any(keyword in filename_lower for keyword in ['evaluation', 'frames', 'unified_async']):
        return 'evaluation'
    
    # 系统相关
    if any(keyword in filename_lower for keyword in ['system', 'config', 'deploy', 'production']):
        return 'system'
    
    # 工具相关
    if any(keyword in filename_lower for keyword in ['tool', 'util', 'helper', 'manager']):
        return 'tools'
    
    return 'misc'

def create_target_directories():
    """创建目标目录"""
    base_dir = Path(__file__).parent.parent.parent
    directories = [
        'testing/scripts',
        'analysis/scripts', 
        'tools/scripts/maintenance',
        'evaluation/scripts',
        'tools/scripts/system',
        'tools/scripts/misc'
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {full_path}")

def move_files():
    """移动文件到相应目录"""
    base_dir = Path(__file__).parent.parent.parent
    root_dir = base_dir
    moved_count = 0
    skipped_count = 0
    
    # 获取根目录下的所有Python文件
    python_files = [f for f in root_dir.glob("*.py") if f.is_file()]
    
    print(f"📋 发现 {len(python_files)} 个Python文件需要分类")
    
    for file_path in python_files:
        filename = file_path.name
        file_type = analyze_file_type(filename)
        
        # 确定目标目录
        if file_type == 'testing':
            target_dir = root_dir / 'testing' / 'scripts'
        elif file_type == 'analysis':
            target_dir = root_dir / 'analysis' / 'scripts'
        elif file_type == 'maintenance':
            target_dir = root_dir / 'tools' / 'scripts' / 'maintenance'
        elif file_type == 'evaluation':
            target_dir = root_dir / 'evaluation' / 'scripts'
        elif file_type == 'system':
            target_dir = root_dir / 'tools' / 'scripts' / 'system'
        else:
            target_dir = root_dir / 'tools' / 'scripts' / 'misc'
        
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
    print("🧹 开始清理根目录Python文件...")
    print("=" * 50)
    
    # 创建目标目录
    create_target_directories()
    
    # 移动文件
    move_files()
    
    print("\n🎉 根目录文件清理完成！")

if __name__ == "__main__":
    main()
