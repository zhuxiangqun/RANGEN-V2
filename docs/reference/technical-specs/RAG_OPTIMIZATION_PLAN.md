    # RAG 模块优化方案：迈向“推理型检索” (Reasoning-Driven Retrieval)

    基于对现有架构的深度分析（Core 作为消费者，KMS 作为服务提供者），本方案旨在弥合“检索”与“推理”之间的鸿沟，实现符合 DDL（深度动态逻辑）思想的下一代 RAG 架构。

    ## 1. 核心理念与架构原则

    ### 1.1 从“静态查询”到“动态求证” (DDL Philosophy)

    目前的 RAG 是“查字典”模式：Core 抛出一个问题，KMS 返回一堆文档。
    优化的目标是**“侦探”模式**：Core 提出假设，KMS 提供线索，Core 根据线索修正假设并再次追问。

    ### 1.2 架构原则：存储计算分离 (Storage-Compute Separation)

    为了实现更好的维护性和扩展性，我们明确 **Core** 与 **KMS** 的职责边界：

    *   **KMS (Knowledge Management System) = 基础设施层 (Storage/Infrastructure)**
        *   **定位**：高效、稳定的知识存储与索引引擎。
        *   **职责**：负责数据的 ETL、分块、向量化、持久化存储，提供原子化的基础检索接口（Vector/Graph/Metadata Search）。
        *   **设计原则**："Dumb but Fast" —— 不包含复杂的推理业务逻辑，只负责快速准确地返回数据。

    *   **Core (RAG Process) = 智能业务层 (Intelligence/Business)**
        *   **定位**：RAG 的大脑，负责推理与策略编排。
        *   **职责**：负责检索策略的选择（HyDE, CoT）、查询的重写与扩展、检索结果的重排与融合、以及最终的答案生成。
        *   **设计原则**："Smart and Adaptive" —— 包含所有与 DDL 相关的动态逻辑（$\beta$ 参数调节）。

    ---

    ## 2. 架构优化方案

    ### 2.1 Core 层：实现“推理引导的检索器” (Reasoning-Guided Retriever)

    在 `src/core/reasoning/` 下新增 `retrieval_strategies/` 模块，接管目前散落在 `real_reasoning_engine.py` 中的简单检索逻辑。

    *   **Query Expansion Agent (查询扩展智能体)**
        *   **现状**: 仅有简单的 `_improve_query_for_retrieval`。
        *   **优化**: 引入 **HyDE (Hypothetical Document Embeddings)** 思想。在检索前，先让 LLM 生成一个“假设性答案”，然后用该答案的向量去检索，而非用问题检索。这能显著提高对“隐含意图”的召回率。
        *   **RAG 2.0 理念**: 引入 **Query Rewriting (查询重写)**，不仅生成假设答案，还利用 LLM 将复杂查询分解为更易检索的子查询 (Sub-queries)，并进行多路召回 (Multi-path Retrieval)。
        *   *DDL 意义*: $\beta \approx 1$ (直觉)，先生成直觉性答案，再求证。

    *   **Iterative Inquiry (迭代追问)**
        *   **现状**: 主要是单次检索，偶尔重试。
        *   **优化**: 实现 **CoT-RAG (Chain-of-Thought RAG)** 和 **Self-RAG (Self-Reflective RAG)**。
            *   Step 1: 检索基础信息。
            *   Step 2: LLM 阅读后发现缺失“年份”信息（Self-Correction）。
            *   Step 3: 生成针对“年份”的特定查询再次检索。
        *   **RAG 2.0 理念**: 强调 **端到端优化 (End-to-End Optimization)**，即根据生成的反馈（Feedback）来调整检索策略，而不仅仅是单向的数据流。
        *   *DDL 意义*: $\beta \approx 2$ (辩证)，通过不断的“检索-反思-再检索”循环逼近真相。

    ### 2.2 KMS 层：增强“语义分辨率”

    在 `knowledge_management_system/` 内部进行算法升级，对 Core 透明。

    *   **Small-to-Big Retrieval (父子文档索引)**
        *   **现状**: 切分后的 Chunk 独立存在，上下文丢失。
        *   **优化**: 索引时使用小粒度 Chunk (Sentence级) 以提高匹配精准度，但检索时返回其所属的**父文档窗口 (Parent Window)** 或**完整段落**。
        *   **RAG 2.0 理念**: **细粒度索引 (Fine-grained Indexing)** 结合 **上下文恢复 (Context Recovery)**，解决“只见树木不见森林”的问题。
        *   *收益*: 既能精准定位（小向量），又能提供完整上下文（大窗口）。

    *   **Metadata Filtering Injection (元数据注入)**
        *   **现状**: 元数据（如 Wikipedia Title, Source）仅用于展示。
        *   **优化**: 将元数据显式作为过滤条件暴露给 Core。
        *   **RAG 2.0 理念**: **结构化与非结构化融合 (Structured + Unstructured Fusion)**，利用元数据（时间、实体、来源）进行精确过滤 (Pre-filtering)。
        *   *场景*: Core 推理出“这个问题是关于电影的”，则在调用 `query_knowledge` 时自动附加 `filter={"category": "movie"}`。

    *   **索引降噪与多路召回 (Index Denoising & Multi-path Recall)**
        *   **新增**: 在 KMS 内部实现**稀疏检索 (Sparse Retrieval, e.g., BM25)** 与 **稠密检索 (Dense Retrieval)** 的混合。
        *   **优化**: 引入 **Rerank (重排序)** 机制作为标配，对多路召回的结果进行统一打分，过滤噪声。

    ### 2.3 接口层：原子化与结构化

    明确 Core 与 KMS 的交互协议。

    *   **KMS 提供原子接口 (Atomic APIs)**
        *   `search_vector(query, top_k, filters)`: 纯向量检索。
        *   `search_graph(entity_id, hops)`: 纯图谱游走。
        *   `get_document(doc_id)`: 获取完整文档内容。
        *   *移除 KMS 中原有的复杂编排逻辑（如 RL 优化器），将其上移至 Core。*

    *   **Core 负责逻辑编排 (Orchestration)**
        *   Core 调用上述原子接口，组合出复杂的检索策略（如 "先查向量，再根据结果查图谱"）。

    *   **Evidence Object (证据对象)**
        *   **现状**: 返回 `List[Dict]` (text, score)。
        *   **优化**: 返回强类型的 `Evidence` 对象，包含：
            *   `fact_chain`: 事实链条（从 Graph 中提取）。
            *   `contradiction_score`: 与当前 Query 的矛盾度（用于 DDL 判别）。
            *   `source_reliability`: 来源可信度评分。

    ---

    ## 3. 实施路线图 (Roadmap)

    ### 第一阶段：Core 侧智能化 (低风险，不改底层)
    1.  **实现 HyDE 查询生成器**: 在 Core 中增加一个预处理步骤，将 User Query 转化为 Hypothetical Document。
    2.  **实现“自省式检索” (Self-Reflective Retrieval)**: 在 `LangGraph` 中增加一个 `EvidenceCheckNode`，如果检索结果不足以回答问题，自动触发基于缺失信息的二次检索。

    ### 第二阶段：KMS 侧精度提升 (中风险，需重建部分索引)
    1.  **实施 Small-to-Big 策略**: 修改 `KnowledgeImporter`，在分块时保留 `parent_id` 映射。
    2.  **优化 Reranker**: 针对特定领域（如 FRAMES 数据集）微调本地 Rerank 模型，或引入更强的 Cross-Encoder。

    ### 第三阶段：深度融合 (高风险，架构重构)
    1.  **Graph-RAG 落地**: 让 Core 能够直接查询 KMS 的知识图谱（不仅仅是向量），实现“实体跳跃”查询。
    2.  **端到端优化**: 将 Core 的推理反馈（如“这个文档没用”）回传给 KMS，用于在线更新向量索引的权重（RLHF for Retrieval）。

    ---

    ## 4. 实施细节与代码设计

    ### 4.1 QueryOrchestrator 设计 (Core Layer)

    位于 `src/core/reasoning/retrieval_strategies/query_orchestrator.py`，负责根据 DDL 参数（$\beta$）动态选择检索策略。

    ```python
    class QueryOrchestrator:
        """查询编排器 - 实现推理引导的检索"""
        
        def __init__(self, llm_service, retrieval_service):
            self.llm = llm_service
            self.retrieval = retrieval_service
            self.strategies = {
                "simple": self._simple_strategy,
                "hyde": self._hyde_strategy,
                "cot_rag": self._cot_rag_strategy
            }
        
        async def orchestrate_retrieval(self, query: str, context: Dict, beta: float = 0.5) -> RetrievalResult:
            """
            根据 DDL β 参数编排检索过程
            β < 0.3: Simple (直觉/记忆)
            β < 1.3: HyDE (假设/联想)
            β >= 1.3: CoT-RAG (辩证/推理)
            """
            # 1. 策略选择
            if beta < 0.3:
                strategy_name = "simple"
            elif beta < 1.3:
                strategy_name = "hyde"
            else:
                strategy_name = "cot_rag"
                
            strategy = self.strategies[strategy_name]
            
            # 2. 执行策略
            result = await strategy(query, context)
            return result

        async def _hyde_strategy(self, query: str, context: Dict) -> RetrievalResult:
            """HyDE: Hypothetical Document Embeddings"""
            # Step 1: 生成假设性答案
            hyde_prompt = f"Please write a passage to answer the question: {query}"
            hypothetical_doc = await self.llm.generate(hyde_prompt)
            
            # Step 2: 使用假设文档进行检索
            # 关键点：用假设答案的向量去匹配真实文档的向量
            return await self.retrieval.query(
                query=hypothetical_doc, 
                metadata={"original_query": query, "strategy": "hyde"}
            )

        async def _cot_rag_strategy(self, query: str, context: Dict) -> RetrievalResult:
            """CoT-RAG: Chain-of-Thought Retrieval"""
            # Step 1: 分析所需信息
            plan = await self.llm.generate(f"Analyze what information is needed to answer: {query}")
            
            # Step 2: 生成子查询
            sub_queries = self._extract_subqueries(plan)
            
            # Step 3: 并行检索
            results = await asyncio.gather(*[self.retrieval.query(q) for q in sub_queries])
            
            # Step 4: 合并去重
            return self._merge_results(results)
    ```

    ### 4.2 Evidence Object 设计 (Interface Layer)

    位于 `src/core/models/evidence.py`，定义强类型的证据结构。

    ```python
    class EvidenceType(str, Enum):
        FACT = "fact"
        CONTRADICTION = "contradiction"
        SUPPORT = "support"

    class Evidence(BaseModel):
        """结构化证据对象"""
        id: str
        content: str
        type: EvidenceType
        source_url: Optional[str]
        relevance_score: float
        
        # DDL 相关属性
        contradictions: List[str] = []  # 与此证据矛盾的证据ID
        beta_group: Optional[str] = None  # 属于哪个β组
        
        # 上下文属性
        parent_doc_id: Optional[str] = None # 用于 Small-to-Big
    ```

    ### 4.3 Small-to-Big Retrieval 设计 (KMS Layer)

    位于 `knowledge_management_system/core/knowledge_importer.py` (索引时) 和 `knowledge_manager.py` (检索时)。

    *   **索引时**:
        1.  将文档切分为 Sentence Level 的 `Child Chunks`。
        2.  保留 Document Level 的 `Parent Window`。
        3.  建立 `Child -> Parent` 的 ID 映射。
    *   **检索时**:
        1.  对 `Child Chunks` 进行向量检索。
        2.  找到 Top-K 的 Child Chunks。
        3.  **映射回 Parent**: 返回其所属的 Parent Window 作为最终内容。

    ### 4.4 Advanced RAG Strategies (RAG 2.0 Features)

    这些高级策略将集成在 `QueryOrchestrator` 中：

    1.  **Self-RAG (Self-Reflective RAG)**:
        *   在检索后，增加一个 `Reflection` 步骤，评估检索内容的质量（相关性、完整性）。
        *   如果质量低，触发 `Rewrite-Retrieve` 循环。

    2.  **Multi-path Recall (多路召回)**:
        *   Core 同时发起 "Keyword Search" (关键词匹配) 和 "Semantic Search" (语义匹配)。
        *   利用 `Reciprocal Rank Fusion (RRF)` 算法合并结果。

    3.  **Context Compression (上下文压缩)**:
        *   在将 Evidence 传递给 LLM 之前，使用专门的 `Compressor` 模型移除无关信息，提高 Token 利用率和推理准确性。

    ### 4.5 DDL 参数动态计算 (Dynamic Beta Calculation)

    为了实现真正的动态调节，我们需要一个 `BetaParameterCalculator`：

    ```python
    class BetaParameterCalculator:
        """DDL β参数计算器"""
        
        def __init__(self, neural_router, performance_monitor):
            self.router = neural_router
            self.monitor = performance_monitor
        
        async def calculate_beta_for_query(self, query: str, context: Dict) -> float:
            """
            计算当前查询的β参数（0-2范围）
            影响因素：查询复杂度、历史表现、系统负载
            """
            # 1. 基础β：查询复杂度
            intent_result = await self.router.classify(query)
            base_beta = self._intent_to_beta(intent_result["top_intent"])
            
            # 2. 历史表现调整
            similar_queries = self.monitor.find_similar_queries(query)
            if similar_queries:
                avg_success = np.mean([q["success_rate"] for q in similar_queries])
                if avg_success < 0.5:  # 历史表现差，需要更多推理（β≈2）
                    base_beta = min(base_beta * 1.5, 2.0)
            
            return round(base_beta, 2)
    ```

    ### 4.6 检索质量评估 (Retrieval Quality Assessment)

    Self-RAG 的核心组件，用于评估检索结果是否满足需求。

    ```python
    class RetrievalQualityAssessor:
        """检索质量评估器"""
        
        async def assess_retrieval_quality(self, query: str, evidences: List[Evidence], beta: float) -> QualityAssessment:
            # 1. 相关性评估
            relevance_scores = await self._score_relevance(query, evidences)
            avg_relevance = np.mean(relevance_scores)
            
            # 2. 覆盖度评估
            coverage_score = await self._assess_coverage(query, evidences)
            
            # 3. 矛盾性评估（β≈2 特别关注）
            contradiction_score = 0
            if beta > 1.3:
                contradiction_score = await self._find_contradictions(evidences)
                
            # 4. 决定是否重试
            overall = self._calculate_overall_score(avg_relevance, coverage_score, contradiction_score)
            needs_retry = overall < self._get_threshold_by_beta(beta)
            
            return QualityAssessment(overall_score=overall, needs_retry=needs_retry)
    ```

    ### 4.7 性能优化与缓存 (Performance & Caching)

    为了缓解高级策略（如 HyDE, CoT）带来的延迟，引入 `CachingOrchestrator`。

    ```python
    class CachingOrchestrator(QueryOrchestrator):
        """带缓存的编排器"""
        
        def __init__(self, llm_service, retrieval_service, cache_backend="redis"):
            super().__init__(llm_service, retrieval_service)
            self.cache = CacheClient(cache_backend)
        
        async def orchestrate_retrieval(self, query: str, context: Dict, beta: float):
            # 1. 语义缓存：计算 Cache Key
            cache_key = await self._generate_semantic_cache_key(query, beta)
            
            # 2. 尝试读取缓存
            cached = await self.cache.get(cache_key)
            if cached and self._is_cache_valid(cached, query):
                return cached["result"]
            
            # 3. 执行检索
            result = await super().orchestrate_retrieval(query, context, beta)
            
            # 4. 异步写入缓存
            asyncio.create_task(self.cache.set(cache_key, result))
            return result
    ```

    ### 4.9 自适应阈值调节器 (Adaptive Beta Threshold)

为了解决静态阈值固化的问题，引入自适应调节机制。

```python
class AdaptiveBetaThreshold:
    """自适应β阈值计算器"""
    
    def __init__(self):
        self.thresholds = {
            "simple_to_hyde": 0.3,  # 初始值
            "hyde_to_cot": 1.3      # 初始值
        }
        self.adjustment_history = []
    
    def adjust_threshold(self, strategy_name: str, success_rate: float):
        """根据策略成功率调整阈值"""
        current = self.thresholds[strategy_name]
        
        # 成功率低 -> 降低门槛（让更多查询使用该策略）
        if success_rate < 0.6:
            new_threshold = current * 0.9  # 降低10%
        # 成功率高但使用率低 -> 提高门槛（优化资源）
        elif success_rate > 0.8 and self._get_usage_rate(strategy_name) < 0.1:
            new_threshold = current * 1.1  # 提高10%
        
        self.thresholds[strategy_name] = new_threshold
```

### 4.10 分布式策略编排 (Distributed Strategy Orchestrator)

解决单点瓶颈问题，支持策略的并行执行与竞速。

```python
class DistributedStrategyOrchestrator:
    """分布式策略编排器"""
    
    async def orchestrate_retrieval(self, query: str, beta: float):
        # 1. 并行执行所有候选策略（带超时）
        tasks = []
        for name, worker in self.strategy_workers.items():
            if self._should_execute_strategy(name, beta):
                task = asyncio.create_task(worker.execute(query), name=f"strategy_{name}")
                tasks.append((name, task))
        
        # 2. 等待最快结果（带质量检查）
        done, pending = await asyncio.wait(
            [t for _, t in tasks],
            timeout=2.0,  # 超时控制
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 3. 质量验证与返回
        for name, task in tasks:
            if task in done:
                result = task.result()
                if await self._validate_result_quality(result, query):
                    for _, pending_task in pending: pending_task.cancel()
                    return result
        
        # 4. 备选：使用简单策略
        return await self.strategy_workers["simple"].execute(query)
```

### 4.11 策略执行跟踪器 (Strategy Tracer)

增强系统的可观测性。

```python
class StrategyTracer:
    """策略执行跟踪器"""
    
    async def trace_execution(self, strategy_name: str, query: str, start_time: float, result: Dict):
        """记录策略执行情况"""
        latency = time.time() - start_time
        relevance = await self._calculate_relevance(query, result)
        
        # 实时分析：如果策略表现持续不佳，发出警告
        if self._is_strategy_degrading(strategy_name):
            logger.warning(f"策略 {strategy_name} 性能下降")
```

### 4.12 全系统 DDL 参数统一管理 (Unified DDL Parameter Management)

为了确保 $\beta$ 参数在系统各模块（Context, Retrieval, Reasoning）中的一致性，建立单一真值来源。

```python
class DDLPhase(Enum):
    """DDL应用阶段 - 明确β在不同阶段的意义"""
    RETRIEVAL = "retrieval"      # β≈0:简单召回, β≈1:HyDE联想, β≈2:CoT辩证
    REASONING = "reasoning"      # β≈0:直觉推理, β≈1:系统分析, β≈2:反思迭代
    MEMORY = "memory"           # β≈1:智能遗忘
    CONTEXT = "context"         # β相关:上下文选择

@dataclass
class DDLParameters:
    """DDL参数包 - 统一输出格式"""
    base_beta: float  # 核心β∈[0,2]
    
    # 派生参数（各模块专用）
    retrieval_threshold: float
    reasoning_complexity: float
    memory_decay_rate: float
    context_window_size: int
    
    # 元数据
    phase: DDLPhase
    confidence: float
    explanation: str

class DDLParameterService:
    """DDL 全局参数服务 - Single Source of Truth"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    async def get_parameters(self, query: str, phase: DDLPhase, user_context: Optional[Dict] = None) -> DDLParameters:
        """获取统一DDL参数"""
        # 1. 计算基础β值
        base_beta = await self._calculate_base_beta(query, user_context)
        
        # 2. 模块特定映射
        mapper = self._beta_mappings[phase]
        derived_params = mapper(base_beta, query, user_context)
        
        return DDLParameters(base_beta=base_beta, **derived_params, phase=phase)

    async def _calculate_base_beta(self, query: str, context: Optional[Dict]) -> float:
        """计算基础β值 - 多因子加权"""
        # 因子：查询复杂度(0.4) + 历史表现(0.3) + 用户偏好(0.2) + 系统负载(0.1)
        # ... (Implementation details as discussed)
        return beta
```

### 4.13 系统集成方案 (Integration Strategy)

1.  **ReAct Workflow**: 移除 `complexity_predictor`，改用 `ddl_service.get_parameters(..., phase=REASONING)`。
2.  **Context Manager**: 移除硬编码阈值，改用 `ddl_service.get_parameters(..., phase=MEMORY)`。
3.  **Retrieval Factory**: 基于 `ddl_params.strategy` 创建策略实例。

### 4.14 无知识图谱场景的优化 (Optimization for No-Graph Scenario)

在缺乏预构建知识图谱的情况下，DDL-RAG 承担了“推理桥梁”的角色，通过推理构建临时的“软图谱”。

#### 4.14.1 关系增强型 HyDE (Relation-Enhanced HyDE)

通过 Prompt Engineering，让 HyDE 不仅生成答案，还生成关系推理框架，补偿图谱缺失。

```python
class GraphCompensatedHyDE(HyDEStrategy):
    async def _generate_hypothesis(self, query: str) -> str:
        prompt = f"""基于这个问题，请推理可能的信息关系：
        问题：{query}
        
        请考虑：
        1. 涉及哪些核心实体？
        2. 这些实体可能有什么关系？
        3. 需要哪些类型的证据？
        4. 时间/因果/对比关系是什么？
        
        推理框架："""
        return await self.llm.generate(prompt)
```

#### 4.14.2 文档关系推理器 (Document Relation Reasoner)

在检索后阶段，利用 LLM 分析检索到的孤立文档片段之间的逻辑联系。

```python
class DocumentRelationReasoner:
    """文档关系推理器 - 用LLM模拟图谱关系"""
    
    async def infer_relations(self, documents: List[Evidence], query: str) -> Dict:
        # 让LLM推理关系：支持、矛盾、因果、时间顺序
        relation_prompt = f"分析以下信息片段之间的关系：\n{self._format_documents(documents)}"
        relations = await self.llm.generate(relation_prompt)
        
        return {
            "logical_chain": self._build_chain(documents, relations),
            "contradictions": self._identify_contradictions(documents, relations)
        }
```

#### 4.14.3 动态检索深度 (Dynamic Depth Retrieval)

根据 $\beta$ 值动态调整检索的广度与深度，模拟图谱的多跳查询。

*   $\beta < 0.5$: 简单检索 (Top-5)
*   $0.5 \le \beta < 1.5$: 增强 HyDE + 多轮扩展 (Breadth)
*   $\beta \ge 1.5$: CoT-RAG + 迭代检索 (Depth)

---

## 5. 实施路线图 (Updated Roadmap)

### P0阶段：核心重构与MVP (Core Refactor) - Quick Wins
1.  **Day 1-2: 建立最小化核心 (Minimal Core)**
    *   创建 `src/core/ddl/` 和 `src/core/reasoning/retrieval_strategies/` 目录。
    *   实现 `MinimalDDLService`: 基于查询长度的启发式规则计算 $\beta$。
    *   实现 `MinimalHyDE`: 极简版的假设文档生成与检索。
2.  **Day 3-4: 兼容性集成 (Integration)**
    *   修改 `RealReasoningEngine`，添加 `use_ddl` 开关。
    *   实现“影子模式”运行，对比新旧策略效果。
3.  **Day 5: 基础监控 (Monitoring)**
    *   建立 `DDLMonitor`，记录 $\beta$ 分布和 HyDE 触发率。

### P1阶段：全系统迁移 (Migration)
1.  **Day 6-8**: 迁移 `ContextManager` 和 `ReActWorkflow` 使用统一 DDL 服务。
2.  **Day 9-10**: 实现 `RetrievalQualityAssessor` (✅ Completed).
3.  **Day 11-12**: 实现自适应 β 阈值调节 (✅ Completed).
4.  **Day 13**: 实现 Self-Correction Loop (✅ Completed).
    *   在 `RealReasoningEngine` 中实现了自动重试循环。
    *   策略：检测到矛盾 -> 强制 CoT；检测到相关性低 -> 查询重写；检测到 Beta 过低 -> 提升 Beta。

### P2阶段：KMS层优化 (Infrastructure)
1.  **Small-to-Big 索引重构** (✅ Completed): 
    *   已修改 `KnowledgeImporter` 支持父子文档关联。
    *   已实现 `DocumentChunker` 的 `parent_id` 注入。
    *   已在 `query_knowledge` 中实现 `expand_context` 逻辑，支持动态获取父文档窗口。
2.  **优化 Reranker** (✅ Completed):
    *   升级模型为 `cross-encoder/ms-marco-MiniLM-L-12-v2`。
    *   在 `HyDEStrategy` 中强制启用 Rerank 并根据 β 值动态开启 Context Expansion。
3.  **Graph-RAG 落地** (⏸️ Postponed): 
    *   暂缓实施，等待知识图谱数据构建完成。
4.  **端到端优化**: 将 Core 的推理反馈回传给 KMS。

---

## 6. 成功指标与验证

### P0阶段优化（本周内）
1.  **Day 1-2**: 建立监控基础设施（StrategyTracer, metrics）。
2.  **Day 3-4**: 实现 **HyDE** 策略（创建 `HyDEStrategy` 类）。
3.  **Day 5-6**: 实现策略工厂模式 (`StrategyFactory`)。
4.  **Day 7-8**: A/B 测试集成与 β 阈值校准。

### P1阶段补充
1.  **Day 9-11**: 实现 `RetrievalQualityAssessor`。
2.  **Day 12-14**: 实现自适应 β 阈值调节。
3.  **Day 15-17**: 策略健康检查器与自动回滚机制。

### P2阶段（KMS 层）
1.  **Small-to-Big** 索引重构。
2.  图谱集成与端到端优化。

---

## 6. 成功指标与验证

    ### 核心指标
    *   **检索质量**: MRR@10 > 0.7 (当前 ≈ 0.5)
    *   **答案准确性**: 事实准确率 > 90% (当前 ≈ 75%)
    *   **性能影响**: P95 延迟增加 < 30% (引入缓存后)

    ### 验证策略
    1.  **影子测试 (Shadow Testing)**: 新旧系统并行运行，比较结果但不影响用户。
    2.  **基准测试 (Benchmark)**: 建立 `test_retrieval_benchmark.py`，定期跑分。

    ---

    ## 7. 立即行动建议

    **推荐的首个任务**:
    今晚开始创建 `src/core/reasoning/retrieval_strategies/` 目录，并实现 `HyDEStrategy`。这是一个低风险、高回报的切入点。
