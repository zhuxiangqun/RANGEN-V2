#!/usr/bin/env python3
"""
检查 SemanticUnderstandingPipeline 环境可用性
验证模型加载、Embedding生成和相似度计算
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline

def check_semantic_pipeline():
    print("\n" + "="*50)
    print("🔍 开始排查 SemanticUnderstandingPipeline 环境可用性")
    print("="*50)

    try:
        # 1. 初始化管道
        print("\n⏳ 正在初始化 SemanticUnderstandingPipeline...")
        start_time = time.time()
        pipeline = get_semantic_understanding_pipeline()
        init_time = time.time() - start_time
        print(f"✅ 初始化完成，耗时: {init_time:.2f}秒")
        
        # 2. 检查模型可用性
        print("\n🔍 检查模型加载状态...")
        are_models_available = pipeline.are_models_available()
        print(f"📊 模型可用状态: {are_models_available}")
        
        if are_models_available:
            print(f"   ✅ NLP 模型已加载: {pipeline._available_models}")
        else:
            print("   ⚠️ NLP 模型未完全加载，将使用降级逻辑")
        
        # 3. 测试语义理解 (Embedding)
        print("\n🧪 测试语义理解 (understand_query)...")
        query = "How to use python pandas dataframe?"
        try:
            understanding = pipeline.understand_query(query)
            embedding = understanding.get("embedding")
            contextual = understanding.get("contextual", {})
            model_used = contextual.get("model", "unknown")
            
            if embedding:
                print(f"   ✅ Embedding 生成成功，维度: {len(embedding)}")
                print(f"   🤖 使用的模型: {model_used}")
            else:
                print("   ❌ Embedding 生成失败 (None)")
            
            keywords = understanding.get("lexical", {}).get("keywords", [])
            print(f"   📝 提取关键词: {keywords}")
        
        except Exception as e:
            print(f"   ❌ understand_query 调用异常: {e}")
        
        # 4. 测试相似度计算
        print("\n🧪 测试相似度计算 (calculate_semantic_similarity)...")
        text1 = "How to use python pandas"
        text2 = "Using dataframe in python"
        text3 = "The capital of France is Paris"
        
        try:
            sim12 = pipeline.calculate_semantic_similarity(text1, text2)
            sim13 = pipeline.calculate_semantic_similarity(text1, text3)
            
            print(f"   ✅ '{text1}' vs '{text2}': {sim12:.4f} (预期: 高)")
            print(f"   ✅ '{text1}' vs '{text3}': {sim13:.4f} (预期: 低)")
            
            if sim12 > sim13:
                print("   ✅ 相似度逻辑正常")
            else:
                print("   ❌ 相似度逻辑异常: 不相关文本得分更高")
                
        except Exception as e:
             print(f"   ❌ 相似度计算异常: {e}")

    except ImportError as e:
        print(f"❌ 导入失败，可能是依赖缺失: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_semantic_pipeline()
