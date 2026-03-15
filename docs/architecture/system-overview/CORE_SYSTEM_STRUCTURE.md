# Core System Structure

本文档详细描述了 RAG 系统核心组件的文件结构和职责划分。

## 1. 核心架构概览

系统主要由两大部分组成：
1.  **Reasoning Core (`src/core`)**: 负责推理流程控制、策略选择、自适应调节和答案生成。
2.  **Knowledge Management System (`knowledge_management_system`)**: 负责底层数据的存储、索引、向量化和检索。

两者通过 `src/services/knowledge_retrieval_service.py` 进行解耦交互。

## 2. 目录结构树

```text
RANGEN-main/
├── src/
│   ├── core/                           # 推理核心
│   │   ├── real_reasoning_engine.py    # [入口] 主推理引擎类
│   │   ├── ddl/                        # 动态难度加载 (DDL)
│   │   │   ├── ddl_parameter_service.py # DDL参数服务
│   │   │   └── adaptive_beta.py        # 自适应Beta阈值管理器
│   │   └── reasoning/
│   │       ├── retrieval_strategies/   # 检索策略集合
│   │       │   ├── direct_strategy.py  # 直接检索
│   │       │   ├── hyde_strategy.py    # HyDE (假设文档)
│   │       │   ├── cot_strategy.py     # CoT (思维链)
│   │       │   └── quality_assessor.py # [P1] 检索质量评估器
│   │       ├── step_generator.py       # 推理步骤生成器
│   │       └── context_manager.py      # 上下文管理器
│   └── services/
│       └── knowledge_retrieval_service.py # KMS 桥接服务
│
├── knowledge_management_system/        # 知识库管理系统 (KMS)
│   ├── config/
│   │   └── system_config.json          # [配置] 核心系统配置
│   ├── core/
│   │   ├── knowledge_manager.py        # KMS 主控制器
│   │   └── vector_index_builder.py     # 向量索引构建器
│   ├── storage/
│   │   ├── vector_storage.py           # FAISS/Vector 存储封装
│   │   └── metadata_storage.py         # 元数据存储
│   └── utils/
│       └── jina_service.py             # Embedding 服务封装
│
├── scripts/                            # 工具与测试脚本
│   ├── test_ddl_p1.py                  # [测试] P1端到端集成测试
│   └── test_small_to_big.py            # [测试] Small-to-Big检索测试
└── docs/
    ├── RAG_OPTIMIZATION_PLAN.md        # 优化计划文档
    └── CORE_SYSTEM_STRUCTURE.md        # (本文档)
```

## 3. 核心组件详解

### 3.1 Reasoning Core (`src/core`)

*   **`real_reasoning_engine.py`**:
    *   **职责**: 系统的“大脑”。接收用户查询，协调 DDL、策略选择、检索和答案生成。
    *   **关键逻辑**:
        *   调用 `DDLParameterService` 获取难度参数 (Beta)。
        *   根据 Beta 和 `AdaptiveBetaThreshold` 选择策略 (Direct/HyDE/CoT)。
        *   执行检索并调用 `RetrievalQualityAssessor` 评估质量。
        *   实现 **Self-Correction Loop** (自动重试与策略调整)。

*   **`ddl/`**:
    *   **`ddl_parameter_service.py`**: 分析查询复杂度，计算 Beta 值。
    *   **`adaptive_beta.py`**: 维护策略切换的阈值，根据历史成功率动态调整。

*   **`reasoning/retrieval_strategies/`**:
    *   **`quality_assessor.py`**: 使用 LLM 对检索结果打分 (Relevance, Coverage, Contradiction)。
    *   **策略类**: 实现了具体的检索逻辑（如 HyDE 生成假设文档，CoT 生成推理步骤）。

### 3.2 Knowledge Management System (`KMS`)

*   **`config/system_config.json`**:
    *   **职责**: 控制 KMS 的所有行为。
    *   **关键项**: `vector_rerank` (开启重排序), `model_path` (模型路径), `query_extraction_rules` (查询提取规则)。

*   **`core/knowledge_manager.py`**:
    *   **职责**: KMS 的外观模式 (Facade)，对外提供统一的 `query_knowledge` 接口。
    *   **逻辑**: 实现了 **Small-to-Big** 检索逻辑（先查小切片，再取父文档）。

*   **`storage/`**:
    *   负责数据的物理存储。目前支持本地 FAISS 索引 (`vector_index.bin`) 和 JSON 元数据。

## 4. 数据流转图 (Data Flow)

1.  **Query Input**: 用户输入查询。
2.  **DDL Analysis**: `DDLParameterService` 分析查询，输出 Beta。
3.  **Strategy Routing**: `RealReasoningEngine` 结合 `AdaptiveBeta` 决定策略 (e.g., CoT)。
4.  **Retrieval**:
    *   策略调用 `KnowledgeRetrievalService`。
    *   KMS 执行向量检索 -> Small-to-Big 扩展 -> Rerank 重排序。
5.  **Quality Check**:
    *   `RetrievalQualityAssessor` 评估检索结果。
    *   **Pass**: 生成最终答案。
    *   **Fail**: 触发 Self-Correction (调整 Beta/重写查询) -> 重试 Step 2/4。
6.  **Feedback**: 最终结果的成功/失败反馈给 `AdaptiveBeta`，用于未来优化。
