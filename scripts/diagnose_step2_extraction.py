#!/usr/bin/env python3
"""
诊断步骤2的答案提取流程
检查是否调用了LLM
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试加载.env文件（如果存在且可访问）
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=project_root / '.env')
except Exception:
    pass  # 如果无法加载.env，继续执行


async def diagnose_step2_extraction():
    """诊断步骤2的答案提取流程"""
    print("=" * 80)
    print("诊断步骤2的答案提取流程")
    print("=" * 80)
    
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        from src.core.reasoning.answer_extraction.answer_extractor import AnswerExtractor
        
        # 初始化推理引擎
        print("\n🔧 初始化推理引擎...")
        engine = RealReasoningEngine()
        print("✅ 推理引擎已初始化")
        
        # 检查answer_extractor
        print("\n" + "=" * 80)
        print("检查AnswerExtractor配置:")
        print("=" * 80)
        
        answer_extractor = engine.answer_extractor
        if not answer_extractor:
            print("❌ answer_extractor 为 None")
            return
        
        print(f"✅ answer_extractor 已初始化")
        print(f"   cognitive_extractor: {answer_extractor.cognitive_extractor is not None}")
        print(f"   llm_integration: {answer_extractor.llm_integration is not None}")
        print(f"   fast_llm_integration: {answer_extractor.fast_llm_integration is not None}")
        
        # 检查策略
        print(f"\n📋 提取策略数量: {len(answer_extractor.strategies)}")
        for i, strategy in enumerate(answer_extractor.strategies):
            print(f"   策略{i+1}: {strategy.__class__.__name__}")
            if hasattr(strategy, 'cognitive_extractor'):
                print(f"      cognitive_extractor: {strategy.cognitive_extractor is not None}")
            if hasattr(strategy, 'llm_integration'):
                print(f"      llm_integration: {strategy.llm_integration is not None}")
        
        # 测试步骤2的查询
        print("\n" + "=" * 80)
        print("测试步骤2的查询:")
        print("=" * 80)
        
        # 模拟步骤2的查询和证据
        sub_query = "Who was the mother of Harriet Lane?"
        print(f"子查询: {sub_query}")
        
        # 检查问题类型分类
        if answer_extractor.cognitive_extractor:
            question_type = answer_extractor.cognitive_extractor._classify_question_type(sub_query)
            print(f"\n问题类型分类: {question_type}")
            
            if question_type == "person_attribute":
                print("✅ 问题类型正确识别为 'person_attribute'")
                print("   应该会调用 _extract_relationship_with_llm_generic")
            else:
                print(f"⚠️ 问题类型识别为 '{question_type}'，可能不会调用LLM")
        
        # 检查LLM集成
        print("\n" + "=" * 80)
        print("检查LLM集成:")
        print("=" * 80)
        
        if answer_extractor.cognitive_extractor:
            cognitive = answer_extractor.cognitive_extractor
            print(f"cognitive_extractor.llm_integration: {cognitive.llm_integration is not None}")
            if cognitive.llm_integration:
                print("✅ LLM集成可用，应该会调用LLM")
            else:
                print("❌ LLM集成不可用，不会调用LLM")
        
        # 检查策略的can_handle
        print("\n" + "=" * 80)
        print("检查策略是否能够处理查询:")
        print("=" * 80)
        
        query_type = answer_extractor._classify_query_type(sub_query)
        print(f"查询类型: {query_type}")
        
        for i, strategy in enumerate(answer_extractor.strategies):
            can_handle = strategy.can_handle(sub_query, query_type)
            print(f"策略{i+1} ({strategy.__class__.__name__}): {'✅ 可以处理' if can_handle else '❌ 不能处理'}")
        
        print("\n✅ 诊断完成")
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose_step2_extraction())

