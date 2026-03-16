import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
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
    "background": "#FAFAFA",
    "surface": "#FFFFFF",
    "text": "#212121",
    "text_secondary": "#757575"
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
    .chat-message-user {{
        background: {COLORS['primary']};
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 3px 15px;
        margin: 0.5rem 0;
    }}
    .chat-message-assistant {{
        background: #F5F5F5;
        color: {COLORS['text']};
        padding: 1rem;
        border-radius: 15px 15px 15px 3px;
        margin: 0.5rem 0;
    }}
    .timestamp {{
        font-size: 0.7rem;
        color: {COLORS['text_secondary']};
        margin-top: 0.25rem;
    }}
    .feature-card {{
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    .feature-card h4 {{
        margin: 0 0 0.5rem 0;
        color: {COLORS['primary']};
    }}
    .quick-action-btn {{
        background: white;
        border: 1px solid {COLORS['secondary']};
        color: {COLORS['secondary']};
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.2s;
    }}
    .quick-action-btn:hover {{
        background: {COLORS['secondary']};
        color: white;
    }}
    .stChatMessage {{
        padding: 0.5rem 0;
    }}
    div[data-testid="stChatMessage"] {{
        background: transparent;
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
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

if "api_key" not in st.session_state:
    st.session_state.api_key = RANGEN_API_KEY

def check_api_status():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
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
    
    st.markdown("### 📊 System Status")
    status_class = "status-online" if api_online else "status-offline"
    status_text = "Online" if api_online else "Offline"
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
        <span class="status-indicator {status_class}">● {status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔧 API Configuration", expanded=True):
        api_url_input = st.text_input("API URL", value=API_URL, key="api_url")
        api_key_input = st.text_input("API Key", value=st.session_state.api_key, type="password", key="api_key_input")
        if api_key_input:
            st.session_state.api_key = api_key_input
        if st.button("🔄 Test Connection"):
            if check_api_status():
                st.success("✅ Connected successfully!")
            else:
                st.error("❌ Connection failed")
    
    st.markdown("### ⚡ Quick Actions")
    quick_actions = [
        "打开 https://www.toutiao.com",
        "搜索今天的热点新闻",
        "帮我写一个Python排序算法",
        "分析这段代码的问题"
    ]
    for action in quick_actions:
        if st.button(action, key=f"quick_{action[:10]}"):
            st.session_state.pending_input = action
    
    st.markdown("### 💬 Session")
    st.text(f"ID: {st.session_state.session_id[:8]}...")
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ Capabilities")
    capabilities = [
        ("🌐", "Web Browsing", "Open websites, extract content"),
        ("🔍", "Web Search", "Search the internet for information"),
        ("📚", "Knowledge RAG", "Query internal knowledge base"),
        ("💻", "Code Execution", "Run and analyze code"),
        ("🧮", "Calculator", "Perform calculations")
    ]
    for icon, name, desc in capabilities:
        st.markdown(f"**{icon} {name}**")
        st.caption(desc)

st.markdown("""
<div class="main-header">
    <h1>🧠 RANGEN Intelligent Assistant</h1>
    <p>Enterprise AI Agent Platform • ReAct Reasoning • Knowledge Retrieval</p>
</div>
""", unsafe_allow_html=True)

if hasattr(st.session_state, 'pending_input'):
    prompt = st.session_state.pending_input
    del st.session_state.pending_input
    st.chat_input(prompt)

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🧠"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message-user">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
        
        if "timestamp" in message:
            st.markdown(f'<div class="timestamp">🕐 {message["timestamp"]}</div>', unsafe_allow_html=True)
        
        if "steps" in message and message["steps"]:
            with st.expander("🔍 Reasoning Trace"):
                for i, step in enumerate(message["steps"], 1):
                    st.text(f"{i}. {step}")
        
        if "tool_result" in message and message["tool_result"]:
            with st.expander("🔧 Tool Execution Result"):
                st.json(message["tool_result"])

if prompt := st.chat_input("💬 Describe what you need me to do..."):
    timestamp = datetime.now().strftime("%H:%M:%S")
    
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
            payload = {
                "query": prompt,
                "session_id": st.session_state.session_id
            }
            
            headers = {}
            api_key = st.session_state.get("api_key") or RANGEN_API_KEY
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                f"{api_url_input}/chat", 
                json=payload, 
                headers=headers, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                steps = data.get("steps", [])
                tool_result = data.get("tool_result")
                error = data.get("error")
                
                if error:
                    message_placeholder.error(f"❌ {error}")
                else:
                    message_placeholder.markdown(answer)
                    
                    response_timestamp = datetime.now().strftime("%H:%M:%S")
                    msg_data = {
                        "role": "assistant", 
                        "content": answer,
                        "timestamp": response_timestamp
                    }
                    if steps:
                        msg_data["steps"] = steps
                    if tool_result:
                        msg_data["tool_result"] = tool_result
                    st.session_state.messages.append(msg_data)
                    
                    if steps:
                        with st.expander("🔍 Reasoning Trace"):
                            for i, step in enumerate(steps, 1):
                                st.text(f"{i}. {step}")
                    
                    if tool_result:
                        with st.expander("🔧 Tool Execution Result"):
                            st.json(tool_result)
            else:
                error_msg = f"❌ Error {response.status_code}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
        except requests.exceptions.Timeout:
            error_msg = "❌ Request timed out. Please try again."
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
        except Exception as e:
            error_msg = f"❌ Connection failed: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

if not st.session_state.messages:
    st.info("👋 Welcome to RANGEN! I'm your AI assistant. Here are some things I can do:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🌐 Web Browsing
        I can open websites and extract content for you.
        - "打开 https://example.com"
        - "获取这个页面的标题"
        """)
    with col2:
        st.markdown("""
        ### 🔍 Information Search
        Search the web for news, facts, and more.
        - "搜索最新的AI新闻"
        - "查一下Python的特点"
        """)
    with col3:
        st.markdown("""
        ### 💻 Code & Analysis
        Help with coding tasks and technical questions.
        - "写一个快速排序算法"
        - "分析这段代码的问题"
        """)
    
    st.markdown("---")
    st.caption("💡 Tip: Use the quick action buttons in the sidebar for common tasks!")
