# T7: 向量存储研究

## 决策日期
2026-03-20

## 研究内容

### 对比方案
- **FAISS**: Facebook AI 相似度搜索库
- **pgvector**: PostgreSQL 向量扩展

### 分析结果

#### FAISS 特点
- 嵌入式库，无需独立服务
- 性能极快（<1ms 延迟）
- 支持 GPU 加速
- 适合单机部署

#### pgvector 特点
- PostgreSQL 扩展
- 原生事务支持
- 并发安全
- 适合需要数据库集成的场景

### RANGEN V2 推荐

**保持 FAISS 方案**

理由：
1. 当前规模适中 (<100万向量)
2. 性能优先 (Agent 响应延迟敏感)
3. 部署简单 (Python 包直接使用)
4. 已有实现 (EnhancedFAISSMemory)

### 优化建议
1. 添加监控指标 (查询延迟、命中率)
2. 自动备份 (定时保存索引文件)
3. 缓存层 (Redis 缓存热点向量)

### 文档
- `docs/vector-storage-comparison.md` - 向量存储方案对比研究

### 结论
当前 FAISS 方案满足需求，无需迁移到 pgvector。
