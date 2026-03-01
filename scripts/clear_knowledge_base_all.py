#!/usr/bin/env python3
"""
清除知识库内容和备份数据
安全地清除所有知识库数据，为重新导入做准备
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def clear_knowledge_base_all():
    """清除所有知识库内容和备份数据"""
    
    print("=" * 80)
    print("清除知识库内容和备份数据")
    print("=" * 80)
    
    # 要清除的路径列表
    paths_to_clear = [
        # 知识库管理系统主数据
        "data/knowledge_management/metadata.json",
        "data/knowledge_management/vector_index.bin",
        "data/knowledge_management/vector_index.mapping.json",
        
        # 知识图谱数据
        "data/knowledge_management/graph/entities.json",
        "data/knowledge_management/graph/relations.json",
        
        # 备份目录
        "data/knowledge_management/backups",
        
        # 旧的FAISS系统
        "data/faiss_memory",
        
        # Wiki知识库
        "data/wiki_knowledge_base.json",
        
        # 向量知识索引
        "data/vector_knowledge_index.bin",
        "data/vector_knowledge_index.metadata",
    ]
    
    # FAISS备份目录（匹配所有备份目录）
    faiss_backup_pattern = "data/faiss_memory_backup_*"
    
    cleared_count = 0
    total_size = 0
    
    print("\n📋 开始清除...\n")
    
    # 清除指定路径
    for path_str in paths_to_clear:
        path = Path(path_str)
        if path.exists():
            try:
                if path.is_file():
                    size = path.stat().st_size
                    path.unlink()
                    print(f"✅ 已删除文件: {path_str} ({size:,} bytes)")
                    cleared_count += 1
                    total_size += size
                elif path.is_dir():
                    # 计算目录大小
                    dir_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    shutil.rmtree(path)
                    print(f"✅ 已删除目录: {path_str}/ ({dir_size:,} bytes)")
                    cleared_count += 1
                    total_size += dir_size
            except Exception as e:
                print(f"❌ 删除失败: {path_str} - {e}")
        else:
            print(f"ℹ️  不存在: {path_str}")
    
    # 清除FAISS备份目录
    print("\n📋 清除FAISS备份目录...\n")
    import glob
    for backup_dir in glob.glob(faiss_backup_pattern):
        backup_path = Path(backup_dir)
        if backup_path.exists() and backup_path.is_dir():
            try:
                dir_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                shutil.rmtree(backup_path)
                print(f"✅ 已删除备份目录: {backup_dir}/ ({dir_size:,} bytes)")
                cleared_count += 1
                total_size += dir_size
            except Exception as e:
                print(f"❌ 删除失败: {backup_dir} - {e}")
    
    # 保留目录结构（但清空内容）
    # 确保必要的目录存在
    Path("data/knowledge_management").mkdir(parents=True, exist_ok=True)
    Path("data/knowledge_management/graph").mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 80)
    print(f"✅ 清除完成!")
    print(f"   删除了 {cleared_count} 个项目")
    print(f"   释放空间: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print("=" * 80)
    
    return cleared_count, total_size

if __name__ == "__main__":
    print("\n⚠️  警告: 此操作将永久删除所有知识库内容和备份数据!")
    response = input("确认要继续吗? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        clear_knowledge_base_all()
        print("\n✅ 知识库已清空，可以重新导入数据了。")
    else:
        print("❌ 操作已取消。")

