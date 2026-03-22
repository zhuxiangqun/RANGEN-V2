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
    /* 全局紧凑布局 */
    .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    
    /* 头部紧凑 */
    .main-header {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 0.5rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.8);
        margin: 0.2rem 0 0 0;
        font-size: 0.85rem;
    }}
    
    /* 卡片紧凑 */
    .app-card {{
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        transition: all 0.2s;
        margin-bottom: 0.3rem;
    }}
    .app-card:hover {{
        border-color: {COLORS['primary']};
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .app-card h3 {{
        margin: 0.2rem 0;
        color: {COLORS['primary']};
        font-size: 0.9rem;
    }}
    .app-card p {{
        color: #757575;
        margin: 0;
        font-size: 0.75rem;
    }}
    .app-card span {{
        font-size: 1.5rem;
    }}
    
    /* 列间距 */
    .stHorizontalBlock {{
        gap: 0.3rem !important;
    }}
    
    /* 减少元素间距 */
    div[data-testid="stHorizontalBlock"] {{
        padding: 0px !important;
    }}
    
    /* 按钮紧凑 */
    .stButton {{
        margin-top: 0px !important;
    }}
    .stButton > button {{
        margin: 0 !important;
    }}
    
    /* info框紧凑 */
    .stAlert {{
        margin-bottom: 0.5rem !important;
        padding: 0.5rem !important;
    }}
    
    /* caption紧凑 */
    .stCaption {{
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }}
    
    /* 分割线紧凑 */
    hr {{
        margin: 0.5rem 0 !important;
    }}
    
    /* markdown紧凑 */
    .stMarkdown {{
        margin-bottom: 0.3rem !important;
    }}
    
    /* 减少所有元素的margin */
    p {{
        margin-bottom: 0.3rem !important;
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
        <span style="font-size: 1.5rem;">💬</span>
        <h3>Chat</h3>
        <p>AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8501", label="Open", icon="🚀", use_container_width=True)

with col2:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 1.5rem;">🔧</span>
        <h3>Management</h3>
        <p>Agent/Skill/Tool</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8502", label="Open", icon="🚀", use_container_width=True)

with col3:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 1.5rem;">📊</span>
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
        <span style="font-size: 1.5rem;">🔌</span>
        <h3>API Docs</h3>
        <p>REST API</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"{API_BASE}/docs", label="Open", icon="🚀", use_container_width=True)

with col5:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 1.5rem;">🔀</span>
        <h3>Workflow</h3>
        <p>Visualization</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(f"http://localhost:8080", label="Open", icon="🚀", use_container_width=True)

with col6:
    st.markdown(f"""
    <div class="app-card">
        <span style="font-size: 1.5rem;">📚</span>
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

col_status, col_tip = st.columns([1, 3])
with col_status:
    st.caption(f"API: {api_status} | v2.0.0")
with col_tip:
    st.caption("💡 ./scripts/start_rangen.sh start")
