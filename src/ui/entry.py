#!/usr/bin/env python3
"""统一入口页面 - RANGEN"""

import streamlit as st

st.set_page_config(
    page_title="RANGEN 统一入口",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 RANGEN 统一入口")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("http://localhost:8501", label="💬 聊天界面")
    st.caption("实时对话 Agent")

with col2:
    st.page_link("http://localhost:8502", label="🔧 管理平台")
    st.caption("Agent/Skill/Tool 管理")

with col3:
    st.page_link("http://localhost:8503", label="📊 治理仪表盘")
    st.caption("监控与治理")

col4, col5, col6 = st.columns(3)

with col4:
    st.page_link("http://localhost:8000/docs", label="🔌 API 文档")
    st.caption("REST API")

with col5:
    st.page_link("http://localhost:8080", label="🔀 Workflow")
    st.caption("工作流可视化")

with col6:
    st.page_link("http://localhost:8000/redoc", label="📚 ReDoc")
    st.caption("API 参考文档")

st.markdown("---")
st.caption("💡 提示: 点击上方链接跳转到对应服务")
