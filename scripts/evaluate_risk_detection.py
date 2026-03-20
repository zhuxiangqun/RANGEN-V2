import json
import logging
from typing import List, Dict, Any
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate_risk_detection")

# 导入 StepGenerator
try:
    from src.core.reasoning.step_generator import StepGenerator
    from src.core.llm_integration import LLMIntegration
except ImportError:
    print("❌ 无法导入 src.core 模块，请确保在项目根目录运行")
    exit(1)

# 智能 Mock LLM
class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def emit(self, record):
        self.logs.append(record.getMessage())

# 智能 Mock LLM
class IntelligentMockLLM(LLMIntegration):
    def __init__(self):
        self.call_count = 0
        
    def call_llm(self, prompt, **kwargs):
        self.call_count += 1
        
        # 简单提取查询内容
        # 修正：prompt 现在是全英文的，所以匹配 "# User Query" 而不是 "# 用户查询"
        query_match = re.search(r'# User Query\s*\n(.*?)\n', prompt, re.DOTALL)
        if not query_match:
             # 回退尝试匹配旧格式（为了兼容性）
             query_match = re.search(r'# 用户查询\s*\n(.*?)\n', prompt, re.DOTALL)
             
        query = query_match.group(1).strip() if query_match else ""
        
        risks = []
        uncertainty = "Low"
        
        if "15th" in query or "2nd" in query or "first" in query.lower():
            risks.append("Ordinal_Ambiguity")
            uncertainty = "High"
        
        if "Paris" in query or "Washington" in query:
            risks.append("Entity_Ambiguity")
        
        if "mother of" in query: # 只有mother of算复杂，capital of算简单
            risks.append("Multi_Hop_Complex")
            
        if not risks:
            risks = ["None"]
            
        # 构建响应
        # 确保 sub_query 是合法的疑问句，且不包含复杂的嵌套
        safe_sub_query = f"What are the facts about {query[:10]}?" 
        
        return json.dumps({
            "reasoning": {
                "thought_process": f"Analyzing query: {query}. Identified risks: {risks}",
                "risk_factors": risks,
                "uncertainty_level": uncertainty
            },
            "steps": [
                {
                    "type": "evidence_gathering",
                    "description": f"Verify key facts for query: {query}",
                    "sub_query": safe_sub_query
                },
                {
                    "type": "answer_synthesis",
                    "description": "Synthesize answer based on gathered evidence"
                }
            ]
        })

def run_risk_evaluation():
    print("🧠 Starting Risk Detection Evaluation...")
    print("========================================")
    
    # 设置日志捕获
    capture_handler = LogCaptureHandler()
    logger = logging.getLogger("src.core.reasoning.step_generator")
    logger.addHandler(capture_handler)
    logger.setLevel(logging.INFO)
    
    llm = IntelligentMockLLM()
    step_gen = StepGenerator(llm_integration=llm)
    
    # 测试用例
    test_cases = [
        ("Who is the 15th president?", "Ordinal_Ambiguity"),
        ("Where is Paris located?", "Entity_Ambiguity"),
        ("Who is the mother of the 2nd president?", "Multi_Hop_Complex"),
        ("What is the capital of France?", "None"), 
        ("Who was the first man on moon?", "Ordinal_Ambiguity")
    ]
    
    results = {
        "passed": 0,
        "failed": 0,
        "risk_detection_correct": 0,
        "total": len(test_cases),
    }
    
    for query, expected_risk in test_cases:
        print(f"\n🔹 Testing Query: '{query}'")
        print(f"   Expected Risk: {expected_risk}")
        
        # 清空日志
        capture_handler.logs = []
        
        steps = step_gen.generate_steps_with_retry(query)
        
        if steps:
            print("   ✅ Step Generation Successful")
            results["passed"] += 1
            
            # 验证风险检测是否正确 (通过检查日志)
            # StepGenerator 会打印 "🚩 [风险识别] 高风险因子: ..."
            found_risk_in_log = False
            for log_msg in capture_handler.logs:
                # 日志消息现在是: "🚩 [风险识别] 高风险因子: Ordinal_Ambiguity"
                if "🚩 [风险识别] 高风险因子" in log_msg:
                    print(f"   📝 Logged Risk: {log_msg}")
                    
                    # 检查预期风险是否在日志中
                    if expected_risk in log_msg:
                        found_risk_in_log = True
                    
                    # 特殊处理 None 的情况
                    # 如果预期是 None，而日志中显示 "None" 或者日志中没有任何风险因子（如果是那种实现的话）
                    if expected_risk == "None" and "None" in log_msg:
                        found_risk_in_log = True
            
            if found_risk_in_log:
                print(f"   🎯 Risk Detection Verified: {expected_risk}")
                results["risk_detection_correct"] += 1
            else:
                print(f"   ⚠️ Risk Detection Failed (Expected {expected_risk} not found in logs)")
        else:
            print("   ❌ Step Generation Failed")
            results["failed"] += 1
            
    print("\n========================================")
    print(f"📊 Overall Results:")
    print(f"   Steps Generated: {results['passed']}/{results['total']}")
    print(f"   Risk Correctly Detected: {results['risk_detection_correct']}/{results['total']}")

if __name__ == "__main__":
    run_risk_evaluation()
