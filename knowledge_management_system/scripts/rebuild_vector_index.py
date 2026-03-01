#!/usr/bin/env python3
"""
重建向量索引脚本
当切换embedding模型时，使用此脚本重建向量索引

使用方法:
  python rebuild_vector_index.py
  python rebuild_vector_index.py --force  # 强制重建（即使维度匹配）
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def check_dimension_match(service) -> bool:
    """检查当前embedding模型的维度是否与索引维度匹配"""
    try:
        # 获取当前embedding模型的维度
        text_processor = service.index_builder.processors.get('text')
        if not text_processor:
            logger.error("无法获取文本处理器")
            return False
        
        current_dimension = text_processor.get_dimension()
        index_dimension = service.index_builder.dimension
        
        logger.info(f"当前embedding模型维度: {current_dimension}")
        logger.info(f"向量索引维度: {index_dimension}")
        
        if current_dimension == index_dimension:
            logger.info("✅ 维度匹配，无需重建索引")
            return True
        else:
            logger.warning(f"⚠️ 维度不匹配（当前: {current_dimension}, 索引: {index_dimension}），需要重建索引")
            return False
    except Exception as e:
        logger.error(f"检查维度失败: {e}")
        return False


def rebuild_vector_index(force: bool = False) -> bool:
    """重建向量索引"""
    try:
        service = get_knowledge_service()
        
        # 检查是否需要重建
        if not force:
            # 检查索引是否存在
            index_path = Path(service.index_builder.index_path)
            if not index_path.exists():
                logger.info("向量索引不存在，将创建新索引")
            else:
                # 检查维度是否匹配
                if check_dimension_match(service):
                    logger.info("维度匹配，跳过重建。如需强制重建，请使用 --force 参数")
                    return True
        
        # 获取统计信息
        stats = service.get_statistics()
        total_entries = stats.get('vector_index_size', 0)
        
        if total_entries == 0:
            logger.warning("⚠️ 向量索引为空，无需重建")
            logger.info("💡 提示: 请先导入知识，系统会自动建立向量索引")
            return True
        
        logger.info(f"开始重建向量索引，共 {total_entries} 条知识")
        
        # 重建索引
        success = service.rebuild_index()
        
        if success:
            logger.info("✅ 向量索引重建成功")
            
            # 显示新的统计信息
            new_stats = service.get_statistics()
            new_total = new_stats.get('vector_index_size', 0)
            logger.info(f"重建后的索引大小: {new_total} 条")
            
            # 显示当前embedding模型信息
            text_processor = service.index_builder.processors.get('text')
            if text_processor:
                if text_processor.use_local_model:
                    # 获取模型名称（从环境变量或默认值）
                    model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                    logger.info(f"当前使用: 本地模型 ({model_name})")
                else:
                    logger.info(f"当前使用: Jina API ({text_processor.model})")
                logger.info(f"向量维度: {text_processor.get_dimension()}")
            
            return True
        else:
            logger.error("❌ 向量索引重建失败")
            return False
            
    except Exception as e:
        logger.error(f"重建向量索引时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="重建向量索引（当切换embedding模型时使用）")
    parser.add_argument("--force", action="store_true", help="强制重建（即使维度匹配）")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 向量索引重建工具")
    print("=" * 70)
    print()
    print("此工具用于重建向量索引，通常在以下情况使用：")
    print("  1. 切换embedding模型（如从Jina API切换到本地模型）")
    print("  2. 向量维度发生变化")
    print("  3. 索引文件损坏")
    print()
    
    if args.force:
        print("⚠️ 强制重建模式：将重建索引，即使维度匹配")
    else:
        print("ℹ️ 自动检测模式：仅在维度不匹配时重建")
    
    print()
    print("=" * 70)
    print()
    
    success = rebuild_vector_index(force=args.force)
    
    if success:
        print()
        print("=" * 70)
        print("✅ 向量索引重建完成")
        print("=" * 70)
        return 0
    else:
        print()
        print("=" * 70)
        print("❌ 向量索引重建失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

