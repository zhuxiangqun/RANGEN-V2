"""
RANGEN 统一入口

独立 Streamlit 应用，作为所有 RANGEN 服务的入口。

使用方式:
    streamlit run apps/entry_app/app.py
"""
import streamlit as st
import requests

st.set_page_config(
    page_title="RANGEN AI Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

COLORS = {
    "primary": "#0D47A1",
    "secondary": "#1565C0",
    "success": "#2E7D32",
}

st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 600;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.8);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }}
    .app-card {{
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s;
        cursor: pointer;
    }}
    .app-card:hover {{
        border-color: {COLORS['primary']};
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .app-card h3 {{
        margin: 0.5rem 0;
        color: {COLORS['primary']};
    }}
    .app-card p {{
        color: #757575;
        margin: 0;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <h1>🧠 RANGEN</h1>
    <p>AI Agent Infrastructure Platform</p>
</div>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000"

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">💬</span>
        <h3>Chat</h3>
        <p>AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8501", label="Open", icon="🚀", use_container_width=True)

with col2:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">🔧</span>
        <h3>Management</h3>
        <p>Agent/Skill/Tool</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8502", label="Open", icon="🚀", use_container_width=True)

with col3:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">📊</span>
        <h3>Governance</h3>
        <p>Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8503", label="Open", icon="🚀", use_container_width=True)

st.markdown("---")

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">🔌</span>
        <h3>API Docs</h3>
        <p>REST API</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"{API_BASE}/docs", label="Open", icon="🚀", use_container_width=True)

with col5:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">🔀</span>
        <h3>Workflow</h3>
        <p>Visualization</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8080", label="Open", icon="🚀", use_container_width=True)

with col6:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 2rem;">📚</span>
        <h3>ReDoc</h3>
        <p>API Reference</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"{API_BASE}/redoc", label="Open", icon="🚀", use_container_width=True)

st.markdown("---")

api_status = "🟢 Online" if True else "🔴 Offline"
try:
    resp = requests.get(f"{API_BASE}/health", timeout=2)
    if resp.status_code == 200:
        api_status = "🟢 Online"
    else:
        api_status = "🔴 Offline"
except:
    api_status = "🔴 Offline"

st.info("💡 Tips: Make sure RANGEN base is running (./start_rangen.sh start)")
st.caption(f"API Status: {api_status} | Version: 2.0.0")
