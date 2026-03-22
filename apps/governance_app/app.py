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
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .metric-box {background: #1E3A5F; border-radius: 8px; padding: 10px; text-align: center;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E3A5F 0%, #2D5A87 100%);
        padding: 15px;
        border-radius: 10px;
        color: white !important;
    }
    div[data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.8) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    div[data-testid="stMetricDelta"] {
        color: #90EE90 !important;
    }
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {
        background: #E8EEF4;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #1E3A5F !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #1E3A5F !important;
        color: white !important;
    }
    .stTabs [aria-selected="false"] {color: #1E3A5F !important;}
    hr {margin: 1rem 0;}
    h3 {color: #1E3A5F; margin-top: 1rem;}
    .capability-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }
    .capability-section h4 {
        color: #1E3A5F;
        margin: 0 0 8px 0;
        font-size: 1rem;
    }
    .capability-section p {
        color: #495057;
        margin: 0;
        font-size: 0.85rem;
    }
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
    st.subheader("System Evaluation")
    
    st.write("**RANGEN Evaluation System**")
    st.write("Run benchmark tests, performance evaluations and quality analysis")
    
    col_eval1, col_eval2 = st.columns(2)
    
    with col_eval1:
        st.info("""
        **Evaluation Types:**
        - FRAMES Benchmark
        - Unified Evaluation
        - Performance Evaluation
        - Quality Analysis
        """)
    
    with col_eval2:
        st.write("**Run Evaluation**")
        
        col_eval_type, col_sample, col_concurrent, col_max_files = st.columns(4)
        
        with col_eval_type:
            eval_type = st.selectbox(
                "Evaluation type",
                ["frames", "unified", "performance", "intelligent_quality", "new_framework"],
                index=4
            )
        
        with col_sample:
            sample_count = st.selectbox(
                "Samples",
                ["1", "3", "5", "10", "20"],
                index=1
            )
        
        with col_concurrent:
            max_concurrent = st.selectbox(
                "Parallel",
                ["1", "2", "3", "5", "10"],
                index=2
            )
        
        with col_max_files:
            max_files = st.selectbox(
                "Max files",
                ["10", "20", "30", "50"],
                index=0
            )
        
        if st.button("Run Evaluation", type="primary"):
            with st.spinner("Evaluating..."):
                try:
                    project_root = "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
                    cmd = None
                    
                    if eval_type == "frames":
                        cmd = ["python", f"{project_root}/evaluation/run_frames_evaluation.py", "--sample-count", sample_count, "--max-concurrent", max_concurrent, "--max-files", max_files]
                    elif eval_type == "unified":
                        cmd = ["python", f"{project_root}/evaluation/run_evaluation.py", "--type", "unified", "--sample-count", sample_count, "--max-concurrent", max_concurrent, "--max-files", max_files]
                    elif eval_type == "performance":
                        cmd = ["python", f"{project_root}/evaluation/run_evaluation.py", "--type", "performance", "--sample-count", sample_count, "--max-concurrent", max_concurrent, "--max-files", max_files]
                    elif eval_type == "intelligent_quality":
                        cmd = ["python", f"{project_root}/evaluation/run_evaluation.py", "--type", "intelligent_quality", "--max-files", max_files]
                    elif eval_type == "new_framework":
                        cmd = ["python", "-c", f"""
import asyncio
import sys
sys.path.insert(0, '{project_root}/evaluation/new_framework')
from runner import RANGENEvaluator
asyncio.run(RANGENEvaluator().run_full_evaluation())
"""]
                    
                    if cmd is None:
                        st.warning("Invalid evaluation type")
                    else:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=600,
                            cwd=project_root
                        )
                        
                        if result.returncode == 0:
                            st.success("Evaluation completed successfully!")
                            
                            if eval_type == "intelligent_quality":
                                    report_path = os.path.join(project_root, "comprehensive_eval_results/intelligent_quality_analysis_report.md")
                                    if os.path.exists(report_path):
                                        try:
                                            with open(report_path, 'r', encoding='utf-8') as f:
                                                content = f.read()
                                            
                                            import re
                                            score_pattern = r'\*\*([^\*]+)\*\*:\s*([0-9.]+)'
                                            scores = re.findall(score_pattern, content)
                                            
                                            if scores:
                                                all_scores = {}
                                                for name, value in scores:
                                                    name = name.strip()
                                                    try:
                                                        all_scores[name] = float(value)
                                                    except:
                                                        pass
                                                
                                                st.write("### 📊 质量分析结果")
                                                
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("🧠 智能质量", f"{all_scores.get('智能质量分数', 0):.3f}" if '智能质量分数' in all_scores else "N/A")
                                                    st.metric("🏗️ 架构质量", f"{all_scores.get('架构质量分数', 0):.3f}" if '架构质量分数' in all_scores else "N/A")
                                                with col2:
                                                    st.metric("🔒 安全质量", f"{all_scores.get('安全质量分数', 0):.3f}" if '安全质量分数' in all_scores else "N/A")
                                                    st.metric("⚡ 性能质量", f"{all_scores.get('性能质量分数', 0):.3f}" if '性能质量分数' in all_scores else "N/A")
                                                with col3:
                                                    st.metric("💻 代码质量", f"{all_scores.get('代码质量分数', 0):.3f}" if '代码质量分数' in all_scores else "N/A")
                                                
                                                st.markdown("---")
                                                
                                                with st.expander("📋 详细评分表格"):
                                                    exclude_patterns = ["数量", "问题", "检测", "分数:", "生成时间", "分析文件数", "分析模式", "nTc机制", "证据积累", "决策承诺", "几何化轨迹", "动态阈值", "承诺锁定"]
                                                    meaningful_scores = []
                                                    
                                                    category_mapping = {
                                                        "智能质量分数": "基础质量",
                                                        "架构质量分数": "基础质量",
                                                        "安全质量分数": "基础质量",
                                                        "性能质量分数": "基础质量",
                                                        "代码质量分数": "基础质量",
                                                        "大脑决策机制分数": "大脑决策",
                                                        "ML-RL协同作用分数": "ML/RL",
                                                        "提示词-上下文协同分数": "提示词",
                                                        "复杂推理能力分数": "推理能力",
                                                        "查询处理流程分数": "查询处理",
                                                        "智能维度综合分数": "智能维度",
                                                        "上下文管理分数": "上下文",
                                                        "系统监控分数": "系统监控",
                                                        "配置管理分数": "配置管理",
                                                        "评分评估分数": "评分评估",
                                                        "安全防护分数": "安全防护",
                                                        "系统集成分数": "系统集成",
                                                        "数据管理分数": "数据管理",
                                                        "学习能力综合分数": "学习能力",
                                                        "业务价值分数": "业务逻辑",
                                                    }
                                                    
                                                    suggestions = {
                                                        "智能质量分数": "增加智能推理模块，优化决策逻辑",
                                                        "架构质量分数": "优化代码结构，减少过度设计",
                                                        "安全质量分数": "加强安全检查和权限控制",
                                                        "性能质量分数": "优化算法复杂度，减少阻塞操作",
                                                        "代码质量分数": "改善代码规范，减少重复代码",
                                                        "大脑决策机制分数": "实现nTc机制、证据积累、决策承诺",
                                                        "ML-RL协同作用分数": "加强ML和RL模块的协同",
                                                        "提示词-上下文协同分数": "优化提示词设计",
                                                        "复杂推理能力分数": "增强复杂问题处理能力",
                                                        "查询处理流程分数": "优化查询理解和处理流程",
                                                        "智能维度综合分数": "提升系统智能水平",
                                                        "上下文管理分数": "优化上下文窗口管理",
                                                        "系统监控分数": "完善监控指标和告警",
                                                        "配置管理分数": "改进配置管理机制",
                                                        "评分评估分数": "完善评分和评估体系",
                                                        "安全防护分数": "加强安全防护措施",
                                                        "系统集成分数": "改进系统集成方案",
                                                        "数据管理分数": "优化数据存储和处理",
                                                        "学习能力综合分数": "增强系统自学习能力",
                                                        "业务价值分数": "提升业务逻辑实现",
                                                    }
                                                    
                                                    for name, value in scores:
                                                        if any(p in name for p in exclude_patterns):
                                                            continue
                                                        try:
                                                            float_val = float(value)
                                                            category = category_mapping.get(name, "其他")
                                                            suggestion = suggestions.get(name, "建议优化") if float_val < 0.7 else "良好"
                                                            meaningful_scores.append((name, f"{float_val:.3f}", category, suggestion))
                                                        except:
                                                            pass
                                                    
                                                    if meaningful_scores:
                                                        table_md = "| 指标 | 分数 | 质量类别 | 质量问题及解决方式 |\n|------|------|----------|--------------------|\n"
                                                        for name, value, category, suggestion in meaningful_scores:
                                                            table_md += f"| {name} | {value} | {category} | {suggestion} |\n"
                                                        st.markdown(table_md)
                                        except Exception as e:
                                            st.warning(f"无法解析评估报告: {e}")
                            
                            elif eval_type == "new_framework":
                                import json
                                result_path = os.path.join(project_root, "evaluation_results")
                                import glob
                                new_framework_files = glob.glob(os.path.join(result_path, "new_framework_*.json"))
                                if new_framework_files:
                                    latest_file = max(new_framework_files, key=os.path.getmtime)
                                    try:
                                        with open(latest_file, 'r', encoding='utf-8') as f:
                                            data = json.load(f)
                                        
                                        st.write("### 📊 新评估框架结果")
                                        
                                        overall = data.get("overall_score", 0)
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("综合评分", f"{overall*100:.1f}%")
                                        with col2:
                                            completed = data.get("completed_count", 0)
                                            total = data.get("evaluator_count", 0)
                                            st.metric("评估维度", f"{completed}/{total}")
                                        with col3:
                                            st.metric("评估时间", data.get("timestamp", "N/A")[:19])
                                        
                                        st.markdown("---")
                                        st.write("#### 各维度评分")
                                        
                                        dims = data.get("dimensions", {})
                                        dim_cols = st.columns(3)
                                        col_idx = 0
                                        for dim_name, dim_data in dims.items():
                                            score = dim_data.get("score", 0)
                                            status = dim_data.get("status", "unknown")
                                            details = dim_data.get("details", "")
                                            
                                            with dim_cols[col_idx % 3]:
                                                status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏭️"
                                                st.metric(f"{status_icon} {dim_name}", f"{score*100:.1f}%", details)
                                            
                                            col_idx += 1
                                            
                                    except Exception as e:
                                        st.warning(f"无法解析新评估结果: {e}")
                                else:
                                    st.info("未找到新评估框架的结果文件")
                            
                            if result.stdout:
                                with st.expander("查看原始输出"):
                                    st.text(result.stdout[:5000])
                        else:
                            st.error("Evaluation failed")
                            if result.stderr:
                                with st.expander("View Error"):
                                    st.text(result.stderr[:2000])
                except subprocess.TimeoutExpired:
                    st.warning("Timed out - try fewer samples or run manually")
                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")
    
    st.markdown("---")
    st.write("**Manual Run**")
    st.info("You can also run evaluation manually in terminal:")
    st.code(f"cd {os.path.expanduser('~')}/workdata/person/zy/RANGEN-main\\(syu-python\\)")
    st.code("python evaluation/run_evaluation.py --type quality")
    
    st.markdown("---")
    st.write("**Evaluation Results Location**")
    st.code("evaluation/results/")
    st.code("evaluation/comprehensive_eval_results/")

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
