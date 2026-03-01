# 统一服务器启动指南

## 🎯 快速开始

### 方法1：一键快速启动（推荐）

```bash
# 启动统一服务器（包含可视化和配置管理）
python scripts/start_unified_server.py --port 8080
```

这将启动完整的统一服务系统，包括：
- ✅ LangGraph 工作流可视化
- ✅ 动态配置管理系统
- ✅ REST API 服务
- ✅ Web管理界面
- ✅ 所有功能在一个端口上

**自定义端口**（避免与其他服务冲突）：
```bash
# 如果8080端口被占用，使用其他端口
python scripts/start_unified_server.py --port 8082
```

### 方法2：智能启动器（自动处理端口冲突）

```bash
# 自动检测可用端口并启动
python scripts/smart_server_launcher.py

# 或指定首选端口
python scripts/smart_server_launcher.py 8080
```

### 方法2：命令行启动

```bash
# 基础模式（仅核心功能）
python scripts/start_dynamic_config_system.py basic --api-port 8082 --web-port 8083

# 完整模式（所有功能）
python scripts/start_dynamic_config_system.py full --api-port 8082 --web-port 8083

# 开发模式（调试功能）
python scripts/start_dynamic_config_system.py dev --api-port 8082 --web-port 8083

# 生产模式（高可用集群）
python scripts/start_dynamic_config_system.py prod --api-port 8082 --web-port 8083
```

**参数说明**：
- `--api-port`: API服务器端口（默认8080）
- `--web-port`: Web界面端口（默认8081）

### 方法3：Shell脚本启动

```bash
# 使用Shell脚本（自动处理端口冲突）
./scripts/quick_start_server.sh

# 或指定端口
./scripts/quick_start_server.sh 8080
```

## 🌐 访问地址

启动成功后，所有功能都在同一个端口上：

- 🌐 **统一主页 & 可视化**: http://localhost:8080/
- ⚙️ **配置管理页面**: http://localhost:8080/config
- 🔗 **API端点**:
  - `GET /api/config` - 获取当前配置
  - `GET /api/route-types` - 路由类型管理
  - `PUT /api/config/thresholds` - 更新阈值
  - `PUT /api/config/keywords` - 更新关键词
  - `POST /api/route-types` - 注册新路由类型
  - `POST /api/config/reset` - 重置配置

## 🎨 界面特色

### 主页功能
- **导航栏**: 快速访问配置管理和API信息
- **状态指示器**: 系统运行状态显示
- **统一入口**: 所有功能一键访问

### 配置管理界面
- **路由阈值配置**: 实时调整路由决策参数
- **关键词管理**: 自定义路由关键词
- **系统状态监控**: 查看配置系统运行状态
- **实时保存**: 配置更改立即生效

### 方法4：程序化启动

```python
from src.core.intelligent_router import IntelligentRouter

# 创建路由器实例
router = IntelligentRouter(enable_advanced_features=True)

# 系统自动启动所有服务
print("系统已启动，访问 http://localhost:8081 查看管理界面")
```

## 📋 前置要求

### 1. 环境准备

```bash
# 确保Python版本 >= 3.8
python --version

# 安装核心依赖
pip install langchain langgraph

# 安装可选依赖（推荐）
pip install -r requirements-optional.txt
```

### 2. 端口配置

**⚠️ 重要：避免端口冲突**

如果系统中已有其他服务使用默认端口，请使用自定义端口：

```bash
# 检查端口占用
lsof -i :8080  # 检查8080端口
lsof -i :8081  # 检查8081端口

# 使用自定义端口启动
python scripts/quick_start.py --api-port 8082 --web-port 8083

# 或使用完整启动脚本
python scripts/start_dynamic_config_system.py full --api-port 8082 --web-port 8083
```

### 3. 权限要求

- ✅ 读写配置文件权限
- ✅ 网络端口访问权限（默认8080, 8081，可自定义）
- ✅ 日志文件写入权限

## 🚀 启动模式详解

### 基础模式 (basic)

**适用场景**: 轻量级使用，测试功能

```bash
python scripts/start_dynamic_config_system.py basic
```

**功能包含**:
- 智能路由引擎
- 基础配置管理
- 规则引擎

**资源占用**: 低
**启动时间**: < 5秒

### 完整模式 (full) - 推荐

**适用场景**: 生产环境，完整功能

```bash
python scripts/start_dynamic_config_system.py full
```

**功能包含**:
- 所有基础功能
- REST API服务
- Web管理界面
- 热更新监控
- 配置分发服务
- 监控和告警
- 用户权限管理

**资源占用**: 中等
**启动时间**: 10-15秒

### 开发模式 (dev)

**适用场景**: 开发调试，功能测试

```bash
python scripts/start_dynamic_config_system.py dev
```

**特殊功能**:
- 详细调试日志
- 热重载支持
- 测试接口开放
- 性能监控

**资源占用**: 中等
**启动时间**: 15-20秒

### 生产模式 (prod)

**适用场景**: 企业生产环境

```bash
python scripts/start_dynamic_config_system.py prod
```

**企业级功能**:
- 高可用集群
- 自动备份
- 安全加固
- 负载均衡
- 故障转移

**资源占用**: 高
**启动时间**: 30-60秒

## 🌐 访问方式

### Web管理界面

启动系统后，打开浏览器访问：
```
http://localhost:8081
```

**界面功能**:
- 📊 配置可视化管理
- 🎛️ 阈值动态调整
- 📈 性能监控图表
- 🔧 系统健康检查
- 👥 用户权限管理

### REST API接口

通过HTTP API进行编程访问：
```
http://localhost:8080
```

**浏览器访问**: 直接在浏览器中打开上述地址，可以看到美观的Web界面和交互式API测试功能。

**主要端点**:
```
GET    /              # API信息和可用端点列表 (支持HTML和JSON)
GET    /config        # 获取当前路由配置 (JSON)
GET    /route-types   # 获取路由类型列表 (JSON)
POST   /route-types   # 注册新的路由类型
PUT    /config/thresholds   # 更新路由阈值
PUT    /config/keywords     # 更新关键词配置
```

**内容协商**: API支持内容协商，如果浏览器访问根路径会返回HTML页面，编程访问会返回JSON数据。

## 🔧 配置验证

启动后可以通过以下方式验证系统正常运行：

### 1. 健康检查

```bash
curl http://localhost:8080/api/v1/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "services": {
    "api": "running",
    "web": "running",
    "monitoring": "running"
  }
}
```

### 2. 配置测试

```python
from src.core.intelligent_router import IntelligentRouter

router = IntelligentRouter(enable_advanced_features=True)

# 测试配置更新
router.update_routing_threshold('simple_max_complexity', 0.08)
print("✅ 配置更新成功")

# 获取配置
config = router.get_routing_config()
print(f"✅ 配置获取成功: {len(config.get('thresholds', {}))} 个阈值")
```

### 3. Web界面检查

访问 `http://localhost:8081` 确认：
- [ ] 页面正常加载
- [ ] 配置面板可操作
- [ ] 监控数据正常显示
- [ ] 没有错误提示

## 🛠️ 故障排除

### 常见启动问题

#### 问题1: 端口被占用

```
错误: [Errno 48] Address already in use
```

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8080
lsof -i :8081

# 杀死进程或更换端口
```

#### 问题2: 依赖缺失

```
ImportError: No module named 'langchain'
```

**解决方案**:
```bash
pip install langchain langgraph
```

#### 问题3: 权限不足

```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:
```bash
# 使用sudo或更改文件权限
chmod 755 scripts/
chmod 644 config/
```

### 日志查看

系统运行日志保存在：
- 控制台输出（实时）
- `logs/dynamic_config.log`（文件）
- Web界面监控面板

### 性能监控

启动后可以通过以下方式监控系统性能：

```bash
# 查看系统指标
curl http://localhost:8080/api/v1/metrics

# 查看路由统计
curl http://localhost:8080/api/v1/routes/stats
```

## 📚 使用示例

### 基本配置操作

```python
from src.core.intelligent_router import IntelligentRouter

router = IntelligentRouter(enable_advanced_features=True)

# 1. 更新阈值
router.update_routing_threshold('simple_max_complexity', 0.08)

# 2. 添加关键词
router.add_routing_keyword('question_words', 'what')

# 3. 应用模板
router.apply_config_template('conservative')

# 4. 获取配置
config = router.get_routing_config()
print(f"配置包含: {len(config.get('thresholds', {}))} 个阈值, {len(config.get('route_types', []))} 个路由类型")
```

### 高级配置管理

```python
# 获取当前配置
config = router.get_routing_config()
print(f"当前阈值: {config['thresholds']}")

# 导出配置
router.export_config('backup_config.json')

# 导入配置
router.import_config('custom_config.json')
```

## 🎯 下一步

启动系统后，您可以：

1. **探索Web界面** - 直观管理所有配置
2. **查看API文档** - 了解编程接口详情
3. **运行测试** - 验证系统功能
4. **自定义配置** - 根据业务需求调整参数
5. **监控性能** - 跟踪系统运行状态

更多详细信息请参考：
- [用户指南](guide/user_guide.md)
- [最佳实践](guide/best_practices.md)
- [API文档](api/dynamic_config_api.md)
