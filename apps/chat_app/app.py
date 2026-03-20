"""
RANGEN 智能对话助手
================

运行方式:
    streamlit run apps/chat_app/app.py
"""
import streamlit as st
import requests
import os
import uuid
from pathlib import Path

# 加载 .env 文件
env_path = Path("/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/.env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

RANGEN_API_BASE = "http://localhost:8000"
RANGEN_API_KEY = os.getenv("RANGEN_API_KEY", "")

st.set_page_config(
    page_title="RANGEN 智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def post_with_auth(url, data=None):
    headers = {"Content-Type": "application/json"}
    if RANGEN_API_KEY:
        headers["Authorization"] = f"Bearer {RANGEN_API_KEY}"
    try:
        return requests.post(url, headers=headers, json=data, timeout=60)
    except:
        return None


# 页面样式
st.markdown("""
<style>
    /* 隐藏默认的 Streamlit 元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 聊天消息样式 */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* 加载动画 */
    .typing-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #667eea;
        animation: typing 1.4s infinite;
    }
    @keyframes typing {
        0%, 20% {transform: translateY(0);}
        60%, 100% {transform: translateY(-10px);}
    }
</style>
""", unsafe_allow_html=True)


# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False


# 主界面
st.title("🤖 RANGEN 智能助手")


# 消息显示区域
chat_container = st.container()

with chat_container:
    # 显示欢迎消息
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; color: #666;">
            <h3>👋 您好！我是 RANGEN 智能助手</h3>
            <p style="margin-top: 20px; font-size: 16px;">
                我可以帮您：<br><br>
                🔍 诊断和修复系统问题<br>
                🔧 创建新的 Agent、Skill、Tool<br>
                💬 回答各种问题<br><br>
                <em>请在下方输入您的问题</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 显示消息历史
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])


# 底部输入区域
if prompt := st.chat_input("输入您的问题..."):
    # 添加用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示思考中状态
    thinking_placeholder = st.empty()
    with thinking_placeholder:
        with st.chat_message("assistant"):
            st.markdown("🤔 思考中...")
    
    # 调用API
    try:
        result = post_with_auth(
            f"{RANGEN_API_BASE}/api/v1/conversation/chat",
            data={
                "message": prompt,
                "session_id": st.session_state.session_id
            }
        )
        
        # 清除思考中状态
        thinking_placeholder.empty()
        
        if result and result.status_code == 200:
            resp_data = result.json()
            response = resp_data.get("response", "处理完成")
            
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 处理确认请求
            if resp_data.get("type") == "confirmation":
                suggested = resp_data.get("suggested_actions", [])
                if suggested:
                    st.info("💡 您可以输入回复继续对话，如：" + "、".join(suggested))
        elif result:
            with st.chat_message("assistant"):
                st.error(f"请求失败 (错误码: {result.status_code})")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"❌ 请求失败 (错误码: {result.status_code})"
            })
        else:
            with st.chat_message("assistant"):
                st.error("❌ 无法连接到 RANGEN 服务")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "❌ 无法连接到 RANGEN 服务"
            })
    except Exception as e:
        thinking_placeholder.empty()
        with st.chat_message("assistant"):
            st.error(f"发生错误: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"❌ 发生错误: {str(e)}"
        })


# 侧边栏 - 设置
with st.sidebar:
    st.markdown("### ⚙️ 设置")
    
    # 连接状态
    try:
        resp = requests.get(f"{RANGEN_API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            st.markdown("""
            <div style="background-color: #28a745; color: white; padding: 12px 16px; 
                        border-radius: 6px; font-weight: 500; margin: 8px 0;">
                ✅ RANGEN 已连接
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #ffc107; color: #333; padding: 12px 16px; 
                        border-radius: 6px; font-weight: 500; margin: 8px 0;">
                ⚠️ RANGEN 连接异常
            </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="background-color: #dc3545; color: white; padding: 12px 16px; 
                    border-radius: 6px; font-weight: 500; margin: 8px 0;">
            ❌ 无法连接到 RANGEN
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 清除对话
    if st.button("🗑️ 新对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 使用提示")
    st.markdown("""
    - 直接输入问题，助手会智能理解
    - 支持运维诊断："根路径404"
    - 支持创建能力："创建一个Agent"
    - 多轮对话：助手会主动询问
    """)
