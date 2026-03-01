# 统一控制台 - LangGraph 可视化与动态配置管理系统

## 🎯 概述

统一控制台将 **LangGraph 工作流可视化** 和 **动态配置管理系统** 集成到一个服务中，提供一站式的AI系统管理和监控体验。

## 🌟 核心特性

### 🔄 一站式管理
- **LangGraph 可视化**: 实时工作流执行监控
- **动态配置管理**: 路由阈值、关键词、路由类型配置
- **统一界面**: 无缝切换不同功能模块

### 🎨 现代化界面
- **响应式设计**: 支持桌面和移动设备
- **实时更新**: WebSocket 实时状态同步
- **直观导航**: 清晰的功能分区和导航

### ⚙️ 配置管理功能
- **阈值调整**: 动态修改路由决策阈值
- **关键词管理**: 添加/修改关键词分类
- **路由类型**: 自定义路由类型和优先级
- **实时生效**: 配置更改立即生效

## 🚀 快速开始

### 安装依赖

```bash
# 核心依赖
pip install langchain langgraph

# 可视化服务器依赖
pip install fastapi uvicorn websockets

# 可选：高级功能
pip install -r requirements-optional.txt
```

### 启动统一控制台

```bash
# 基本启动（推荐）
python scripts/start_unified_server.py --port 8080

# 这将启动：
# - API服务器: http://localhost:8080 (JSON API)
# - 可视化服务器: http://localhost:8081 (Web界面 + 配置管理)

# 自定义基础端口
python scripts/start_unified_server.py --port 9000
# - API服务器: http://localhost:9000
# - 可视化服务器: http://localhost:9001

# 语法验证（可选）
python test_unified_server_syntax.py
```

### 访问控制台

打开浏览器访问：**http://localhost:8081** (可视化服务器)

## 🔌 端口分配

统一服务器自动分配端口以避免冲突：

- **API服务器**: 指定端口 (默认 8080) - 提供JSON API
- **可视化服务器**: 指定端口 + 1 (默认 8081) - 提供Web界面

例如，`--port 8080` 将启动：
- 🔗 **API服务器**: `http://localhost:8080` (JSON API + 配置管理API)
- 🌐 **可视化服务器**: `http://localhost:8081` (Web界面 + LangGraph可视化 + 配置管理界面)

## 📱 界面导航

### 主页 (/)
- **统一导航**: 选择 LangGraph 可视化或配置管理
- **系统状态**: 显示服务运行状态和端口信息
- **快速链接**: 直接跳转到各个功能模块

### 配置管理 (/config)
- **概览标签页**: 系统状态和配置统计
- **阈值配置**: 调整路由决策参数
- **关键词配置**: 管理关键词分类
- **路由类型**: 查看和管理路由类型

### LangGraph 可视化 (/)
如果存在 `src/visualization/static/index.html`，会显示完整的工作流可视化界面。

## 🔧 配置选项

### 命令行参数

```bash
python scripts/start_unified_server.py [选项]

选项:
  --port PORT          服务器端口 (默认: 8080)
  --help               显示帮助信息
```

### 环境变量

```bash
# 设置可视化端口
export VISUALIZATION_PORT=8080

# 启用/禁用工作流
export ENABLE_UNIFIED_WORKFLOW=true

# 禁用可视化（只启动配置管理）
export ENABLE_BROWSER_VISUALIZATION=false
```

## 📊 API 接口

### 配置管理 API

```
GET  /api/config          # 获取当前配置
GET  /api/route-types     # 获取路由类型列表
PUT  /api/config/thresholds   # 更新阈值
PUT  /api/config/keywords     # 更新关键词
```

### LangGraph API

```
GET  /api/workflow/graph      # 获取工作流图
POST /api/workflow/execute    # 执行工作流
GET  /api/workflow/health     # 工作流健康检查
GET  /api/executions          # 获取执行历史
```

## 🎨 界面定制

### 添加自定义导航

在 `BrowserVisualizationServer` 中修改主页：

```python
# 在 _generate_main_page_html 中添加自定义链接
custom_links = '''
<div class="custom-nav">
    <a href="/your-feature">您的功能</a>
</div>
'''
```

### 自定义样式

修改 `BrowserVisualizationServer._generate_config_dashboard_html()` 中的CSS样式。

## 🔍 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 检查端口使用
lsof -i :8080

# 使用不同端口
python scripts/start_unified_server.py --port 8081
```

#### 2. 可视化界面不显示
- 确保 `src/visualization/static/index.html` 存在
- 检查 FastAPI 和相关依赖已安装

#### 3. 配置不生效
- 确保修改后点击"保存"按钮
- 检查浏览器控制台是否有错误

### 日志查看

```bash
# 查看服务器日志
tail -f logs/unified_server.log

# 查看 LangGraph 执行日志
tail -f logs/langgraph_execution.log
```

## 🏗️ 架构说明

### 系统组件

```
统一控制台
├── LangGraph 可视化服务器 (FastAPI)
│   ├── 工作流执行监控
│   ├── WebSocket 实时更新
│   └── 静态文件服务
├── 动态配置管理器
│   ├── 路由配置管理
│   ├── API 接口
│   └── 配置持久化
└── 集成界面
    ├── 统一导航
    ├── 状态监控
    └── 功能切换
```

### 数据流

1. **用户请求** → 统一服务器
2. **路由判断** → 可视化界面 or 配置管理界面
3. **功能执行** → 对应的业务逻辑
4. **结果返回** → 用户界面更新

## 📈 性能优化

### 缓存策略
- 工作流图缓存
- 配置数据缓存
- 静态资源缓存

### 并发处理
- 异步请求处理
- WebSocket 连接池
- 数据库连接池

## 🔒 安全考虑

### API 安全
- 请求频率限制
- 输入验证和清理
- CORS 配置

### 配置安全
- 配置数据加密
- 访问权限控制
- 操作审计日志

## 📚 扩展开发

### 添加新功能模块

1. 在 `BrowserVisualizationServer` 中添加路由
2. 创建对应的HTML界面生成方法
3. 添加API端点处理逻辑

### 自定义主题

修改 `_generate_config_dashboard_html()` 中的CSS样式定义。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 支持

如有问题，请：
1. 查看本文档的故障排除部分
2. 检查 GitHub Issues
3. 提交新的 Issue

---

**🎉 享受统一控制台带来的高效AI系统管理体验！**
