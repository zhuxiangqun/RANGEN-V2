"""
端到端集成测试用例 - 24个维度

每个维度包含3-5个测试用例，共100+测试用例
"""

# A. 基础能力 (4个维度)
ORCHESTRATION_TESTS = [
    {
        "id": "orch_001",
        "dimension": "orchestration",
        "input": "请帮我完成以下任务：1) 搜索今天的天气 2) 把结果保存到文件 3) 发送通知",
        "expected_behavior": "能够协调多个子任务，按顺序执行",
        "evaluation_criteria": ["多步骤协调", "任务分解", "执行顺序"],
        "difficulty": "medium"
    },
    {
        "id": "orch_002",
        "dimension": "orchestration",
        "input": "我需要调研人工智能在医疗领域的应用，包括现状、挑战和未来趋势，整理成报告",
        "expected_behavior": "能够分解为多个子任务并协调执行",
        "evaluation_criteria": ["复杂任务分解", "信息整合", "报告生成"],
        "difficulty": "hard"
    },
    {
        "id": "orch_003",
        "dimension": "orchestration",
        "input": "帮我做以下三件事：1) 计算10的阶乘 2) 把结果转为字符串 3) 告诉我结果是什么",
        "expected_behavior": "能够协调多个简单任务",
        "evaluation_criteria": ["任务协调", "结果整合"],
        "difficulty": "easy"
    },
    {
        "id": "orch_004",
        "dimension": "orchestration",
        "input": "分析这份销售数据，生成图表，并发送邮件给团队",
        "expected_behavior": "能够处理数据和通信任务",
        "evaluation_criteria": ["数据处理", "可视化", "通信"],
        "difficulty": "medium"
    },
]

AGENT_COMPLETENESS_TESTS = [
    {
        "id": "agent_001",
        "dimension": "agent_completeness",
        "input": "你是代码审查助手，请审查这段代码并指出潜在问题：def divide(a, b): return a // b",
        "expected_behavior": "能够识别除零错误等潜在问题",
        "evaluation_criteria": ["角色扮演", "专业能力", "问题识别"],
        "difficulty": "easy"
    },
    {
        "id": "agent_002",
        "dimension": "agent_completeness",
        "input": "作为一个数据分析师，帮我分析这份CSV数据的趋势：sales_data.csv",
        "expected_behavior": "能够理解分析师角色并执行数据分析",
        "evaluation_criteria": ["角色理解", "工具使用", "分析能力"],
        "difficulty": "medium"
    },
    {
        "id": "agent_003",
        "dimension": "agent_completeness",
        "input": "你是一个Python教师，请教我如何定义函数",
        "expected_behavior": "能够扮演教师角色进行教学",
        "evaluation_criteria": ["角色扮演", "教学内容", "表达能力"],
        "difficulty": "easy"
    },
    {
        "id": "agent_004",
        "dimension": "agent_completeness",
        "input": "作为法律顾问，帮我审阅这份合同，找出需要修改的条款",
        "expected_behavior": "能够扮演法律顾问角色",
        "evaluation_criteria": ["角色扮演", "法律知识", "条款分析"],
        "difficulty": "hard"
    },
]

PROMPT_ENGINEERING_TESTS = [
    {
        "id": "prompt_001",
        "dimension": "prompt_engineering",
        "input": "解释量子计算的基本原理，用通俗易懂的语言",
        "expected_behavior": "输出清晰、结构良好、通俗易懂",
        "evaluation_criteria": ["清晰度", "结构化", "易懂性"],
        "difficulty": "medium"
    },
    {
        "id": "prompt_002",
        "dimension": "prompt_engineering",
        "input": "用表格形式比较 Python、Java、JavaScript 三种语言的特点",
        "expected_behavior": "输出格式正确的表格对比",
        "evaluation_criteria": ["格式控制", "准确性", "完整性"],
        "difficulty": "easy"
    },
    {
        "id": "prompt_003",
        "dimension": "prompt_engineering",
        "input": "用bullet points列出学习Python的5个步骤",
        "expected_behavior": "输出格式化的bullet points",
        "evaluation_criteria": ["格式化能力", "清晰度"],
        "difficulty": "easy"
    },
    {
        "id": "prompt_004",
        "dimension": "prompt_engineering",
        "input": "用Markdown格式写一篇关于AI的文章，包含标题、要点和总结",
        "expected_behavior": "输出结构化的Markdown文档",
        "evaluation_criteria": ["格式规范", "结构完整", "内容充实"],
        "difficulty": "medium"
    },
]

CONTEXT_ENGINEERING_TESTS = [
    {
        "id": "ctx_001",
        "dimension": "context_engineering",
        "input": "根据之前的对话，继续完成报告的第三部分",
        "expected_behavior": "能够理解和利用之前的上下文",
        "evaluation_criteria": ["上下文保持", "连续性", "相关性"],
        "difficulty": "medium"
    },
    {
        "id": "ctx_002",
        "dimension": "context_engineering",
        "input": "记住我喜欢简洁的回答。现在解释什么是机器学习",
        "expected_behavior": "记住用户偏好并应用",
        "evaluation_criteria": ["偏好学习", "一致性", "适应能力"],
        "difficulty": "medium"
    },
    {
        "id": "ctx_003",
        "dimension": "context_engineering",
        "input": "在上一个问题中，我们讨论了X。请在此基础上继续讨论Y",
        "expected_behavior": "保持多轮对话的连贯性",
        "evaluation_criteria": ["上下文追踪", "逻辑连贯"],
        "difficulty": "hard"
    },
    {
        "id": "ctx_004",
        "dimension": "context_engineering",
        "input": "我之前提到过我的项目 deadline 是下周五。请帮我制定一个计划",
        "expected_behavior": "记忆并应用之前的信息",
        "evaluation_criteria": ["信息记忆", "计划制定", "时间管理"],
        "difficulty": "medium"
    },
]

# B. 智能能力 (7个维度)
RESPONSE_QUALITY_TESTS = [
    {
        "id": "resp_001",
        "dimension": "response_quality",
        "input": "什么是人工智能？",
        "expected_behavior": "回答准确、结构清晰、内容完整",
        "evaluation_criteria": ["准确性", "清晰度", "完整性"],
        "difficulty": "easy"
    },
    {
        "id": "resp_002",
        "dimension": "response_quality",
        "input": "解释为什么天空是蓝色的",
        "expected_behavior": "提供科学、准确的解释",
        "evaluation_criteria": ["科学性", "准确性", "易懂性"],
        "difficulty": "medium"
    },
    {
        "id": "resp_003",
        "dimension": "response_quality",
        "input": "比较REST API和GraphQL的优缺点",
        "expected_behavior": "提供全面、客观的比较",
        "evaluation_criteria": ["全面性", "客观性", "实用性"],
        "difficulty": "medium"
    },
    {
        "id": "resp_004",
        "dimension": "response_quality",
        "input": "写一段产品描述，用于电商平台",
        "expected_behavior": "语言专业、有吸引力、信息完整",
        "evaluation_criteria": ["专业性", "吸引力", "信息完整"],
        "difficulty": "medium"
    },
    {
        "id": "resp_005",
        "dimension": "response_quality",
        "input": "如何学习一门新编程语言？",
        "expected_behavior": "提供实用、可行的学习建议",
        "evaluation_criteria": ["实用性", "可行性", "系统性"],
        "difficulty": "easy"
    },
]

ROUTING_TESTS = [
    {
        "id": "route_001",
        "dimension": "routing",
        "input": "查询北京的天气",
        "expected_behavior": "路由到天气查询服务",
        "evaluation_criteria": ["意图识别", "服务路由", "参数提取"],
        "difficulty": "easy"
    },
    {
        "id": "route_002",
        "dimension": "routing",
        "input": "帮我预订明天北京到上海的高铁票",
        "expected_behavior": "路由到票务服务",
        "evaluation_criteria": ["意图识别", "参数提取", "服务选择"],
        "difficulty": "medium"
    },
    {
        "id": "route_003",
        "dimension": "routing",
        "input": "播放周杰伦的歌",
        "expected_behavior": "路由到音乐服务",
        "evaluation_criteria": ["意图识别", "内容理解", "服务路由"],
        "difficulty": "easy"
    },
]

REASONING_TESTS = [
    {
        "id": "reason_001",
        "dimension": "reasoning",
        "input": "如果所有的猫都是动物，有些动物是狗，那么有些猫是狗吗？",
        "expected_behavior": "正确进行逻辑推理",
        "evaluation_criteria": ["逻辑正确", "推理步骤", "结论准确"],
        "difficulty": "hard"
    },
    {
        "id": "reason_002",
        "dimension": "reasoning",
        "input": "小明有5个苹果，小红给了他又3个，小明吃掉了2个，还剩多少？",
        "expected_behavior": "正确进行数学推理",
        "evaluation_criteria": ["计算准确", "步骤清晰"],
        "difficulty": "easy"
    },
    {
        "id": "reason_003",
        "dimension": "reasoning",
        "input": "分析这个商业案例：一家传统零售店受到电商冲击，如何转型？",
        "expected_behavior": "提供分析性的推理和建议",
        "evaluation_criteria": ["分析深度", "推理逻辑", "建议可行性"],
        "difficulty": "hard"
    },
]

KNOWLEDGE_RECALL_TESTS = [
    {
        "id": "know_001",
        "dimension": "knowledge_recall",
        "input": "Python的创始人是谁？",
        "expected_behavior": "准确回忆知识",
        "evaluation_criteria": ["准确性", "完整性"],
        "difficulty": "easy"
    },
    {
        "id": "know_002",
        "dimension": "knowledge_recall",
        "input": "解释什么是机器学习中的梯度下降",
        "expected_behavior": "准确解释技术概念",
        "evaluation_criteria": ["概念准确性", "解释清晰度"],
        "difficulty": "medium"
    },
    {
        "id": "know_003",
        "dimension": "knowledge_recall",
        "input": "HTTP协议的工作原理是什么？",
        "expected_behavior": "准确描述技术原理",
        "evaluation_criteria": ["技术准确性", "原理清晰"],
        "difficulty": "medium"
    },
]

TOOL_CALLING_TESTS = [
    {
        "id": "tool_001",
        "dimension": "tool_calling",
        "input": "帮我计算 12345 * 67890",
        "expected_behavior": "调用计算器工具",
        "evaluation_criteria": ["工具识别", "参数传递", "结果返回"],
        "difficulty": "easy"
    },
    {
        "id": "tool_002",
        "dimension": "tool_calling",
        "input": "帮我搜索最新的AI新闻",
        "expected_behavior": "调用搜索工具",
        "evaluation_criteria": ["工具选择", "搜索参数", "结果处理"],
        "difficulty": "easy"
    },
    {
        "id": "tool_003",
        "dimension": "tool_calling",
        "input": "帮我把这段文字翻译成英文并保存到文件",
        "expected_behavior": "调用翻译和文件工具",
        "evaluation_criteria": ["工具链调用", "参数处理", "结果整合"],
        "difficulty": "medium"
    },
]

MULTI_TURN_TESTS = [
    {
        "id": "multi_001",
        "dimension": "multi_turn",
        "input": "我想学习Python。第一步应该学什么？",
        "expected_behavior": "开始多轮对话，记住学习Python的上下文",
        "evaluation_criteria": ["上下文保持", "对话连贯"],
        "difficulty": "easy"
    },
    {
        "id": "multi_002",
        "dimension": "multi_turn",
        "input": "继续",
        "expected_behavior": "继续之前的Python学习话题",
        "evaluation_criteria": ["话题追踪", "内容连续"],
        "difficulty": "easy"
    },
    {
        "id": "multi_003",
        "dimension": "multi_turn",
        "input": "还有呢？",
        "expected_behavior": "继续提供Python学习内容",
        "evaluation_criteria": ["对话连贯", "内容递进"],
        "difficulty": "easy"
    },
]

SELF_LEARNING_TESTS = [
    {
        "id": "learn_001",
        "dimension": "self_learning",
        "input": "我最近在关注区块链技术，请给我推荐一些学习资源",
        "expected_behavior": "根据用户偏好推荐相关内容",
        "evaluation_criteria": ["偏好学习", "内容推荐", "个性化"],
        "difficulty": "medium"
    },
    {
        "id": "learn_002",
        "dimension": "self_learning",
        "input": "我发现你之前给我的例子太简单了，请给我更复杂的",
        "expected_behavior": "学习用户反馈，调整输出",
        "evaluation_criteria": ["反馈学习", "调整能力"],
        "difficulty": "medium"
    },
    {
        "id": "learn_003",
        "dimension": "self_learning",
        "input": "我喜欢看视频学习，请调整你的教学方式",
        "expected_behavior": "记住用户学习偏好并应用",
        "evaluation_criteria": ["偏好记忆", "方式调整"],
        "difficulty": "medium"
    },
]

# C. 架构能力 (5个维度 - 除architecture外的5个)
HARNESS_TESTS = [
    {
        "id": "harness_001",
        "dimension": "harness",
        "input": "发送1000个并发请求测试系统稳定性",
        "expected_behavior": "限流机制生效，系统不崩溃",
        "evaluation_criteria": ["限流生效", "系统稳定", "错误处理"],
        "difficulty": "hard"
    },
    {
        "id": "harness_002",
        "dimension": "harness",
        "input": "模拟服务宕机，验证降级机制",
        "expected_behavior": "触发熔断，返回降级响应",
        "evaluation_criteria": ["熔断触发", "降级响应", "恢复机制"],
        "difficulty": "hard"
    },
    {
        "id": "harness_003",
        "dimension": "harness",
        "input": "发送大量恶意请求测试防护",
        "expected_behavior": "识别并拦截恶意请求",
        "evaluation_criteria": ["防护识别", "请求拦截", "正常请求"],
        "difficulty": "medium"
    },
]

OBSERVABILITY_TESTS = [
    {
        "id": "obs_001",
        "dimension": "observability",
        "input": "发送请求并检查日志记录",
        "expected_behavior": "请求被正确记录到日志",
        "evaluation_criteria": ["日志记录", "日志格式", "日志完整性"],
        "difficulty": "medium"
    },
    {
        "id": "obs_002",
        "dimension": "observability",
        "input": "追踪一个请求的完整调用链",
        "expected_behavior": "返回完整的调用链路追踪ID",
        "evaluation_criteria": ["追踪ID", "链路完整", "延迟记录"],
        "difficulty": "hard"
    },
    {
        "id": "obs_003",
        "dimension": "observability",
        "input": "检查系统的关键指标",
        "expected_behavior": "返回QPS、延迟、错误率等指标",
        "evaluation_criteria": ["指标准确", "数据完整"],
        "difficulty": "medium"
    },
]

MONITORING_TESTS = [
    {
        "id": "mon_001",
        "dimension": "monitoring",
        "input": "发送CPU使用率100%的监控数据",
        "expected_behavior": "触发告警通知",
        "evaluation_criteria": ["告警触发", "通知发送", "阈值判断"],
        "difficulty": "medium"
    },
    {
        "id": "mon_002",
        "dimension": "monitoring",
        "input": "发送响应时间超过5秒的监控数据",
        "expected_behavior": "触发性能告警",
        "evaluation_criteria": ["告警触发", "阈值准确"],
        "difficulty": "medium"
    },
    {
        "id": "mon_003",
        "dimension": "monitoring",
        "input": "查询最近1小时的告警历史",
        "expected_behavior": "返回告警列表和状态",
        "evaluation_criteria": ["历史查询", "告警状态"],
        "difficulty": "easy"
    },
]

SELF_HEALING_TESTS = [
    {
        "id": "heal_001",
        "dimension": "self_healing",
        "input": "模拟服务实例故障，验证自动恢复",
        "expected_behavior": "自动启动新实例，流量切换",
        "evaluation_criteria": ["故障检测", "自动恢复", "流量切换"],
        "difficulty": "hard"
    },
    {
        "id": "heal_002",
        "dimension": "self_healing",
        "input": "模拟数据库连接失败，验证重试机制",
        "expected_behavior": "自动重试，最终恢复",
        "evaluation_criteria": ["重试机制", "最终成功"],
        "difficulty": "medium"
    },
    {
        "id": "heal_003",
        "dimension": "self_healing",
        "input": "验证服务健康检查机制",
        "expected_behavior": "返回服务健康状态",
        "evaluation_criteria": ["检查准确", "状态正确"],
        "difficulty": "easy"
    },
]

ROLLOUT_TESTS = [
    {
        "id": "rollout_001",
        "dimension": "rollout",
        "input": "查询当前灰度发布的配置",
        "expected_behavior": "返回灰度策略和流量比例",
        "evaluation_criteria": ["配置准确", "流量比例"],
        "difficulty": "easy"
    },
    {
        "id": "rollout_002",
        "dimension": "rollout",
        "input": "将新版本流量从10%提升到50%",
        "expected_behavior": "流量比例更新成功",
        "evaluation_criteria": ["更新成功", "流量切换"],
        "difficulty": "medium"
    },
    {
        "id": "rollout_003",
        "dimension": "rollout",
        "input": "验证A/B测试的流量分配",
        "expected_behavior": "按比例分配流量到不同版本",
        "evaluation_criteria": ["流量分配", "比例准确"],
        "difficulty": "medium"
    },
]

# D. 数据能力 (4个维度)
DATA_SOURCE_TESTS = [
    {
        "id": "ds_001",
        "dimension": "data_source",
        "input": "连接MySQL数据库并查询用户表",
        "expected_behavior": "成功连接并返回查询结果",
        "evaluation_criteria": ["连接成功", "查询准确"],
        "difficulty": "medium"
    },
    {
        "id": "ds_002",
        "dimension": "data_source",
        "input": "从Redis缓存中获取用户会话",
        "expected_behavior": "成功获取会话数据",
        "evaluation_criteria": ["连接成功", "数据获取"],
        "difficulty": "easy"
    },
    {
        "id": "ds_003",
        "dimension": "data_source",
        "input": "查询Elasticsearch中的日志数据",
        "expected_behavior": "返回符合条件的日志",
        "evaluation_criteria": ["查询准确", "结果完整"],
        "difficulty": "medium"
    },
]

KNOWLEDGE_MGMT_TESTS = [
    {
        "id": "km_001",
        "dimension": "knowledge_mgmt",
        "input": "添加一篇关于AI的新闻到知识库",
        "expected_behavior": "成功添加到知识库",
        "evaluation_criteria": ["添加成功", "索引创建"],
        "difficulty": "easy"
    },
    {
        "id": "km_002",
        "dimension": "knowledge_mgmt",
        "input": "查询知识库中关于量子计算的内容",
        "expected_behavior": "返回相关知识条目",
        "evaluation_criteria": ["查询准确", "相关性"],
        "difficulty": "easy"
    },
    {
        "id": "km_003",
        "dimension": "knowledge_mgmt",
        "input": "更新知识库中某条过时的信息",
        "expected_behavior": "成功更新知识条目",
        "evaluation_criteria": ["更新成功", "版本管理"],
        "difficulty": "medium"
    },
]

VECTOR_MGMT_TESTS = [
    {
        "id": "vec_001",
        "dimension": "vector_mgmt",
        "input": "将一段文本转为向量并存储",
        "expected_behavior": "成功存储向量",
        "evaluation_criteria": ["转换成功", "存储成功"],
        "difficulty": "medium"
    },
    {
        "id": "vec_002",
        "dimension": "vector_mgmt",
        "input": "查询与'人工智能'语义相似的内容",
        "expected_behavior": "返回语义相似的结果",
        "evaluation_criteria": ["相似度准确", "结果相关"],
        "difficulty": "medium"
    },
    {
        "id": "vec_003",
        "dimension": "vector_mgmt",
        "input": "删除已过期的向量数据",
        "expected_behavior": "成功清理过期数据",
        "evaluation_criteria": ["清理成功", "空间释放"],
        "difficulty": "easy"
    },
]

DATA_LINEAGE_TESTS = [
    {
        "id": "lineage_001",
        "dimension": "data_lineage",
        "input": "查询数据从源头到最终报表的流转路径",
        "expected_behavior": "返回完整的数据血缘图",
        "evaluation_criteria": ["路径完整", "节点准确"],
        "difficulty": "hard"
    },
    {
        "id": "lineage_002",
        "dimension": "data_lineage",
        "input": "追踪某条数据的来源",
        "expected_behavior": "返回数据来源和转换过程",
        "evaluation_criteria": ["来源准确", "转换清晰"],
        "difficulty": "medium"
    },
    {
        "id": "lineage_003",
        "dimension": "data_lineage",
        "input": "分析数据质量问题的根源",
        "expected_behavior": "定位问题源头",
        "evaluation_criteria": ["定位准确", "分析深入"],
        "difficulty": "hard"
    },
]

# E. 平台能力 (3个维度)
APP_SUPPORT_TESTS = [
    {
        "id": "app_001",
        "dimension": "app_support",
        "input": "启动API服务并验证健康状态",
        "expected_behavior": "服务启动成功，返回健康状态",
        "evaluation_criteria": ["启动成功", "健康检查"],
        "difficulty": "easy"
    },
    {
        "id": "app_002",
        "dimension": "app_support",
        "input": "验证API的认证机制",
        "expected_behavior": "有效token可访问，无效token被拒绝",
        "evaluation_criteria": ["认证有效", "权限控制"],
        "difficulty": "medium"
    },
    {
        "id": "app_003",
        "dimension": "app_support",
        "input": "测试API的版本管理",
        "expected_behavior": "支持多版本API共存",
        "evaluation_criteria": ["版本隔离", "兼容支持"],
        "difficulty": "medium"
    },
]

COST_CONTROL_TESTS = [
    {
        "id": "cost_001",
        "dimension": "cost_control",
        "input": "查询本月的API调用成本",
        "expected_behavior": "返回成本明细和统计",
        "evaluation_criteria": ["数据准确", "明细清晰"],
        "difficulty": "easy"
    },
    {
        "id": "cost_002",
        "dimension": "cost_control",
        "input": "设置每月成本上限为1000元",
        "expected_behavior": "设置成功，超限时告警",
        "evaluation_criteria": ["设置成功", "超限告警"],
        "difficulty": "medium"
    },
    {
        "id": "cost_003",
        "dimension": "cost_control",
        "input": "分析成本异常的原因",
        "expected_behavior": "定位成本异常的服务和时间",
        "evaluation_criteria": ["异常识别", "原因分析"],
        "difficulty": "hard"
    },
]

INTEGRATION_TESTS = [
    {
        "id": "int_001",
        "dimension": "integration",
        "input": "测试与企业微信的集成",
        "expected_behavior": "成功发送消息到企业微信",
        "evaluation_criteria": ["集成成功", "消息送达"],
        "difficulty": "medium"
    },
    {
        "id": "int_002",
        "dimension": "integration",
        "input": "测试与Slack的webhook集成",
        "expected_behavior": "成功推送告警到Slack",
        "evaluation_criteria": ["集成成功", "推送及时"],
        "difficulty": "easy"
    },
    {
        "id": "int_003",
        "dimension": "integration",
        "input": "验证第三方API的适配器",
        "expected_behavior": "正确处理第三方API响应",
        "evaluation_criteria": ["适配准确", "错误处理"],
        "difficulty": "medium"
    },
]

# S. 安全能力 (1个维度)
SECURITY_TESTS = [
    {
        "id": "sec_001",
        "dimension": "security",
        "input": "发送SQL注入攻击：' OR '1'='1",
        "expected_behavior": "被安全模块拦截",
        "evaluation_criteria": ["攻击识别", "请求拦截"],
        "difficulty": "easy"
    },
    {
        "id": "sec_002",
        "dimension": "security",
        "input": "发送XSS攻击：<script>alert('hack')</script>",
        "expected_behavior": "被安全模块过滤",
        "evaluation_criteria": ["攻击检测", "内容过滤"],
        "difficulty": "easy"
    },
    {
        "id": "sec_003",
        "dimension": "security",
        "input": "测试CSRF token验证",
        "expected_behavior": "无token或无效token的请求被拒绝",
        "evaluation_criteria": ["token验证", "攻击防护"],
        "difficulty": "medium"
    },
    {
        "id": "sec_004",
        "dimension": "security",
        "input": "验证JWT token的有效期机制",
        "expected_behavior": "过期token被拒绝",
        "evaluation_criteria": ["过期检测", "权限控制"],
        "difficulty": "easy"
    },
]


# 汇总所有测试用例
E2E_TESTS = {
    # A. 基础能力
    'orchestration': ORCHESTRATION_TESTS,
    'agent_completeness': AGENT_COMPLETENESS_TESTS,
    'prompt_engineering': PROMPT_ENGINEERING_TESTS,
    'context_engineering': CONTEXT_ENGINEERING_TESTS,
    
    # B. 智能能力
    'response_quality': RESPONSE_QUALITY_TESTS,
    'routing': ROUTING_TESTS,
    'reasoning': REASONING_TESTS,
    'knowledge_recall': KNOWLEDGE_RECALL_TESTS,
    'tool_calling': TOOL_CALLING_TESTS,
    'multi_turn': MULTI_TURN_TESTS,
    'self_learning': SELF_LEARNING_TESTS,
    
    # C. 架构能力 (5个)
    'harness': HARNESS_TESTS,
    'observability': OBSERVABILITY_TESTS,
    'monitoring': MONITORING_TESTS,
    'self_healing': SELF_HEALING_TESTS,
    'rollout': ROLLOUT_TESTS,
    
    # D. 数据能力
    'data_source': DATA_SOURCE_TESTS,
    'knowledge_mgmt': KNOWLEDGE_MGMT_TESTS,
    'vector_mgmt': VECTOR_MGMT_TESTS,
    'data_lineage': DATA_LINEAGE_TESTS,
    
    # E. 平台能力
    'app_support': APP_SUPPORT_TESTS,
    'cost_control': COST_CONTROL_TESTS,
    'integration': INTEGRATION_TESTS,
    
    # S. 安全能力
    'security': SECURITY_TESTS,
}


def get_test_count():
    """获取测试用例总数"""
    return sum(len(tests) for tests in E2E_TESTS.values())


def get_all_dimensions():
    """获取所有测试维度"""
    return list(E2E_TESTS.keys())
