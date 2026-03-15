import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from unittest.mock import MagicMock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("benchmark_debug.log", mode='w')
    ]
)
logger = logging.getLogger("quality_benchmark")

# 配置日志捕获
class BenchmarkLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def emit(self, record):
        self.logs.append(record)

# 导入 StepGenerator
try:
    from src.core.reasoning.step_generator import StepGenerator
    from src.core.llm_integration import LLMIntegration
except ImportError:
    print("❌ 无法导入 src.core 模块，请确保在项目根目录运行")
    exit(1)

# Mock LLM (用于快速测试，如果不使用真实LLM)
class MockLLM(LLMIntegration):
    def __init__(self):
        self.call_count = 0
        self.fail_rate = 0.0 # 模拟失败率
        self.bad_json_rate = 0.0 # 模拟坏JSON率
        
    def call_llm(self, prompt, **kwargs):
        self.call_count += 1
        
        # 模拟 One-Shot 效果：大部分时间返回完美JSON
        return json.dumps({
            "reasoning": {
                "thought_process": "Mock thinking process... analyzing dependencies...",
                "risk_factors": ["Ordinal ambiguity", "Entity verification"],
                "uncertainty_level": "Low"
            },
            "steps": [
                {
                    "type": "evidence_gathering",
                    "description": "Find information about the query",
                    "sub_query": "What is the capital of France?"
                },
                {
                    "type": "answer_synthesis",
                    "description": "Combine findings"
                }
            ]
        })

def run_benchmark(use_mock=True, num_queries=5):
    print(f"🚀 Starting Quality Benchmark (Use Mock: {use_mock})...")
    
    # Setup
    log_handler = BenchmarkLogHandler()
    logger = logging.getLogger("src.core.reasoning.step_generator")
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    
    if use_mock:
        llm = MockLLM()
    else:
        # 尝试使用真实 LLM (需要配置)
        try:
            from src.core.llm_integration import LLMIntegration
            import os
            # 尝试从环境变量加载配置，或者使用默认值
            config = {
                "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": os.getenv("LLM_MODEL", "deepseek-reasoner"),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            }
            if not config["api_key"]:
                print("⚠️ 未检测到 API Key，请设置 DEEPSEEK_API_KEY 环境变量")
                raise ValueError("Missing API Key")
                
            llm = LLMIntegration(config)
            print(f"✅ 真实 LLM 模式已激活: {config['llm_provider']} / {config['model']}")
            
            # Initialize Fast LLM (deepseek-chat) for semantic routing
            fast_config = config.copy()
            fast_config["model"] = "deepseek-chat"
            fast_llm = LLMIntegration(fast_config)
            print(f"✅ Fast LLM 模式已激活: {fast_config['llm_provider']} / {fast_config['model']}")
            
        except Exception as e:
            print(f"⚠️ 无法初始化真实 LLM ({e})，回退到 Mock 模式")
            llm = MockLLM()
            fast_llm = None
        
    step_gen = StepGenerator(llm_integration=llm, fast_llm_integration=fast_llm)
    
    # Test Queries
    queries = [
        "Who is the president of USA?",
        "What is the capital of France?",
        "Who is the mother of the 15th president of the United States?", # Complex
        "If a=1 and b=2, what is a+b?", # Logical
        "Tell me a joke about AI" # Edge case
    ]
    
    # Metrics
    metrics = {
        "total_queries": 0,
        "success_first_try": 0,
        "success_with_retry": 0,
        "failed": 0,
        "total_retries": 0,
        "error_types": {}
    }
    
    start_time = time.time()
    
    for i, query in enumerate(queries[:num_queries]):
        print(f"\n🔹 Query {i+1}: {query}")
        metrics["total_queries"] += 1
        
        # Clear logs for this run
        log_handler.logs = []
        
        # Run
        steps = step_gen.generate_steps_with_retry(query)
        
        # Analyze logs to determine what happened
        retries = 0
        success = False
        raw_quality_fail = False # Track if raw output failed validation
        
        for record in log_handler.logs:
            msg = record.getMessage()
            if "步骤生成成功" in msg or "命中简单查询模式" in msg or "[Semantic Router] Intent:" in msg:
                success = True
                # Check if it was a fast path success (Router or Regex)
                if "命中简单查询模式" in msg or ("[Semantic Router] Intent:" in msg and "COMPLEX" not in msg):
                    metrics["success_first_try"] += 1
                elif "尝试1" in msg:
                    metrics["success_first_try"] += 1
                else:
                    metrics["success_with_retry"] += 1
            if "重试尝试" in msg:
                retries += 1
                metrics["total_retries"] += 1
            if "Schema验证失败" in msg or "步骤逻辑验证不合格" in msg:
                raw_quality_fail = True
                metrics["error_types"]["validation_fail"] = metrics["error_types"].get("validation_fail", 0) + 1
            if "解析失败" in msg:
                 metrics["error_types"]["parse_error"] = metrics["error_types"].get("parse_error", 0) + 1

        if not success:
            metrics["failed"] += 1
            print("   ❌ Failed")
        else:
            status = "✅ Perfect Raw Quality" if not raw_quality_fail and retries == 0 else f"⚠️ Fixed via Retry ({retries})"
            print(f"   {status}")
            
    end_time = time.time()
    duration = end_time - start_time
    
    # Report
    print("\n" + "="*50)
    print("📊 BENCHMARK REPORT")
    print("="*50)
    print(f"Total Queries:      {metrics['total_queries']}")
    print(f"Success (1st Try):  {metrics['success_first_try']} ({metrics['success_first_try']/metrics['total_queries']*100:.1f}%)")
    print(f"Success (Retry):    {metrics['success_with_retry']} ({metrics['success_with_retry']/metrics['total_queries']*100:.1f}%)")
    print(f"Failed:             {metrics['failed']} ({metrics['failed']/metrics['total_queries']*100:.1f}%)")
    print(f"Avg Retries/Query:  {metrics['total_retries']/metrics['total_queries']:.2f}")
    print(f"Total Time:         {duration:.2f}s")
    print("-" * 30)
    print("Error Distribution:")
    for k, v in metrics['error_types'].items():
        print(f"  - {k}: {v}")
    print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Use real LLM instead of mock")
    args = parser.parse_args()
    
    run_benchmark(use_mock=not args.real)
