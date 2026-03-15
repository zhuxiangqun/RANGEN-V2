import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
RANGEN_API_KEY = os.getenv("RANGEN_API_KEY", "")

st.set_page_config(page_title="RANGEN Chat", page_icon="🤖", layout="wide")

st.title("🤖 RANGEN Intelligent Assistant")
st.markdown("Powered by ReAct Reasoning & Knowledge Retrieval")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.text(f"Session ID: {st.session_state.session_id}")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "steps" in message and message["steps"]:
            with st.expander("View Reasoning Trace"):
                for step in message["steps"]:
                    st.text(step)

# Input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            payload = {
                "query": prompt,
                "session_id": st.session_state.session_id
            }
            
            # Prepare headers - auto-use API key from environment
            headers = {}
            api_key = st.session_state.get("api_key") or RANGEN_API_KEY
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(f"{API_URL}/chat", json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                steps = data.get("steps", [])
                
                message_placeholder.markdown(answer)
                
                if steps:
                    with st.expander("View Reasoning Trace"):
                        for step in steps:
                            st.text(step)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "steps": steps
                })
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except Exception as e:
            error_msg = f"Connection Failed: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
