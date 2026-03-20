# RANGEN 工程规范

> 本文档定义了 RANGEN 工程的基本原则和操作规范

---

## 1. 索引优先原则

### 1.1 创建前必查索引

**原则**: 创建新工具/Agent 前，必须先查阅索引文档确认不存在。

```bash
# 查询工具索引
cat docs/TOOLS_INDEX.md

# 查询 Agent 索引
cat docs/AGENTS_INDEX.md

# 或使用 grep 搜索
grep -r "keyword" docs/
```

### 1.2 创建后必更新索引

**原则**: 创建新工具/Agent 后，必须更新对应索引文档。

#### 更新 TOOLS_INDEX.md

在对应分类下添加：

```markdown
| **YourTool** | `agents/tools/your_tool.py` | 功能描述 | 🟢 生产 |
```

#### 更新 AGENTS_INDEX.md

在对应分类下添加：

```markdown
| **YourAgent** | `agents/your_agent.py` | 功能描述 | 🟢 生产 |
```

---

## 2. 状态标注原则

每个工具/Agent 必须标注状态：

| 状态 | 标识 | 说明 |
|------|------|------|
| 生产 | 🟢 | 已在生产环境使用，稳定性高 |
| 实验 | 🟡 | 可用但功能可能变化 |
| 废弃 | 🔴 | 不推荐使用，会在未来移除 |

---

## 3. 废弃处理原则

当废弃旧功能时，必须执行以下三步：

### Step 1: 移动到 archive

```bash
# 工具移动到 core/archive/deprecated_workflows/
mv src/agents/tools/old_tool.py src/core/archive/deprecated_workflows/

# Agent 移动到 core/archive/
mv src/agents/old_agent.py src/core/archive/
```

### Step 2: 更新索引文档

将状态从 🟢/🟡 改为 🔴，并更新位置：

```markdown
| **OldTool** | `archive/deprecated_workflows/old_tool.py` | 🔴 废弃 | 使用 NewTool 替代 |
```

### Step 3: 添加废弃警告

在归档文件的 docstring 中添加：

```python
"""
⚠️ DEPRECATED
此文件已废弃，请使用 NewTool 替代
废弃日期: 2026-03-21
"""
```

---

## 4. 重复功能检查原则

### 4.1 搜索相关关键词

| 功能 | 搜索关键词 |
|------|------------|
| 搜索 | search, web_search, real_search |
| 提取 | extract, content_extract, answer_extract |
| 抓取 | crawl, scrape |
| 清洗 | clean, deduplicate |

### 4.2 重复检查流程

```
遇到新需求
    ↓
搜索索引文档 (TOOLS_INDEX.md, AGENTS_INDEX.md)
    ↓
搜索代码库 (find + grep)
    ↓
找到相似功能?
├── 是 → 使用现有功能或扩展它
└── 否 → 创建新功能 + 更新索引
```

---

## 5. 文档更新触发条件

| 操作 | 必须更新索引 | 备注 |
|------|-------------|------|
| 创建新工具 | ✅ | 在 TOOLS_INDEX.md 添加 |
| 创建新 Agent | ✅ | 在 AGENTS_INDEX.md 添加 |
| 修改工具名称 | ✅ | 更新位置和名称 |
| 废弃工具 | ✅ | 改为 🔴 + 移动到 archive |
| 删除工具 | ✅ | 从索引中移除 |

---

## 6. 提交规范

### 6.1 提交前检查

```bash
# 检查是否需要更新索引
git diff --name-only | grep -E "(tools|agents)" 

# 如果有变化，确认已更新索引
cat docs/TOOLS_INDEX.md | grep "your_new_tool"
cat docs/AGENTS_INDEX.md | grep "your_new_agent"
```

### 6.2 提交信息格式

```
<type>: <简短描述>

<详细描述>

<影响范围>
- TOOLS_INDEX.md: 更新
- AGENTS_INDEX.md: 更新
```

示例：

```
feat: add data collection tools for pipeline workflow

Add three tools for data collection pipeline:
- ContentExtractor
- DataCleaner  
- URLDiscoverer

- TOOLS_INDEX.md: Updated
```

---

## 7. 工具关系说明

### 7.1 搜索工具演进

```
SearchTool (示例) → WebSearchTool (DuckDuckGo) → RealSearchTool (Tavily)
    🔴 废弃              🟢 生产                    🟢 推荐
```

### 7.2 提取工具演进

```
QueryExtraction → AnswerExtraction → ContentExtractor
    🟡 实验         🟢 生产              🟢 新增推荐
```

### 7.3 工具选择指南

| 需求 | 推荐工具 |
|------|----------|
| 网络搜索 | `RealSearchTool` |
| HTML 解析 | `ContentExtractor` |
| 数据清洗 | `DataCleaner` |
| URL 发现 | `URLDiscoverer` |
| 浏览器自动化 | `BrowserTool` |

---

## 8. 违反规范的后果

| 违反 | 影响 |
|------|------|
| 未查索引创建重复功能 | 代码冗余，维护困难 |
| 未更新索引 | 其他开发者找不到功能 |
| 未标注状态 | 使用者不知道稳定性 |
| 未按流程废弃 | 废弃功能被误用 |

---

## 9. 规范维护

| 项目 | 负责人 | 更新频率 |
|------|--------|----------|
| TOOLS_INDEX.md | 贡献者 | 创建/废弃时 |
| AGENTS_INDEX.md | 贡献者 | 创建/废弃时 |
| PROJECT_GUIDELINES.md | 维护者 | 规范变更时 |

---

## 10. 违规处理

如果发现违反规范的情况：

1. **提醒**: 友好提醒贡献者更新索引
2. **PR 反馈**: 在代码审查中要求更新索引
3. **自动化检查**: 未来添加 CI 检查（可选）

---

**最后更新**: 2026-03-21
