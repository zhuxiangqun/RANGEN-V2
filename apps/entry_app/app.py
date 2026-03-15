"""
RANGEN 统一入口

独立 Streamlit 应用，作为所有 RANGEN 服务的入口。

使用方式:
    streamlit run apps/entry_app/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="RANGEN 统一入口",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 RANGEN 统一入口")
st.markdown("---")

API_BASE = "http://localhost:8000"

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 💬 聊天界面
    实时对话 Agent
    """)
    st.page_link(f"http://localhost:8500", label="打开聊天", icon="💬")

with col2:
    st.markdown("""
    ### 🔧 管理平台
    Agent/Skill/Tool 管理
    """)
    st.page_link(f"http://localhost:8501", label="打开管理", icon="🔧")

with col3:
    st.markdown("""
    ### 📊 治理仪表盘
    监控与治理
    """)
    st.page_link(f"http://localhost:8502", label="打开仪表盘", icon="📊")

st.markdown("---")

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    ### 🔌 API 文档
    REST API 文档
    """)
    st.page_link(f"{API_BASE}/docs", label="打开文档", icon="🔌")

with col5:
    st.markdown("""
    ### 🔀 Workflow
    工作流可视化
    """)
    st.page_link(f"http://localhost:8080", label="打开Workflow", icon="🔀")

with col6:
    st.markdown("""
    ### 📚 ReDoc
    API 参考文档
    """)
    st.page_link(f"{API_BASE}/redoc", label="打开ReDoc", icon="📚")

st.markdown("---")

st.info("💡 提示: 请确保 RANGEN 基座已启动 (./start_rangen.sh start)")
