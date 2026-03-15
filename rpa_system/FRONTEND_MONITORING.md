# RPA系统前端监控功能说明

## 📋 功能概述

RPA系统可以**自动检测前端系统的各种问题**，包括：

### ✅ 已实现的检查项

#### 1. **静态检查**（文件系统层面）

- ✅ **检查前端目录是否存在**
  - 检查 `frontend_monitor` 目录是否存在
  - 如果不存在，标记为严重问题

- ✅ **检查后端目录是否存在**
  - 检查 `frontend_monitor/backend` 目录是否存在
  - 如果不存在，标记为严重问题

- ✅ **检查关键文件是否存在**
  - 检查 `backend/app.py` 是否存在
  - 如果不存在，标记为严重问题

- ✅ **检查Python语法错误**
  - 使用 `py_compile` 检查后端Python文件的语法
  - 如果发现语法错误，标记为可修复问题

- ✅ **检查依赖是否安装**
  - 检查常见依赖（flask, flask-cors）是否已安装
  - 如果缺失，标记为可修复问题

#### 2. **运行时检查**（服务层面）

- ✅ **检查前端服务是否运行**
  - 检查前端服务端口（默认5173）是否开放
  - 尝试HTTP请求验证服务是否正常响应
  - 如果服务未运行，标记为可修复问题

- ✅ **检查后端服务是否运行**
  - 检查后端服务端口（默认5001）是否开放
  - 尝试HTTP请求验证服务是否正常响应
  - 如果服务未运行，标记为可修复问题

- ✅ **检查前端页面是否可访问**
  - 尝试访问前端页面
  - 检查HTTP状态码
  - 验证页面内容是否包含预期内容（如"RANGEN"、"系统监控"等）
  - 如果页面不可访问，标记为问题

- ✅ **检查后端API是否正常**
  - 尝试调用后端API端点（如 `/api/logs`）
  - 检查HTTP状态码
  - 如果API异常，标记为问题

- ✅ **检查端口状态**
  - 检查端口是否被占用
  - 检查端口是否可访问

## 🔧 自动修复功能

RPA系统可以**自动修复**以下问题：

### 1. **安装缺失的依赖**
- 自动检测缺失的依赖
- 使用 `pip install` 自动安装

### 2. **启动服务**（提供建议）
- 检测到服务未运行时，提供启动建议
- 提供具体的启动命令

### 3. **语法错误修复**（待实现）
- 计划集成代码修复工具（如autopep8, black）
- 或使用LLM进行代码修复

## 📊 检查流程

每次RPA系统运行时会自动执行以下检查：

```
1. 检查前端目录是否存在
   ↓
2. 检查后端目录是否存在
   ↓
3. 检查关键文件是否存在
   ↓
4. 检查Python语法错误
   ↓
5. 检查依赖是否安装
   ↓
6. 检查前端服务是否运行
   ↓
7. 检查后端服务是否运行
   ↓
8. 检查前端页面是否可访问
   ↓
9. 检查后端API是否正常
   ↓
10. 检查端口状态
   ↓
11. 生成检查报告
   ↓
12. 尝试自动修复可修复的问题
```

## 🎯 使用示例

### 检查结果示例

```json
{
  "status": "issues_found",
  "issues": [
    {
      "type": "service_not_running",
      "severity": "high",
      "message": "前端服务未运行: 端口 5173 未开放或服务未运行",
      "fixable": true,
      "details": {
        "running": false,
        "error": "端口 5173 未开放或服务未运行"
      }
    },
    {
      "type": "missing_dependencies",
      "severity": "medium",
      "message": "缺少依赖: flask-cors",
      "fixable": true,
      "details": ["flask-cors"]
    }
  ],
  "checked_at": 1234567890.123
}
```

### 修复结果示例

```json
{
  "status": "success",
  "fixes_applied": 1,
  "fixes_failed": 1,
  "details": {
    "applied": [
      {
        "issue": {
          "type": "missing_dependencies",
          "message": "缺少依赖: flask-cors"
        },
        "fix": {
          "success": true,
          "message": "成功安装依赖: flask-cors"
        }
      }
    ],
    "failed": [
      {
        "issue": {
          "type": "service_not_running",
          "message": "前端服务未运行"
        },
        "reason": "前端服务需要手动启动（npm run dev）"
      }
    ]
  }
}
```

## ⚙️ 配置

### 环境变量

可以通过环境变量配置前端和后端URL：

```bash
export FRONTEND_URL=http://localhost:5173
export BACKEND_URL=http://localhost:5001
```

### 配置文件

在 `rpa_system/config.py` 中配置：

```python
"frontend": {
    "frontend_url": "http://localhost:5173",
    "backend_url": "http://localhost:5001",
}
```

## 🔍 检查时机

前端系统检查会在以下时机执行：

1. **每次RPA系统运行开始时**
   - 在运行核心系统之前检查前端系统
   - 如果发现问题，尝试自动修复

2. **手动触发检查**（通过API）
   - 可以通过API手动触发检查
   - 返回详细的检查结果

## 📝 注意事项

1. **服务启动检查**
   - 服务启动检查需要服务正在运行
   - 如果服务未运行，会提供启动建议，但不会自动启动（因为服务是长期运行的进程）

2. **端口检查**
   - 端口检查使用socket连接，超时时间为2秒
   - HTTP请求超时时间为3-5秒

3. **依赖检查**
   - 目前只检查常见依赖（flask, flask-cors）
   - 可以扩展检查 `requirements.txt` 中的所有依赖

4. **语法检查**
   - 使用Python内置的 `py_compile` 模块
   - 只能检查语法错误，不能检查逻辑错误

## 🚀 未来改进

1. **扩展依赖检查**
   - 读取 `requirements.txt` 检查所有依赖
   - 检查版本兼容性

2. **增强服务启动**
   - 尝试在后台启动服务
   - 监控服务启动状态

3. **代码修复**
   - 集成代码修复工具
   - 使用LLM进行智能修复

4. **性能监控**
   - 监控服务响应时间
   - 监控资源使用情况

5. **日志分析**
   - 分析服务日志中的错误
   - 提供更详细的问题诊断

## 📚 相关文档

- `rpa_system/README.md` - RPA系统完整文档
- `rpa_system/QUICKSTART.md` - 快速开始指南

