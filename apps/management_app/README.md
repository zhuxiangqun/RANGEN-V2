# RANGEN 管理应用

基于 RANGEN AI 基座的管理控制台。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│              RANGEN AI 基座 (src/api/)                    │
│                                                              │
│  - /api/v1/agents      (CRUD + 测试)                      │
│  - /api/v1/skills     (CRUD + 优化)                       │
│  - /api/v1/tools      (CRUD)                               │
│  - /api/v1/teams     (CRUD + 执行)                         │
│  - /api/v1/workflows  (CRUD + 测试)                         │
│  - /chat              (对话)                                │
└─────────────────────────────────────────────────────────────┘
                              ↑↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│              管理应用 (apps/management_app/)                │
│                                                              │
│  - 通过 HTTP API 调用 RANGEN 基座                           │
│  - 不直接导入 RANGEN 内部模块                               │
│  - 独立的 Streamlit 应用                                    │
└─────────────────────────────────────────────────────────────┘
```

## 运行

### 1. 启动 RANGEN API 服务

```bash
cd RANGEN-main(syu-python)
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

### 2. 启动管理应用

```bash
cd apps/management_app
pip install -r requirements.txt
streamlit run app.py
```

管理应用将运行在 `http://localhost:8501`

## 功能

| 页面 | 功能 |
|------|------|
| 💬 聊天测试 | 测试 RANGEN 对话能力 |
| 🤖 Agent 管理 | 列表/测试 Agent |
| 🌟 Skill 管理 | 列表/测试 Skill |
| 🔧 Tool 管理 | 列表 Tool |
| 🔀 Workflow 管理 | 列表/测试 Workflow |
| 👥 Team 管理 | 列表 Team |

## 开发

此应用完全通过 HTTP API 与 RANGEN 交互，不依赖 RANGEN 内部代码。

如需添加新功能，只需：
1. 在 RANGEN 中添加相应的 API 端点
2. 在 `app.py` 中调用该 API
