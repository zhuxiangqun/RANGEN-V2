
import asyncio
import sys
import os
import json
import logging
from typing import Dict, Any, List

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.core.reasoning.engine import RealReasoningEngine
from src.core.reasoning.models import ReasoningStep

async def verify_end_to_end():
    print("\n🚀 Starting End-to-End Verification...")
    
    # Initialize Engine
    try:
        engine = RealReasoningEngine()
        print("✅ RealReasoningEngine initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize RealReasoningEngine: {e}")
        return

    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    print(f"\n❓ Query: {query}\n")
    
    try:
        # Execute reasoning
        print("⏳ Executing reasoning (this may take a moment)...")
        steps = await engine.reason(query, {})
        
        if not steps:
            print("❌ Reasoning returned None or empty list.")
            return

        print(f"\n✅ Reasoning completed with {len(steps.reasoning_steps)} steps.\n")
        
        # Analyze steps
        found_15th_first_lady = False
        harriet_lane_found = False
        none_error_found = False
        
        for i, step in enumerate(steps.reasoning_steps):
            step_desc = step.description if hasattr(step, 'description') else str(step)
            # 🚀 修复：step.output_evidence 可能不是直接的 result，需要适配
            # 假设 ReasoningStep 的 result 存储在 output_evidence 或者其他字段
            # 查看 models.py，ReasoningStep 没有 result 字段，而是 output_evidence
            # 但是日志显示有 result，可能是 dynamic attribute 或者在这个脚本里怎么处理
            # 让我们打印 step 的所有属性来看看
            
            # 尝试获取 result，如果不存在，查看 output_evidence
            if hasattr(step, 'result'):
                step_result = step.result
            elif hasattr(step, 'output_evidence') and step.output_evidence:
                # 假设 output_evidence 是 Evidence 列表，取第一个的 content
                if isinstance(step.output_evidence, list) and len(step.output_evidence) > 0:
                    step_result = step.output_evidence[0].content
                else:
                    step_result = str(step.output_evidence)
            else:
                 # 检查是否是字典（有时候 step 可能是 dict）
                if isinstance(step, dict):
                    step_result = step.get('result', 'N/A')
                    step_desc = step.get('description', 'N/A')
                else:
                    step_result = "N/A"

            print(f"🔹 Step {i+1}: {step_desc}")
            print(f"   Result: {step_result}")
            
            # Check for Step 1 accuracy
            if "15th first lady" in step_desc.lower():
                found_15th_first_lady = True
                if "harriet lane" in str(step_result).lower():
                    harriet_lane_found = True
                    print("   ✅ CORRECT FACT FOUND: Harriet Lane")
                else:
                    print("   ⚠️ FACT CHECK FAILED: Expected 'Harriet Lane'")
            
            # Check for None errors
            if step_result is None or step_result == "None":
                none_error_found = True
                print("   ❌ ERROR: Step result is None")

        # Summary
        print("\n📊 Verification Summary:")
        if found_15th_first_lady:
            if harriet_lane_found:
                print("✅ Step 1 Fact Check: PASSED (Harriet Lane found)")
            else:
                print("❌ Step 1 Fact Check: FAILED (Harriet Lane NOT found)")
        else:
            print("⚠️ Step 1 Fact Check: SKIPPED (Step 1 not identified)")
            
        if none_error_found:
            print("❌ Error Check: FAILED (None results found)")
        else:
            print("✅ Error Check: PASSED (No None results)")
            
    except Exception as e:
        print(f"❌ Execution failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_end_to_end())
