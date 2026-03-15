
import os
import asyncio
import logging
import sys
from datetime import datetime
from src.core.reasoning.engine import RealReasoningEngine
from src.core.reasoning.config import get_default_config

# 配置日志
log_filename = f"current_debug_future_wife_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def reproduce_reasoning():
    print(f"🚀 Starting reproduction... Logs will be saved to {log_filename}")
    
    # 1. 初始化引擎
    engine = RealReasoningEngine()
    
    # 强制开启详细日志和调试模式
    if hasattr(engine, 'config'):
        if hasattr(engine.config, 'generation'):
             engine.config.generation.debug_mode = True
    
    # 2. 构造查询
    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    print(f"\n❓ Query: {query}\n")
    
    # 3. 执行推理
    try:
        # 使用 reason 方法，它会包含完整的推理流程（分步生成 -> 执行 -> 验证）
        result = await engine.reason(query, context={})
        
        print("\n✅ Execution Completed!")
        print(f"💡 Final Answer: {result.final_answer}")
        
        # 4. 提取并展示推理步骤
        steps = result.reasoning_steps
        if steps:
            print("\n📜 Execution Trace (Reasoning Steps):")
            for i, step in enumerate(steps):
                # step 是 ReasoningStep 对象或字典
                if hasattr(step, 'step_type'):
                    # ReasoningStep 对象 (models.py 定义)
                    step_type = step.step_type
                    step_desc = step.description
                    # ReasoningStep 没有 sub_query 和 result 字段，这些可能在 reasoning_process 或 metadata 中
                    # 但 engine.py _generate_reasoning_steps 返回的是 dict 列表
                    # 而 engine.py reason 返回的 ReasoningResult.reasoning_steps 可能是 ReasoningStep 对象列表
                    # 检查 models.py: ReasoningStep 确实没有 sub_query 和 result
                    # 检查 engine.py: _convert_steps_to_objects 可能会转换
                    
                    # 尝试从 reasoning_process 或其他字段获取信息
                    step_sub_query = "N/A (ReasoningStep object)"
                    step_result = step.reasoning_process
                elif isinstance(step, dict):
                    # 字典格式
                    step_type = step.get('type')
                    step_desc = step.get('description')
                    step_sub_query = step.get('sub_query')
                    step_result = step.get('result', 'Pending/No Result')
                else:
                    # 其他情况
                    step_type = getattr(step, 'type', 'Unknown')
                    step_desc = getattr(step, 'description', 'Unknown')
                    step_sub_query = getattr(step, 'sub_query', 'Unknown')
                    step_result = getattr(step, 'result', 'Pending/No Result')
                
                print(f"\n[Step {i+1}] Type: {step_type}")
                print(f"  Description: {step_desc}")
                print(f"  Sub-query: {step_sub_query}")
                print(f"  Result: {step_result}")
        else:
            print("\n⚠️ No structured steps found. The model might have used direct reasoning.")
            
        # 5. 检查是否有思维链日志 (ReasoningResult 可能没有 reasoning_trace 字段，除非它是后来添加的)
        if hasattr(result, 'reasoning_trace') and result.reasoning_trace:
             print("\n🧠 Model Reasoning Trace (CoT):")
             print(result.reasoning_trace[:1000] + "..." if len(result.reasoning_trace) > 1000 else result.reasoning_trace)

    except Exception as e:
        logger.error(f"❌ Execution failed: {e}", exc_info=True)
        print(f"\n❌ Execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce_reasoning())
