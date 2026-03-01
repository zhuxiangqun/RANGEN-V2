# 动态配置管理系统使用指南

## 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [配置管理](#配置管理)
4. [模板系统](#模板系统)
5. [监控和告警](#监控和告警)
6. [用户权限管理](#用户权限管理)
7. [高级功能](#高级功能)
8. [故障排除](#故障排除)

## 快速开始

### 系统启动

1. **安装依赖**:
```bash
pip install -r requirements.txt
```

2. **启动系统**:
```python
from src.core.intelligent_router import IntelligentRouter

# 创建智能路由器实例（启用所有高级功能）
router = IntelligentRouter(enable_advanced_features=True)

# 系统会自动启动：
# - 配置API服务器 (http://localhost:8080)
# - Web管理界面 (http://localhost:8081)
# - 热更新监控
# - 配置分发服务
```

3. **访问Web界面**:
打开浏览器访问 `http://localhost:8081` 进入管理界面。

### 基本操作

#### 更新配置
```python
# 更新阈值
router.update_routing_threshold('simple_max_complexity', 0.08)

# 添加关键词
router.add_routing_keyword('question_words', 'what')
```

#### 应用模板
```python
# 应用预定义模板
router.apply_config_template('conservative')
```

## 系统架构

### 核心组件

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web界面       │    │   REST API      │    │   配置存储       │
│   (Port 8081)   │    │   (Port 8080)   │    │   (File/DB)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  配置管理器     │
                    │                 │
                    │ • 验证器        │
                    │ • 监控器        │
                    │ • 模板管理器    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  高级功能       │
                    │                 │
                    │ • 热更新        │
                    │ • 分发系统      │
                    │ • 告警系统      │
                    │ • 权限控制      │
                    └─────────────────┘
```

### 数据流

1. **配置更新** → 验证 → 持久化 → 同步 → 通知
2. **查询路由** → 特征提取 → 规则匹配 → 决策输出
3. **监控数据** → 指标计算 → 告警触发 → 自动调整

## 配置管理

### 配置结构

系统配置包含以下主要部分：

```json
{
  "thresholds": {
    "simple_max_complexity": 0.05,
    "medium_min_complexity": 0.05,
    "medium_max_complexity": 0.25,
    "complex_min_complexity": 0.25
  },
  "keywords": {
    "question_words": ["what", "why", "how", "when", "where"],
    "complexity_indicators": ["explain", "analyze", "compare"]
  },
  "routing_rules": []
}
```

### 阈值配置

#### 复杂度阈值
- `simple_max_complexity`: 简单查询的最大复杂度 (0.0-1.0)
- `medium_min_complexity`: 中等查询的最小复杂度
- `medium_max_complexity`: 中等查询的最大复杂度
- `complex_min_complexity`: 复杂查询的最小复杂度

#### 词数阈值
- `simple_max_words`: 简单查询的最大词数
- `medium_min_words`: 中等查询的最小词数
- `medium_max_words`: 中等查询的最大词数
- `complex_min_words`: 复杂查询的最小词数

### 关键词配置

#### 问题词
用于识别查询中的问题类型：
```json
{
  "question_words": [
    "what", "why", "how", "when", "where", "who",
    "请问", "如何", "为什么", "什么是"
  ]
}
```

#### 复杂度指标
用于判断查询复杂度：
```json
{
  "complexity_indicators": [
    "explain", "analyze", "compare", "evaluate",
    "解释", "分析", "比较", "评估"
  ]
}
```

## 模板系统

### 内置模板

#### 1. 保守模板 (conservative)
- **适用环境**: 生产环境
- **特点**: 较低的阈值，更严格的路由判断
- **优势**: 高准确性，稳定性好
- **劣势**: 可能误判简单查询为中等查询

#### 2. 激进模板 (aggressive)
- **适用环境**: 开发/测试环境
- **特点**: 较高的阈值，更宽松的路由判断
- **优势**: 高性能，响应快
- **劣势**: 准确性稍低

#### 3. 平衡模板 (balanced)
- **适用环境**: 生产环境
- **特点**: 中等阈值，平衡性能和准确性
- **优势**: 综合性能好
- **劣势**: 在极端情况下可能不够极致

#### 4. 高精度模板 (high_precision)
- **适用环境**: 对准确性要求极高的场景
- **特点**: 最低阈值，最全面的关键词识别
- **优势**: 最高准确率
- **劣势**: 性能开销较大

### 模板继承

模板支持继承机制：

```python
# 自定义模板继承内置模板
custom_template = {
    'extends': 'conservative',  # 继承保守模板
    'thresholds': {
        'simple_max_complexity': 0.03  # 覆盖父模板设置
    },
    'keywords': {
        'question_words': ['what', 'why', 'how', '自定义问题词']
    }
}
```

### 环境自适应

模板会根据运行环境自动推荐：

```python
context = {
    'environment': 'production',      # 环境类型
    'system_load': 0.8,              # 系统负载
    'accuracy_requirement': 'high'   # 准确性要求
}

recommended_template = template_manager.get_recommended_template(context)
```

## 监控和告警

### 监控指标

#### 配置变更指标
- **总变更次数**: 系统运行以来配置变更总数
- **7天内变更**: 最近7天的变更次数
- **变更频率**: 每天平均变更次数
- **健康分数**: 系统配置健康度评分 (0-100)

#### 作者统计
- 各作者的变更贡献度
- 主要贡献者识别
- 变更集中度分析

#### 类型分布
- 手动变更 vs 自动变更
- 不同类型变更的占比

### 告警规则

#### 内置告警规则

1. **频繁变更告警**
   ```
   条件: 每天变更次数 > 10
   级别: 中等
   建议: 检查变更流程，增加测试覆盖
   ```

2. **单一作者告警**
   ```
   条件: 单一作者贡献率 > 80%
   级别: 中等
   建议: 增加多人审核机制
   ```

3. **配置验证失败告警**
   ```
   条件: 配置验证失败
   级别: 高
   建议: 立即检查配置格式和值
   ```

#### 自定义告警规则

```python
# 添加自定义告警规则
alert_manager.add_alert_rule('custom_rule', {
    'name': '自定义告警',
    'severity': 'medium',
    'time_window_minutes': 60,        # 时间窗口
    'max_changes_per_hour': 20,      # 每小时最大变更数
    'channels': ['console', 'log']   # 通知渠道
})
```

### 告警通知

#### 支持的通知渠道

1. **控制台输出**: 直接输出到控制台
2. **日志记录**: 写入系统日志
3. **邮件通知**: 发送邮件告警 (可扩展)
4. **Webhook**: HTTP回调通知 (可扩展)

#### 配置通知渠道

```python
# 添加邮件通知渠道
def email_notifier(message, context):
    # 发送邮件逻辑
    send_email(
        to='admin@example.com',
        subject=f'配置告警: {context.get("alert_id")}',
        body=message
    )

alert_manager.add_alert_channel('email', email_notifier)
```

## 用户权限管理

### 角色系统

#### 内置角色

1. **管理员 (admin)**
   ```
   权限: 所有权限
   描述: 完全控制系统
   ```

2. **运维人员 (operator)**
   ```
   权限: 配置读取、阈值更新、关键词更新、系统监控
   描述: 日常运维管理
   ```

3. **开发人员 (developer)**
   ```
   权限: 配置读取、模板应用、测试权限
   描述: 开发调试使用
   ```

4. **查看者 (viewer)**
   ```
   权限: 配置读取、系统监控
   描述: 只读访问权限
   ```

### 用户管理

#### 添加用户
```python
from src.core.advanced_config_features import AccessControlManager

ac_manager = AccessControlManager()

# 添加用户
ac_manager.add_user('john_doe', {
    'email': 'john@example.com',
    'department': 'engineering'
})

# 分配角色
ac_manager.assign_role('john_doe', 'developer')
```

#### 会话管理
```python
# 创建会话
session_id = ac_manager.create_session('john_doe', '192.168.1.100')

# 验证会话
user_id = ac_manager.validate_session(session_id)

# 销毁会话
ac_manager.destroy_session(session_id)
```

### 权限检查

```python
# 检查权限
has_permission = ac_manager.check_permission('john_doe', 'config.update.thresholds')

if has_permission:
    # 执行操作
    router.update_routing_threshold('test', 0.5)
else:
    print("权限不足")
```

## 高级功能

### 热更新机制

#### 自动监控
系统会自动监控配置文件的变化：

```python
# 启动热更新监控
hot_reload.start_monitoring()

# 添加自定义回调
def on_config_reload():
    print("配置已重新加载")
    # 执行自定义逻辑

hot_reload.add_reload_callback(on_config_reload)
```

#### 监控的文件
- `dynamic_config.json` - 主配置文件
- `routing_config.json` - 路由配置
- `config_changes.log` - 变更日志

### 配置分发

#### 注册节点
```python
# 注册分发节点
distribution.register_node('node_1', {
    'endpoint': 'http://node1.example.com:8080',
    'region': 'us-east',
    'environment': 'production'
})
```

#### 分发策略

1. **推送模式**: 主节点主动推送配置到各节点
2. **拉取模式**: 各节点主动从主节点拉取配置

#### 分发状态监控
```python
# 获取分发状态
status = distribution.get_distribution_status()
print(f"活跃节点: {status['active_nodes']}")
print(f"失败节点: {status['failed_nodes']}")
```

### 版本控制

#### 分支管理
```python
# 创建分支
store.create_branch('feature_branch')

# 切换分支
store.switch_branch('feature_branch')

# 合并分支
store.merge_branch('feature_branch', 'main')
```

#### 标签管理
```python
# 创建标签
store.create_tag('v1.0.0', description='正式发布版本')

# 检出标签
store.checkout_tag('v1.0.0')
```

### 导入导出

#### 配置导出
```python
from src.core.config_web_interface import ConfigImportExportManager

import_export = ConfigImportExportManager(router)

# 导出为JSON
json_config = import_export.export_config('json')

# 导出为YAML
yaml_config = import_export.export_config('yaml')
```

#### 配置导入
```python
# 导入配置（试运行）
result = import_export.import_config(json_config, 'json', dry_run=True)
if result['success']:
    print("导入预览:")
    for change in result['changes']:
        print(f"  {change['type']}: {change['key']}")

    # 执行实际导入
    result = import_export.import_config(json_config, 'json', dry_run=False)
```

## 故障排除

### 常见问题

#### 1. 配置更新不生效

**症状**: 修改配置后查询路由结果未改变

**解决方法**:
1. 检查配置是否正确保存
2. 验证配置格式是否正确
3. 重启系统或触发热更新
4. 查看系统日志确认配置加载

#### 2. Web界面无法访问

**症状**: 浏览器无法打开管理界面

**解决方法**:
1. 检查端口是否被占用
2. 确认服务已启动
3. 检查防火墙设置
4. 查看系统日志

#### 3. API调用失败

**症状**: API请求返回错误

**解决方法**:
1. 检查API端点URL是否正确
2. 验证认证令牌是否有效
3. 确认请求数据格式正确
4. 查看详细错误信息

#### 4. 性能下降

**症状**: 系统响应变慢

**解决方法**:
1. 检查系统负载
2. 查看监控指标
3. 优化配置参数
4. 考虑启用缓存

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 配置验证
```python
# 手动验证配置
validation = router.config_manager.config_validator.validate(config)
if not validation.is_valid:
    print("配置错误:")
    for error in validation.errors:
        print(f"  - {error}")
```

#### 性能监控
```python
# 查看性能指标
metrics = router.performance_monitor.get_stats()
print("性能统计:", metrics)

# 查看系统状态
status = router.get_system_status()
print("系统状态:", status)
```

### 联系支持

如果问题无法解决，请：

1. 收集相关日志文件
2. 记录重现步骤
3. 描述系统环境
4. 联系技术支持团队

---

**版本**: 1.0.0
**更新日期**: 2024-01-15
**文档维护**: 系统管理员
