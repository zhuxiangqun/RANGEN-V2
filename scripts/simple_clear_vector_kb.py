#!/usr/bin/env python3
"""
简化的向量知识库清理脚本
绕过复杂的依赖，直接清理文件
"""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime
import sys


def simple_clear_vector_knowledge_base(backup: bool = True) -> bool:
    """
    简化的向量知识库清理函数，不依赖复杂的ML库

    Args:
        backup: 是否在清理前备份

    Returns:
        是否成功
    """
    print("🧹 开始简化的向量知识库清理...")

    # 定义要清理的文件路径
    files_to_clear = [
        "data/knowledge_management/metadata.json",
        "data/knowledge_management/vector_index.bin",
        "data/knowledge_management/vector_index.mapping.json",
        "data/knowledge_management/vector_import_progress.json",
        "data/knowledge_management/bayesian_optimization.json",
        "data/knowledge_management/embedding_cache.json",
    ]

    # 统计信息
    total_files = 0
    cleared_files = 0
    backup_count = 0

    try:
        # 创建备份目录
        if backup:
            backup_dir = f"data/knowledge_management/backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            print(f"💾 创建备份目录: {backup_dir}")

        # 清理每个文件
        for file_path in files_to_clear:
            file_obj = Path(file_path)

            if file_obj.exists():
                total_files += 1
                print(f"📄 发现文件: {file_path}")

                # 创建备份
                if backup:
                    try:
                        backup_path = Path(backup_dir) / file_obj.name
                        shutil.copy2(file_obj, backup_path)
                        backup_count += 1
                        print(f"✅ 已备份: {file_path} -> {backup_path}")
                    except Exception as e:
                        print(f"⚠️ 备份失败 {file_path}: {e}")

                # 删除文件
                try:
                    if file_obj.is_file():
                        file_obj.unlink()
                        cleared_files += 1
                        print(f"🗑️ 已删除: {file_path}")
                    elif file_obj.is_dir():
                        shutil.rmtree(file_obj)
                        cleared_files += 1
                        print(f"🗑️ 已删除目录: {file_path}")
                except Exception as e:
                    print(f"❌ 删除失败 {file_path}: {e}")
            else:
                print(f"ℹ️ 文件不存在: {file_path}")

        # 清理空的备份目录（如果没有备份任何文件）
        if backup and backup_count == 0:
            try:
                os.rmdir(backup_dir)
                print(f"ℹ️ 删除空的备份目录: {backup_dir}")
            except:
                pass

        print("\n📊 清理统计:")
        print(f"   • 发现文件: {total_files} 个")
        print(f"   • 成功清理: {cleared_files} 个")
        if backup:
            print(f"   • 成功备份: {backup_count} 个")

        return True

    except Exception as e:
        print(f"❌ 清理过程中出现错误: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="简化的向量知识库清理工具")
    parser.add_argument("--no-backup", action="store_true",
                       help="不创建备份（默认会备份）")

    args = parser.parse_args()

    print("=" * 50)
    print("🧹 简化的向量知识库清理工具")
    print("=" * 50)
    print()

    if args.no_backup:
        print("⚠️ 警告: 已禁用备份功能，清理的文件将无法恢复")
        backup = False
    else:
        print("💾 将自动创建备份")
        backup = True

    print()

    # 执行清理
    success = simple_clear_vector_knowledge_base(backup=backup)

    print()
    if success:
        print("✅ 向量知识库清理完成！")
        print("💡 提示: 重启相关服务后，知识库将被重新构建")
    else:
        print("❌ 向量知识库清理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
