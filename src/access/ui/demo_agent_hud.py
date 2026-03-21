#!/usr/bin/env python3
"""
AgentHUD 演示应用

体验 Agent 实时状态面板功能
"""

import streamlit as st
import time
import random
from datetime import datetime

st.set_page_config(
    page_title="AgentHUD 演示",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AgentHUD 实时状态面板演示")

st.markdown("""
## 功能说明

此演示展示 AgentHUD 的核心功能:

- **上下文健康度** - 实时显示 token 使用百分比
- **工具活动追踪** - 记录每个工具的执行状态
- **Agent 状态显示** - 展示活跃的 Agent 数量
- **Todo 进度追踪** - 进度条可视化
- **错误监控** - 实时显示错误信息
""")

# 初始化 session state
if "hud_data" not in st.session_state:
    st.session_state.hud_data = {
        "context_percent": 45,
        "usage_percent": 30,
        "active_agents": 3,
        "duration": 0,
        "tools": [],
        "todo_progress": (3, 10),
        "last_error": None
    }

# 侧边栏控制
st.sidebar.header("🎮 模拟控制")

if st.sidebar.button("🔄 模拟工具调用"):
    tool_names = ["search", "code_gen", "file_read", "reasoning", "validation"]
    tool_name = random.choice(tool_names)
    st.session_state.hud_data["tools"].append({
        "name": tool_name,
        "status": "completed",
        "duration": random.uniform(0.1, 2.0),
        "success": True
    })
    st.session_state.hud_data["context_percent"] = min(95, st.session_state.hud_data["context_percent"] + random.randint(1, 5))
    st.rerun()

if st.sidebar.button("❌ 模拟错误"):
    errors = ["网络超时", "API 限流", "解析失败", "认证过期"]
    st.session_state.hud_data["last_error"] = random.choice(errors)
    st.rerun()

if st.sidebar.button("✅ 清除错误"):
    st.session_state.hud_data["last_error"] = None
    st.rerun()

if st.sidebar.button("📈 增加上下文"):
    st.session_state.hud_data["context_percent"] = min(95, st.session_state.hud_data["context_percent"] + 10)
    st.rerun()

if st.sidebar.button("📉 减少上下文"):
    st.session_state.hud_data["context_percent"] = max(5, st.session_state.hud_data["context_percent"] - 10)
    st.rerun()

if st.sidebar.button("➕ 添加 Agent"):
    st.session_state.hud_data["active_agents"] += 1
    st.rerun()

if st.sidebar.button("➖ 移除 Agent"):
    st.session_state.hud_data["active_agents"] = max(1, st.session_state.hud_data["active_agents"] - 1)
    st.rerun()

if st.sidebar.button("🔄 重置"):
    st.session_state.hud_data = {
        "context_percent": 45,
        "usage_percent": 30,
        "active_agents": 3,
        "duration": 0,
        "tools": [],
        "todo_progress": (3, 10),
        "last_error": None
    }
    st.rerun()

# 主面板
st.markdown("---")
st.subheader("📊 实时状态")

# 第一行: 核心指标
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

# 上下文健康度
with col1:
    percent = st.session_state.hud_data["context_percent"]
    if percent < 60:
        color, emoji = "🟢", "健康"
    elif percent < 85:
        color, emoji = "🟡", "警告"
    else:
        color, emoji = "🔴", "危险"
    
    st.metric("上下文使用率", f"{percent}%", emoji)
    st.progress(percent / 100)
    max_tokens = 200000
    current_tokens = int(max_tokens * percent / 100)
    st.caption(f"{current_tokens:,} / {max_tokens:,} tokens ({color} {emoji})")

# 使用量
with col2:
    usage = st.session_state.hud_data["usage_percent"]
    st.metric("API 使用量", f"{usage}%")
    st.progress(usage / 100)
    st.caption("基于当前会话周期")

# Agent 数量
with col3:
    st.metric("活跃 Agent", st.session_state.hud_data["active_agents"])

# 执行时间
with col4:
    st.metric("执行时间", f"{st.session_state.hud_data['duration']:.1f}s")

# 第二行: 详细状态
st.markdown("---")
col_left, col_right = st.columns([2, 1])

# 工具活动
with col_left:
    st.subheader("🔧 工具活动")
    
    if st.session_state.hud_data["tools"]:
        for tool in st.session_state.hud_data["tools"][-5:][::-1]:
            icon = "✅" if tool["success"] else "❌"
            st.markdown(f"{icon} **{tool['name']}** - {tool['duration']:.2f}s")
    else:
        st.info("暂无工具活动记录，点击左侧「模拟工具调用」开始")

# Todo 进度
with col_right:
    st.subheader("📋 任务进度")
    completed, total = st.session_state.hud_data["todo_progress"]
    st.progress(completed / total, text=f"进度: {completed}/{total}")
    
    if st.button("✅ 完成一个任务"):
        if completed < total:
            st.session_state.hud_data["todo_progress"] = (completed + 1, total)
        st.rerun()

# 错误显示
if st.session_state.hud_data["last_error"]:
    st.error(f"❌ 错误: {st.session_state.hud_data['last_error']}")

# Agent 状态卡片
st.markdown("---")
st.subheader("🤖 Agent 状态")

agent_cols = st.columns(min(st.session_state.hud_data["active_agents"], 4))
for i in range(min(st.session_state.hud_data["active_agents"], 4)):
    with agent_cols[i]:
        agent_names = ["ReasoningAgent", "ValidationAgent", "ToolExecutor", "ContextManager"]
        st.metric(f"Agent {i+1}", agent_names[i % len(agent_names)], "运行中")

# 自动更新
time.sleep(1)
st.rerun()
