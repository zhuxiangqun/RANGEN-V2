#!/usr/bin/env python3
"""
清除知识图谱数据
只清除知识图谱实体和关系，不清除向量知识库
"""

import json
import shutil
from pathlib import Path
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def clear_knowledge_graph(
    graph_entities_path: str = "data/knowledge_management/graph/entities.json",
    graph_relations_path: str = "data/knowledge_management/graph/relations.json",
    backup: bool = True
) -> bool:
    """
    清除知识图谱数据（不清除向量知识库）
    
    Args:
        graph_entities_path: 知识图谱实体文件路径
        graph_relations_path: 知识图谱关系文件路径
        backup: 是否在清理前备份
    
    Returns:
        是否成功
    """
    try:
        entities_file = Path(graph_entities_path)
        relations_file = Path(graph_relations_path)
        
        # 统计现有数据
        entity_count = 0
        relation_count = 0
        
        if entities_file.exists():
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            # 🚀 修复：实体存储为字典格式 {entity_id: entity_data}，关系存储为列表格式
            if isinstance(entities, dict):
                entity_count = len(entities)
            elif isinstance(entities, list):
                entity_count = len(entities)
            else:
                entity_count = 0
        
        if relations_file.exists():
            with open(relations_file, 'r', encoding='utf-8') as f:
                relations = json.load(f)
            # 🚀 修复：关系存储为列表格式
            if isinstance(relations, list):
                relation_count = len(relations)
            elif isinstance(relations, dict):
                relation_count = len(relations)
            else:
                relation_count = 0
        
        print("📊 当前知识图谱状态:")
        print(f"   实体: {entity_count} 个")
        print(f"   关系: {relation_count} 条")
        
        # 🚀 修复：即使知识图谱是空的，也要检查并删除进度文件
        graph_cleared = (entity_count == 0 and relation_count == 0)
        
        if graph_cleared:
            print("\n✅ 知识图谱已经是空的，无需清理数据文件")
        
        # 备份（只在有数据时备份）
        if not graph_cleared and backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("data/knowledge_management/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_subdir = backup_dir / f"graph_backup_{timestamp}"
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📦 创建备份: {backup_subdir}")
            
            if entities_file.exists():
                shutil.copy2(entities_file, backup_subdir / "graph_entities.json")
            if relations_file.exists():
                shutil.copy2(relations_file, backup_subdir / "graph_relations.json")
            
            print(f"   ✅ 备份完成")
        
        # 删除知识图谱文件（只在有数据时删除）
        if not graph_cleared:
            if entities_file.exists():
                entities_file.unlink()
                print("   ✅ 已删除知识图谱实体文件")
            
            if relations_file.exists():
                relations_file.unlink()
                print("   ✅ 已删除知识图谱关系文件")
        
        # 🚀 修复：无论知识图谱是否为空，都要清除进度文件
        graph_progress_file = Path("data/knowledge_management/graph_progress.json")
        if graph_progress_file.exists():
            graph_progress_file.unlink()
            print("   ✅ 已删除知识图谱构建进度文件")
        
        print(f"\n✅ 知识图谱清理完成")
        print("   ⚠️  注意：向量知识库数据未被清除（如需清除，请使用 clear_vector_knowledge_base.py）")
        return True
        
    except Exception as e:
        logger.error(f"清理知识图谱失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="清除知识图谱数据（不清除向量知识库）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 清除知识图谱（自动备份）
  python clear_knowledge_graph.py
  
  # 清除知识图谱（不备份）
  python clear_knowledge_graph.py --no-backup
        """
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不创建备份（默认会备份）'
    )
    
    args = parser.parse_args()
    
    print("🗑️  知识图谱清理工具")
    print("=" * 70)
    print("\n⚠️  警告：此操作将删除所有知识图谱数据！")
    print("   - 知识图谱实体")
    print("   - 知识图谱关系")
    print("   - 构建进度")
    print()
    print("   ⚠️  向量知识库数据不会被清除（如需清除，请使用 clear_vector_knowledge_base.py）")
    
    if not args.no_backup:
        print("   - 清理前会自动创建备份")
    
    response = input("\n确认要继续吗？(yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = clear_knowledge_graph(backup=not args.no_backup)
        if success:
            print("\n✅ 清理完成，可以重新构建知识图谱了")
            sys.exit(0)
        else:
            print("\n❌ 清理失败")
            sys.exit(1)
    else:
        print("\n⏭️  已取消清理")
        sys.exit(0)

