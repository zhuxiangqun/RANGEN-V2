# RANGEN V2 向量存储方案对比研究

## 研究日期
2026-03-20

## 研究目标
对比 FAISS 与 pgvector，选择适合 RANGEN V2 的向量存储方案。

---

## 一、当前实现分析

### 1.1 现有向量存储组件

| 组件 | 位置 | 说明 |
|------|------|------|
| `EnhancedFAISSMemory` | `src/memory/enhanced_faiss_memory.py` | 3219 行，增强版 FAISS 内存 |
| `FAISSService` | `src/services/faiss_service.py` | 单例模式 FAISS 管理 |
| `VectorDatabaseManager` | `src/utils/vector_database_manager.py` | 向量数据库管理器 |
| `faiss_utils` | `src/memory/faiss_utils.py` | FAISS 工具函数 |
| `vector_database` | `src/knowledge/vector_database.py` | 知识向量数据库 |

### 1.2 配置现状

```yaml
# config/rangen_v2.yaml
knowledge_base:
  vector_store_path: "${VECTOR_STORE_PATH:./data/vector_store}"
  embedding_model: "${EMBEDDING_MODEL:all-mpnet-base-v2}"
```

### 1.3 依赖

```python
# requirements.txt
faiss-cpu           # Facebook AI 相似度搜索
sentence-transformers  # 向量化模型
numpy                # 数值计算
```

---

## 二、方案对比

### 2.1 FAISS vs pgvector

| 维度 | FAISS | pgvector |
|------|-------|----------|
| **类型** | 嵌入式库 | PostgreSQL 扩展 |
| **部署** | 单机/内存 | 独立服务器 |
| **规模** | <10亿向量 | 受限于磁盘 |
| **性能** | 极快（内存） | 快（索引优化） |
| **查询** | ANN/精确 | ANN/精确 |
| **持久化** | 文件 | 数据库事务 |
| **并发** | 需外部管理 | 原生支持 |
| **备份** | 手动 | 自动 |

### 2.2 详细对比

#### FAISS (当前方案)

**优点：**
- 🚀 极致性能：内存中向量运算，延迟 <1ms
- 📦 零部署：Python 包，直接使用
- 💰 免费：MIT 许可证
- 🔧 多种索引：Flat, IVF, HNSW, PQ, IVF-PQ
- 📈 可扩展：支持 GPU 加速

**缺点：**
- ⚠️ 单机限制：难以水平扩展
- ⚠️ 持久化：需手动备份
- ⚠️ 并发：需外部锁机制
- ⚠️ 管理：缺少监控工具

#### pgvector

**优点：**
- 🔒 事务安全：ACID 特性
- 🔄 自动备份：数据库自动处理
- 👥 并发安全：PostgreSQL 原生
- 📊 监控友好：可使用 pg_stat_statements
- 🔗 关联查询：可与业务数据 JOIN

**缺点：**
- ⚠️ 性能稍低：比 FAISS 慢 10-50%
- ⚠️ 资源占用：PostgreSQL 额外开销
- ⚠️ 部署复杂：需要数据库集群
- ⚠️ 依赖：需要 PostgreSQL 服务

### 2.3 性能对比（参考数据）

| 操作 | FAISS | pgvector |
|------|-------|----------|
| 100万向量检索 | ~5ms | ~20ms |
| 1000万向量检索 | ~15ms | ~80ms |
| 插入吞吐量 | ~50K/s | ~10K/s |
| 内存占用 | 全量加载 | 按需加载 |

---

## 三、推荐方案

### 3.1 场景分析

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| **开发/测试** | FAISS | 快速启动，无需额外服务 |
| **小型生产 (<100万向量)** | FAISS | 性能优先，简单部署 |
| **中型生产 (100万-1亿)** | pgvector | 扩展性，并发支持 |
| **大型生产 (>1亿)** | FAISS + Redis | 分片 + 缓存 |
| **多租户** | pgvector | 隔离性强 |

### 3.2 RANGEN V2 推荐

**结论：保持 FAISS 方案**

**理由：**

1. **当前规模适中**：RANGEN 主要用于 Agent 推理，向量规模 <100万
2. **性能优先**：Agent 响应延迟敏感，FAISS 性能更优
3. **部署简单**：RANGEN 目标是快速部署，FAISS 更轻量
4. **已有基础**：`EnhancedFAISSMemory` 已实现，无需迁移

### 3.3 优化建议

#### 当前问题
1. 并发访问需要外部锁（已通过 FAISSService 单例解决）
2. 持久化依赖手动备份（可添加自动备份）
3. 缺少监控（可添加指标收集）

#### 优化方案

```python
# src/services/faiss_service.py 已有优化
class FAISSService:
    """统一FAISS服务 - 单例 + 懒加载 + 健康检查"""
```

### 3.4 未来迁移路径

如果未来需要扩展到多租户或超大规模：

```
当前: FAISS (单机)
       ↓
中期: FAISS + Redis Cache (分片)
       ↓
长期: pgvector (如果需要数据库集成)
```

---

## 四、实施建议

### 4.1 保持现状
- ✅ 继续使用 FAISS
- ✅ 保持 `EnhancedFAISSMemory`
- ✅ 使用 `FAISSService` 管理实例

### 4.2 可选优化

| 优化项 | 优先级 | 说明 |
|--------|--------|------|
| 添加监控指标 | P2 | 记录查询延迟、命中率 |
| 自动备份 | P2 | 定时保存索引文件 |
| 缓存层 | P3 | Redis 缓存热点向量 |
| 分片支持 | P3 | 大规模时水平扩展 |

### 4.3 监控配置

```python
# metrics.py 添加
FAISS_QUERY_LATENCY = Histogram('faiss_query_latency', 'FAISS query latency')
FAISS_INDEX_SIZE = Gauge('faiss_index_size', 'FAISS index size')
FAISS_CACHE_HIT = Counter('faiss_cache_hit', 'FAISS cache hits')
```

---

## 五、结论

| 决策 | 内容 |
|------|------|
| **选择** | 保持 FAISS |
| **理由** | 性能优先，部署简单，规模适中 |
| **优化** | 添加监控、自动备份 |
| **迁移** | 如需大规模/多租户，可迁移 pgvector |

---

## 附录：相关文件

### 核心文件
- `src/memory/enhanced_faiss_memory.py` - FAISS 内存实现
- `src/services/faiss_service.py` - FAISS 服务
- `src/utils/vector_database_manager.py` - 向量管理器
- `src/knowledge/vector_database.py` - 知识向量库

### 配置
- `config/rangen_v2.yaml` - 主配置
- `config/system_config.json` - 系统配置
