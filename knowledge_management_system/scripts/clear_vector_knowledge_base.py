#!/usr/bin/env python3
"""
清除向量知识库数据
只清除知识条目、向量索引，不清除知识图谱
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


def clear_vector_knowledge_base(
    metadata_path: str = "data/knowledge_management/metadata.json",
    vector_index_path: str = "data/knowledge_management/vector_index.bin",
    mapping_path: str = "data/knowledge_management/vector_index.mapping.json",
    backup: bool = True
) -> bool:
    """
    清除向量知识库数据（不清除知识图谱）
    
    Args:
        metadata_path: 元数据文件路径
        vector_index_path: 向量索引文件路径
        mapping_path: 向量索引映射文件路径
        backup: 是否在清理前备份
    
    Returns:
        是否成功
    """
    try:
        metadata_file = Path(metadata_path)
        vector_file = Path(vector_index_path)
        mapping_file = Path(mapping_path)
        
        # 统计现有数据
        entry_count = 0
        vector_count = 0
        metadata_corrupted = False
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                entry_count = len(data.get('entries', {}))
            except (json.JSONDecodeError, ValueError) as e:
                # 🚀 修复：JSON文件损坏时，仍然可以清理
                logger.warning(f"⚠️  元数据文件可能损坏，无法解析: {e}")
                print(f"   ⚠️  警告: 元数据文件可能损坏（JSON解析失败）")
                print(f"   💡 提示: 将直接删除损坏的文件")
                metadata_corrupted = True
                # 尝试获取文件大小作为参考
                try:
                    file_size = metadata_file.stat().st_size
                    print(f"   📁 文件大小: {file_size / 1024 / 1024:.2f} MB")
                except:
                    pass
        
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                vector_count = len(mapping) if isinstance(mapping, dict) else 0
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️  向量索引映射文件可能损坏，无法解析: {e}")
                print(f"   ⚠️  警告: 向量索引映射文件可能损坏（JSON解析失败）")
        
        print("📊 当前向量知识库状态:")
        if metadata_corrupted:
            print(f"   知识条目: ⚠️  文件损坏，无法统计")
        else:
            print(f"   知识条目: {entry_count} 条")
        print(f"   向量索引: {vector_count} 条")
        
        if not metadata_corrupted and entry_count == 0 and vector_count == 0:
            print("\n✅ 向量知识库已经是空的，无需清理")
            return True
        
        # 备份
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("data/knowledge_management/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_subdir = backup_dir / f"vector_backup_{timestamp}"
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📦 创建备份: {backup_subdir}")
            
            # 🚀 修复：即使JSON文件损坏，也尝试备份（直接复制文件）
            if metadata_file.exists():
                try:
                    shutil.copy2(metadata_file, backup_subdir / "metadata.json")
                    print(f"   ✅ 已备份元数据文件")
                except Exception as e:
                    logger.warning(f"备份元数据文件失败: {e}")
                    print(f"   ⚠️  备份元数据文件失败: {e}")
            
            if vector_file.exists():
                try:
                    shutil.copy2(vector_file, backup_subdir / "vector_index.bin")
                    print(f"   ✅ 已备份向量索引文件")
                except Exception as e:
                    logger.warning(f"备份向量索引文件失败: {e}")
                    print(f"   ⚠️  备份向量索引文件失败: {e}")
            
            if mapping_file.exists():
                try:
                    shutil.copy2(mapping_file, backup_subdir / "vector_index.mapping.json")
                    print(f"   ✅ 已备份向量索引映射文件")
                except Exception as e:
                    logger.warning(f"备份向量索引映射文件失败: {e}")
                    print(f"   ⚠️  备份向量索引映射文件失败: {e}")
            
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
        
        # 清除失败记录文件（与向量知识库相关）
        failed_entries_file = Path("data/knowledge_management/failed_entries.json")
        if failed_entries_file.exists():
            failed_entries_file.unlink()
            print("   ✅ 已删除失败记录文件")
        
        # 清除进度文件（与向量知识库相关）
        # 🚀 修复：清除所有相关的进度文件
        progress_files = [
            Path("data/knowledge_management/vector_import_progress.json"),  # build_vector_knowledge_base.py 使用的
            Path("data/knowledge_management/import_progress.json")  # import_wikipedia_from_frames.py 使用的
        ]
        for progress_file in progress_files:
            if progress_file.exists():
                progress_file.unlink()
                print(f"   ✅ 已删除进度文件: {progress_file.name}")
        
        print(f"\n✅ 向量知识库清理完成")
        print("   ⚠️  注意：知识图谱数据未被清除（如需清除，请使用 clear_knowledge_graph.py）")
        return True
        
    except Exception as e:
        logger.error(f"清理向量知识库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="清除向量知识库数据（不清除知识图谱）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 清除向量知识库（自动备份）
  python clear_vector_knowledge_base.py
  
  # 清除向量知识库（不备份）
  python clear_vector_knowledge_base.py --no-backup
        """
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不创建备份（默认会备份）'
    )
    
    args = parser.parse_args()
    
    print("🗑️  向量知识库清理工具")
    print("=" * 70)
    print("\n⚠️  警告：此操作将删除所有向量知识库数据！")
    print("   - 知识条目")
    print("   - 向量索引")
    print("   - 向量索引映射")
    print("   - 失败记录")
    print("   - 导入进度")
    print()
    print("   ⚠️  知识图谱数据不会被清除（如需清除，请使用 clear_knowledge_graph.py）")
    
    if not args.no_backup:
        print("   - 清理前会自动创建备份")
    
    response = input("\n确认要继续吗？(yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = clear_vector_knowledge_base(backup=not args.no_backup)
        if success:
            print("\n✅ 清理完成，可以重新导入向量数据了")
            sys.exit(0)
        else:
            print("\n❌ 清理失败")
            sys.exit(1)
    else:
        print("\n⏭️  已取消清理")
        sys.exit(0)

