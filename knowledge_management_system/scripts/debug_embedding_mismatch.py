#!/usr/bin/env python3
"""
Embedding 一致性深度调试脚本
用于比对FAISS索引中的向量与当前TextProcessor生成的向量是否一致
"""

import sys
import os
import json
import numpy as np
import faiss
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.utils.logger import get_logger
from knowledge_management_system.modalities.text_processor import get_text_processor
from knowledge_management_system.api.service_interface import get_knowledge_service

logger = get_logger()

def debug_embedding_mismatch():
    print("=" * 70)
    print("🔬 Embedding 一致性深度调试")
    print("=" * 70)

    # 1. 加载知识库服务和索引
    print("\n🔄 初始化服务...")
    service = get_knowledge_service()
    
    # 尝试直接访问底层索引
    # 修正：service.knowledge_manager.vector_storage 或 service.vector_storage (根据实际实现调整)
    vector_storage = None
    if hasattr(service, 'vector_storage'):
        vector_storage = service.vector_storage
    elif hasattr(service, 'knowledge_manager') and hasattr(service.knowledge_manager, 'vector_storage'):
        vector_storage = service.knowledge_manager.vector_storage
    
    if not vector_storage:
        print("❌ 无法获取向量存储实例")
        return
        
    index_builder = vector_storage.get_index_builder()
    if not index_builder.ensure_index_ready():
        print("❌ 索引未就绪")
        return
        
    index = index_builder.index
    mapping = index_builder.entry_mapping
    
    if index.ntotal == 0:
        print("❌ 索引为空")
        return
        
    print(f"✅ 索引加载成功: {index.ntotal} 条向量")

    # 1.5 加载元数据文件（绕过服务层）
    print("\n📥 直接加载元数据文件...")
    metadata_path = "data/knowledge_management/metadata.json"
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata_json = json.load(f)
            # 处理可能的结构：{'entries': {...}} 或 直接 {...}
            if 'entries' in metadata_json:
                knowledge_data = metadata_json['entries']
            else:
                knowledge_data = metadata_json
        print(f"✅ 元数据加载成功，共 {len(knowledge_data)} 条记录")
        
        # 🚀 验证一致性
        index_count = index.ntotal
        meta_count = len(knowledge_data)
        print(f"\n📊 数量对比:")
        print(f"   Index Count:    {index_count}")
        print(f"   Metadata Count: {meta_count}")
        if index_count == meta_count:
            print("   ✅ 数量完全一致")
        else:
            diff = abs(index_count - meta_count)
            ratio = index_count / meta_count if meta_count > 0 else 0
            print(f"   ⚠️ 数量不一致 (差值: {diff}, 比例: {ratio:.2f})")
            
    except Exception as e:
        print(f"❌ 元数据加载失败: {e}")
        return

    # 2. 随机抽取一个有效的知识条目
    print(f"\n🎲 从 {index.ntotal} 个向量中抽取样本...")
    
    sample_idx = 0
    knowledge_id = None
    knowledge_entry = None
    
    # 查找有对应知识条目的索引ID
    for i in range(min(100, index.ntotal)):
        # 将索引ID转为字符串key（如果mapping是str:int格式的）
        # 这里需要注意：mapping通常是 int(faiss_id) -> str(knowledge_id)
        # index_builder.entry_mapping 是 dict[int, str]
        kid = mapping.get(i)
        
        # 也有可能mapping文件加载后key变成了str
        if kid is None and str(i) in mapping:
            kid = mapping[str(i)]
            
        if kid:
            # 直接从加载的json中查找
            entry = knowledge_data.get(kid)
            if entry:
                # 尝试获取内容（可能在root或metadata中）
                content_val = entry.get('content')
                if not content_val and entry.get('metadata'):
                    content_val = entry['metadata'].get('content')
                
                if content_val:
                    sample_idx = i
                    knowledge_id = kid
                    knowledge_entry = entry
                    content = content_val
                    break
    
    if not knowledge_id:
        print("❌ 未找到有效的知识条目样本")
        print(f"   Mapping size: {len(mapping)}")
        print(f"   Metadata size: {len(knowledge_data)}")
        if len(mapping) > 0:
             first_key = list(mapping.keys())[0]
             print(f"   Sample Mapping: {first_key} -> {mapping[first_key]}")
        return

    print(f"✅ 选中样本:")
    print(f"   Index ID: {sample_idx}")
    print(f"   Knowledge ID: {knowledge_id}")
    print(f"   Title: {knowledge_entry.get('metadata', {}).get('title', 'N/A')}")
    # content 已在上方获取
    print(f"   Content Preview: {content[:50]}...")

    # 3. 提取索引中的向量
    print("\n📥 提取索引中的向量...")
    try:
        stored_vector = index.reconstruct(sample_idx)
        print(f"   Stored Vector Norm: {np.linalg.norm(stored_vector):.6f}")
        print(f"   First 5 dims: {stored_vector[:5]}")
    except Exception as e:
        print(f"❌ 无法提取向量: {e}")
        return

    # 4. 使用当前TextProcessor重新生成向量
    print("\n🔄 重新生成向量...")
    processor = get_text_processor()
    try:
        new_vector = processor.encode(content)
        if new_vector is None:
            print("❌ 生成向量失败")
            return
            
        # 归一化（模拟IndexFlatIP的要求）
        new_vector_norm = new_vector / np.linalg.norm(new_vector)
        
        print(f"   New Vector Norm (Raw): {np.linalg.norm(new_vector):.6f}")
        print(f"   First 5 dims (Normalized): {new_vector_norm[:5]}")
    except Exception as e:
        print(f"❌ 生成向量过程出错: {e}")
        return

    # 5. 计算相似度对比
    print("\n⚖️  一致性对比...")
    
    # 计算余弦相似度 (因为向量已归一化，即点积)
    similarity = np.dot(stored_vector, new_vector_norm)
    print(f"   Cosine Similarity: {similarity:.6f}")
    
    if similarity > 0.99:
        print("✅ 向量一致性极高 (Match)")
    elif similarity > 0.9:
        print("✅ 向量基本一致 (Pass)")
    elif similarity > 0.0001:
        print("⚠️ 向量存在差异 (Mismatch)")
        print("   可能原因: 模型版本不同、预处理逻辑变更、或者浮点精度问题")
    else:
        print("❌ 向量完全不匹配 (Orthogonal/Zero)")
        print("   可能原因: 严重错误，如使用了完全不同的模型，或者索引ID映射错位")

    # 6. 验证搜索能否找到自己
    print("\n🔍 验证自检索...")
    try:
        results = service.query_knowledge(content[:100], top_k=5, similarity_threshold=0.0)
        found = False
        for res in results:
            if res['id'] == knowledge_id:
                print(f"✅ 在搜索结果中找到了该条目 (Score: {res['similarity']:.4f})")
                found = True
                break
        if not found:
            print(f"❌ 搜索未能找回该条目")
            if results:
                print(f"   Top1 Score: {results[0]['similarity']:.4f}")
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    debug_embedding_mismatch()
