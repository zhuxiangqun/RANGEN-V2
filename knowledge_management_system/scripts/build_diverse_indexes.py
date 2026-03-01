#!/usr/bin/env python3
"""
构建多元化索引脚本
从现有知识库构建LlamaIndex的多样化索引（树索引、关键词索引、列表索引等）
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.integrations.llamaindex_index_manager import LlamaIndexIndexManager
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def convert_knowledge_to_documents(knowledge_entries: List[Dict[str, Any]]) -> List[Any]:
    """
    将知识条目转换为LlamaIndex Document格式
    
    Args:
        knowledge_entries: 知识条目列表
        
    Returns:
        LlamaIndex Document列表
    """
    try:
        from llama_index.core import Document
        
        documents = []
        for entry in knowledge_entries:
            # 提取内容
            content = entry.get('metadata', {}).get('content', '') or \
                     entry.get('metadata', {}).get('content_preview', '') or \
                     entry.get('content', '')
            
            if not content:
                continue
            
            # 提取元数据
            metadata = {
                'knowledge_id': entry.get('knowledge_id', ''),
                'source': entry.get('metadata', {}).get('source', ''),
                'title': entry.get('metadata', {}).get('title', ''),
                'url': entry.get('metadata', {}).get('url', ''),
                **entry.get('metadata', {})
            }
            
            # 创建Document
            doc = Document(
                text=content,
                metadata=metadata
            )
            documents.append(doc)
        
        logger.info(f"✅ 成功转换 {len(documents)} 个知识条目为LlamaIndex Document")
        return documents
        
    except ImportError:
        logger.error("LlamaIndex 未安装，无法转换文档")
        return []


def build_diverse_indexes(
    index_types: Optional[List[str]] = None,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    构建多元化索引
    
    Args:
        index_types: 要构建的索引类型列表（['tree', 'keyword', 'list', 'vector']）
                    如果为None，构建所有类型
        save_path: 索引保存路径（可选）
        
    Returns:
        构建结果字典
    """
    try:
        # 获取知识库服务
        kms = get_knowledge_service()
        
        # 获取所有知识条目
        logger.info("📚 正在获取知识条目...")
        knowledge_manager = kms.knowledge_manager
        all_entries = knowledge_manager.list_all_knowledge()
        
        if not all_entries:
            logger.warning("⚠️ 知识库为空，无法构建索引")
            return {'success': False, 'error': '知识库为空'}
        
        logger.info(f"📊 找到 {len(all_entries)} 个知识条目")
        
        # 转换为LlamaIndex Document格式
        documents = convert_knowledge_to_documents(all_entries)
        if not documents:
            logger.error("❌ 无法转换知识条目为Document格式")
            return {'success': False, 'error': '文档转换失败'}
        
        # 初始化索引管理器
        index_manager = LlamaIndexIndexManager()
        if not index_manager.enabled:
            logger.error("❌ LlamaIndex 未安装或未启用")
            return {'success': False, 'error': 'LlamaIndex未启用'}
        
        # 确定要构建的索引类型
        if index_types is None:
            index_types = ['tree', 'keyword', 'list', 'vector']
        
        results = {
            'success': True,
            'total_documents': len(documents),
            'indexes_built': {}
        }
        
        # 构建各种索引
        logger.info(f"🔨 开始构建索引，类型: {', '.join(index_types)}")
        
        if 'tree' in index_types:
            logger.info("🌳 构建树索引...")
            tree_index = index_manager.build_tree_index(documents)
            if tree_index:
                results['indexes_built']['tree'] = True
                logger.info("✅ 树索引构建成功")
            else:
                results['indexes_built']['tree'] = False
                logger.warning("⚠️ 树索引构建失败")
        
        if 'keyword' in index_types:
            logger.info("🔑 构建关键词索引...")
            keyword_index = index_manager.build_keyword_index(documents)
            if keyword_index:
                results['indexes_built']['keyword'] = True
                logger.info("✅ 关键词索引构建成功")
            else:
                results['indexes_built']['keyword'] = False
                logger.warning("⚠️ 关键词索引构建失败")
        
        if 'list' in index_types:
            logger.info("📋 构建列表索引...")
            list_index = index_manager.build_list_index(documents)
            if list_index:
                results['indexes_built']['list'] = True
                logger.info("✅ 列表索引构建成功")
            else:
                results['indexes_built']['list'] = False
                logger.warning("⚠️ 列表索引构建失败")
        
        if 'vector' in index_types:
            logger.info("🔍 构建向量索引...")
            vector_index = index_manager.build_vector_index(documents)
            if vector_index:
                results['indexes_built']['vector'] = True
                logger.info("✅ 向量索引构建成功")
            else:
                results['indexes_built']['vector'] = False
                logger.warning("⚠️ 向量索引构建失败")
        
        # 保存索引管理器实例（可选）
        if save_path:
            # 这里可以添加索引持久化逻辑
            logger.info(f"💾 索引保存路径: {save_path}")
        
        # 显示可用索引
        available = index_manager.get_available_index_types()
        logger.info(f"✅ 可用索引类型: {', '.join(available)}")
        results['available_indexes'] = available
        
        return results
        
    except Exception as e:
        logger.error(f"❌ 构建索引失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def test_router_query(query: str, index_manager: LlamaIndexIndexManager):
    """
    测试路由查询
    
    Args:
        query: 测试查询
        index_manager: 索引管理器实例
    """
    logger.info(f"🔍 测试查询: {query}")
    result = index_manager.query_with_router(query)
    if result:
        logger.info(f"✅ 查询结果: {result}")
    else:
        logger.warning("⚠️ 查询无结果")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='构建LlamaIndex多元化索引')
    parser.add_argument(
        '--index-types',
        nargs='+',
        choices=['tree', 'keyword', 'list', 'vector', 'all'],
        default=['all'],
        help='要构建的索引类型（默认：all）'
    )
    parser.add_argument(
        '--save-path',
        type=str,
        default=None,
        help='索引保存路径（可选）'
    )
    parser.add_argument(
        '--test-query',
        type=str,
        default=None,
        help='测试查询（可选）'
    )
    
    args = parser.parse_args()
    
    # 处理索引类型
    index_types = args.index_types
    if 'all' in index_types:
        index_types = ['tree', 'keyword', 'list', 'vector']
    
    # 构建索引
    results = build_diverse_indexes(
        index_types=index_types,
        save_path=args.save_path
    )
    
    if results['success']:
        logger.info("=" * 60)
        logger.info("✅ 索引构建完成！")
        logger.info(f"📊 总文档数: {results['total_documents']}")
        logger.info(f"🔨 构建的索引: {results['indexes_built']}")
        logger.info(f"✅ 可用索引: {', '.join(results['available_indexes'])}")
        logger.info("=" * 60)
        
        # 测试查询
        if args.test_query:
            index_manager = LlamaIndexIndexManager()
            test_router_query(args.test_query, index_manager)
    else:
        logger.error(f"❌ 索引构建失败: {results.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

