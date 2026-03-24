"""
AI中台能力测试数据集

覆盖 V1 (7维度) 和 V2 (26维度) 所有评估维度
每个测试用例包含：输入、预期行为、评估标准
"""

# V2 维度映射到测试用例
# A. 基础能力 (25%)
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
]

# B. 智能能力 (30%)
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
]

# C. 架构能力 (28%) - 这些主要评估系统架构设计
HARNESS_TESTS = [
    {
        "id": "harness_001",
        "dimension": "harness",
        "category": "C",
        "input": "当系统过载时，如何保证核心服务不受影响？",
        "expected_behavior": "能够描述或实现降级策略",
        "evaluation_criteria": ["降级机制", "容错能力", "设计合理性"],
        "difficulty": "hard"
    },
]

ARCHITECTURE_TESTS = [
    {
        "id": "arch_001",
        "dimension": "architecture",
        "category": "C",
        "input": "设计一个高可用的微服务架构需要考虑哪些因素？",
        "expected_behavior": "能够提供全面的架构建议",
        "evaluation_criteria": ["架构思维", "全面性", "实用性"],
        "difficulty": "hard"
    },
]

OBSERVABILITY_TESTS = [
    {
        "id": "observe_001",
        "dimension": "observability",
        "category": "C",
        "input": "如何监控一个分布式系统的健康状态？",
        "expected_behavior": "能够提供监控方案",
        "evaluation_criteria": ["监控意识", "指标选择", "告警机制"],
        "difficulty": "medium"
    },
]

MONITORING_TESTS = [
    {
        "id": "monitor_001",
        "dimension": "monitoring",
        "category": "C",
        "input": "系统响应变慢如何排查？",
        "expected_behavior": "能够提供排查思路和工具",
        "evaluation_criteria": ["排查能力", "工具使用", "系统性"],
        "difficulty": "medium"
    },
]

SELF_HEALING_TESTS = [
    {
        "id": "heal_001",
        "dimension": "self_healing",
        "category": "C",
        "input": "描述一个自动故障恢复系统的设计思路",
        "expected_behavior": "能够设计自愈机制",
        "evaluation_criteria": ["自愈意识", "恢复策略", "自动化程度"],
        "difficulty": "hard"
    },
]

ROLLOUT_TESTS = [
    {
        "id": "rollout_001",
        "dimension": "rollout",
        "category": "C",
        "input": "如何安全地发布一个新功能到生产环境？",
        "expected_behavior": "能够描述灰度发布策略",
        "evaluation_criteria": ["发布策略", "风险控制", "回滚机制"],
        "difficulty": "medium"
    },
]

# D. 数据能力 (10%)
DATA_SOURCE_TESTS = [
    {
        "id": "data_001",
        "dimension": "data_source",
        "category": "D",
        "input": "如何将MySQL数据库的数据实时同步到Elasticsearch？",
        "expected_behavior": "能够提供数据同步方案",
        "evaluation_criteria": ["方案完整性", "技术选型", "可行性"],
        "difficulty": "hard"
    },
]

KNOWLEDGE_MGMT_TESTS = [
    {
        "id": "km_001",
        "dimension": "knowledge_mgmt",
        "category": "D",
        "input": "企业如何构建知识库系统？有哪些最佳实践？",
        "expected_behavior": "能够提供知识管理方案",
        "evaluation_criteria": ["方案完整性", "实用性", "可扩展性"],
        "difficulty": "medium"
    },
]

VECTOR_MGMT_TESTS = [
    {
        "id": "vector_001",
        "dimension": "vector_mgmt",
        "category": "D",
        "input": "向量数据库在语义搜索中如何提升搜索效果？",
        "expected_behavior": "能够解释向量搜索原理",
        "evaluation_criteria": ["原理理解", "应用场景", "效果提升"],
        "difficulty": "medium"
    },
]

DATA_LINEAGE_TESTS = [
    {
        "id": "lineage_001",
        "dimension": "data_lineage",
        "category": "D",
        "input": "数据血缘追踪有什么价值？如何实现？",
        "expected_behavior": "能够解释数据血缘概念",
        "evaluation_criteria": ["概念理解", "价值说明", "实现方式"],
        "difficulty": "medium"
    },
]

# E. 平台能力 (7%)
APP_SUPPORT_TESTS = [
    {
        "id": "app_001",
        "dimension": "app_support",
        "category": "E",
        "input": "如何设计一个支持多租户的SaaS应用？",
        "expected_behavior": "能够提供多租户设计方案",
        "evaluation_criteria": ["隔离性", "扩展性", "资源效率"],
        "difficulty": "hard"
    },
]

COST_CONTROL_TESTS = [
    {
        "id": "cost_001",
        "dimension": "cost_control",
        "category": "E",
        "input": "如何优化大模型API调用成本？",
        "expected_behavior": "能够提供成本优化方案",
        "evaluation_criteria": ["优化意识", "方案有效性", "权衡分析"],
        "difficulty": "medium"
    },
]

INTEGRATION_TESTS = [
    {
        "id": "int_001",
        "dimension": "integration",
        "category": "E",
        "input": "如何将第三方支付系统集成到现有平台？",
        "expected_behavior": "能够提供集成方案",
        "evaluation_criteria": ["方案完整性", "安全性", "可维护性"],
        "difficulty": "hard"
    },
]

# 汇总所有测试用例
ALL_TESTS = {
    # A. 基础能力
    "orchestration": ORCHESTRATION_TESTS,
    "agent_completeness": AGENT_COMPLETENESS_TESTS,
    "prompt_engineering": PROMPT_ENGINEERING_TESTS,
    "context_engineering": CONTEXT_ENGINEERING_TESTS,
    # B. 智能能力
    "response_quality": RESPONSE_QUALITY_TESTS,
    "routing": ROUTING_TESTS,
    "reasoning": REASONING_TESTS,
    "knowledge_recall": KNOWLEDGE_RECALL_TESTS,
    "tool_calling": TOOL_CALLING_TESTS,
    "multi_turn": MULTI_TURN_TESTS,
    "self_learning": SELF_LEARNING_TESTS,
    # C. 架构能力
    "harness": HARNESS_TESTS,
    "architecture": ARCHITECTURE_TESTS,
    "observability": OBSERVABILITY_TESTS,
    "monitoring": MONITORING_TESTS,
    "self_healing": SELF_HEALING_TESTS,
    "rollout": ROLLOUT_TESTS,
    # D. 数据能力
    "data_source": DATA_SOURCE_TESTS,
    "knowledge_mgmt": KNOWLEDGE_MGMT_TESTS,
    "vector_mgmt": VECTOR_MGMT_TESTS,
    "data_lineage": DATA_LINEAGE_TESTS,
    # E. 平台能力
    "app_support": APP_SUPPORT_TESTS,
    "cost_control": COST_CONTROL_TESTS,
    "integration": INTEGRATION_TESTS,
}

# V2 维度到 V1 维度的映射
V2_TO_V1_MAPPING = {
    "orchestration": "core_capability",
    "agent_completeness": "core_capability",
    "prompt_engineering": "core_capability",
    "context_engineering": "core_capability",
    "response_quality": "performance",
    "routing": "performance",
    "reasoning": "performance",
    "knowledge_recall": "performance",
    "tool_calling": "performance",
    "multi_turn": "performance",
    "self_learning": "performance",
    "harness": "reliability",
    "architecture": "reliability",
    "observability": "reliability",
    "monitoring": "reliability",
    "self_healing": "reliability",
    "rollout": "reliability",
    "data_source": "code_quality",
    "knowledge_mgmt": "code_quality",
    "vector_mgmt": "code_quality",
    "data_lineage": "code_quality",
    "app_support": "platform_features",
    "cost_control": "platform_features",
    "integration": "integration",
}

# 获取所有测试用例
def get_all_tests():
    """获取所有测试用例"""
    tests = []
    for dimension, test_cases in ALL_TESTS.items():
        for test in test_cases:
            test["dimension"] = dimension
            test["v1_category"] = V2_TO_V1_MAPPING.get(dimension, "unknown")
            tests.append(test)
    return tests

def get_tests_by_dimension(dimension: str, limit: int = None):
    """获取指定维度的测试用例"""
    tests = ALL_TESTS.get(dimension, [])
    if limit:
        tests = tests[:limit]
    return tests

def get_tests_by_category(category: str):
    """获取指定类别的测试用例"""
    tests = []
    for dimension, test_cases in ALL_TESTS.items():
        if dimension.startswith(category.lower()):
            tests.extend(test_cases)
    return tests

def get_test_count():
    """获取测试用例总数"""
    return sum(len(tests) for tests in ALL_TESTS.values())
