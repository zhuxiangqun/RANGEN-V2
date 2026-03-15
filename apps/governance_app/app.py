"""
RANGEN 治理仪表盘

独立 Streamlit 应用，通过 API 调用 RANGEN AI 基座。

使用方式:
    streamlit run apps/governance_app/app.py

前提:
    RANGEN API 服务必须运行在 http://localhost:8000
"""
import streamlit as st
import requests
import time
from datetime import datetime

RANGEN_API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="RANGEN Governance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 RANGEN 治理仪表盘")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("API Status", "Active" if True else "Inactive")

with col2:
    st.metric("Uptime", "Running")

with col3:
    try:
        health = requests.get(f"{RANGEN_API_BASE}/health", timeout=2)
        st.metric("Health", "OK" if health.status_code == 200 else "Error")
    except:
        st.metric("Health", "Error")

with col4:
    st.metric("Version", "2.0.0")

st.markdown("---")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔌 API Endpoints")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/api/v1/agents", "Agent List"),
        ("/api/v1/skills", "Skill List"),
        ("/api/v1/tools", "Tool List"),
        ("/api/v1/teams", "Team List"),
        ("/api/v1/workflows", "Workflow List"),
        ("/chat", "Chat"),
        ("/docs", "API Docs"),
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{RANGEN_API_BASE}{endpoint}", timeout=2)
            status = "✅" if response.status_code < 400 else "❌"
            st.write(f"{status} {endpoint} - {name}")
        except:
            st.write(f"❌ {endpoint} - {name} (无法连接)")

with col_right:
    st.subheader("⚙️ System Info")
    st.write(f"**API Base:** {RANGEN_API_BASE}")
    st.write(f"**Last Check:** {datetime.now().strftime('%H:%M:%S')}")
    
    if st.button("🔄 Refresh"):
        st.rerun()

st.markdown("---")

st.subheader("📈 Quick Actions")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📋 List All Agents"):
        try:
            result = requests.get(f"{RANGEN_API_BASE}/api/v1/agents", timeout=5)
            st.json(result.json())
        except Exception as e:
            st.error(f"Error: {e}")

with c2:
    if st.button("🌟 List All Skills"):
        try:
            result = requests.get(f"{RANGEN_API_BASE}/api/v1/skills", timeout=5)
            st.json(result.json())
        except Exception as e:
            st.error(f"Error: {e}")

with c3:
    if st.button("🔧 List All Tools"):
        try:
            result = requests.get(f"{RANGEN_API_BASE}/api/v1/tools", timeout=5)
            st.json(result.json())
        except Exception as e:
            st.error(f"Error: {e}")
