"""
RANGEN Monitor - 监控与评估面板
"""
import streamlit as st
import requests
import os
import time
import subprocess
import json
import uuid
from datetime import datetime

# 加载 .env 文件
from pathlib import Path
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
    page_title="RANGEN Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_with_auth(url):
    headers = {}
    if RANGEN_API_KEY:
        headers["Authorization"] = f"Bearer {RANGEN_API_KEY}"
    try:
        return requests.get(url, headers=headers, timeout=5)
    except:
        return None

def post_with_auth(url, data=None):
    headers = {"Content-Type": "application/json"}
    if RANGEN_API_KEY:
        headers["Authorization"] = f"Bearer {RANGEN_API_KEY}"
    try:
        return requests.post(url, headers=headers, json=data, timeout=30)
    except:
        return None

st.markdown("""
<style>
    /* 全局紧凑布局 */
    .block-container {padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important;}
    
    /* Metric卡片紧凑 */
    .metric-box {background: #1E3A5F; border-radius: 6px; padding: 6px; text-align: center;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E3A5F 0%, #2D5A87 100%);
        padding: 8px !important;
        border-radius: 6px;
        color: white !important;
        margin: 2px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.8) !important;
        font-size: 0.75rem !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: bold;
        font-size: 1rem !important;
    }
    div[data-testid="stMetricDelta"] {color: #90EE90 !important;}
    
    /* Tabs紧凑 */
    .stTabs [data-baseweb="tab-list"] {gap: 4px !important; padding: 0 !important;}
    .stTabs [data-baseweb="tab"] {
        background: #E8EEF4;
        border-radius: 4px 4px 0 0;
        padding: 4px 12px !important;
        color: #1E3A5F !important;
        font-weight: 600;
        font-size: 0.85rem !important;
    }
    .stTabs [aria-selected="true"] {background: #1E3A5F !important; color: white !important;}
    .stTabs [aria-selected="false"] {color: #1E3A5F !important;}
    
    /* 标题紧凑 */
    h1 {font-size: 1.5rem !important; margin-bottom: 0.5rem !important;}
    h2 {font-size: 1.2rem !important; margin-bottom: 0.3rem !important;}
    h3 {color: #1E3A5F; margin-top: 0.3rem !important; margin-bottom: 0.3rem !important;}
    h4 {font-size: 0.9rem !important; margin-bottom: 0.2rem !important;}
    
    /* 元素间距 */
    hr {margin: 0.3rem 0 !important;}
    p {margin-bottom: 0.2rem !important;}
    
    /* 分区紧凑 */
    .capability-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 6px;
        padding: 8px;
        margin: 6px 0;
    }
    .capability-section h4 {color: #1E3A5F; margin: 0 0 4px 0; font-size: 0.85rem !important;}
    .capability-section p {color: #495057; margin: 0; font-size: 0.8rem !important;}
    
    /* Alert紧凑 */
    .stAlert {margin-bottom: 0.3rem !important; padding: 0.5rem !important;}
    
    /* Expander紧凑 */
    .streamlit-expanderHeader {padding: 0.3rem 0.5rem !important;}
    .streamlit-expanderContent {padding: 0.3rem !important;}
</style>
""", unsafe_allow_html=True)

st.title("📊 RANGEN Monitor")

st.markdown("---")
st.info("💡 需要智能对话？访问 [RANGEN 智能助手](http://localhost:8505)")

st.markdown("---")

health_resp = get_with_auth(f"{RANGEN_API_BASE}/health")
agents_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/agents")
skills_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/skills")
tools_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/tools")
resource_resp = get_with_auth(f"{RANGEN_API_BASE}/health/resource")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📈 概览", "💻 资源", "🧩 组件", "🔌 接口", "⚡ 执行", "💵 安全与成本", "🔗 集成", "📊 评估", "📋 SOP"
])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    health_ok = health_resp and health_resp.status_code == 200
    with c1:
        st.metric("API", "🟢 在线" if health_ok else "🔴 离线")
    with c2:
        a_count = agents_resp.json().get("total", 0) if agents_resp and agents_resp.status_code == 200 else 0
        st.metric("🤖 Agents", a_count)
    with c3:
        s_count = skills_resp.json().get("total", 0) if skills_resp and skills_resp.status_code == 200 else 0
        st.metric("🌟 Skills", s_count)
    with c4:
        t_count = tools_resp.json().get("total", 0) if tools_resp and tools_resp.status_code == 200 else 0
        st.metric("🔧 Tools", t_count)
    
    st.markdown("---")
    st.subheader("🧠 RANGEN 核心能力")
    
    col_cap1, col_cap2, col_cap3 = st.columns(3)
    
    with col_cap1:
        st.markdown("""
        <div class="capability-section">
            <h4>🤖 智能体系统</h4>
            <p>30+ 专业Agent：推理Agent、验证Agent、引用Agent、RAG Agent、日本/中国市场Agent</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="capability-section">
            <h4>⚡ 执行引擎</h4>
            <p>LangGraph工作流、智能路由、上下文管理、ReAct推理循环</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_cap2:
        st.markdown("""
        <div class="capability-section">
            <h4>🔧 工具生态</h4>
            <p>40+ Tools：MCP工具、Skill技能、浏览器自动化、代码执行沙箱</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="capability-section">
            <h4>🌐 多渠道接入</h4>
            <p>Gateway：Slack/Telegram/WhatsApp/WebChat、REST API、Streamlit管理界面</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_cap3:
        st.markdown("""
        <div class="capability-section">
            <h4>📊 质量保障</h4>
            <p>成本控制、Token预算管理、安全控制、持续学习ML优化</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="capability-section">
            <h4>🔌 标准化接口</h4>
            <p>MCP协议、外部集成、模型管理(DeepSeek/Llama/Qwen)、SOP标准化流程</p>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("📋 快捷操作"):
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

with tab2:
    if resource_resp and resource_resp.status_code == 200:
        resources = resource_resp.json().get("resources", {})
        memory = resources.get("memory", {})
        cpu = resources.get("cpu", {})
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("内存", f"{memory.get('system_percent', 0):.1f}%")
        with c2:
            st.metric("内存(已用)", f"{memory.get('system_used_mb', 0)/1024:.1f} GB")
        with c3:
            st.metric("CPU", f"{cpu.get('system_percent', 0):.1f}%")
        with c4:
            st.metric("CPU(进程)", f"{cpu.get('process_percent', 0):.1f}%")
        
        with st.expander("📋 详细资源信息"):
            st.json(resources)
    else:
        st.error("❌ 无法获取资源信息")

with tab3:
    col_a, col_s, col_t = st.columns(3)
    
    with col_a:
        st.subheader("🤖 Agent 类型分布")
        if agents_resp and agents_resp.status_code == 200:
            agents_data = agents_resp.json()
            type_count = {}
            for agent in agents_data.get("agents", []):
                t = agent.get("type", "unknown")
                type_count[t] = type_count.get(t, 0) + 1
            for t, c in sorted(type_count.items(), key=lambda x: -x[1])[:10]:
                st.write(f"**{t}**: {c}")
        else:
            st.write("暂无数据")
    
    with col_s:
        st.subheader("🌟 Skill 分类分布")
        if skills_resp and skills_resp.status_code == 200:
            skills_data = skills_resp.json()
            skill_category = {
                "测试": 0, "编程": 0, "数据": 0, "项目": 0, 
                "文档": 0, "CI/CD": 0, "需求": 0, "架构": 0, "其他": 0
            }
            for skill in skills_data.get("skills", []):
                name = skill.get("name", "").lower()
                desc = skill.get("description", "").lower()
                text = name + " " + desc
                if "测试" in text or "test" in text:
                    skill_category["测试"] += 1
                elif "编程" in text or "开发" in text or "code" in text or "programming" in text:
                    skill_category["编程"] += 1
                elif "数据" in text or "data" in text or "sql" in text or "机器学习" in text or "ml" in text:
                    skill_category["数据"] += 1
                elif "项目" in text or "project" in text or "管理" in text:
                    skill_category["项目"] += 1
                elif "文档" in text or "document" in text:
                    skill_category["文档"] += 1
                elif "ci" in text or "cd" in text or "持续集成" in text or "部署" in text:
                    skill_category["CI/CD"] += 1
                elif "需求" in text or "requirement" in text:
                    skill_category["需求"] += 1
                elif "架构" in text or "architecture" in text or "系统设计" in text:
                    skill_category["架构"] += 1
                else:
                    skill_category["其他"] += 1
            for cat, count in sorted(skill_category.items(), key=lambda x: -x[1]):
                if count > 0:
                    st.write(f"**{cat}**: {count}")
        else:
            st.write("暂无数据")
    
    with col_t:
        st.subheader("🔧 Tool 功能分布")
        if tools_resp and tools_resp.status_code == 200:
            tools_data = tools_resp.json()
            tool_category = {
                "检索": 0, "搜索": 0, "浏览器": 0, "执行": 0,
                "RAG": 0, "多模态": 0, "策略": 0, "注册": 0, "其他": 0
            }
            for tool in tools_data.get("tools", []):
                name = tool.get("name", "").lower()
                desc = tool.get("description", "").lower()
                text = name + " " + desc
                if "retriev" in text or "knowledge" in text or "rag" in text:
                    tool_category["检索"] += 1
                elif "search" in text:
                    tool_category["搜索"] += 1
                elif "browser" in text or "web" in text:
                    tool_category["浏览器"] += 1
                elif "execut" in text or "calculator" in text:
                    tool_category["执行"] += 1
                elif "rag" in text:
                    tool_category["RAG"] += 1
                elif "multi" in text or "image" in text or "vision" in text:
                    tool_category["多模态"] += 1
                elif "policy" in text or "approval" in text:
                    tool_category["策略"] += 1
                elif "regist" in text or "init" in text:
                    tool_category["注册"] += 1
                else:
                    tool_category["其他"] += 1
            for cat, count in sorted(tool_category.items(), key=lambda x: -x[1]):
                if count > 0:
                    st.write(f"**{cat}**: {count}")
        else:
            st.write("暂无数据")

with tab4:
    st.subheader("🔌 API 接口状态")
    endpoints = [
        ("/", "根路径"),
        ("/health", "健康检查"),
        ("/health/resource", "资源监控"),
        ("/api/v1/agents", "Agent管理"),
        ("/api/v1/skills", "Skill管理"),
        ("/api/v1/tools", "Tool管理"),
        ("/sops", "SOP流程"),
        ("/api/v1/cost/providers", "成本控制"),
        ("/api/v1/security/status", "安全控制"),
        ("/api/v1/sandbox/status", "沙箱"),
        ("/mcp/status", "MCP服务"),
        ("/api/v1/models/switch/available", "模型管理"),
    ]
    
    cols = st.columns(3)
    
    for i, (endpoint, name) in enumerate(endpoints):
        resp = get_with_auth(f"{RANGEN_API_BASE}{endpoint}")
        with cols[i % 3]:
            if resp is None:
                st.error(f"🔴 {name} - 离线")
            elif resp.status_code == 200:
                st.success(f"🟢 {name} - 在线")
            elif resp.status_code == 401:
                st.warning(f"🔐 {name} - 未授权")
            else:
                st.warning(f"🟡 {name} - 部分可用 ({resp.status_code})")
    
    st.info("💡 发现接口异常？请使用页面顶部的「🤖 智能诊断与修复助手」")

with tab5:
    st.subheader("⚡ 执行状态")
    
    routing_resp = get_with_auth(f"{RANGEN_API_BASE}/api/routing/statistics")
    if routing_resp and routing_resp.status_code == 200:
        routing_data = routing_resp.json()
        
        c1, c2, c3 = st.columns(3)
        with c1:
            total = routing_data.get("total_decisions", 0)
            st.metric("📊 总决策数", total)
        with c2:
            success = routing_data.get("successful_decisions", 0)
            st.metric("✅ 成功", success)
        with c3:
            failed = routing_data.get("failed_decisions", 0)
            st.metric("❌ 失败", failed)
        
        with st.expander("📋 详细路由统计"):
            st.json(routing_data)
    else:
        st.info("📊 路由统计: 暂无数据（系统未执行过路由决策）")
    
    st.info("💡 需要执行操作？请使用页面顶部的「🤖 智能诊断与修复助手」")
    
    st.markdown("---")
    st.subheader("🧪 测试执行")
    
    test_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/test/execute")
    if test_resp and test_resp.status_code == 200:
        test_data = test_resp.json()
        st.write(f"✅ 测试执行已就绪")
        st.write(f"**说明**: 可通过 POST /api/v1/test/execute 触发测试")
    else:
        st.info("🧪 测试执行: 暂无执行记录")

with tab6:
    st.subheader("💵 安全与成本")
    
    cost_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/cost/providers")
    if cost_resp and cost_resp.status_code == 200:
        providers = cost_resp.json().get("providers", [])
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("💰 LLM供应商", len(providers))
        
        provider_names = [p.get("name", "N/A") for p in providers]
        st.write("**可用供应商:**")
        for name in provider_names:
            st.write(f"   • {name}")
        
        with st.expander("Pricing Details"):
            for p in providers:
                pricing = p.get("pricing", {})
                st.write(f"   **{p.get('name')}**: Input \\${pricing.get('input_per_million',0)}/M tokens, Output \\${pricing.get('output_per_million',0)}/M tokens")
    else:
        st.info("💰 成本控制: 暂无数据")
    
    st.markdown("---")
    
    security_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/security/status")
    if security_resp and security_resp.status_code == 200:
        sec_data = security_resp.json()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            level = sec_data.get("security_level", "unknown")
            level_emoji = "🔴" if level == "high" else "🟡" if level == "medium" else "🟢"
            st.metric("🔒 安全级别", f"{level_emoji} {level}")
        with c2:
            pending = sec_data.get("pending_requests", 0)
            st.metric("⏳ 待审批", pending)
        with c3:
            whitelist = sec_data.get("whitelist_entries", 0)
            st.metric("📝 白名单", whitelist)
        with c4:
            api_key_protected = sec_data.get("api_key_protected", False)
            st.metric("🔑 API密钥", "已保护" if api_key_protected else "未保护")
    else:
        st.info("🔒 安全控制: 暂无数据")
    
    st.markdown("---")
    
    sandbox_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/sandbox/status")
    if sandbox_resp and sandbox_resp.status_code == 200:
        sand_data = sandbox_resp.json()
        
        c1, c2 = st.columns(2)
        with c1:
            enabled = sand_data.get("enabled", False)
            st.metric("📦 沙箱", "✅ 已启用" if enabled else "❌ 已禁用")
        with c2:
            exec_count = sand_data.get("executions", 0)
            st.metric("🔄 执行次数", exec_count)
        
        types = sand_data.get("types", [])
        if types:
            st.write("**支持的沙箱类型:**")
            for t in types:
                st.write(f"   • {t}")
    else:
        st.info("📦 沙箱状态: 暂无数据")

with tab7:
    st.subheader("🔗 集成状态")
    
    mcp_resp = get_with_auth(f"{RANGEN_API_BASE}/mcp/status")
    if mcp_resp and mcp_resp.status_code == 200:
        mcp_data = mcp_resp.json()
        
        c1, c2 = st.columns(2)
        with c1:
            status = mcp_data.get("status", "unknown")
            st.metric("🔌 MCP状态", "✅ 运行中" if status == "running" else "⏹️ 已停止")
        with c2:
            servers = mcp_data.get("servers", [])
            st.metric("🖥️ 服务器", len(servers))
        
        if servers:
            st.write("**MCP服务器:**")
            for s in servers:
                st.write(f"   • {s.get('name', 'N/A')}: {s.get('status', 'unknown')}")
    else:
        st.info("🔌 MCP 服务器: 暂无数据")
    
    st.markdown("---")
    
    external_resp = get_with_auth(f"{RANGEN_API_BASE}/external/integrations")
    if external_resp and external_resp.status_code == 200:
        ext_data = external_resp.json()
        
        c1 = st.columns(1)[0]
        st.metric("🌍 外部集成", len(ext_data) if isinstance(ext_data, list) else "N/A")
        
        if isinstance(ext_data, list) and ext_data:
            st.write("**已集成的服务:**")
            for e in ext_data[:5]:
                st.write(f"   • {e.get('name', e.get('type', 'N/A'))}")
    else:
        st.info("🌍 外部集成: 暂无数据")
    
    st.markdown("---")
    
    model_resp = get_with_auth(f"{RANGEN_API_BASE}/api/v1/models/switch/available")
    if model_resp and model_resp.status_code == 200:
        model_data = model_resp.json()
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🤖 可用模型", len(model_data))
        with c2:
            current = get_with_auth(f"{RANGEN_API_BASE}/api/v1/models/switch/current")
            if current and current.status_code == 200:
                curr_model = current.json().get("display_name", current.json().get("name", "N/A"))
                st.metric("⚡ 当前模型", curr_model)
            else:
                st.metric("⚡ 当前模型", "未设置")
        
        st.write("**模型列表:**")
        for m in model_data:
            name = m.get("display_name", m.get("name", "N/A"))
            provider = m.get("provider_name", "N/A")
            is_default = "⭐" if m.get("is_default", False) else ""
            context = m.get("context_length", 0) // 1000
            st.write(f"   • {name} ({provider}) {is_default} | 上下文: {context}K")
    else:
        st.info("🤖 可用模型: 暂无数据")

with tab8:
    st.subheader("📊 System Evaluation")
    
    col_eval1, col_eval2 = st.columns([1, 3])
    
    with col_eval1:
        eval_desc_html = """
        <div style="height: 200px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 12px; background: #fafafa;">
            <h4 style="margin-top: 0; color: #333;">📋 评估类型说明</h4>
            <div>
                <b>📡 端到端集成测试 (E2E)</b><br/>
                <span style="color: #666; font-size: 13px;">通过真实API调用验证系统能力:</span><br/>
                <span style="font-size: 12px; color: #555;">
                • 编排能力 · Agent完整性 · Prompt工程<br/>
                • 响应质量 · 路由机制 · 推理能力<br/>
                • 知识召回 · 工具调用 · 多轮对话<br/>
                • 监控告警 · 故障自愈 · 安全防护<br/>
                • 数据管理 · 成本控制 · 集成扩展
                </span>
            </div>
            <br/>
            <div>
                <b>🔍 静态代码分析</b><br/>
                <span style="color: #666; font-size: 13px;">分析源码结构验证系统质量:</span><br/>
                <span style="font-size: 12px; color: #555;">
                • 架构合理性：模块结构、分层设计<br/>
                • 代码质量：复杂度、文档、测试覆盖
                </span>
            </div>
            <br/>
            <div style="border-top: 1px solid #ddd; padding-top: 8px; margin-top: 8px;">
                <span style="font-size: 12px; color: #888;">
                共 <b>26个维度</b>：<br/>
                • E2E测试: 24个维度 (79个测试用例)<br/>
                • 静态分析: 2个维度
                </span>
            </div>
        </div>
        """
        st.html(eval_desc_html)
    
    with col_eval2:
        st.write("**Run Evaluation**")
        
        col1, col2 = st.columns(2)
        with col1:
            sample_count = st.selectbox("样本数", ["1", "3", "5", "10", "20"], index=1, key="sample_count")
        with col2:
            max_concurrent = st.selectbox("并发数", ["1", "2", "3", "5", "10"], index=2, key="max_concurrent")
        
        use_real_api = st.toggle("真实API测试 (E2E)", value=True, help="开启后调用真实DeepSeek API进行测试")
        
        if st.button("🚀 Run Full Evaluation", type="primary", use_container_width=True):
            with st.spinner("正在运行全部评估..."):
                try:
                    project_root = "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
                    
                    # 运行完整评估（E2E + 静态分析）
                    cmd = [
                        "python", "-m", "evaluation.main",
                        "--mode", "all",
                        "--sample-count", str(sample_count),
                        "--max-concurrent", str(max_concurrent),
                        "--output", f"/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/evaluation/v2_capability/results/unified_evaluation.json"
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=project_root, env=os.environ.copy())
                    
                    if result.returncode == 0:
                        st.success("✅ 评估完成！")
                        st.session_state.eval_results_updated = True
                    else:
                        st.error(f"评估失败: {result.stderr[:500]}")
                        st.session_state.eval_results_updated = None
                except Exception as e:
                    st.error(f"评估执行出错: {str(e)}")
                    st.session_state.eval_results_updated = None
        
        # 显示评估结果
        if 'eval_results_updated' not in st.session_state:
            st.session_state.eval_results_updated = None
        
        result_file = "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/evaluation/v2_capability/results/unified_evaluation.json"
        if os.path.exists(result_file):
            try:
                import json
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                st.markdown("---")
                st.write("### 📊 评估结果 (26个维度)")
                
                overall = data.get("overall_score", 0)
                dim_count = data.get("dimensions_tested", 0)
                timestamp = data.get("summary", {}).get("timestamp", "N/A")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("综合评分", f"{overall*100:.1f}%")
                with col2:
                    st.metric("评估维度", f"{dim_count}个")
                with col3:
                    passed = data.get("summary", {}).get("passed", 0)
                    st.metric("通过", f"{passed}个")
                with col4:
                    failed = data.get("summary", {}).get("failed", 0)
                    st.metric("待改进", f"{failed}个")
                
                st.markdown("---")
                st.write("### 📊 评估维度详情")
                
                # E2E维度映射
                e2e_dims = [
                    {"name": "编排能力", "icon": "🔄", "id": "orchestration"},
                    {"name": "Agent完备性", "icon": "🤖", "id": "agent_completeness"},
                    {"name": "Prompt工程", "icon": "💬", "id": "prompt_engineering"},
                    {"name": "上下文工程", "icon": "🧠", "id": "context_engineering"},
                    {"name": "响应质量", "icon": "✨", "id": "response_quality"},
                    {"name": "路由机制", "icon": "🛤️", "id": "routing"},
                    {"name": "推理能力", "icon": "🧩", "id": "reasoning"},
                    {"name": "知识召回", "icon": "📚", "id": "knowledge_recall"},
                    {"name": "工具调用", "icon": "🔧", "id": "tool_calling"},
                    {"name": "多轮对话", "icon": "💭", "id": "multi_turn"},
                    {"name": "自学习能力", "icon": "📈", "id": "self_learning"},
                    {"name": "Harness治理", "icon": "🛡️", "id": "harness"},
                    {"name": "可观测性", "icon": "👁️", "id": "observability"},
                    {"name": "监控告警", "icon": "🚨", "id": "monitoring"},
                    {"name": "故障自愈", "icon": "🔄", "id": "self_healing"},
                    {"name": "灰度发布", "icon": "🚀", "id": "rollout"},
                    {"name": "数据源接入", "icon": "🗄️", "id": "data_source"},
                    {"name": "知识管理", "icon": "📖", "id": "knowledge_mgmt"},
                    {"name": "向量管理", "icon": "📐", "id": "vector_mgmt"},
                    {"name": "数据血缘", "icon": "🔗", "id": "data_lineage"},
                    {"name": "应用支撑", "icon": "🏗️", "id": "app_support"},
                    {"name": "成本控制", "icon": "💰", "id": "cost_control"},
                    {"name": "集成扩展", "icon": "🔌", "id": "integration"},
                    {"name": "安全能力", "icon": "🔒", "id": "security"},
                ]
                
                # 静态分析维度
                static_dims = [
                    {"name": "架构合理性", "icon": "🏛️", "id": "architecture"},
                    {"name": "代码质量", "icon": "📝", "id": "code_quality"},
                ]
                
                dim_results = data.get("dimension_results", {})
                
                # E2E测试部分
                st.markdown("**📡 端到端集成测试 (E2E)**")
                e2e_cols = st.columns(6)
                for idx, dim in enumerate(e2e_dims):
                    dim_id = dim["id"]
                    dim_result = dim_results.get(dim_id, {})
                    score = dim_result.get("score", 0)
                    status_icon = "🌟" if score >= 0.9 else "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                    
                    with e2e_cols[idx % 6]:
                        st.markdown(f"{dim['icon']} {dim['name']}<br>{status_icon} {score*100:.0f}%", unsafe_allow_html=True)
                
                # 静态分析部分
                st.markdown("---")
                st.markdown("**🔍 静态代码分析**")
                static_cols = st.columns(2)
                for idx, dim in enumerate(static_dims):
                    dim_id = dim["id"]
                    dim_result = dim_results.get(dim_id, {})
                    score = dim_result.get("score", 0)
                    status_icon = "🌟" if score >= 0.9 else "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                    
                    with static_cols[idx % 2]:
                        st.markdown(f"{dim['icon']} **{dim['name']}** - {status_icon} {score*100:.0f}%")
                        
                        # 显示检查项详情
                        checks = dim_result.get("checks", [])
                        if checks:
                            for check in checks:
                                check_icon = "✅" if check.get("passed") else "❌"
                                st.caption(f"&nbsp;&nbsp;{check_icon} {check.get('name', '')}: {check.get('score', 0)*100:.0f}%")
                
                # 详细结果展开
                st.markdown("---")
                with st.expander("📋 详细评估结果", expanded=False):
                    for dim in e2e_dims + static_dims:
                        dim_id = dim["id"]
                        dim_result = dim_results.get(dim_id, {})
                        if dim_result:
                            score = dim_result.get("score", 0)
                            test_count = dim_result.get("test_count", 0) or len(dim_result.get("checks", []))
                            test_type = "📡 E2E" if dim_id not in ["architecture", "code_quality"] else "🔍 静态"
                            
                            st.markdown(f"**{dim['icon']} {dim['name']}** [{test_type}] - {score*100:.1f}%")
                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;测试项: {test_count}个")
                
            except Exception as e:
                st.warning(f"无法解析评估结果: {e}")
        else:
            st.info("请点击上方按钮运行评估")
            st.caption(f"结果文件: {result_file}")

with tab9:
    st.subheader("📋 SOP 标准流程")
    
    sops_resp = get_with_auth(f"{RANGEN_API_BASE}/sops/statistics/stats")
    if sops_resp and sops_resp.status_code == 200:
        sops_data = sops_resp.json()
        stats = sops_data.get("statistics", {})
        total = stats.get("total_sops", "N/A")
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("📊 SOP 总数", total)
        with col_stat2:
            quality = stats.get("average_quality_score", 0)
            quality_status = "✅ 良好" if quality >= 0.7 else "⚠️ 一般" if quality >= 0.3 else "❌ 需改进"
            st.metric("⭐ 质量评分", f"{quality*100:.0f}%", quality_status)
        
        by_category = stats.get("by_category", {})
        if by_category:
            st.write("📂 **按类别分布:**")
            for cat, count in by_category.items():
                st.write(f"   • {cat}: {count}")
        
        by_level = stats.get("by_level", {})
        if by_level:
            st.write("📑 **按级别分布:**")
            for level, count in by_level.items():
                st.write(f"   • {level}: {count}")
        
        st.markdown("---")
        st.subheader("🔍 SOP 质量问题详情")
        
        sop_list_resp = get_with_auth(f"{RANGEN_API_BASE}/sops")
        if sop_list_resp and sop_list_resp.status_code == 200:
            sop_list = sop_list_resp.json().get("sops", [])
            for sop in sop_list:
                sop_id = sop.get("sop_id")
                sop_name = sop.get("name", sop_id)
                
                sop_detail_resp = get_with_auth(f"{RANGEN_API_BASE}/sops/{sop_id}")
                if sop_detail_resp and sop_detail_resp.status_code == 200:
                    sop_detail = sop_detail_resp.json().get("sop", {})
                    quality_data = sop_detail_resp.json().get("quality", {})
                    
                    with st.expander(f"📋 {sop_name}"):
                        q_score = quality_data.get("quality_score", 0)
                        step_complete = quality_data.get("step_completeness", 0)
                        exec_count = quality_data.get("execution_count", 0)
                        success_rate = quality_data.get("success_rate", 0)
                        is_valid = quality_data.get("is_valid", False)
                        validation_errors = quality_data.get("validation_errors", [])
                        
                        q_col1, q_col2, q_col3 = st.columns(3)
                        with q_col1:
                            st.metric("质量分数", f"{q_score*100:.0f}%")
                        with q_col2:
                            st.metric("步骤完整度", f"{step_complete*100:.0f}%")
                        with q_col3:
                            st.metric("执行次数", exec_count)
                        
                        st.write(f"**状态:** {'✅ 有效' if is_valid else '❌ 无效'}")
                        st.write(f"**成功率:** {success_rate*100:.0f}%")
                        
                        if validation_errors:
                            st.write("**❌ 验证错误:**")
                            for err in validation_errors:
                                st.write(f"   - {err}")
                        
                        suggestions = quality_data.get("suggestions", [])
                        if suggestions:
                            st.write("**💡 改进建议:**")
                            for sug in suggestions:
                                priority_emoji = "🔴" if sug.get("priority") == "high" else "🟡" if sug.get("priority") == "medium" else "🟢"
                                st.write(f"   {priority_emoji} {sug.get('description', '')}")
    else:
        st.info("暂无 SOP 数据")

st.caption(f"🕐 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
