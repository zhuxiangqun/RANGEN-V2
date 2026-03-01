#!/usr/bin/env python3
"""
清理知识库数据
清空所有知识条目、向量索引和知识图谱
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


def clear_knowledge_base(
    metadata_path: str = "data/knowledge_management/metadata.json",
    vector_index_path: str = "data/knowledge_management/vector_index.bin",
    mapping_path: str = "data/knowledge_management/vector_index.mapping.json",
    graph_entities_path: str = "data/knowledge_management/graph_entities.json",
    graph_relations_path: str = "data/knowledge_management/graph_relations.json",
    backup: bool = True
) -> bool:
    """
    清理知识库数据
    
    Args:
        metadata_path: 元数据文件路径
        vector_index_path: 向量索引文件路径
        mapping_path: 向量索引映射文件路径
        graph_entities_path: 知识图谱实体文件路径
        graph_relations_path: 知识图谱关系文件路径
        backup: 是否在清理前备份
    
    Returns:
        是否成功
    """
    try:
        metadata_file = Path(metadata_path)
        vector_file = Path(vector_index_path)
        mapping_file = Path(mapping_path)
        entities_file = Path(graph_entities_path)
        relations_file = Path(graph_relations_path)
        
        # 统计现有数据
        entry_count = 0
        vector_count = 0
        entity_count = 0
        relation_count = 0
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entry_count = len(data.get('entries', {}))
        
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
            vector_count = len(mapping) if isinstance(mapping, dict) else 0
        
        if entities_file.exists():
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            entity_count = len(entities) if isinstance(entities, list) else 0
        
        if relations_file.exists():
            with open(relations_file, 'r', encoding='utf-8') as f:
                relations = json.load(f)
            relation_count = len(relations) if isinstance(relations, list) else 0
        
        print("📊 当前知识库状态:")
        print(f"   知识条目: {entry_count} 条")
        print(f"   向量索引: {vector_count} 条")
        print(f"   知识图谱实体: {entity_count} 个")
        print(f"   知识图谱关系: {relation_count} 条")
        
        if entry_count == 0 and vector_count == 0:
            print("\n✅ 知识库已经是空的，无需清理")
            return True
        
        # 备份
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("data/knowledge_management/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_subdir = backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📦 创建备份: {backup_subdir}")
            
            if metadata_file.exists():
                shutil.copy2(metadata_file, backup_subdir / "metadata.json")
            if vector_file.exists():
                shutil.copy2(vector_file, backup_subdir / "vector_index.bin")
            if mapping_file.exists():
                shutil.copy2(mapping_file, backup_subdir / "vector_index.mapping.json")
            if entities_file.exists():
                shutil.copy2(entities_file, backup_subdir / "graph_entities.json")
            if relations_file.exists():
                shutil.copy2(relations_file, backup_subdir / "graph_relations.json")
            
            print(f"   ✅ 备份完成")
        
        # 清理元数据（重置为空结构）
        if metadata_file.exists():
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'entries': {},
                    'content_hash_index': {}
                }, f, ensure_ascii=False, indent=2)
            print("   ✅ 已清空元数据")
        
        # 删除向量索引文件
        if vector_file.exists():
            vector_file.unlink()
            print("   ✅ 已删除向量索引")
        
        if mapping_file.exists():
            mapping_file.unlink()
            print("   ✅ 已删除向量索引映射")
        
        # 清理知识图谱
        if entities_file.exists():
            entities_file.unlink()
            print("   ✅ 已删除知识图谱实体")
        
        if relations_file.exists():
            relations_file.unlink()
            print("   ✅ 已删除知识图谱关系")
        
        print(f"\n✅ 知识库清理完成")
        return True
        
    except Exception as e:
        logger.error(f"清理知识库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理知识库数据")
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不创建备份（默认会备份）'
    )
    
    args = parser.parse_args()
    
    print("🗑️  知识库清理工具")
    print("=" * 60)
    print("\n⚠️  警告：此操作将删除所有知识库数据！")
    
    if not args.no_backup:
        print("   - 清理前会自动创建备份")
    
    response = input("\n确认要继续吗？(yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = clear_knowledge_base(backup=not args.no_backup)
        if success:
            print("\n✅ 清理完成，可以重新导入数据了")
            sys.exit(0)
        else:
            print("\n❌ 清理失败")
            sys.exit(1)
    else:
        print("\n⏭️  已取消清理")
        sys.exit(0)

