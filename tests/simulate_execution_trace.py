import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.step_generator import StepGenerator

def simulate_execution():
    print("\n🔍 模拟 7 步推理的执行过程 (Simulation of Execution Trace)\n")
    print("Query: If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?\n")

    # 1. Initialize Generator
    generator = StepGenerator()
    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    # 2. Generate Steps (Force fallback logic)
    steps = generator._generate_fallback_steps(query, "logical_reasoning")
    
    if not steps or len(steps) < 6:
        print("❌ 未能生成预期的 7 个步骤，请检查 StepGenerator 逻辑")
        return

    # 3. Simulate Execution Loop
    context = {}
    
    # Define Ground Truth Data for Simulation
    ground_truth = {
        "15th first lady": "Harriet Lane (niece of James Buchanan)",
        "mother of Harriet Lane": "Jane Ann Buchanan",
        "first name of Jane Ann Buchanan": "Jane",
        "second assassinated president": "James A. Garfield",
        "mother of James A. Garfield": "Eliza Ballou",
        "maiden name of Eliza Ballou": "Ballou"
    }

    # Define Common Error Data (Hallucination)
    # 错误情景：模型不知道布坎南未婚，或者错误地找了第14任或16任的妻子
    error_scenario = {
        "15th first lady": "Jane Pierce (Wife of Franklin Pierce, 14th President) [INCORRECT]",
        "mother of Jane Pierce": "Mary Means Appleton [INCORRECT PATH]",
        "first name of Mary Means Appleton": "Mary [INCORRECT]",
        # Assuming second branch is correct
        "second assassinated president": "James A. Garfield",
        "mother of James A. Garfield": "Eliza Ballou",
        "maiden name of Eliza Ballou": "Ballou"
    }

    print("-" * 80)
    print(f"{'Step':<5} | {'Description':<50} | {'Simulated Result (Common Error Path)':<40}")
    print("-" * 80)

    step_results = {}

    for i, step in enumerate(steps):
        step_id = f"step_{i+1}"
        description = step['description']
        sub_query = step.get('sub_query', 'N/A')
        
        # Simulate LLM Response logic
        result = "N/A"
        
        # Logic for Step 1: 15th First Lady
        if "Identify the 15th first lady" in description:
            result = error_scenario["15th first lady"]
            
        # Logic for Step 2: Mother of 15th FL
        elif "Find the mother of the 15th first lady" in description:
            prev_result = step_results.get(f"step_{i}", "Unknown") # i is current index, so step_{i} is previous step (step_1)
            # wait, i=1, step_1 is previous.
            if "Jane Pierce" in prev_result:
                result = error_scenario["mother of Jane Pierce"]
            else:
                result = ground_truth["mother of Harriet Lane"]

        # Logic for Step 3: First name
        elif "Extract the first name" in description:
             # Check step 2 result (which is step_{i} when i=2)
             prev_result = step_results.get(f"step_{i}", "Unknown")
             if "Mary Means Appleton" in prev_result:
                 result = error_scenario["first name of Mary Means Appleton"]
             else:
                 result = ground_truth["first name of Jane Ann Buchanan"]

        # Logic for Step 4: 2nd Assassinated President
        elif "Identify the second assassinated president" in description:
            result = ground_truth["second assassinated president"]

        # Logic for Step 5: Mother of President
        elif "Find the mother of the second assassinated president" in description:
            result = ground_truth["mother of James A. Garfield"]

        # Logic for Step 6: Maiden Name
        elif "Find the maiden name" in description:
            result = ground_truth["maiden name of Eliza Ballou"]

        # Logic for Step 7: Synthesis
        elif "Combine" in description or "Synthesize" in description:
            # Try to grab from context
            first_name = "Mary" # from error path
            surname = "Ballou"
            result = f"{first_name} {surname}"

        step_results[step_id] = result
        
        # Output Row
        print(f"{i+1:<5} | {description[:48]:<50} | {result:<40}")

    print("-" * 80)
    print(f"\n❌ 最终错误结果: Mary Ballou (或其他组合)")
    print(f"✅ 正确事实结果: Jane Ballou")
    print("\n🔍 根本原因分析 (Root Cause Analysis):")
    print("Step 1 是关键失效点。由于第15任总统 James Buchanan 终身未婚，")
    print("模型极易错误地将第14任总统夫人 (Jane Pierce) 或第16任 (Mary Todd Lincoln)")
    print("识别为'第15位第一夫人'，导致后续关于母亲名字的查询全部偏离事实。")

if __name__ == "__main__":
    simulate_execution()
