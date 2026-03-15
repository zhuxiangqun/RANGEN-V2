# 🔧 开发指南

RANGEN系统的开发技术文档，包括API参考、开发规范和扩展开发指南。

## 🎯 目标读者

- RANGEN系统的开发者
- 希望扩展或定制系统的集成开发者
- 为系统贡献代码的开源贡献者
- 基于RANGEN进行二次开发的团队

## 📋 内容导航

### 📚 API参考
- [API认证文档](api-reference/API_AUTHENTICATION.md) - API认证和授权机制
- [动态配置API](api-reference/dynamic_config_api.md) - 系统动态配置接口

### 🔌 系统扩展
- [自定义智能体](extending-system/custom-agents.md) - 开发新的AI Agent
- [LangGraph实现指南](extending-system/langgraph_implementation_roadmap.md) - LangGraph工作流开发
- [OpenTelemetry集成指南](extending-system/opentelemetry_integration_guide.md) - 监控系统集成
- [测试执行指南](extending-system/test_execution_guide.md) - 系统测试和验证

### 🧪 测试
- [单元测试指南](testing/unit-testing.md) - 编写和运行单元测试
- [首席代理统一架构测试指南](testing/chief_agent_unified_architecture_test_guide.md) - 核心架构测试
- [编排可视化测试指南](testing/orchestration_visualization_test_guide.md) - 工作流可视化测试

### 🏗️ 开发环境
- [开发环境搭建](development-environment.md) - 本地开发环境配置
- [代码规范](code-style-guide.md) - 代码风格和规范
- [Cursor节点文档字符串指南](cursor_node_docstring_guide.md) - LangGraph节点文档规范

## 🔗 相关资源

- [架构设计](../architecture/README.md) - 系统架构和设计理念
- [技术参考](../reference/README.md) - 详细技术规格和配置
- [最佳实践](../best-practices/README.md) - 开发经验和优化建议
- [运维部署](../operations/README.md) - 部署和运维指南

## 📖 学习路径

### 新开发者路径 (6小时)
1. 搭建[开发环境](development-environment.md) (1小时)
2. 学习[代码规范](code-style-guide.md) (1小时)
3. 了解[API认证](api-reference/API_AUTHENTICATION.md) (1小时)
4. 编写[单元测试](testing/unit-testing.md) (1小时)
5. 开发[自定义智能体](extending-system/custom-agents.md) (2小时)

### 高级开发者路径 (10小时)
1. 完成新开发者路径所有内容
2. 学习[系统扩展](extending-system/) (3小时)
3. 掌握[首席代理架构测试](testing/chief_agent_unified_architecture_test_guide.md) (2小时)
4. 了解[部署和高可用性](../operations/deployment/high-availability.md) (2小时)
5. 贡献[开源代码](../CONTRIBUTING.md) (3小时)

## 🛠️ 开发工具

### 核心开发工具
- **语言**：Python 3.9+
- **Web框架**：FastAPI
- **工作流引擎**：LangGraph
- **前端框架**：Streamlit + Vue.js
- **数据库**：SQLite + 向量数据库

### 开发辅助工具
- **代码格式化**：Black, isort
- **代码检查**：Pylint, MyPy
- **测试框架**：pytest, pytest-asyncio
- **文档生成**：MkDocs, pydoc
- **包管理**：Poetry, pip

### 开发环境配置
```bash
# 克隆代码库
git clone https://github.com/your-repo/RANGEN.git

# 安装依赖
cd RANGEN
pip install -r requirements-dev.txt

# 设置环境变量
cp .env.example .env

# 启动开发服务器
python src/api/server.py
```

## 📝 开发规范

### 代码质量要求
1. **测试覆盖率**：核心模块≥80%，重要功能≥95%
2. **代码检查**：通过Pylint检查，无严重警告
3. **类型注解**：公共API必须有完整类型注解
4. **文档要求**：公共函数和类必须有完整文档字符串

### 提交规范
1. **提交消息格式**：遵循Conventional Commits规范
2. **代码审查**：所有提交必须通过代码审查
3. **测试要求**：新功能必须包含相应测试
4. **文档更新**：API变更必须更新相关文档

### 发布流程
1. **版本号**：遵循语义化版本控制
2. **发布检查**：通过所有测试和代码检查
3. **文档同步**：更新变更日志和API文档
4. **发布通知**：通知用户和开发者

## 🔄 贡献指南

### 如何贡献
1. **报告问题**：使用Issue模板提交问题报告
2. **建议功能**：在讨论区提出功能建议
3. **提交代码**：遵循Pull Request流程
4. **改进文档**：直接提交文档改进

### 贡献者权益
1. **贡献者名单**：列入项目贡献者名单
2. **代码署名**：在相关文件中保留贡献者信息
3. **社区认可**：在社区活动中获得认可
4. **优先支持**：获得优先技术支持

## 📞 开发支持

- 开发问题？[提交开发问题](https://github.com/your-repo/RANGEN/issues)
- 技术讨论？[参与开发讨论](https://github.com/your-repo/RANGEN/discussions/categories/development)
- 代码审查？[提交Pull Request](https://github.com/your-repo/RANGEN/pulls)
- 寻求帮助？[加入开发者社区](https://github.com/your-repo/RANGEN/discussions)

## 📝 文档状态

| 文档 | 状态 | 最后更新 | 维护者 |
|------|------|----------|--------|
| API认证文档 | ✅ 完成 | 2026-03-07 | 开发团队 |
| 自定义智能体 | ✅ 完成 | 2026-03-07 | 开发团队 |
| 单元测试指南 | ✅ 完成 | 2026-03-07 | 测试团队 |
| 开发环境搭建 | ✅ 完成 | 2026-03-07 | 开发团队 |
| 代码规范指南 | ✅ 完成 | 2026-03-07 | 开发团队 |

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN开发工作组*