#!/usr/bin/env python3
"""
ADR 示例 - 基于 Harrison Chase 和 Perplexity 文章洞见

这些 ADR 记录了 RANGEN 系统的关键架构决策
"""
from src.core.adr_registry import (
    ADRRegistry, ADR, ADRStatus, create_adr, get_adr_registry
)


def initialize_sample_adrs():
    """初始化示例 ADR"""
    registry = get_adr_registry()
    
    # === ADR-001: 渐进式工具加载策略 ===
    adr_001 = create_adr(
        adr_id="ADR-001",
        title="采用渐进式工具加载 (Progressive Tool Loading)",
        background="""
MCP (Model Context Protocol) 存在线性上下文成本问题：
每增加一个工具定义，都需要消耗 token 上下文。
Perplexity 已在 2026 年放弃 MCP，转向 CLI 作为更自然的执行层。

当前问题：
- 工具越多，context 消耗越大
- MCP 需要额外的协议层
- Skill 封装成本更低
        """,
        decision="""
采用优先级系统：Skill > CLI > API > MCP

具体实现：
1. Skill: 首选项，内置成本最低
2. CLI: 标准化封装，易于调试
3. API: 外部服务集成
4. MCP: 仅在特定场景使用（如需要实时同步）
        """,
        consequences="""
正面影响：
- 减少 token 消耗，提升响应速度
- 更自然的执行层（composable, debuggable）
- 降低维护复杂度

负面影响：
- 需要重构现有工具注册逻辑
- CLI 封装需要额外开发工作

回滚条件：
- 如果 Skill 触发机制出现严重性能问题
- 如果 MCP 解决了上下文成本问题
        """,
        alternatives=[
            "继续使用 MCP 作为主要工具协议",
            "完全移除 MCP，仅保留 Skill",
            "使用原生 API 而非 CLI"
        ],
        tags=["tool-loading", "mcp", "skill", "performance"]
    )
    adr_001.status = ADRStatus.ACCEPTED
    registry.add(adr_001)
    
    # === ADR-002: Builder/Reviewer 角色分离 ===
    adr_002 = create_adr(
        adr_id="ADR-002",
        title="建立 Builder/Reviewer 角色分离",
        background="""
Harrison Chase (LangChain CEO) 在文章中指出：

"编程 Agent 改写的，是整个 EPD 协作链路的瓶颈位置"

核心洞察：
- 原型成本急剧下降
- 评审吞吐成为新瓶颈
- 最稀缺的资源从"实现能力"转向"判断能力"

问题：
- RANGEN 有 30+ Agent，角色混杂
- 缺少明确的职责分离
- 评审机制不够突出
        """,
        decision="""
建立明确的角色分类：

Builder (23个):
- 负责创建/生成/实现
- 如: ReasoningAgent, EngineeringAgent, DesignAgent

Reviewer (4个):
- 负责验证/检查/质量控制
- 如: ValidationAgent, QualityController, CitationAgent

Coordinator (3个):
- 负责编排/协调
- 如: ChiefAgent, MultiAgentCoordinator
        """,
        consequences="""
正面影响：
- 明确职责边界
- 便于评审流程优化
- 支持更精细的资源分配

负面影响：
- 需要重构部分 Agent 交互逻辑
- 增加系统复杂度

回滚条件：
- 如果角色分离导致协作效率下降
- 如果发现更好的协作模式
        """,
        alternatives=[
            "保持现有混合角色模式",
            "按功能域分离（研究/实现/验证）",
            "完全按技能类型分离"
        ],
        tags=["agent-roles", "builder", "reviewer", "architecture"]
    )
    adr_002.status = ADRStatus.ACCEPTED
    registry.add(adr_002)
    
    # === ADR-003: 评审优先原则 ===
    adr_003 = create_adr(
        adr_id="ADR-003",
        title="评审升级为主流程",
        background="""
文章指出："问题不在 'AI 做得太快'，而在 '错误方向太容易显得像一个差不多能上线的版本'"

现象：
- 原型越来越多
- 评审越来越疲惫
- 团队开始怀疑 Agent 拉低工程质量

根本原因：
- 评审是"附属动作"，不是"主流程"
- 缺少明确的验收标准
- 缺少上下文传递机制
        """,
        decision="""
将评审从附属升级为主流程：

1. 明确验收标准 (Acceptance Criteria)
   - 什么是"可接受"的输出
   - 什么是"必须修复"的问题
   
2. 分级评审机制
   - L0: 自动检查（格式、语法）
   - L1: Builder 自检
   - L2: Reviewer 评审
   - L3: 专家评审
   
3. 上下文传递协议
   - 每个产出必须附带意图说明
   - 临时实现 vs 刻意设计需区分
   - 验收标准必须明确
        """,
        consequences="""
正面影响：
- 减少错误方向进入主干
- 评审更有针对性
- 上下文更清晰

负面影响：
- 增加开发流程时间
- 需要更多 Reviewer 资源

回滚条件：
- 如果评审成为新的瓶颈
- 如果自动检查足够可靠
        """,
        alternatives=[
            "保持现有评审模式",
            "完全自动化评审（AI 评审 AI）",
            "仅对关键路径进行评审"
        ],
        tags=["review", "quality", "workflow"]
    )
    adr_003.status = ADRStatus.PROPOSED
    registry.add(adr_003)
    
    # === ADR-004: 意图说明优先于实现文档 ===
    adr_003 = create_adr(
        adr_id="ADR-004",
        title="采用 ADR 替代传统 PRD",
        background="""
Harrison Chase 说 "PRD is dead"，但真正死的是"文档先行、实现滞后"的老流程。

新流程：
- 先有原型
- 再补意图说明

问题：
- 传统 PRD 记录"要做什么"
- 但在 Agent 时代，更需要记录"为什么选这个方案"
- 需要记录"已知的 trade-off"
        """,
        decision="""
采用 ADR (Architecture Decision Record) 格式：

替代方案：
- 传统 PRD: "要做什么"
- ADR: "为什么选这个方案"
- 轻量 RFC: "意图说明"

ADR 核心字段：
1. Background: 决策前的上下文
2. Decision: 实际选择（不是"要做什么"）
3. Consequences: 正面和负面影响
4. Alternatives Considered: 考虑的替代方案
5. Rollback Conditions: 什么条件下应该回滚
        """,
        consequences="""
正面影响：
- 关注"为什么"而非"是什么"
- 记录已知风险和 trade-off
- 便于后续维护者理解决策

负面影响：
- 需要额外文档工作
- 需要团队形成决策记录习惯

回滚条件：
- 如果发现 ADR 格式不适用于 RANGEN
- 如果团队倾向使用其他格式
        """,
        alternatives=[
            "继续使用传统 PRD",
            "使用轻量 RFC",
            "不记录架构决策"
        ],
        tags=["adr", "documentation", "decision-making"]
    )
    adr_003.status = ADRStatus.ACCEPTED
    registry.add(adr_003)
    
    # === ADR-005: Reading-Reasoning 解耦 ===
    adr_005 = create_adr(
        adr_id="ADR-005",
        title="采用 Reading-Reasoning 解耦架构",
        background="""
来自上海AI Lab DRIFT论文洞见：

问题：
- 长上下文成为负担：1M+ tokens 但效果未必提升
- 关键信息容易被淹没在冗余文本中
- 原始文本可能藏匿恶意内容

核心问题：
- 知识获取(reading)与逻辑推理(reasoning)是否必须由同一个模型完成？
- 传统方式：大模型同时"读"+"想"，上下文越长负担越重
        """,
        decision="""
采用 Reading-Reasoning 解耦架构：

1. 小模型(Knowledge Model)负责读取+压缩
   - 从超长文档中抽取与任务相关的关键信息
   - 压缩为高密度隐空间表示

2. 大模型(Reasoning Model)负责推理
   - 不再直接处理原始文本
   - 基于压缩后的知识表示进行推理

RANGEN 映射：
- Builder = Knowledge Model（读取+压缩）
- Reviewer = Reasoning Model（推理+判断）
- 意图说明 = 压缩表示的具体形式
        """,
        consequences="""
正面影响：
- 32x压缩后性能接近甚至超过全文本
- 64x/128x压缩仍优于传统方法
- 推理延迟在各长度下保持最低
- 天然安全收益：推理模型不直接接触原始文本

负面影响：
- 需要维护双模型架构
- 压缩模型的选择和训练需要成本

回滚条件：
- 如果单模型能达到同等效果
- 如果压缩导致关键信息丢失
        """,
        alternatives=[
            "继续使用单一模型处理全部上下文",
            "仅使用检索增强(RAG)",
            "使用纯压缩方法"
        ],
        tags=["architecture", "decoupling", "drift", "efficiency"]
    )
    adr_005.status = ADRStatus.ACCEPTED
    registry.add(adr_005)
    
    print(f"✅ 已初始化 {len(registry.get_all())} 条 ADR 记录")


if __name__ == "__main__":
    initialize_sample_adrs()
    registry = get_adr_registry()
    
    print("\n=== 活跃 ADR ===")
    for adr in registry.get_active():
        print(f"  {adr.adr_id}: {adr.title} [{adr.status.value}]")
    
    print("\n=== 导出 Markdown ===")
    print(registry.to_markdown()[:500] + "...")
