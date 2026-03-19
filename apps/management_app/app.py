"""
RANGEN 管理应用 (Management App)

这是一个独立的管理界面，通过 API 调用 RANGEN AI 基座。
不直接导入 RANGEN 内部模块，只通过 REST API 进行交互。

使用方式:
    streamlit run apps/management_app/app.py

前提:
    RANGEN API 服务必须运行在 http://localhost:8000
"""
import streamlit as st
import requests
import json
from typing import Dict, Any, List, Optional

# 配置
RANGEN_API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="RANGEN Management",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

COLORS = {
    "primary": "#0D47A1",
    "secondary": "#1565C0",
}

st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🔧 RANGEN Management</h1>
</div>
""", unsafe_allow_html=True)


def api_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
    """统一的 API 请求方法"""
    url = f"{RANGEN_API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code >= 400:
            return {"error": f"API Error: {response.status_code}", "detail": response.text}
        
        return response.json() if response.text else {}
    except requests.exceptions.ConnectionError:
        return {"error": f"无法连接到 RANGEN API，请确保服务运行在 {RANGEN_API_BASE}"}
    except Exception as e:
        return {"error": str(e)}


def render_mermaid(mermaid_code: str, height: int = 400):
    """渲染 Mermaid 图表"""
    if not mermaid_code:
        return
    
    safe_code = mermaid_code.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    </head>
    <body>
        <div class="mermaid" style="display: flex; justify-content: center;">
        {mermaid_code}
        </div>
        <script>
            mermaid.initialize({{ startOnLoad: true }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=height + 50)


def render_agent_page():
    """Agent 管理页面"""
    st.header("🤖 Agent 管理")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Agent 列表")
        
        # 获取 Agent 列表
        agents_data = api_request("GET", "/api/v1/agents")
        
        if "error" in agents_data:
            st.error(agents_data["error"])
            return
            
        agents = agents_data.get("agents", [])
        
        if not agents:
            st.info("暂无 Agent")
            return
            
        agent_names = [a.get("name", "Unknown") for a in agents]
        selected_agent = st.selectbox("选择 Agent", agent_names)
    
    with col2:
        if selected_agent:
            st.subheader(f"🧪 测试: {selected_agent}")
            
            test_input = st.text_area(
                "测试输入",
                placeholder="输入测试内容...",
                height=100
            )
            
            if st.button("▶️ 执行测试", type="primary"):
                if not test_input:
                    st.warning("请输入测试内容")
                else:
                    with st.spinner("正在执行测试..."):
                        result = api_request(
                            "POST",
                            "/api/v1/test/execute",
                            data={
                                "agent_id": selected_agent,
                                "query": test_input
                            }
                        )
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            # 显示测试结果
                            st.success("测试完成!")
                            
                            score = result.get("overall_score", 0)
                            st.metric("综合评分", f"{score:.1f}")
                            
                            dimensions = result.get("dimensions", {})
                            if dimensions:
                                st.write("**维度评分:**")
                                for dim_key, dim_data in dimensions.items():
                                    score_val = dim_data.get("score", 0)
                                    st.write(f"- {dim_key}: {score_val:.0%}")
                            
                            # 执行轨迹
                            trace = result.get("execution_trace", [])
                            if trace:
                                st.write("**执行轨迹:**")
                                for i, step in enumerate(trace):
                                    with st.expander(f"Step {i+1}: {step.get('node', 'unknown')}"):
                                        st.write(f"状态: {step.get('status', 'unknown')}")
                                        st.write(f"耗时: {step.get('duration', 0)}ms")
                                        if step.get("output"):
                                            st.write(f"输出: {str(step.get('output'))[:200]}")


def render_skill_page():
    """Skill 管理页面"""
    st.header("🌟 Skill 管理")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Skill 列表")
        
        skills_data = api_request("GET", "/api/v1/skills")
        
        if "error" in skills_data:
            st.error(skills_data["error"])
            return
            
        skills = skills_data.get("skills", [])
        
        if not skills:
            st.info("暂无 Skill")
            return
            
        skill_names = [s.get("name", "Unknown") for s in skills]
        selected_skill = st.selectbox("选择 Skill", skill_names)
    
    with col2:
        if selected_skill:
            st.subheader(f"🧪 测试: {selected_skill}")
            
            test_input = st.text_area(
                "测试输入",
                placeholder="输入测试内容...",
                height=100
            )
            
            if st.button("▶️ 执行测试", type="primary"):
                if not test_input:
                    st.warning("请输入测试内容")
                else:
                    with st.spinner("正在执行测试..."):
                        result = api_request(
                            "POST",
                            "/api/v1/skills/trigger",
                            data={
                                "skill_id": selected_skill,
                                "input": test_input
                            }
                        )
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success("执行完成!")
                            st.json(result)


def render_tool_page():
    """Tool 管理页面"""
    st.header("🔧 Tool 管理")
    
    tools_data = api_request("GET", "/api/v1/tools")
    
    if "error" in tools_data:
        st.error(tools_data["error"])
        return
    
    tools = tools_data.get("tools", [])
    
    if not tools:
        st.info("暂无 Tool")
        return
    
    st.write(f"**共 {len(tools)} 个 Tool**")
    
    for tool in tools:
        with st.expander(f"🔧 {tool.get('name', 'Unknown')}"):
            st.write(f"**类型**: {tool.get('type', 'N/A')}")
            st.write(f"**描述**: {tool.get('description', 'N/A')}")


def render_workflow_page():
    """Workflow 管理页面"""
    st.header("🔀 Workflow 管理")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Workflow 列表")
        
        workflows_data = api_request("GET", "/api/v1/workflows")
        
        if "error" in workflows_data:
            st.error(workflows_data["error"])
            return
            
        workflows = workflows_data.get("workflows", [])
        
        if not workflows:
            st.info("暂无 Workflow")
            return
            
        wf_names = [w.get("name", "Unknown") for w in workflows]
        selected_wf = st.selectbox("选择 Workflow", wf_names)
    
    with col2:
        if selected_wf:
            st.subheader(f"🧪 测试: {selected_wf}")
            
            test_input = st.text_area(
                "测试输入",
                placeholder="输入测试内容...",
                height=100
            )
            
            if st.button("▶️ 执行测试", type="primary"):
                if not test_input:
                    st.warning("请输入测试内容")
                else:
                    with st.spinner("正在执行测试..."):
                        result = api_request(
                            "POST",
                            "/api/v1/workflows/test",
                            data={
                                "workflow_name": selected_wf,
                                "test_input": test_input
                            }
                        )
                        
                        if "error" in result:
                            st.error(result.get("error", "未知错误"))
                        else:
                            st.success("测试完成!")
                            
                            score = result.get("overall_score", 0)
                            st.metric("综合评分", f"{score:.1f}")
                            
                            dimensions = result.get("dimensions", {})
                            if dimensions:
                                st.write("**维度评分:**")
                                for dim_key, dim_data in dimensions.items():
                                    score_val = dim_data.get("score", 0)
                                    st.write(f"- {dim_key}: {score_val:.0%}")


def render_team_page():
    """Team 管理页面"""
    st.header("👥 Team 管理")
    
    teams_data = api_request("GET", "/api/v1/teams")
    
    if "error" in teams_data:
        st.error(teams_data["error"])
        return
    
    teams = teams_data.get("teams", [])
    
    if not teams:
        st.info("暂无 Team")
        return
    
    st.write(f"**共 {len(teams)} 个 Team**")
    
    for team in teams:
        with st.expander(f"👥 {team.get('name', 'Unknown')}"):
            st.write(f"**描述**: {team.get('description', 'N/A')}")
            st.write(f"**成员数**: {len(team.get('members', []))}")


def render_chat_page():
    """聊天测试页面"""
    st.header("💬 聊天测试")
    
    query = st.text_area("输入消息", placeholder="请输入您的问题...", height=100)
    
    if st.button("▶️ 发送", type="primary"):
        if not query:
            st.warning("请输入消息")
        else:
            with st.spinner("AI 正在思考..."):
                result = api_request(
                    "POST",
                    "/chat",
                    data={"query": query}
                )
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("收到回复!")
                    st.write("**回复:**")
                    st.write(result.get("answer", result.get("response", "")))


def main():
    """主函数"""
    st.title("🎛️ RANGEN 管理控制台")
    st.markdown("---")
    
    # 检查 API 连接
    health = api_request("GET", "/health")
    if "error" in health:
        st.error(f"⚠️ 无法连接到 RANGEN API: {health['error']}")
        st.info(f"请确保 RANGEN 服务运行在 {RANGEN_API_BASE}")
        st.stop()
    else:
        st.success(f"✅ 已连接到 RANGEN API")
    
    # 侧边栏导航
    st.sidebar.title("导航")
    
    pages = {
        "💬 聊天测试": render_chat_page,
        "🤖 Agent 管理": render_agent_page,
        "🌟 Skill 管理": render_skill_page,
        "🔧 Tool 管理": render_tool_page,
        "🔀 Workflow 管理": render_workflow_page,
        "👥 Team 管理": render_team_page,
    }
    
    selected_page = st.sidebar.radio("选择页面", list(pages.keys()))
    
    # 执行选中的页面
    pages[selected_page]()


if __name__ == "__main__":
    main()
