# Knowledge Management System (KMS) Architecture

本文档详细描述了 RANGEN V2 中 **Knowledge Management System (KMS)** 的架构设计。KMS 是一个独立、高性能、多模态的知识存储与检索引擎。

## 1. 系统概览

KMS 旨在提供一个轻量级但功能强大的本地知识库解决方案，支持向量检索、元数据管理和多模态扩展。它采用了 **"流固分离"** 的设计思想，将元数据管理（Metadata）与向量索引（Vector Index）解耦，以实现高效的读写性能和数据安全性。

### 1.1 核心设计目标
*   **独立性**: 可作为独立服务运行，不强依赖上层业务逻辑。
*   **高性能**: 使用 FAISS 进行毫秒级向量检索，支持 MPS (Metal Performance Shaders) 硬件加速。
*   **鲁棒性**: 采用原子性写入（Atomic Writes）和文件锁，防止数据损坏。
*   **成本效益**: 优先使用本地开源模型（如 `all-mpnet-base-v2`），支持 API Fallback。

## 2. 架构图

```mermaid
graph TD
    User[Client / Reasoning Core] --> API[Service Interface]
    
    subgraph "Core Layer"
        API --> KM[Knowledge Manager]
        API --> VIB[Vector Index Builder]
        
        KM -->|CRUD| MetaStore[Metadata Storage]
        VIB -->|Search/Add| VecStore[Vector Storage]
    end
    
    subgraph "Processing Layer"
        VIB --> TP[Text Processor]
        VIB --> IP[Image Processor]
        
        TP -->|Encode| LocalModel[Local Model (sentence-transformers)]
        TP -.->|Fallback| JinaAPI[Jina AI API]
    end
    
    subgraph "Storage Layer"
        MetaStore -->|JSON| DiskMeta[metadata.json]
        VecStore -->|Binary| DiskVec[vector_index.bin]
        DiskMeta -.->|Content Hash| Dedup[Deduplication Index]
    end
```

## 3. 核心组件详解

### 3.1 Knowledge Manager (`core/knowledge_manager.py`)
**职责**: 负责知识条目的生命周期管理（创建、读取、更新、删除）。

*   **元数据存储**: 使用 JSON 文件存储元数据，包含 `id`, `content`, `modality`, `created_at` 等字段。
*   **原子性写入**: 采用 `Write-to-Temp` -> `fsync` -> `Rename` 的策略，确保在系统崩溃时不会损坏元数据文件。
*   **去重机制**: 维护一个 `content_hash_index`（基于 SHA256），在插入新知识时自动检测重复内容，避免冗余。

### 3.2 Vector Index Builder (`core/vector_index_builder.py`)
**职责**: 负责向量索引的构建、维护和检索。

*   **索引引擎**: 基于 **FAISS** (Facebook AI Similarity Search)。
*   **索引类型**: `IndexFlatIP` (Inner Product)，配合归一化向量实现余弦相似度检索。
*   **动态加载**: 运行时动态检查 FAISS 可用性，支持优雅降级。
*   **ID 映射**: 维护 `FAISS ID (int)` <-> `Knowledge ID (UUID)` 的双向映射关系。

### 3.3 Text Processor (`modalities/text_processor.py`)
**职责**: 将文本转换为向量嵌入 (Embedding)。

*   **双模式引擎**:
    1.  **Local Mode (优先)**: 使用 `sentence-transformers` 加载本地模型（默认 `all-mpnet-base-v2`）。
        *   **硬件加速**: 自动检测并利用 Apple Silicon (MPS) 或 NVIDIA GPU (CUDA)。
        *   **并发保护**: 使用单例模式和信号量限制并发，防止内存爆炸。
        *   **缓存管理**: 自动检测模型文件完整性，支持断点续传和损坏清理。
    2.  **API Mode (Fallback)**: 如果本地模型不可用，自动降级调用 Jina AI API。

## 4. 数据流转

### 4.1 知识导入 (Import Flow)
1.  **接收数据**: 客户端发送文本内容。
2.  **查重**: `KnowledgeManager` 计算哈希，检查是否存在。
3.  **持久化**:
    *   写入 `metadata.json` (Atomic)。
    *   调用 `TextProcessor` 生成向量。
    *   写入 `vector_index.bin` (FAISS)。
4.  **返回**: 返回生成的 UUID。

### 4.2 知识检索 (Retrieval Flow)
1.  **接收查询**: 客户端发送查询文本。
2.  **向量化**: `TextProcessor` 将查询转换为向量。
3.  **检索**: `VectorIndexBuilder` 在 FAISS 中搜索 Top-K 近邻。
4.  **元数据回填**: 根据返回的 FAISS ID，从 `KnowledgeManager` 获取完整的文本内容和元数据。
5.  **重排序 (可选)**: 如果配置了 Rerank，对候选结果进行精细打分。

## 5. 存储结构

```text
data/knowledge_management/
├── metadata.json          # 核心元数据（JSON）
├── vector_index.bin       # FAISS 向量索引
├── vector_index.mapping.json # ID 映射表
└── graph/                 # 知识图谱数据（可选）
    ├── entities.json
    └── relations.json
```

## 6. 关键配置 (`config/system_config.json`)

*   **`vector.default_dimension`**: 768 (对应 `all-mpnet-base-v2`)。
*   **`modalities.text.model`**: 指定使用的 Embedding 模型。
*   **`retrieval_strategies`**: 定义检索参数（Top-K, 阈值, 重排序模型）。

## 7. 扩展性与未来规划

*   **多模态支持**: 架构已预留 `ImageProcessor`, `AudioProcessor` 接口，未来可轻松集成 CLIP 等模型。
*   **知识图谱融合**: `graph/` 模块已初步实现，未来将支持 Vector + Graph 的混合检索 (GraphRAG)。
*   **LlamaIndex 集成**: `integrations/` 模块提供了适配器，可将 KMS 作为 LlamaIndex 的 Retriever 使用。
