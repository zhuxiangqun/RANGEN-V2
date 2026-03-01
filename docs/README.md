# RANGEN 项目文档

## 📚 文档导航

RANGEN 是一个高度智能化的多智能体研究系统，本文档库提供了完整的使用指南、架构说明和技术参考。

### 🚀 快速开始

| 文档 | 描述 | 适用人群 |
|------|------|----------|
| [快速开始指南](usage/quick_start.md) | 5分钟内启动系统 | 新用户 |
| [安装指南](installation/) | 详细安装步骤 | 开发者 |
| [系统使用指南](usage/system_usage_guide.md) | 核心功能使用 | 普通用户 |

### 🏗️ 架构与设计

#### 系统架构
- [系统架构总览](SYSTEM_AGENTS_OVERVIEW.md) - 完整的系统架构说明
- [架构分析](architecture/) - 详细的架构设计文档
- [分层架构](architecture/layered_architecture_design.md) - 系统分层设计

#### Agent 架构
- [Agent 架构概览](architecture/agent_architecture/) - 多智能体系统设计
- [推理专家](architecture/reasoning_expert_design.md) - 推理引擎设计
- [质量控制器](architecture/quality_controller_design.md) - 质量评估系统

### 🔧 开发指南

#### 开发环境
- [开发环境搭建](development/) - 开发环境配置
- [代码规范](development/coding_standards.md) - 编码规范和最佳实践
- [测试指南](testing/) - 测试策略和方法

#### API 文档
- [API 参考](api/) - 系统API文档
- [动态配置API](api/dynamic_config_api.md) - 配置管理系统API

### 📊 运维与监控

#### 监控系统
- [监控面板使用指南](usage/browser_monitoring_guide.md) - 系统监控方法
- [性能分析工具](tools/performance_analyzer_usage.md) - 性能分析指南
- [OpenTelemetry 监控](installation/opentelemetry_monitoring_setup.md) - 可观测性配置

#### 故障排除
- [故障排除指南](guide/troubleshooting.md) - 常见问题解决方案
- [诊断指南](analysis/) - 系统诊断和分析
- [端口冲突解决](port_conflict_solution.md) - 网络配置问题

### 🔄 迁移与升级

#### 系统迁移
- [迁移指南](migration_guide.md) - 系统迁移说明
- [逐步替换指南](gradual_replacement_guide.md) - 平滑升级策略
- [迁移实施日志](migration_implementation_log.md) - 迁移过程记录

#### 兼容性
- [向后兼容性](architecture/backward_compatibility_design.md) - API兼容性保证
- [版本升级](architecture/version_upgrade_strategy.md) - 升级策略

### 🧪 测试与质量

#### 测试框架
- [测试策略](testing/) - 测试方法和框架
- [质量保证](architecture/quality_assurance_system.md) - 质量管理系统
- [性能基准](testing/performance_benchmarking.md) - 性能测试标准

#### 覆盖率分析
- [测试覆盖率报告](reports/coverage_analysis_report.json) - 当前覆盖率状态
- [测试运行器](tests/test_runner.py) - 统一测试执行工具

### 📈 分析与优化

#### 系统分析
- [性能优化](architecture/performance_optimization/) - 性能调优指南
- [架构重构](refactoring/) - 系统重构计划
- [改进记录](improvements/) - 持续改进记录

#### 智能分析
- [检索质量评估](retrieval_quality_assessment.md) - 知识检索质量分析
- [答案准确性分析](analysis/answer_accuracy_issue.md) - 答案质量分析
- [推理路径诊断](analysis/how_to_diagnose_reasoning_path_issues.md) - 推理过程诊断

### 🔗 外部集成

#### 工具集成
- [工具集成指南](architecture/tool_integration/) - 外部工具集成
- [可视化集成](visualization/) - 可视化系统集成
- [监控集成](architecture/monitoring_integration.md) - 监控系统集成

### 📋 最佳实践

#### 使用最佳实践
- [最佳实践指南](guide/best_practices.md) - 使用建议
- [用户指南](guide/user_guide.md) - 详细使用说明
- [自动通知指南](automatic_notification_guide.md) - 通知系统使用

#### 开发最佳实践
- [代码审查清单](development/code_review_checklist.md) - 代码质量检查
- [性能优化建议](architecture/performance_optimization/best_practices.md) - 性能调优建议
- [安全编码指南](architecture/security_design.md) - 安全编码实践

## 📊 项目状态

### 当前版本
- **版本**: v1.0.0
- **状态**: 生产就绪
- **测试覆盖率**: 分析中 (运行 `python tests/coverage_analyzer.py`)

### 系统指标
- **核心Agent**: 8个 (ReasoningExpert, QualityController, RAGExpert等)
- **工具支持**: 15+ 种工具
- **测试文件**: 100+ 个
- **文档页数**: 200+ 页

### 最新更新
- ✅ RAG系统优化完成
- ✅ Agent性能优化完成
- ✅ 测试框架完善
- 🔄 文档系统持续改进

## 🆘 获取帮助

### 问题反馈
1. 查看[故障排除指南](guide/troubleshooting.md)
2. 检查[常见问题解答](faq.md)
3. 查看[系统诊断指南](analysis/)

### 技术支持
- **问题报告**: 在项目中创建Issue
- **功能请求**: 使用Feature Request模板
- **代码贡献**: 遵循[贡献指南](CONTRIBUTING.md)

### 社区资源
- **项目主页**: [GitHub Repository]
- **文档站点**: [在线文档]
- **讨论区**: [GitHub Discussions]

## 📝 文档维护

### 更新频率
- **主要版本**: 全面更新文档
- **次要版本**: 更新相关章节
- **补丁版本**: 更新修复说明

### 贡献文档
1. Fork 项目
2. 创建特性分支
3. 提交文档更新
4. 创建 Pull Request

### 文档规范
- 使用 Markdown 格式
- 遵循现有的文档结构
- 包含必要的代码示例
- 更新相关的交叉引用

---

**最后更新**: 2026-01-02
**维护者**: RANGEN 开发团队
**许可证**: MIT License
