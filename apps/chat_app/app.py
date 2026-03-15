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

RANGEN_API_BASE = "http://localhost:8000"

st.set_page_config(page_title="RANGEN Chat", page_icon="🤖", layout="wide")

st.title("🤖 RANGEN Intelligent Assistant")
st.markdown("Powered by ReAct Reasoning & Knowledge Retrieval")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Intent detection keywords
WORKFLOW_CREATE_KEYWORDS = [
    "创建流程", "创建研发", "做一个流程", "研发流程",
    "产品经理", "开发者", "测试工程师", "架构师",
    "需求到上线", "需求到发布", "开发流程"
]

def detect_intent(prompt: str) -> str:
    """检测用户意图"""
    prompt_lower = prompt.lower()
    
    # 检测是否是要创建研发流程
    for keyword in WORKFLOW_CREATE_KEYWORDS:
        if keyword in prompt_lower:
            return "create_workflow"
    
    return "chat"


def handle_create_workflow(prompt: str):
    """处理创建工作流请求"""
    try:
        response = requests.post(
            f"{RANGEN_API_BASE}/api/v1/auto/create-workflow",
            json={
                "description": prompt,
                "auto_execute": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 构建响应消息
            message = result.get("message", "")
            
            # 添加工作流详情
            if result.get("agents"):
                message += "\n\n**创建的角色:**\n"
                for agent in result["agents"]:
                    message += f"- {agent.get('name', 'Unknown')}: {agent.get('role_type', '')}\n"
            
            if result.get("workflow_steps"):
                message += "\n**工作流步骤:**\n"
                for i, step in enumerate(result["workflow_steps"], 1):
                    message += f"{i}. {step}\n"
            
            return message
        else:
            return f"❌ 创建失败: {response.status_code}"
    except Exception as e:
        return f"❌ 错误: {str(e)}"


with st.sidebar:
    st.header("Settings")
    st.text(f"Session ID: {st.session_state.session_id}")
    
    st.markdown("---")
    st.header("API Status")
    try:
        health = requests.get(f"{RANGEN_API_BASE}/health", timeout=2)
        if health.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.warning("⚠️ API Error")
    except:
        st.error("❌ API Unavailable")
    
    st.markdown("---")
    st.header("Quick Actions")
    
    # 显示可用模板
    try:
        templates = requests.get(f"{RANGEN_API_BASE}/api/v1/auto/templates", timeout=5)
        if templates.status_code == 200:
            st.write("**可用模板:**")
            for t in templates.json().get("templates", []):
                st.write(f"- {t['name']}: {t['description']}")
    except:
        pass
    
    st.markdown("---")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "steps" in message and message["steps"]:
            with st.expander("View Reasoning Trace"):
                for step in message["steps"]:
                    st.text(step)

if prompt := st.chat_input("输入需求... (例如: 帮我创建一个研发流程，包含产品经理、开发者、测试工程师)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 检测意图
            intent = detect_intent(prompt)
            
            if intent == "create_workflow":
                # 处理创建工作流
                result_message = handle_create_workflow(prompt)
                st.markdown(result_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result_message
                })
            else:
                # 正常对话
                try:
                    response = requests.post(
                        f"{RANGEN_API_BASE}/chat",
                        json={
                            "query": prompt,
                            "session_id": st.session_state.session_id
                        },
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result.get("answer", str(result))
                        steps = result.get("reasoning_steps", [])
                        
                        st.markdown(answer)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "steps": steps
                        })
                    else:
                        st.error(f"Error: {response.status_code}")
                except requests.exceptions.Timeout:
                    st.error("Request timeout")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
