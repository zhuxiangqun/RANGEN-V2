"""
RANGEN 聊天应用

独立 Streamlit 应用，通过 API 调用 RANGEN AI 基座。

使用方式:
    streamlit run apps/chat_app/app.py

前提:
    RANGEN API 服务必须运行在 http://localhost:8000
"""
import streamlit as st
import requests
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RANGEN_API_BASE = os.getenv("API_URL", "http://localhost:8000")
RANGEN_API_KEY = os.getenv("RANGEN_API_KEY", "")

st.set_page_config(
    page_title="RANGEN AI Agent Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    "primary": "#0D47A1",
    "secondary": "#1565C0",
    "accent": "#00ACC1",
    "success": "#2E7D32",
    "warning": "#F57C00",
    "error": "#C62828",
}

st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.8);
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }}
    .status-indicator {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }}
    .status-online {{
        background: rgba(46, 125, 50, 0.1);
        color: {COLORS['success']};
    }}
    .status-offline {{
        background: rgba(198, 40, 40, 0.1);
        color: {COLORS['error']};
    }}
    .timestamp {{
        font-size: 0.7rem;
        color: #757575;
        margin-top: 0.25rem;
    }}
    .feature-card {{
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    .sidebar-section {{
        background: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    .sidebar-section h3 {{
        margin: 0 0 0.5rem 0;
        font-size: 0.9rem;
        color: #757575;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "api_key" not in st.session_state:
    st.session_state.api_key = RANGEN_API_KEY

WORKFLOW_CREATE_KEYWORDS = [
    "创建流程", "创建研发", "做一个流程", "研发流程",
    "产品经理", "开发者", "测试工程师", "架构师",
    "需求到上线", "需求到发布", "开发流程"
]

def detect_intent(prompt: str) -> str:
    prompt_lower = prompt.lower()
    for keyword in WORKFLOW_CREATE_KEYWORDS:
        if keyword in prompt_lower:
            return "create_workflow"
    return "chat"

def check_api_status():
    try:
        response = requests.get(f"{RANGEN_API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

api_online = check_api_status()

with st.sidebar:
    st.markdown(f"""
    <div class="main-header" style="padding: 1rem; margin-bottom: 1rem;">
        <h1 style="font-size: 1.4rem;">🧠 RANGEN</h1>
        <p>AI Agent Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    status_class = "status-online" if api_online else "status-offline"
    status_text = "Online" if api_online else "Offline"
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
        <span class="status-indicator {status_class}">● {status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()
    
    with st.expander("⚙️ Settings"):
        api_key_input = st.text_input("API Key", value=st.session_state.api_key, type="password", key="api_key_input")
        if api_key_input:
            st.session_state.api_key = api_key_input

st.markdown("""
<div class="main-header">
    <h1>🧠 RANGEN Intelligent Assistant</h1>
    <p>Enterprise AI Agent Platform • ReAct Reasoning • Knowledge Retrieval</p>
</div>
""", unsafe_allow_html=True)

if hasattr(st.session_state, 'pending_input'):
    prompt = st.session_state.pending_input
    del st.session_state.pending_input
    st.rerun()

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🧠"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        
        if "timestamp" in message:
            st.markdown(f'<div class="timestamp">🕐 {message["timestamp"]}</div>', unsafe_allow_html=True)
        
        if "steps" in message and message["steps"]:
            with st.expander("🔍 Reasoning Trace"):
                for i, step in enumerate(message["steps"], 1):
                    st.text(f"{i}. {step}")
        
        if "tool_result" in message and message["tool_result"]:
            with st.expander("🔧 Tool Result"):
                st.json(message["tool_result"])

if prompt := st.chat_input("💬 Describe what you need me to do..."):
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    intent = detect_intent(prompt)
    
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "timestamp": timestamp
    })
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.markdown(f'<div class="timestamp">🕐 {timestamp}</div>', unsafe_allow_html=True)
    
    with st.chat_message("assistant", avatar="🧠"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 **Thinking...**")
        
        try:
            headers = {}
            api_key = st.session_state.get("api_key") or RANGEN_API_KEY
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            if intent == "create_workflow":
                try:
                    from apps.entry_app.workflow_creator import create_workflow
                    result = create_workflow(prompt, headers)
                    answer = result.get("message", "")
                except Exception as e:
                    answer = f"Workflow creation not available: {str(e)}"
            else:
                payload = {"query": prompt, "session_id": st.session_state.session_id}
                response = requests.post(
                    f"{RANGEN_API_BASE}/chat", 
                    json=payload, 
                    headers=headers, 
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                else:
                    answer = f"Error: {response.status_code}"
            
            message_placeholder.markdown(answer)
            
            response_timestamp = datetime.now().strftime("%H:%M:%S")
            msg_data = {
                "role": "assistant", 
                "content": answer,
                "timestamp": response_timestamp
            }
            st.session_state.messages.append(msg_data)
                
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

if not st.session_state.messages:
    st.info("👋 Welcome to RANGEN! I'm your AI assistant.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🌐 Web Browsing\nI can open websites for you.")
    with col2:
        st.markdown("### 🔍 Search\nSearch the web for information.")
    with col3:
        st.markdown("### 💻 Code\nHelp with coding tasks.")
    
    st.markdown("---")
    st.caption("💡 Tip: Use quick action buttons in the sidebar!")
