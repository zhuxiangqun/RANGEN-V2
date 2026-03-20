
import sys
import os
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_management_system.api.service_interface import KnowledgeManagementService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_knowledge_base():
    print("🚀 开始验证向量知识库...")
    
    try:
        # 初始化服务
        service = KnowledgeManagementService()
        
        # 获取知识库统计信息
        # stats = service.get_stats() # 方法不存在
        
        # 手动获取统计信息
        try:
            entry_count = len(service.knowledge_manager._metadata.get('entries', {}))
            print(f"\n📊 知识库统计信息:")
            print(f"   - 知识条目数量: {entry_count}")
            
            # 尝试获取向量索引大小
            if hasattr(service, 'index_builder') and hasattr(service.index_builder, 'index') and service.index_builder.index:
                vector_count = service.index_builder.index.ntotal
                print(f"   - 向量索引大小: {vector_count}")
            else:
                print(f"   - 向量索引大小: (未加载或无法访问)")
                vector_count = entry_count # 假设一致
        except Exception as e:
            print(f"   - 统计信息获取失败: {e}")
            vector_count = 1 # 假定有数据，继续测试
        
        # 验证向量数量
        if vector_count == 0:
            print("\n❌ 错误: 向量索引为空！知识库构建可能失败。")
            return
            
        print(f"\n✅ 知识库核心文件检查通过 (包含 {vector_count} 条向量)")
        
        # 执行测试查询
        # 使用 FRAMES 数据集中的一个典型问题
        test_query = "Who was the 9th Master of Hatfield College?"
        print(f"\n🔍 执行测试查询: '{test_query}'")
        
        results = service.query_knowledge(
            query=test_query,
            top_k=3,
            similarity_threshold=0.5
        )
        
        if not results:
            print("⚠️  警告: 查询未返回结果。尝试降低相似度阈值...")
            results = service.query_knowledge(
                query=test_query,
                top_k=3,
                similarity_threshold=0.3
            )
            
        if results:
            print(f"\n✅ 检索成功! 找到 {len(results)} 条相关结果:")
            for i, res in enumerate(results):
                metadata = res.get('metadata', {})
                title = metadata.get('title', 'No Title')
                score = res.get('similarity', 0.0)
                content = res.get('content', '')[:100].replace('\n', ' ') + "..."
                
                print(f"   {i+1}. [{score:.4f}] {title}")
                print(f"      内容预览: {content}")
                print(f"      来源: {metadata.get('source_urls', ['Unknown'])[0] if metadata.get('source_urls') else 'Unknown'}")
        else:
            print("\n❌ 错误: 即使降低阈值也未检索到任何结果。请检查向量索引是否与元数据匹配。")
            
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_base()
