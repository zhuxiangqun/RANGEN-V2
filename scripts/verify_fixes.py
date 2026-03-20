import sys
import os
import logging
import json
import time
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🚀 Testing: {title}")
    print(f"{'='*60}")

def test_cache_fixes():
    print_header("Cache Pollution Prevention")
    from src.core.reasoning.cache_manager import CacheManager
    
    cm = CacheManager()
    
    # Test Case 1: Cross-Domain Pollution (The "Chinese Academy" Bug)
    query = "Who was the 15th president of the United States?"
    corrupted_response = "The Chinese Academy of Sciences was founded in 1949."
    
    print(f"🔹 Scenario 1: Cross-Domain Check")
    print(f"   Query: {query}")
    print(f"   Response: {corrupted_response}")
    
    is_valid = cm._validate_cache_content("test_key", corrupted_response, query)
    if not is_valid:
        print("   ✅ PASS: Corrupted content rejected.")
    else:
        print("   ❌ FAIL: Corrupted content accepted!")

    # Test Case 2: Valid Content
    valid_response = "James Buchanan was the 15th president."
    print(f"\n🔹 Scenario 2: Valid Content Check")
    is_valid = cm._validate_cache_content("test_key", valid_response, query)
    if is_valid:
        print("   ✅ PASS: Valid content accepted.")
    else:
        print("   ❌ FAIL: Valid content rejected!")

    # Test Case 3: Invalid/Empty Responses
    error_response = "Error: API timeout"
    print(f"\n🔹 Scenario 3: Error Response Check")
    is_valid = cm._validate_cache_content("test_key", error_response, query)
    if not is_valid:
        print("   ✅ PASS: Error response rejected.")
    else:
        print("   ❌ FAIL: Error response accepted!")

def test_step_generator_fixes():
    print_header("Step Generator Validation & Retry")
    from src.core.reasoning.step_generator import StepGenerator
    from src.core.llm_integration import LLMIntegration
    
    # Mock LLM Integration
    mock_llm = MagicMock(spec=LLMIntegration)
    mock_llm.model = "test-model"
    step_gen = StepGenerator(llm_integration=mock_llm)
    
    # Test Case 1: Hallucination in Steps
    query = "Who is the president of USA?"
    hallucinated_steps = [
        {"type": "search", "description": "Search for Chinese Academy of Sciences", "sub_query": "CAS history"},
        {"type": "search", "description": "Search for US president", "sub_query": "US president"}
    ]
    
    print(f"🔹 Scenario 1: Hallucination Validation")
    validation = step_gen._validate_steps(hallucinated_steps, query)
    if not validation["is_valid"] and "Chinese Academy" in validation["reason"]:
        print(f"   ✅ PASS: Hallucination detected. Reason: {validation['reason']}")
    else:
        print(f"   ❌ FAIL: Hallucination NOT detected. Result: {validation}")

    # Test Case 2: Direct Answer instead of Steps (The "I can't do that" or just answer case)
    # This tests the _parse_llm_response logic detecting direct answers
    raw_response = "The president is Joe Biden."
    print(f"\n🔹 Scenario 2: Direct Answer Parsing")
    
    # We need to capture the stdout/logging to see if it detects it, 
    # but for now we check if it returns empty list (triggering fallback) instead of crashing or returning garbage
    parsed = step_gen._parse_llm_response(raw_response, query)
    if parsed == []:
        print("   ✅ PASS: Direct answer rejected (returned empty list).")
    else:
        print(f"   ❌ FAIL: Direct answer accepted as steps: {parsed}")

    # Test Case 3: Valid JSON Steps
    valid_json = """
    {
        "steps": [
            {"type": "evidence_gathering", "description": "Search for current president", "sub_query": "Who is the current president of the United States?"},
            {"type": "evidence_gathering", "description": "Find vice president", "sub_query": "Who is the vice president of the United States?"}
        ]
    }
    """
    print(f"\n🔹 Scenario 3: Valid JSON Parsing")
    parsed = step_gen._parse_llm_response(valid_json, query)
    if len(parsed) == 2:
        print(f"   ✅ PASS: Valid JSON parsed correctly ({len(parsed)} steps).")
    else:
        print(f"   ❌ FAIL: Valid JSON failed to parse. Result: {parsed}")

    # Test Case 4: Thinking Content Extraction
    print(f"\n🔹 Scenario 4: Thinking Content Extraction")
    thinking_content = """
    Thinking Process:
    1. First, I need to search for the capital of France.
    2. Then, I should find the population of that city.
    """
    extracted = step_gen._extract_reasoning_steps_from_thinking(thinking_content, query)
    if extracted and len(extracted) == 2:
        print(f"   ✅ PASS: Extracted 2 steps from thinking content.")
        print(f"      Step 1: {extracted[0]['description']}")
    else:
        print(f"   ❌ FAIL: Failed to extract steps from thinking content. Result: {extracted}")

    # Test Case 6: Generate Steps with Retry
    print(f"\n🔹 Scenario 6: Generate Steps with Retry")
    # Mock LLM response for strict prompt
    strict_response = """
    {
        "steps": [
            {"type": "evidence_gathering", "description": "Search for capital", "sub_query": "What is the capital of France?"},
            {"type": "answer_synthesis", "description": "Synthesize answer", "sub_query": "N/A"}
        ]
    }
    """
    
    # We need to mock llm_integration.call_llm
    step_gen.llm_integration.call_llm = MagicMock(return_value=strict_response)
    
    steps = step_gen.generate_steps_with_retry("What is the capital of France?")
    if steps and len(steps) == 2:
        print(f"   ✅ PASS: generate_steps_with_retry succeeded with {len(steps)} steps.")
    else:
        print(f"   ❌ FAIL: generate_steps_with_retry failed. Result: {steps}")

    # Test Case 7: Main Path Integration
    print(f"\n🔹 Scenario 7: Main Path Integration (_generate_reasoning_steps_impl)")
    # Mock transformer planner to be disabled or return None
    step_gen.transformer_planner_enabled = False
    
    steps = step_gen._generate_reasoning_steps_impl("What is the capital of France?", {})
    if steps and len(steps) == 2:
        print(f"   ✅ PASS: Main path used generate_steps_with_retry successfully.")
    else:
        print(f"   ❌ FAIL: Main path failed. Result: {steps}")

def test_llm_integration_retry():
    print_header("LLM Integration Retry")
    from src.core.llm_integration import LLMIntegration
    import requests
    
    config = {"api_key": "test", "llm_provider": "deepseek"}
    llm = LLMIntegration(config)
    
    # Mock requests.post
    with patch('requests.post') as mock_post:
        # Scenario 1: Fail twice then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Network Error")
        
        mock_response_success = MagicMock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}]
        }
        
        # Side effect: fail, fail, success
        mock_post.side_effect = [
            requests.exceptions.RequestException("Fail 1"),
            requests.exceptions.RequestException("Fail 2"),
            mock_response_success
        ]
        
        print(f"🔹 Scenario 1: Retry on Network Error")
        response = llm._call_llm("test prompt")
        
        if response == "Success" and mock_post.call_count == 3:
            print(f"   ✅ PASS: Retried 3 times and succeeded.")
        else:
            print(f"   ❌ FAIL: Retry logic failed. Response: {response}, Call count: {mock_post.call_count}")

def test_json_parsing_fixes():
    print_header("JSON Parsing Fixes")
    from src.core.reasoning.step_generator import StepGenerator
    from unittest.mock import MagicMock
    
    step_gen = StepGenerator(llm_integration=MagicMock())
    
    # Test Case 1: Single quotes JSON (invalid standard JSON)
    single_quote_json = "{'steps': [{'type': 'evidence_gathering', 'description': 'test'}]}"
    query = "test"
    
    print(f"🔹 Scenario 1: Single Quote JSON (Strict Mode)")
    parsed = step_gen._parse_llm_response(single_quote_json, query)
    if not parsed:
        print(f"   ✅ PASS: Single quote JSON rejected (as expected in Strict Mode).")
    else:
        print(f"   ❌ FAIL: Single quote JSON accepted: {parsed}")

    # Test Case 2: Trailing Comma JSON
    trailing_comma_json = '{"steps": [{"type": "evidence_gathering", "description": "test"}, ]}'
    print(f"\n🔹 Scenario 2: Trailing Comma JSON (Strict Mode)")
    parsed = step_gen._parse_llm_response(trailing_comma_json, query)
    if not parsed:
        print(f"   ✅ PASS: Trailing comma JSON rejected (as expected in Strict Mode).")
    else:
        print(f"   ❌ FAIL: Trailing comma JSON accepted: {parsed}")

    # Test Case 8: Intelligent Fallback
    print(f"\n🔹 Scenario 8: Intelligent Fallback (Complex Query)")
    complex_query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    # We need to test _generate_fallback_steps directly
    # Mock logger to avoid noise
    step_gen.logger = MagicMock()
    
    fallback_steps = step_gen._generate_fallback_steps(complex_query)
    
    if len(fallback_steps) >= 3 and fallback_steps[0]['type'] == 'evidence_gathering':
        print(f"   ✅ PASS: Intelligent Fallback generated {len(fallback_steps)} steps.")
        print(f"      Step 1: {fallback_steps[0]['sub_query']}")
        print(f"      Step 2: {fallback_steps[1]['sub_query']}")
        
        # Check if sub-queries are specific
        if "15th" in fallback_steps[0]['sub_query'] and "second" in fallback_steps[1]['sub_query']:
             print(f"   ✅ PASS: Sub-queries are specific.")
        else:
             print(f"   ❌ FAIL: Sub-queries are still vague: {fallback_steps[0]['sub_query']}")
    else:
        print(f"   ❌ FAIL: Intelligent Fallback failed. Steps: {fallback_steps}")

def test_schema_validation():
    print_header("Strict Schema Validation")
    from src.core.reasoning.step_generator import StepGenerator
    from unittest.mock import MagicMock
    
    step_gen = StepGenerator(llm_integration=MagicMock())
    
    # Test Case 1: Valid Steps
    valid_steps = [
        {"type": "evidence_gathering", "description": "Valid description length here", "sub_query": "Valid query"},
        {"type": "answer_synthesis", "description": "Valid synthesis description"}
    ]
    is_valid, reason = step_gen._validate_against_schema(valid_steps)
    if is_valid:
        print(f"   ✅ PASS: Valid steps accepted.")
    else:
        print(f"   ❌ FAIL: Valid steps rejected: {reason}")
        
    # Test Case 2: Invalid Type
    invalid_type_steps = [
        {"type": "INVALID_TYPE", "description": "Valid description length here", "sub_query": "Valid query"},
        {"type": "answer_synthesis", "description": "Valid synthesis description"}
    ]
    is_valid, reason = step_gen._validate_against_schema(invalid_type_steps)
    if not is_valid:
        print(f"   ✅ PASS: Invalid type rejected. Reason: {reason}")
    else:
        print(f"   ❌ FAIL: Invalid type accepted.")
        
    # Test Case 3: Description Too Short
    short_desc_steps = [
        {"type": "evidence_gathering", "description": "Short", "sub_query": "Valid query"},
        {"type": "answer_synthesis", "description": "Valid synthesis description"}
    ]
    is_valid, reason = step_gen._validate_against_schema(short_desc_steps)
    if not is_valid:
        print(f"   ✅ PASS: Short description rejected. Reason: {reason}")
    else:
        print(f"   ❌ FAIL: Short description accepted.")
        
    # Test Case 4: Missing Sub-query
    missing_sub_steps = [
        {"type": "evidence_gathering", "description": "Valid description length here"},
        {"type": "answer_synthesis", "description": "Valid synthesis description"}
    ]
    is_valid, reason = step_gen._validate_against_schema(missing_sub_steps)
    if not is_valid:
        print(f"   ✅ PASS: Missing sub-query rejected. Reason: {reason}")
    else:
        print(f"   ❌ FAIL: Missing sub-query accepted.")

def check_syntax():
    print_header("Syntax Check")
    import py_compile
    file_path = "src/core/reasoning/step_generator.py"
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"   ✅ PASS: {file_path} compiles successfully.")
    except Exception as e:
        print(f"   ❌ FAIL: Syntax error in {file_path}: {e}")

if __name__ == "__main__":
    try:
        test_cache_fixes()
        test_step_generator_fixes()
        test_llm_integration_retry()
        test_json_parsing_fixes()
        test_schema_validation()
        check_syntax()
        print("\n✨ All verification tests completed.")
    except Exception as e:
        print(f"\n❌ FATAL ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
