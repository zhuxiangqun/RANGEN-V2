import json
import time

NEW_PROMPT = """**🚨🚨🚨 CRITICAL TASK DEFINITION - READ THIS FIRST 🚨🚨🚨**

**THIS IS A REASONING STEPS GENERATION TASK, NOT AN ANSWER GENERATION TASK!**

**YOUR TASK**: Generate the REASONING STEPS (in JSON format) that the system will use to FIND the answer.
**NOT YOUR TASK**: Provide the final answer directly.

**🚨🚨🚨 ABSOLUTELY FORBIDDEN - DO NOT RETURN DIRECT ANSWERS 🚨🚨🚨**

**CRITICAL UNDERSTANDING**:
- Even if you KNOW the answer (e.g., "Paris" or "Albert Einstein"), you MUST NOT return it directly
- You MUST return the REASONING STEPS that lead to finding that answer
- The system will execute these steps to retrieve information from the knowledge base
- Your job is to describe HOW to find the answer, NOT to provide the answer itself

**🚨 CRITICAL RULE #1: You MUST return ONLY valid JSON format. Your response MUST start with {{ and end with }}.**
**🚨 CRITICAL RULE #2: DO NOT return plain text answers.**
**🚨 CRITICAL RULE #3: DO NOT return explanations outside JSON.**
**🚨 CRITICAL RULE #4: DO NOT return just the answer - you MUST return the reasoning steps in JSON format.**
**🚨 CRITICAL RULE #5: If you return non-JSON format, your response will be REJECTED and the system will fail.**

**🚨 CRITICAL: Even if you know the answer, you MUST return JSON format reasoning steps, NOT the direct answer! 🚨**

**❌ FORBIDDEN RESPONSES (DO NOT DO THIS):**
- "Paris"
- "42"
- Any plain text answer without JSON structure
- Any response that doesn't start with {{ and end with }}

**✅ REQUIRED RESPONSE FORMAT (MUST DO THIS):**
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "...",
      "sub_query": "..."
    }}
  ]
}}

**🚀🚀🚀 CRITICAL: NO DUPLICATE STEPS - READ CAREFULLY 🚀🚀🚀**

**ABSOLUTELY FORBIDDEN:**
- DO NOT create duplicate steps with the same sub_query
- DO NOT repeat the same question in different steps
- DO NOT create multiple steps asking the same thing
- Each step MUST have a UNIQUE sub_query
- If you need similar information, combine them into ONE step or make them DISTINCT

**Example of WRONG (DO NOT DO THIS):**
Step 1: {{"sub_query": "What is the capital of X?"}}
Step 2: {{"sub_query": "What is the capital of X?"}}  ← DUPLICATE! FORBIDDEN!

**Example of CORRECT:**
Step 1: {{"sub_query": "What is the capital of X?"}}
Step 2: {{"sub_query": "What is the population of [result from step 1]?"}}

**Example of CORRECT format:**
{{"steps": [{{"type": "evidence_gathering", "sub_query": "What is X?", "description": "..."}}]}}

**Example of WRONG format (DO NOT DO THIS):**
The answer is Paris.

---

You are a universal reasoning engine. Your task is to analyze ANY type of problem and generate a rigorous, verifiable reasoning chain adapted to the problem's nature.

Query: {query}

**CRITICAL REQUIREMENTS - READ CAREFULLY**:

## Phase 1: Problem Analysis and Strategy Selection

### 1.1 Problem Understanding and Classification

First, understand and classify the problem:
- **Restate the problem** in one sentence: [Your understanding]
- **Problem type** (select ALL that apply):
  □ Factual verification (requires finding/confirming specific information)
  □ Logical derivation (requires deduction/induction/abduction)
  □ Mathematical calculation (requires formulas/computations)
  □ Creative generation (requires brainstorming)
  □ Comparative analysis (requires comparing multiple items)
  □ Causal analysis (requires finding causes/effects)

### 1.2 Key Elements Extraction

- **Known conditions**: [List all explicitly given information]
- **Implicit conditions**: [Derive necessary assumptions]
- **Target to find**: [Clearly state what needs to be found]

### 1.3 Strategy Selection

Select the dominant reasoning strategy based on problem type.

### 1.4 Problem Decomposition - 🚀 CRITICAL: Universal Problem Deconstruction Framework

**CORE PRINCIPLE: Problem Deconstruction and Dependency Graph Construction**

**Step 1: Identify the Final Goal**
- Clearly state what the problem ultimately requires as output.

**Step 2: List All Sub-goals**
- Identify ALL intermediate information pieces required to achieve the final goal.

**Step 3: Analyze Dependencies Between Sub-goals**
- **CRITICAL JUDGMENT CRITERION**: Does obtaining "Sub-goal A" require information from "Sub-goal B"?
  - If NO → They are **INDEPENDENT** and can be processed in parallel.
  - If YES → They have a **DEPENDENCY** and must be processed sequentially.

**Step 4: Build Query Chains for Each Sub-goal**
- For each independent sub-goal, work backwards to derive the series of atomic queries needed to obtain it.

**Step 5: Define Steps and Dependencies**
- Each atomic query becomes a step.
- The  field MUST accurately reflect information dependencies.
- **Independent query chains**: Their initial steps MUST have  (empty array).
- Use  to mark steps belonging to the same independent query chain.

**�� Example: Deconstructing a Composite Query**

**User Query**: "What is the currency of the country where the 2008 Summer Olympics were held?"

**Your Thinking Process**:
1. **Final Goal**: A currency name.
2. **Sub-goals**:
   - Sub-goal 1: Identify the country where the 2008 Summer Olympics were held.
   - Sub-goal 2: Identify the currency of that country.
3. **Dependency Analysis**: Sub-goal 2 depends on Sub-goal 1.
4. **Steps**:
   - Step 1: "Where were the 2008 Summer Olympics held?"
   - Step 2: "What is the currency of [result from step 1]?"

**🚀 SPECIAL ATTENTION FOR MULTI-HOP QUERIES:**
- **Multi-hop queries** require multiple sequential knowledge base lookups
- Example: "Who is the CEO of the company that created the iPhone?" requires:
  1. First: "Which company created the iPhone?"
  2. Then: "Who is the CEO of [result from step 1]?"

**🚨🚨🚨 CRITICAL: QUERY OBJECT ACCURACY 🚨🚨🚨**

**THE MOST COMMON ERROR: Querying the wrong object in multi-hop queries**

**Example of WRONG (DO NOT DO THIS):**
- Query: "Who is the CEO of the company that created the iPhone?"
- Step 1: "Which company created the iPhone?" → Answer: "Apple"
- Step 2: "Who is the CEO of the iPhone?" ✗ **WRONG!** This queries the iPhone's CEO, not the company's!

**Example of CORRECT:**
- Step 1: "Which company created the iPhone?" → Answer: "Apple"
- Step 2: "Who is the CEO of [result from step 1]?" → Answer: "Tim Cook" ✓ **CORRECT!** This queries the company's CEO!

**CRITICAL RULE:**
- In multi-hop queries like "X's Y's Z", you MUST query Z of the result from the previous step, NOT Z of X.
- Always trace back: What does the previous step return? Query the property of THAT result, not the original entity.

**MANDATORY REQUIREMENTS:**
- You MUST explicitly perform **dependency analysis** when generating steps.
- If sub-goals have no information dependency, their initial steps MUST have .
- Use  to mark steps belonging to the same independent query chain.
- **FORBIDDEN**: Do NOT incorrectly chain independent sub-goals into a single long chain.
- **CRITICAL**: You MUST generate steps for ALL independent sub-goals, not just one.

**🚨🚨🚨 CRITICAL: DO NOT USE YOUR TRAINING DATA KNOWLEDGE IN SUB_QUERIES 🚨🚨🚨**

**WHY THIS IS CRITICAL:**
- The system executes steps sequentially. Each step queries the knowledge base.
- If you use specific names from your training data (like "Apple", "Tesla"), the system cannot execute the step properly if the previous step failed or returned something else.
- The system needs to find the answer from the knowledge base, not from your training data.

**ABSOLUTELY FORBIDDEN - DO NOT DO THIS:**
- ❌ "Who is the CEO of Apple?" (Used specific name "Apple" instead of placeholder)

**REQUIRED - YOU MUST DO THIS:**
- ✅ "Who is the CEO of [step 1 result]?" (Used placeholder)

**VALID PLACEHOLDER FORMATS:**
- "[step 1 result]" or "[步骤1的结果]" - Reference to previous step result
- "[company]" - Reference to role/type (generic)

**🚨🚨🚨 CRITICAL: PLACEHOLDER REFERENCE RULES - STEPS EXECUTE SEQUENTIALLY 🚨🚨🚨**

**ABSOLUTELY FORBIDDEN - DO NOT REFERENCE FUTURE STEPS:**
- ❌ "[step 3 result]" in Step 2 (Step 3 hasn't been executed yet!)
- ❌ "[step X result]" where X >= current step number

**WHY THIS IS WRONG:**
- Steps are executed **SEQUENTIALLY** (Step 1 → Step 2 → Step 3 → ...)
- When Step 2 executes, Step 3 hasn't been executed yet
- Referencing a future step will cause execution failure

**REQUIRED - YOU MUST DO THIS:**
- ✅ "[step 1 result]" in Step 2 (Step 1 has already been executed)
- ✅ "[previous step result]" in Step 2 (references Step 1)

**VALIDATION RULE FOR PLACEHOLDERS:**
- If your sub_query contains "[step X result]" where X >= current step number, it is **WRONG**
- You MUST use "[step (X-1) result]" or "[previous step result]" instead

**VALIDATION RULE FOR NAMES:**
- If your sub_query contains a capitalized name from the query's answer (that you shouldn't know yet), it is WRONG.
- You MUST replace it with a placeholder.
- The ONLY exception is if the name is part of the original query.

**Universal Decomposition Rules:**
- DO NOT simply restate the original query
- DO NOT combine multiple questions into one step
- **ALWAYS follow the 5-step deconstruction framework**:
  1. Identify the final goal
  2. List all sub-goals
  3. Analyze dependencies between sub-goals
  4. Build query chains for each sub-goal
  5. Define steps with accurate dependencies
- **Dependency Analysis is MANDATORY**: Before generating steps, you MUST analyze whether sub-goals are independent or dependent.
- **Independent sub-goals**: Their initial steps MUST have  and be marked with .
- **Dependent sub-goals**: Their steps MUST have correct  relationships.
- For multi-hop queries, break them into sequential single-hop queries
- Each step should be a SINGLE, EXECUTABLE query that can be answered by the knowledge base
- **CRITICAL**: You MUST generate steps for ALL sub-goals identified in Step 2, not just one.

## Phase 2: Reasoning Chain Generation

For each sub-problem, generate appropriate steps based on the selected strategy:

### Step Types (Choose based on problem type):

1. **Knowledge Query Steps** (for factual verification):
   - **type**: "evidence_gathering" or "knowledge_query"

**FEW-SHOT EXAMPLES:**

Example 1 - Query: "Who is the CEO of the company that created the iPhone?"
✅ CORRECT:
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "Find the company",
      "sub_query": "Which company created the iPhone?"
    }},
    {{
      "type": "evidence_gathering",
      "description": "Find the CEO",
      "sub_query": "Who is the CEO of [step 1 result]?"
    }}
  ]
}}

❌ WRONG (DO NOT DO THIS):
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "Find the company",
      "sub_query": "Which company created the iPhone?"
    }},
    {{
      "type": "evidence_gathering",
      "description": "Find the CEO",
      "sub_query": "Who is the CEO of Apple?"
    }}
  ]
}}

Example 2 - Query: "What is the currency of the country where the 2008 Summer Olympics were held?"
✅ CORRECT:
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "Find the country",
      "sub_query": "Where were the 2008 Summer Olympics held?"
    }},
    {{
      "type": "evidence_gathering",
      "description": "Find the currency",
      "sub_query": "What is the currency of [step 1 result]?"
    }}
  ]
}}

❌ WRONG (DO NOT DO THIS):
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "Find the country",
      "sub_query": "Where were the 2008 Summer Olympics held?"
    }},
    {{
      "type": "evidence_gathering",
      "description": "Find the currency",
      "sub_query": "What is the currency of China?"
    }}
  ]
}}

**NOW REGENERATE THE REASONING STEPS FOR THIS QUERY:**
Query: {query}

**CRITICAL REMINDERS:**
1. Use placeholders like "[step 1 result]", "[company]", "[country]"
2. DO NOT use specific names from your training data
3. Each step must be executable independently
4. Return ONLY valid JSON format

Return the corrected reasoning steps in JSON format:"""

try:
    with open('templates/templates.json', 'r') as f:
        data = json.load(f)
    
    updated = False
    for template in data.get('templates', []):
        if template['name'] in ['reasoning_steps_generation', 'fallback_reasoning_steps_generation']:
            template['content'] = NEW_PROMPT
            template['quality_score'] = 0.95
            print(f"Updated template: {template['name']}")
            updated = True
            
    if updated:
        with open('templates/templates.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Successfully updated templates.json")
    else:
        print("No templates found to update")
        
except Exception as e:
    print(f"Error: {e}")
