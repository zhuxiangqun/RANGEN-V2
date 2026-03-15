#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试知识检索服务"""

import sys
sys.path.insert(0, '.')

print('=== 测试知识检索服务 ===')

try:
    # 测试导入知识检索相关模块
    print('1. 测试导入知识检索模块...')
    from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
    from src.services.knowledge_retriever import KnowledgeRetriever
    print('   ✓ 知识检索模块导入成功')
    
    # 测试导入知识管理系统的配置
    print('2. 测试导入知识管理系统配置...')
    from src.services.frames_dataset_integration import FramesDatasetIntegrator
    print('   ✓ FramesDatasetIntegrator 导入成功')
    
    # 测试导入认知检索系统
    print('3. 测试导入认知检索系统...')
    from src.services.cognitive_retrieval_system import CognitiveRetrievalSystem
    print('   ✓ CognitiveRetrievalSystem 导入成功')
    
    # 检查向量存储目录
    print('4. 检查向量存储...')
    import os
    vector_store_path = os.path.join('knowledge_management_system', 'vector_store')
    if os.path.exists(vector_store_path):
        files = os.listdir(vector_store_path)
        print(f'   ✓ 向量存储目录存在, 文件数: {len(files)}')
    else:
        print(f'   ⚠ 向量存储目录不存在: {vector_store_path}')
    
    print()
    print('=== 知识检索服务 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
