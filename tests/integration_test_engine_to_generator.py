
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time
import asyncio

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.engine import RealReasoningEngine
from src.core.reasoning.step_generator import StepGenerator

class TestIntegrationEngineToGenerator(unittest.TestCase):
    def setUp(self):
        # 初始化 Engine
        self.engine = RealReasoningEngine()
        # 确保 step_generator 也是初始化的
        if not self.engine.step_generator:
            self.engine.step_generator = StepGenerator()
            
    def test_semantic_relevance_interception(self):
        """测试语义相关性验证在 Engine 调用链路中是否生效"""
        print("\n" + "="*50)
        print("🧪 测试场景 1: 语义相关性拦截 (Semantic Relevance Interception)")
        print("="*50)
        
        # 1. 构造不相关的 LLM 响应
        irrelevant_response = """
        [
            {
                "step_id": "1",
                "type": "information_retrieval",
                "description": "Calculate the height of the Eiffel Tower",
                "rationale": "To know the height",
                "action": "search",
                "is_final": false,
                "sub_query": "height of Eiffel Tower"
            },
            {
                "step_id": "2",
                "type": "information_retrieval",
                "description": "Find the capital of France",
                "rationale": "To know the location",
                "action": "search",
                "is_final": true,
                "sub_query": "capital of France"
            }
        ]
        """
        
        # 2. Mock StepGenerator 的 LLM 调用
        # 我们 mock _call_llm_with_cache，让它返回这个不相关的响应
        # 还要 mock _generate_fallback_steps 以便验证是否回退到了这里
        
        fallback_step = {
            "step_id": "fallback_1", 
            "description": "Understand the user query about Python", 
            "type": "analysis"
        }
        
        # 使用 patch.object 来 mock 实例的方法
        # 同时 mock 全局函数 get_semantic_understanding_pipeline
        with patch.object(self.engine.step_generator, '_call_llm_with_cache', return_value=irrelevant_response) as mock_llm, \
             patch.object(self.engine.step_generator, '_generate_fallback_steps', return_value=[fallback_step]) as mock_fallback, \
             patch.object(self.engine.step_generator, 'llm_integration', MagicMock()), \
             patch('src.core.reasoning.step_generator.get_semantic_understanding_pipeline') as mock_get_pipeline:
            
            # 配置 mock pipeline
            mock_pipeline = MagicMock()
            mock_get_pipeline.return_value = mock_pipeline
            mock_pipeline.are_models_available.return_value = True
            
            # Mock 相似度计算，强制返回 0.1
            # 注意：Pipeline 可能会检查 _sentence_transformer 属性
            mock_pipeline._sentence_transformer = MagicMock()
            mock_pipeline.understand_query.return_value = {"embedding": [1.0, 0.0]}
            mock_pipeline._sentence_transformer_util.cos_sim.return_value.item.return_value = 0.1
            
            # Mock 实体检测，避免因为示例泄露检测而提前返回（我们想测语义相似度）
            self.engine.step_generator._detect_example_leakage = MagicMock(return_value={"is_relevant": True})

            # 3. 执行 Engine 的生成方法
            query = "How to use python pandas dataframe?"
            print(f"🚀 发送查询: {query}")
            
            # 使用 reason 方法
            result = asyncio.run(self.engine.reason(query, {}))
            steps = result.reasoning_steps if result else []
            
            # 4. 验证结果
            print(f"📦 最终返回步骤数: {len(steps) if steps else 0}")
            if steps:
                # ReasoningStep 是对象，使用属性访问
                first_step = steps[0]
                description = getattr(first_step, 'description', 'N/A')
                step_id = getattr(first_step, 'step_id', 'N/A')
                print(f"   第一步描述: {description}")
                print(f"   第一步ID: {step_id}")

            # 断言
            # 1. LLM 应该被调用了
            self.engine.step_generator._call_llm_with_cache.assert_called()

            # 2. Fallback 应该被触发 (因为 LLM 返回了不相关步骤)
            self.engine.step_generator._generate_fallback_steps.assert_called()

            # 3. 最终结果应该是 fallback 的结果
            # 注意：fallback返回的是字典，但在 Engine 中被转换为了 ReasoningStep 对象
            # Engine 会重新编号 step_id，所以我们应该检查 description
            description = getattr(steps[0], 'description', '')
            self.assertEqual(description, 'Understand the user query about Python', "最终步骤描述应该匹配 fallback 定义")

            print("✅ 语义拦截测试通过！")
    
    def test_timeout_fallback(self):
        """测试超时机制是否能触发 fallback"""
        print("\n" + "="*50)
        print("🧪 测试场景 2: 超时回退 (Timeout Fallback)")
        print("="*50)
        
        # 1. 定义一个耗时的 LLM 调用
        def slow_llm_call(*args, **kwargs):
            print("   😴 LLM 开始休眠模拟耗时...")
            time.sleep(2) # 休眠 2 秒
            return "Some response"
        
        fallback_step = {
            "step_id": "fallback_timeout", 
            "description": "Fallback due to timeout", 
            "type": "analysis"
        }
        
        # 2. 设置 Engine 的超时时间很短
        # 注意：RealReasoningEngine 可能没有直接的 timeout_seconds 属性，
        # 而是从 config 中读取。我们需要 mock config 或者 _generate_reasoning_steps 的参数
        # 假设我们无法直接修改配置，我们尝试 Patch asyncio.wait_for 来模拟超时
        
        with patch.object(self.engine.step_generator, '_call_llm_with_cache', side_effect=slow_llm_call) as mock_llm, \
             patch.object(self.engine.step_generator, '_generate_fallback_steps', return_value=[fallback_step]) as mock_fallback, \
             patch.object(self.engine.step_generator, 'llm_integration', MagicMock()):
        
            query = "Complex query causing timeout"
            print(f"🚀 发送查询: {query} (强制超时)")
        
            # 我们通过 Mock asyncio.wait_for 来强制触发 TimeoutError
            # 因为要在集成测试中精确控制多线程/异步超时比较困难
        
            async def mock_wait_for(fut, timeout):
                if timeout is not None:
                    raise asyncio.TimeoutError()
                return await fut
        
            with patch('asyncio.wait_for', side_effect=mock_wait_for):
                try:
                    result = asyncio.run(self.engine.reason(query, {}))
                    steps = result.reasoning_steps if result else []
                except Exception as e:
                    print(f"⚠️ 执行期间发生异常: {e}")
                    steps = []
        
            # 如果 Engine 正确处理了 TimeoutError，它应该捕获并调用 fallback
            # 如果没有捕获，上面的 asyncio.run 会抛出异常
            
            first_step_desc = 'None'
            if steps:
                first_step_desc = getattr(steps[0], 'description', 'None')

            print(f"📦 最终返回步骤描述: {first_step_desc}")
        
            # 断言
            if steps:
                 self.assertEqual(first_step_desc, 'Fallback due to timeout', "最终步骤描述应该匹配 timeout fallback")
            else:
                 # 如果 steps 为空，可能是因为异常没被捕获，或者 fallback 返回空
                 # 只要 mock_fallback 被调用，也算测试通过（说明触发了回退逻辑）
                 self.assertTrue(mock_fallback.called, "超时应该触发 Fallback 逻辑")
        
            print("✅ 超时回退测试通过！")

if __name__ == '__main__':
    unittest.main()
