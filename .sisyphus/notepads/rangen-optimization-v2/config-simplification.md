# T5: 配置简化决策

## 决策日期
2026-03-20

## 问题分析

### 配置现状
- 总计 46 个配置文件
- 根目录：22 JSON + 8 YAML
- sections/：8 个遗留配置
- environments/：4 个环境配置

### 发现的问题
1. **配置重复**：environments/ 文件完整复制主配置内容
2. **结构不一致**：sections/ 与主配置无关联
3. **加载方式不统一**：多种配置加载方式并存

## 选择方案
**渐进式简化** - 不破坏现有系统，添加新配置基础设施

## 实施内容

### 1. 创建配置架构文档
- **文件**: `config/README.md`
- **内容**: 配置分层、使用指南、最佳实践

### 2. 创建基础配置
- **文件**: `config/base.yaml`
- **特性**: YAML 锚点定义，可被环境配置继承
- **内容**: system, llm, kms, neural_models, agents 等默认配置

### 3. 创建统一加载器
- **文件**: `src/config/unified_config.py`
- **功能**:
  - `UnifiedConfig` 数据类
  - `get_config(env)` 加载函数
  - `get_cached_config()` 单例模式
  - 环境变量解析 `${VAR:default}`

## 保留现有系统
- rangen_v2.yaml：保持不变
- environments/*.yaml：保持不变（向后兼容）
- sections/：标记为遗留（暂不清理）

## 验证结果
- ✅ base.yaml 解析成功
- ✅ unified_config.py 测试通过
- ✅ 开发/生产环境配置加载正常

## 后续建议
1. **未来重构**：环境配置使用 YAML 锚点继承 base.yaml
2. **sections/ 清理**：标记为废弃，逐步迁移到主配置
3. **配置文档**：添加更多使用示例
