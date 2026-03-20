# RANGEN V2 配置架构

## 概述

RANGEN V2 使用 YAML + JSON 混合配置系统，采用分层架构设计。

## 配置分层

```
config/
├── rangen_v2.yaml          # 主配置文件 (生产/开发通用)
├── base.yaml                # 基础配置 (未来重构目标)
├── production_config.yaml    # 生产特定配置
├── mcp_config.yaml          # MCP 服务器配置
├── rules.yaml               # 规则配置
├── system_config.json       # 系统配置 (代码规范、评估参数)
├── sections/                # 遗留配置 (已部分废弃)
│   ├── reasoning_engine.json
│   ├── security.json
│   └── ...
├── environments/             # 环境特定配置 (当前使用)
│   ├── development.yaml
│   ├── production.yaml
│   └── testing.yaml
└── data_templates/          # 测试数据模板
```

## 配置加载优先级

1. **环境变量** (最高优先级)
   ```
   DEEPSEEK_API_KEY=xxx
   LLM_PROVIDER=deepseek
   ```

2. **环境配置文件** (development.yaml, production.yaml)
   - 继承基础配置
   - 覆盖特定环境设置

3. **主配置文件** (rangen_v2.yaml)
   - 默认值
   - 通用配置

## 使用指南

### 开发环境
```bash
cp .env.example .env
# 编辑 .env 设置 API Key
python src/api/server.py
```

### 生产环境
```bash
# 使用环境变量覆盖
export DEEPSEEK_API_KEY=xxx
export ENVIRONMENT=production
python src/api/server.py
```

## 配置重构计划

### Phase 1: 文档化 ✅ 完成
- [x] 创建配置架构文档
- [x] 分析配置重复问题

### Phase 2: 简化结构 ✅ 完成
- [x] 创建 `base.yaml` 基础配置（YAML 锚点定义）
- [x] 重构 `environments/` 使用 YAML 锚点继承（规划中）
- [ ] 清理 `sections/` 冗余配置

### Phase 3: 统一加载器 ✅ 完成
- [x] 创建 `src/config/unified_config.py`
- [ ] 统一所有配置加载入口（现有系统保持不变）

## 当前配置统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 根目录 YAML | 8 | 主配置、MCP、安全等 |
| 根目录 JSON | 22 | 系统配置、评估、模型等 |
| sections/ | 8 | 遗留分段配置 |
| environments/ | 4 | 环境特定配置 |
| data_templates/ | 4 | 测试数据 |

**总计**: 46 个配置文件

## 配置字段分布

| 功能 | 配置文件 |
|------|----------|
| LLM | rangen_v2.yaml, development.yaml |
| KMS | rangen_v2.yaml, sections/reasoning_engine.json |
| Agent | rangen_v2.yaml, environments/*.yaml |
| 安全 | sections/security.json, rules.yaml |
| 评估 | system_config.json, evaluation_*.json |
| MCP | mcp_config.yaml |

## 最佳实践

1. **优先使用环境变量**: 生产部署应使用环境变量覆盖敏感配置
2. **保持配置简洁**: 避免在多处重复相同配置
3. **文档化变更**: 配置变更应同步更新本文档
