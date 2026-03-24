"""
AI中台能力测试数据集

包含所有可以通过真实API测试评估的维度
"""

# A. 基础能力
ORCHESTRATION_TESTS = [
    {
        "id": "orch_001",
        "dimension": "orchestration",
        "category": "A",
        "input": "请帮我完成以下任务：1) 搜索今天的天气 2) 把结果保存到文件 3) 发送通知",
        "expected_behavior": "能够协调多个子任务，按顺序执行",
        "evaluation_criteria": ["多步骤协调", "任务分解", "执行顺序"],
        "difficulty": "medium"
    },
    {
        "id": "orch_002",
        "dimension": "orchestration",
        "category": "A",
        "input": "我需要调研人工智能在医疗领域的应用，包括现状、挑战和未来趋势，整理成报告",
        "expected_behavior": "能够分解为多个子任务并协调执行",
        "evaluation_criteria": ["复杂任务分解", "信息整合", "报告生成"],
        "difficulty": "hard"
    },
    {
        "id": "orch_003",
        "dimension": "orchestration",
        "category": "A",
        "input": "帮我做以下三件事：1) 计算10的阶乘 2) 把结果转为字符串 3) 告诉我结果是什么",
        "expected_behavior": "能够协调多个简单任务",
        "evaluation_criteria": ["任务协调", "结果整合"],
        "difficulty": "easy"
    },
]

AGENT_COMPLETENESS_TESTS = [
    {
        "id": "agent_001",
        "dimension": "agent_completeness",
        "category": "A",
        "input": "你是代码审查助手，请审查这段代码并指出潜在问题：def divide(a, b): return a // b",
        "expected_behavior": "能够识别除零错误等潜在问题",
        "evaluation_criteria": ["角色扮演", "专业能力", "问题识别"],
        "difficulty": "easy"
    },
    {
        "id": "agent_002",
        "dimension": "agent_completeness",
        "category": "A",
        "input": "作为一个数据分析师，帮我分析这份CSV数据的趋势：sales_data.csv",
        "expected_behavior": "能够理解分析师角色并执行数据分析",
        "evaluation_criteria": ["角色理解", "工具使用", "分析能力"],
        "difficulty": "medium"
    },
    {
        "id": "agent_003",
        "dimension": "agent_completeness",
        "category": "A",
        "input": "你是一个Python教师，请教我如何定义函数",
        "expected_behavior": "能够扮演教师角色进行教学",
        "evaluation_criteria": ["角色扮演", "教学内容", "表达能力"],
        "difficulty": "easy"
    },
]

PROMPT_ENGINEERING_TESTS = [
    {
        "id": "prompt_001",
        "dimension": "prompt_engineering",
        "category": "A",
        "input": "解释量子计算的基本原理，用通俗易懂的语言",
        "expected_behavior": "输出清晰、结构良好、通俗易懂",
        "evaluation_criteria": ["清晰度", "结构化", "易懂性"],
        "difficulty": "medium"
    },
    {
        "id": "prompt_002",
        "dimension": "prompt_engineering",
        "category": "A",
        "input": "用表格形式比较 Python、Java、JavaScript 三种语言的特点",
        "expected_behavior": "输出格式正确的表格对比",
        "evaluation_criteria": ["格式控制", "准确性", "完整性"],
        "difficulty": "easy"
    },
    {
        "id": "prompt_003",
        "dimension": "prompt_engineering",
        "category": "A",
        "input": "用bullet points列出学习Python的5个步骤",
        "expected_behavior": "输出格式化的bullet points",
        "evaluation_criteria": ["格式化能力", "清晰度"],
        "difficulty": "easy"
    },
]

CONTEXT_ENGINEERING_TESTS = [
    {
        "id": "ctx_001",
        "dimension": "context_engineering",
        "category": "A",
        "input": "根据之前的对话，继续完成报告的第三部分",
        "expected_behavior": "能够理解和利用之前的上下文",
        "evaluation_criteria": ["上下文保持", "连续性", "相关性"],
        "difficulty": "medium"
    },
    {
        "id": "ctx_002",
        "dimension": "context_engineering",
        "category": "A",
        "input": "记住我喜欢简洁的回答。现在解释什么是机器学习",
        "expected_behavior": "记住用户偏好并应用",
        "evaluation_criteria": ["偏好学习", "一致性", "适应能力"],
        "difficulty": "medium"
    },
    {
        "id": "ctx_003",
        "dimension": "context_engineering",
        "category": "A",
        "input": "之前我们讨论了Python的变量，现在继续讲数据类型",
        "expected_behavior": "能够追踪对话历史",
        "evaluation_criteria": ["历史追踪", "上下文连贯"],
        "difficulty": "medium"
    },
]

# B. 智能能力
RESPONSE_QUALITY_TESTS = [
    {
        "id": "resp_001",
        "dimension": "response_quality",
        "category": "B",
        "input": "什么是人工智能？",
        "expected_behavior": "回答准确、完整、有深度",
        "evaluation_criteria": ["准确性", "完整性", "深度"],
        "difficulty": "easy"
    },
    {
        "id": "resp_002",
        "dimension": "response_quality",
        "category": "B",
        "input": "为什么天空是蓝色的？请给出科学解释",
        "expected_behavior": "科学准确且易于理解",
        "evaluation_criteria": ["科学性", "可理解性", "完整性"],
        "difficulty": "medium"
    },
    {
        "id": "resp_003",
        "dimension": "response_quality",
        "category": "B",
        "input": "用简洁的语言解释区块链技术",
        "expected_behavior": "简洁准确，适合非专业人士理解",
        "evaluation_criteria": ["简洁性", "准确性", "易懂性"],
        "difficulty": "medium"
    },
]

ROUTING_TESTS = [
    {
        "id": "route_001",
        "dimension": "routing",
        "category": "B",
        "input": "帮我写一个Python函数计算阶乘",
        "expected_behavior": "识别为代码生成任务",
        "evaluation_criteria": ["任务识别", "技能路由", "执行正确"],
        "difficulty": "easy"
    },
    {
        "id": "route_002",
        "dimension": "routing",
        "category": "B",
        "input": "今天北京天气怎么样？适合出门吗？",
        "expected_behavior": "识别为信息查询+建议任务",
        "evaluation_criteria": ["多意图识别", "路由准确性"],
        "difficulty": "medium"
    },
    {
        "id": "route_003",
        "dimension": "routing",
        "category": "B",
        "input": "帮我分析这份销售数据并生成图表",
        "expected_behavior": "识别为数据分析任务",
        "evaluation_criteria": ["任务识别", "工具选择"],
        "difficulty": "medium"
    },
]

REASONING_TESTS = [
    {
        "id": "reason_001",
        "dimension": "reasoning",
        "category": "B",
        "input": "如果所有的猫都是动物，有些动物是狗，那么有些猫是狗吗？为什么？",
        "expected_behavior": "正确进行逻辑推理并给出解释",
        "evaluation_criteria": ["逻辑推理", "演绎能力", "解释清晰"],
        "difficulty": "hard"
    },
    {
        "id": "reason_002",
        "dimension": "reasoning",
        "category": "B",
        "input": "一个数除以3余1，除以5余2，这个数最小是多少？",
        "expected_behavior": "正确运用数学推理",
        "evaluation_criteria": ["数学推理", "问题解决", "步骤清晰"],
        "difficulty": "medium"
    },
    {
        "id": "reason_003",
        "dimension": "reasoning",
        "category": "B",
        "input": "小明有5个苹果，小红给了他3个，小明吃掉了2个，还剩多少？",
        "expected_behavior": "正确进行算术推理",
        "evaluation_criteria": ["算术能力", "逻辑清晰"],
        "difficulty": "easy"
    },
]

KNOWLEDGE_RECALL_TESTS = [
    {
        "id": "know_001",
        "dimension": "knowledge_recall",
        "category": "B",
        "input": "《哈利·波特》系列小说的作者是谁？她还写过哪些作品？",
        "expected_behavior": "准确回忆相关知识",
        "evaluation_criteria": ["知识准确性", "知识广度", "关联能力"],
        "difficulty": "easy"
    },
    {
        "id": "know_002",
        "dimension": "knowledge_recall",
        "category": "B",
        "input": "2024年诺贝尔物理学奖获得者是谁？他们的主要贡献是什么？",
        "expected_behavior": "准确回忆最新知识",
        "evaluation_criteria": ["知识时效性", "准确性"],
        "difficulty": "medium"
    },
    {
        "id": "know_003",
        "dimension": "knowledge_recall",
        "category": "B",
        "input": "解释相对论的基本概念",
        "expected_behavior": "准确回忆物理学知识",
        "evaluation_criteria": ["知识深度", "准确性", "表达能力"],
        "difficulty": "hard"
    },
]

TOOL_CALLING_TESTS = [
    {
        "id": "tool_001",
        "dimension": "tool_calling",
        "category": "B",
        "input": "帮我搜索一下今天有什么好看的电影",
        "expected_behavior": "能够调用搜索工具",
        "evaluation_criteria": ["工具识别", "参数正确", "结果整合"],
        "difficulty": "medium"
    },
    {
        "id": "tool_002",
        "dimension": "tool_calling",
        "category": "B",
        "input": "帮我计算一下 2 的 10 次方等于多少",
        "expected_behavior": "能够调用计算工具",
        "evaluation_criteria": ["工具选择", "参数传递", "结果返回"],
        "difficulty": "easy"
    },
    {
        "id": "tool_003",
        "dimension": "tool_calling",
        "category": "B",
        "input": "帮我把这段文字翻译成英文：今天天气真好",
        "expected_behavior": "能够调用翻译工具",
        "evaluation_criteria": ["工具识别", "翻译质量"],
        "difficulty": "easy"
    },
]

MULTI_TURN_TESTS = [
    {
        "id": "multi_001",
        "dimension": "multi_turn",
        "category": "B",
        "turns": [
            {"role": "user", "content": "我想学习Python"},
            {"role": "assistant", "content": "好的，Python是一门易学易用的编程语言。你想从哪里开始？"},
            {"role": "user", "content": "先教我变量"},
            {"role": "assistant", "content": "变量是存储数据的容器..."},
            {"role": "user", "content": "那数据类型有哪些？"},
        ],
        "expected_behavior": "保持对话连贯，理解上下文",
        "evaluation_criteria": ["上下文保持", "对话连贯", "渐进学习"],
        "difficulty": "medium"
    },
    {
        "id": "multi_002",
        "dimension": "multi_turn",
        "category": "B",
        "turns": [
            {"role": "user", "content": "帮我写一个排序算法"},
            {"role": "assistant", "content": "好的，你想要快速排序、归并排序还是冒泡排序？"},
            {"role": "user", "content": "快速排序吧"},
            {"role": "assistant", "content": "快速排序使用分治策略..."},
            {"role": "user", "content": "时间复杂度是多少？"},
        ],
        "expected_behavior": "能够继续之前的对话上下文",
        "evaluation_criteria": ["上下文保持", "话题连贯"],
        "difficulty": "medium"
    },
]

SELF_LEARNING_TESTS = [
    {
        "id": "learn_001",
        "dimension": "self_learning",
        "category": "B",
        "input": "我教了你一个新词 'foo' 意思是快速行动，现在用它造句",
        "expected_behavior": "能够学习并应用新知识",
        "evaluation_criteria": ["知识学习", "灵活应用", "一致性"],
        "difficulty": "medium"
    },
    {
        "id": "learn_002",
        "dimension": "self_learning",
        "category": "B",
        "input": "记住我的名字叫小明。以后用这个名字称呼我。",
        "expected_behavior": "记住并使用新信息",
        "evaluation_criteria": ["记忆能力", "后续使用", "适应性"],
        "difficulty": "easy"
    },
    {
        "id": "learn_003",
        "dimension": "self_learning",
        "category": "B",
        "input": "我更喜欢详细的长回答。现在解释什么是机器学习。",
        "expected_behavior": "学习并应用用户偏好",
        "evaluation_criteria": ["偏好学习", "一致性", "适应性"],
        "difficulty": "medium"
    },
]

ALL_TESTS = {
    "orchestration": ORCHESTRATION_TESTS,
    "agent_completeness": AGENT_COMPLETENESS_TESTS,
    "prompt_engineering": PROMPT_ENGINEERING_TESTS,
    "context_engineering": CONTEXT_ENGINEERING_TESTS,
    "response_quality": RESPONSE_QUALITY_TESTS,
    "routing": ROUTING_TESTS,
    "reasoning": REASONING_TESTS,
    "knowledge_recall": KNOWLEDGE_RECALL_TESTS,
    "tool_calling": TOOL_CALLING_TESTS,
    "multi_turn": MULTI_TURN_TESTS,
    "self_learning": SELF_LEARNING_TESTS,
}

def get_all_tests():
    return ALL_TESTS

def get_test_count():
    return sum(len(tests) for tests in ALL_TESTS.values())
