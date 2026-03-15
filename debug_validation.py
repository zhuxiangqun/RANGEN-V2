import sys
import os
import logging
from typing import Dict, Any, List

sys.path.append(os.getcwd())

from src.core.reasoning.step_generator import StepGenerator
from src.core.llm_integration import LLMIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_validation_logic():
    """测试 StepGenerator 的验证逻辑"""
    print("\n🚀 开始测试验证逻辑...")
    
    # 模拟 LLMIntegration
    class MockLLM(LLMIntegration):
        def __init__(self):
            self.model = 'mock-model'
            
        def _call_llm(self, prompt, **kwargs):
            return ""

    step_gen = StepGenerator(llm_integration=MockLLM())
    
    # 测试用例 1: 完美步骤
    valid_steps = [
        {"type": "evidence_gathering", "description": "Find X", "sub_query": "What is X?"},
        {"type": "evidence_gathering", "description": "Find Y", "sub_query": "What is Y?"}
    ]
    result = step_gen._validate_steps(valid_steps, "What is X and Y?")
    print(f"✅ Case 1 (Valid): {result['is_valid']} (Score: {result['quality_score']})")
    assert result['is_valid'] == True

    # 测试用例 2: 幻觉 (中国科学院)
    hallucinated_steps = [
        {"type": "evidence_gathering", "description": "Find founding date of Chinese Academy of Sciences", "sub_query": "When was Chinese Academy of Sciences founded?"},
        {"type": "evidence_gathering", "description": "Find Y", "sub_query": "What is Y?"}
    ]
    result = step_gen._validate_steps(hallucinated_steps, "Who is the president of USA?")
    print(f"✅ Case 2 (Hallucination): {result['is_valid']} (Reason: {result['reason']})")
    assert result['is_valid'] == False
    assert "Chinese Academy" in result['reason']

    # 测试用例 3: 格式错误 (缺少字段)
    invalid_format_steps = [
        {"description": "Find X"}, # 缺少 type
        {"type": "evidence_gathering", "description": "Find Y"}
    ]
    result = step_gen._validate_steps(invalid_format_steps, "Query")
    print(f"✅ Case 3 (Missing Fields): {result['is_valid']} (Reason: {result['reason']})")
    assert result['is_valid'] == False

    # 测试用例 4: 无效查询 (无 sub_query)
    no_action_steps = [
        {"type": "thinking", "description": "I need to think about X", "sub_query": ""},
        {"type": "thinking", "description": "I need to think about Y", "sub_query": ""}
    ]
    result = step_gen._validate_steps(no_action_steps, "Query")
    print(f"✅ Case 4 (No Action): {result['is_valid']} (Reason: {result['reason']})")
    assert result['is_valid'] == False

    print("\n🎉 所有验证逻辑测试通过！")

if __name__ == "__main__":
    test_validation_logic()
