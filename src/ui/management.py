"""
AI中台管理界面 - Streamlit UI for comprehensive system management
"""
import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def render_mermaid(mermaid_code: str, height: int = 400):
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
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
        </script>
    </body>
    </html>
    """
    import base64
    b64 = base64.b64encode(html_code.encode('utf-8')).decode('utf-8')
    st.markdown(
        f'<iframe src="data:text/html;base64,{b64}" width="100%" height="{height+50}px" style="border:none; border-radius:10px;"></iframe>',
        unsafe_allow_html=True
    )

from src.ui.discovery_helper import (
    discover_agents_from_registry,
    discover_skills_from_registry,
    discover_tools_from_registry,
    discover_teams_from_registry,
    discover_services_from_registry,
    discover_workflows_from_registry,
    discover_gateways_from_registry,
    discover_ml_components,
    discover_configs,
    discover_models,
    discover_tests,
    discover_evaluations,
    read_skill_yaml,
    save_skill_yaml,
    test_skill,
    test_agent,
    test_tool,
    test_team,
    test_workflow,
    test_service,
    analyze_skill_triggers,
    optimize_skill_triggers,
    optimize_skill_description,
    validate_skill_quality,
    optimize_agent,
    optimize_tool,
    optimize_team,
    optimize_workflow,
    optimize_service,
    optimize_skill,
    get_system_modules,
    test_system_module,
    optimize_system_module
)

try:
    from src.ui.test_framework import generate_coverage_report, analyze_coverage
except ImportError:
    generate_coverage_report = None
    analyze_coverage = None

# 导入统一创建服务
try:
    from src.services.unified_creator import UnifiedCreator
    unified_creator = UnifiedCreator()
except ImportError:
    unified_creator = None


# 优化函数映射表
OPTIMIZE_FUNCTIONS = {
    'Skill': optimize_skill,
    'Agent': optimize_agent,
    'Tool': optimize_tool,
    'Team': optimize_team,
    'Workflow': optimize_workflow,
    'Service': optimize_service,
    'system_module': optimize_system_module
}


def render_test_ui(item_name: str, test_func, items: list, session_key: str, optimize_func=None):
    """通用测试UI渲染函数"""
    items_by_type = {}
    for s in items:
        t = s.get('type', 'unknown')
        if t not in items_by_type:
            items_by_type[t] = []
        items_by_type[t].append(s)
    
    if f'selected_{session_key}' not in st.session_state:
        st.session_state[f'selected_{session_key}'] = items[0]['name'] if items else None
    
    selected_item = st.session_state[f'selected_{session_key}']
    current_item = next((s for s in items if s['name'] == selected_item), None)
    
    col1, col2 = st.columns([2, 0.7])
    with col1:
        item_names = [s['name'] for s in items]
        new_selected = st.selectbox(
            f"选择 {item_name}", 
            item_names, 
            index=item_names.index(selected_item) if selected_item in item_names else 0,
            key=f"{session_key}_selectbox"
        )
        if new_selected != selected_item:
            st.session_state[f'selected_{session_key}'] = new_selected
            selected_item = new_selected
            current_item = next((s for s in items if s['name'] == selected_item), None)
            if f'{session_key}_action' in st.session_state:
                del st.session_state[f'{session_key}_action']

    with col2:
        if st.button(f"🧪 测试", key=f"test_{session_key}_btn", use_container_width=True):
            st.session_state[f'{session_key}_action'] = "test"
            st.rerun()

    st.subheader(f"所有 {item_name}")
    
    for item_type, type_items in items_by_type.items():
        with st.expander(f"**{item_type.upper()}** - {len(type_items)}个", expanded=True):
            for s in type_items:
                is_selected = s['name'] == selected_item
                icon = "👉" if is_selected else "○"
                desc = s.get('description', '')[:80] + '...' if len(s.get('description', '')) > 80 else s.get('description', '')
                detail = s.get('detail', '')
                status = s.get('status', 'active')
                
                status_color = "🟢" if status == "active" else "🔴"
                
                col_icon, col_name, col_desc = st.columns([0.5, 1.5, 4])
                
                with col_icon:
                    st.write(f"**{icon}**")
                with col_name:
                    st.write(f"**{s['name']}** {status_color}")
                with col_desc:
                    st.caption(desc)
                    if detail:
                        st.caption(f"📌 {detail}")

    if f'{session_key}_action' not in st.session_state:
        st.session_state[f'{session_key}_action'] = None

    action = st.session_state[f'{session_key}_action']

    if action and current_item:
        st.markdown("---")
        if action == "test":
            # 使用当前选中项的描述来生成提示
            item_desc = current_item.get('description', '') if current_item else ''
            st.subheader(f"🧪 测试 {item_name}: {selected_item}")
            if item_desc:
                st.caption(f"📝 功能描述: {item_desc}")
            
            # 根据描述生成合适的输入提示
            placeholder = f"输入测试内容测试 {selected_item} 的功能"
            if item_desc:
                placeholder = f"例如：{item_desc.split('，')[0].split('，')[0]}"
            
            st.caption(f"💡 提示: 根据功能描述输入相应的测试内容")
            test_input = st.text_area(
                "测试输入",
                placeholder=placeholder,
                height=100,
                key=f"{session_key}_test_input"
            )
            
            col_run = st.columns([1])
            
            session_key_test = f"{selected_item}_test_result"
            test_result = st.session_state.get(session_key_test)
            
            with col_run[0]:
                if st.button("▶️ 执行测试", type="primary", key=f"{session_key}_test"):
                    if not test_input:
                        st.warning("请输入测试内容")
                    else:
                        with st.spinner("正在执行测试..."):
                            test_result = test_func(selected_item, test_input)
                            st.session_state[session_key_test] = test_result
            
            if test_result and test_result.get('success'):
                result_quality = "有返回结果"
                overall_score = test_result.get('overall_score', 0)
                quality_level = test_result.get('quality_level', 'unknown')
                
                tab1, tab2, tab3 = st.tabs(["🎯 评分", "📥📤 IO", "📋 详情"])
                
                with tab1:
                    if quality_level == 'excellent':
                        level_color = '#28a745'
                    elif quality_level == 'good':
                        level_color = '#0d6efd'
                    else:
                        level_color = '#ffc107'
                    
                    st.markdown(f"""
                    <div style="text-align: center; padding: 30px;">
                        <div style="font-size: 60px; font-weight: bold; color: {level_color};">
                            {overall_score}
                        </div>
                        <div style="font-size: 20px; color: #666;">综合评分</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    dimensions = test_result.get('dimensions', {})
                    if dimensions:
                        for dim_key, dim_data in dimensions.items():
                            score = dim_data.get('score', 0)
                            name = dim_data.get('name', dim_key)
                            st.write(f"**{name}**: {score:.0%}")
                    
                    st.markdown("---")
                    st.markdown("### 🔧 核心组件使用情况")
                    
                    component_usage = test_result.get('component_usage', {})
                    if component_usage:
                        cols = st.columns(4)
                        for i, (comp_key, comp_data) in enumerate(component_usage.items()):
                            with cols[i % 4]:
                                used = comp_data.get('used', False)
                                count = comp_data.get('count', 0)
                                name = comp_data.get('name', comp_key)
                                desc = comp_data.get('desc', '')
                                
                                icon = '✅' if used else '❌'
                                st.markdown(f"**{icon} {comp_key}**")
                                st.metric("调用次数", count)
                                st.caption(desc)
                    else:
                        st.info("暂无组件使用数据")
                
                with tab2:
                    col_io1, col_io2 = st.columns(2)
                    with col_io1:
                        st.subheader("📥 输入")
                        st.code(test_result.get('input', ''))
                    with col_io2:
                        st.subheader("📤 输出")
                        result_data = test_result.get('result', {})
                        
                        if isinstance(result_data, dict):
                            answer = result_data.get('answer', '')
                            if answer:
                                st.markdown(f"**Answer:**\n{answer}")
                            
                            status = result_data.get('status', '')
                            if status:
                                st.markdown(f"**Status:** {status}")
                            
                            error = result_data.get('error', '')
                            if error:
                                st.error(f"**Error:** {error}")
                            
                            steps = result_data.get('steps', 0)
                            if steps:
                                st.markdown(f"**Steps:** {steps}")
                            
                            execution_time = result_data.get('execution_time', 0)
                            if execution_time:
                                st.markdown(f"**Execution Time:** {execution_time:.2f}s")
                            
                            trace = result_data.get('trace', '')
                            if trace:
                                with st.expander("🔍 Agent 执行追踪 (Trace)"):
                                    st.markdown(trace)
                            
                            metadata = result_data.get('metadata', {})
                            if metadata:
                                with st.expander("📊 元数据"):
                                    for k, v in metadata.items():
                                        st.markdown(f"**{k}:** {v}")
                            
                            output_keys = [k for k in result_data.keys() if k not in ['answer', 'status', 'error', 'steps', 'execution_time', 'metadata']]
                            if output_keys:
                                with st.expander("其他输出"):
                                    for k in output_keys:
                                        st.markdown(f"**{k}:** {result_data[k]}")
                        else:
                            st.code(str(result_data))
                
                with tab3:
                    st.subheader("执行流程")
                    execution_trace = test_result.get('execution_trace', [])
                    if execution_trace:
                        for i, step in enumerate(execution_trace):
                            node = step.get('node', 'unknown')
                            status = step.get('status', 'unknown')
                            duration = step.get('duration', 0)
                            node_input = step.get('input', '')[:50]
                            node_output = step.get('output', '')[:80]
                            action_desc = step.get('action', '')
                            module = step.get('module', '')
                            module_desc = step.get('module_desc', '')
                            component = step.get('component', '')
                            
                            status_icon = "[OK]" if status == "completed" else "[>>]"
                            with st.expander(f"{status_icon} Step {i+1}: {node} ({duration}ms) - {component}"):
                                if action_desc:
                                    st.caption(f"Action: {action_desc}")
                                st.write(f"**Input:** {node_input}...")
                                st.write(f"**Output:** {node_output}")
                                st.caption(f"Module: {module} - {module_desc}")
                    
                    st.markdown("---")
                    st.subheader("LangGraph 工作流图")
                    
                    langgraph_diagram = test_result.get('langgraph_workflow_diagram', '')
                    if langgraph_diagram:
                        render_mermaid(langgraph_diagram, height=300)
                        
                        st.markdown("""
                        **节点说明：**
                        | 节点 | 功能 |
                        |------|------|
                        | **think** | 推理思考 - 根据问题进行推理，决定下一步行动 |
                        | **act** | 调用工具 - 执行工具调用，产生 Observation |
                        | **challenge** | 辩证挑战 - 质疑审查最终答案，判断是否需要修改 |
                        | **observation** | 观察结果 - 不是独立节点，是 act 的输出结果 |
                        """)
                    else:
                        st.info("暂无 LangGraph 工作流图")
                    
                    st.markdown("---")
                    st.subheader("Mermaid 执行流程图")
                    
                    mermaid_code = test_result.get('mermaid_flowchart', '')
                    if mermaid_code:
                        render_mermaid(mermaid_code, height=300)
                    else:
                        st.info("暂无流程图")
                    
                    react_steps = test_result.get('react_steps', [])
                    if react_steps:
                        st.markdown("---")
                        st.subheader("ReAct 推理步骤")
                        for step in react_steps:
                            node = step.get('node', 'unknown')
                            desc = step.get('desc', '')
                            step_name = step.get('step', '')
                            
                            icon = "[THINK]" if node == 'think' else "[ACT]" if node == 'act' else "[OBS]"
                            with st.expander(f"{icon} {step_name}"):
                                st.write(desc)
                    
                    system_modules = test_result.get('system_modules', [])
                    if system_modules:
                        st.markdown("---")
                        st.subheader("调用的系统模块")
                        for mod, desc in system_modules:
                            st.code(f"{mod}: {desc}")
                    else:
                        st.info("暂无执行流程信息")
                    
                    st.markdown("---")
                    st.subheader("综合建议")
                    suggestions = test_result.get('suggestions', [])
                    if suggestions:
                        for sug in suggestions:
                            category = sug.get('category', 'execution')
                            dim = sug.get('dimension', '')
                            issue = sug.get('issue', '')
                            suggestion = sug.get('suggestion', '')
                            
                            if category == 'dimension':
                                st.error(f"**{dim}**\n\n{issue}\n\n{suggestion}")
                            elif category == 'component':
                                st.warning(f"**{dim}**\n\n{issue}\n\n{suggestion}")
                            elif category == 'overall':
                                st.success(f"**{dim}**\n\n{issue}\n\n{suggestion}")
                            elif category in ['performance', 'efficiency', 'quality', 'result']:
                                st.info(f"**{dim}**\n\n{issue}\n\n{suggestion}")
                            else:
                                st.warning(f"**{dim}**\n\n{issue}\n\n{suggestion}")
                    else:
                        st.success("暂无建议")
                    
                    st.markdown("---")
                    st.subheader("Agent 自动优化")
                    
                    col_opt1, col_opt2 = st.columns(2)
                    with col_opt1:
                        if st.button("分析问题", key="analyze_agent_btn", use_container_width=True):
                            with st.spinner("正在分析问题..."):
                                opt_result = optimize_agent(selected_item, test_result, auto_fix=False)
                                if opt_result.get('success'):
                                    status = opt_result.get('status', '')
                                    if status == 'already_optimal':
                                        st.success(opt_result.get('message', 'Agent运行良好'))
                                    else:
                                        # 显示错误根因分析
                                        error_analysis = opt_result.get('error_analysis', {})
                                        if error_analysis.get('root_cause'):
                                            with st.expander("🔍 根本原因分析", expanded=True):
                                                st.markdown(error_analysis['root_cause'])
                                        
                                        # 显示具体解决方案
                                        if error_analysis.get('solutions'):
                                            with st.expander("🔧 具体解决方案", expanded=True):
                                                for i, sol in enumerate(error_analysis['solutions'], 1):
                                                    st.markdown(f"**{sol.get('title', f'方案{i}')}**")
                                                    st.markdown(f"📝 {sol.get('steps', '')}")
                                                    st.code(sol.get('command', ''), language='bash')
                                                    st.markdown(f"✅ 预期: {sol.get('expected', '')}")
                                                    st.markdown(f"📁 文件: `{sol.get('file', '')}`")
                                                    st.markdown("---")
                                        
                                        # 显示需要检查的文件
                                        if error_analysis.get('files_to_check'):
                                            with st.expander("📂 需要检查的文件"):
                                                for f in error_analysis['files_to_check']:
                                                    st.write(f"- `{f}`")
                                        
                                        # 显示验证方法
                                        if error_analysis.get('verification'):
                                            st.info(f"🔎 验证方法: {error_analysis['verification']}")
                                        
                                        issues = opt_result.get('issues', [])
                                        auto_fixable = opt_result.get('auto_fixable', [])
                                        
                                        if issues:
                                            st.error("发现问题:")
                                            for issue in issues:
                                                st.write(f"- {issue}")
                                        
                                        if auto_fixable:
                                            st.info("可自动修复的项目:")
                                            for fix in auto_fixable:
                                                st.write(f"- **{fix.get('issue')}**: {fix.get('fix')}")
                                            
                                            st.success(f"共 {len(auto_fixable)} 个问题可修复")
                                else:
                                    st.error(f"分析失败: {opt_result.get('error', '未知错误')}")
                    
                    with col_opt2:
                        if st.button("自动修复", key="auto_fix_agent_btn", use_container_width=True):
                            test_result_for_fix = st.session_state.get(session_key_test)
                            if not test_result_for_fix:
                                st.warning("请先执行测试")
                            else:
                                with st.spinner("正在自动修复问题..."):
                                    opt_result = optimize_agent(selected_item, test_result_for_fix, auto_fix=True)
                                    if opt_result.get('success'):
                                        fix_results = opt_result.get('fix_results', [])
                                        error_analysis = opt_result.get('error_analysis', {})
                                        
                                        if fix_results:
                                            st.success("修复完成:")
                                            for result in fix_results:
                                                if result.get('status') == 'fixed':
                                                    st.write(f"✅ {result.get('issue')}: {result.get('detail')}")
                                                elif result.get('status') == 'skipped':
                                                    st.write(f"⏭️ {result.get('issue')}: {result.get('detail')}")
                                                else:
                                                    st.write(f"❌ {result.get('issue')}: {result.get('detail')}")
                                        else:
                                            st.info("无需修复或无法自动修复")
                                        
                                        if error_analysis.get('verification'):
                                            st.info(f"🔎 验证方法: {error_analysis['verification']}")
                                    else:
                                        st.error(f"修复失败: {opt_result.get('error', '未知错误')}")
            
            elif test_result:
                st.error(f"测试失败: {test_result.get('error', '未知错误')}")


def render_item_list(items, title, show_details=True):
    if items:
        st.write(f"**共发现 {len(items)} 个**")
        by_type = {}
        for item in items:
            t_type = item.get('type', 'unknown')
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(item)
        
        for t_type, type_items in by_type.items():
            with st.expander(f"{t_type.upper()} - {len(type_items)}个"):
                for item in type_items:
                    with st.expander(f"{item['name']}"):
                        st.write(f"**描述**: {item.get('description', 'N/A')}")
                        if show_details:
                            if 'skills' in item:
                                st.write(f"**Skills**: {', '.join(item.get('skills', [])) or 'None'}")
                            if 'capabilities' in item:
                                st.write(f"**Capabilities**: {', '.join(item.get('capabilities', [])) or 'None'}")
                            if 'tools' in item and item.get('tools'):
                                st.write(f"**Tools**: {', '.join(item.get('tools', []))}")
                            if 'version' in item:
                                st.write(f"**版本**: {item.get('version', 'N/A')}")
                            if 'provider' in item:
                                st.write(f"**Provider**: {item.get('provider', 'N/A')}")
                            if 'tags' in item and item.get('tags'):
                                st.write(f"**Tags**: {', '.join(item.get('tags', []))}")
                            if 'dependencies' in item and item.get('dependencies'):
                                st.write(f"**依赖**: {', '.join(item.get('dependencies', []))}")
                        st.caption(f"来源: {item.get('source', 'unknown')}")
    else:
        st.info("暂无数据")


def skill_page():
    st.header("📦 Skill管理")
    try:
        items = discover_skills_from_registry()
    except:
        items = []
    render_test_ui("Skill", test_skill, items, "skill", optimize_skill)


def gateway_page():
    st.header("🌐 Gateway通道")
    try:
        items = discover_gateways_from_registry()
    except:
        items = []
    render_test_ui("Gateway", test_service, items, "gateway", optimize_service)


def tool_page():
    st.header("🔧 Tool管理")
    try:
        items = discover_tools_from_registry()
    except:
        items = []
    render_test_ui("Tool", test_tool, items, "tool", optimize_tool)


def team_page():
    st.header("👥 Team管理")
    try:
        items = discover_teams_from_registry()
    except:
        items = []
    render_test_ui("Team", test_team, items, "team", optimize_team)


def workflow_page():
    st.header("🔀 Workflow管理")
    try:
        items = discover_workflows_from_registry()
    except:
        items = []
    render_test_ui("Workflow", test_workflow, items, "workflow", optimize_workflow)


def service_page():
    st.header("🛠️ Service管理")
    try:
        items = discover_services_from_registry()
    except:
        items = []
    render_test_ui("Service", test_service, items, "service", optimize_service)


def system_module_page():
    st.header("⚙️ 系统核心模块")
    st.markdown("测试和优化系统级核心模块")
    
    modules = get_system_modules()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("选择模块")
        selected_module = st.radio(
            "系统模块",
            [m['name'] for m in modules],
            format_func=lambda x: f"{x} - {[m for m in modules if m['name']==x][0]['description']}",
            key="sys_module_select"
        )
    
    with col2:
        if selected_module:
            st.subheader(f"模块: {selected_module}")
            
            placeholders = {
                'LLM': '输入问题测试 LLM 响应，例如: "你好，请介绍一下自己"',
                'Tools': '输入问题测试工具调用，例如: "搜索今天的天气"',
                'Memory': '输入内容测试记忆存储',
                'Prompt': '输入内容测试提示词模板',
                'Execution Loop': '输入问题测试执行循环',
                'State Management': '输入内容测试状态管理',
                'Error Handling': '输入内容测试错误处理',
                'Context Management': '输入内容测试上下文管理',
                'Cache': '输入内容测试缓存',
                'Security': '输入内容测试安全控制',
                'Monitoring': '输入内容测试监控',
                'Routing': '输入内容测试路由',
                'Configuration': '输入内容测试配置',
                'Event System': '输入内容测试事件系统',
                'Skill Registry': '输入内容测试技能注册',
                'Gateway': '输入内容测试网关',
                'MCP Server': '输入内容测试MCP服务器',
                'Retrieval': '输入内容测试检索系统',
                'Cost Control': '输入内容测试成本控制',
                'Agent Coordinator': '输入内容测试智能体协调',
                'Dependency Injection': '输入内容测试依赖注入',
                'Storage': '输入内容测试存储'
            }
            test_input = st.text_area(
                "测试输入", 
                value="测试输入内容",
                placeholder=placeholders.get(selected_module, "输入测试内容"),
                key="sys_test_input",
                height=100
            )
            
            col_test, col_analyze = st.columns(2)
            
            with col_test:
                if st.button("🧪 开始测试", key="start_sys_test", type="primary"):
                    with st.spinner("正在测试..."):
                        test_result = test_system_module(selected_module, test_input)
                        st.session_state['sys_test_result'] = test_result
                        st.session_state['sys_module_name'] = selected_module
            
            with col_analyze:
                if st.button("🔄 重新测试", key="retest_sys_module"):
                    if 'sys_test_result' in st.session_state:
                        del st.session_state['sys_test_result']
                    st.rerun()
            
            if 'sys_test_result' in st.session_state and st.session_state.get('sys_module_name') == selected_module:
                test_result = st.session_state['sys_test_result']
                
                if test_result.get('success'):
                    health = test_result.get('health_score', 0)
                    status = test_result.get('status', 'unknown')
                    
                    col_score1, col_score2 = st.columns(2)
                    with col_score1:
                        st.metric("健康评分", f"{int(health * 100)}%")
                    with col_score2:
                        st.write(f"**状态**: {status}")
                    
                    if test_result.get('api_configured') is not None:
                        st.write(f"**API已配置**: {'是' if test_result.get('api_configured') else '否'}")
                    
                    if selected_module == 'LLM':
                        response = test_result.get('response', '')
                        if response:
                            st.write(f"**响应**: {response[:200]}")
                        else:
                            st.warning("LLM 未返回响应，请检查 API 配置")
                            if test_result.get('error'):
                                st.error(f"**错误**: {test_result.get('error')}")
                    elif selected_module == 'Tools':
                        st.write(f"**工具数量**: {test_result.get('tool_count', 0)}")
                        st.write(f"**工具列表**: {', '.join(test_result.get('tools', []))}")
                    elif selected_module == 'Memory':
                        st.write(f"**持久化测试**: {test_result.get('persistence_result', 'N/A')}")
                    elif selected_module == 'Prompt':
                        st.write(f"**提示词文件数**: {test_result.get('prompt_count', 0)}")
                        render_result = test_result.get('render_result', '')
                        validation_result = test_result.get('validation_result', '')
                        if render_result:
                            st.write(f"**渲染结果**: {render_result}")
                        if validation_result:
                            st.write(f"**验证结果**: {validation_result}")
                    elif selected_module == 'Execution Loop':
                        st.write(f"**执行时间**: {test_result.get('duration', 0):.2f}ms")
                    elif selected_module == 'State Management':
                        st.write(f"**状态类**: {', '.join(test_result.get('state_classes', []))}")
                    elif selected_module == 'Error Handling':
                        st.write(f"**处理器**: {', '.join(test_result.get('handlers', []))}")
                        error_result = test_result.get('error_handling_result', '')
                        if error_result:
                            st.write(f"**测试结果**: {error_result}")
                    elif selected_module == 'Context Management':
                        st.write(f"**管理器**: {', '.join(test_result.get('managers', []))}")
                        op_result = test_result.get('operation_result', '')
                        compression_result = test_result.get('compression_result', '')
                        keyword_result = test_result.get('keyword_result', '')
                        if op_result:
                            st.write(f"**基础操作**: {op_result}")
                        if compression_result:
                            st.write(f"**压缩功能**: {compression_result}")
                        if keyword_result:
                            st.write(f"**关键词提取**: {keyword_result}")
                    else:
                        components = test_result.get('components', [])
                        if components:
                            st.write(f"**组件**: {', '.join(components)}")
                        op_result = test_result.get('operation_result', '')
                        if op_result:
                            st.write(f"**测试结果**: {op_result}")
                    
                    dimensions = test_result.get('dimensions', {})
                    if dimensions:
                        st.markdown("---")
                        st.subheader("📊 测试维度")
                        cols = st.columns(3)
                        for i, (dim_key, dim_data) in enumerate(dimensions.items()):
                            with cols[i % 3]:
                                score = dim_data.get('score', 0)
                                name = dim_data.get('name', dim_key)
                                color = "green" if score >= 0.8 else "orange" if score >= 0.5 else "red"
                                st.markdown(f"**{name}**: :{color}[{score:.0%}]")
                    
                    st.markdown("---")
                    st.subheader("🔧 优化/修复")
                    
                    col_opt1, col_opt2 = st.columns(2)
                    with col_opt1:
                        if st.button("📋 分析问题", key="analyze_sys_module", use_container_width=True):
                            opt_result = optimize_system_module(selected_module, test_result)
                            st.session_state['sys_opt_result'] = opt_result
                            st.rerun()
                    with col_opt2:
                        if st.button("🔄 重新测试", key="retest_sys_module2", use_container_width=True):
                            if 'sys_test_result' in st.session_state:
                                del st.session_state['sys_test_result']
                            st.rerun()
                    
                    if 'sys_opt_result' in st.session_state:
                        opt_result = st.session_state['sys_opt_result']
                        if opt_result.get('success'):
                            if opt_result.get('full_score'):
                                st.success("✅ 模块完全正常运行，所有维度均已达标")
                            elif opt_result.get('needs_optimization'):
                                st.warning("⚠️ 发现以下问题：")
                                
                                dimension_issues = opt_result.get('dimension_issues', [])
                                if dimension_issues:
                                    for i, dim_issue in enumerate(dimension_issues, 1):
                                        with st.expander(f"📌 问题{i}: {dim_issue['dimension']} (得分: {dim_issue['score']:.0%})"):
                                            st.error(f"**问题**: {dim_issue['issue']}")
                                            st.info(f"**修复建议**: {dim_issue['fix']}")
                                            st.code(f"# 建议操作\n{dim_issue['fix']}", language="bash")
                                else:
                                    for issue in opt_result.get('issues', []):
                                        st.error(f"问题: {issue}")
                                    for fix in opt_result.get('fixes', []):
                                        st.info(f"修复建议: {fix}")
                            else:
                                st.success("模块运行正常，无需优化")
                else:
                    st.error(f"测试失败: {test_result.get('error', '未知错误')}")
            else:
                st.info("点击上方「开始测试」按钮测试选中模块")
        else:
            st.info("请选择一个模块进行测试")


def agent_page():
    st.header("🤖 Agent管理")
    try:
        items = discover_agents_from_registry()
    except:
        items = []
    render_test_ui("Agent", test_agent, items, "agent", optimize_agent)


def ml_page():
    st.header("🤖 ML组件")
    try:
        items = discover_ml_components()
    except:
        items = []
    render_test_ui("ML组件", test_service, items, "ml", optimize_service)


def config_page():
    st.header("⚙️ 配置管理")
    try:
        items = discover_configs()
    except:
        items = []
    render_test_ui("配置", test_service, items, "config", optimize_service)


def model_page():
    st.header("🧠 模型管理")
    try:
        items = discover_models()
    except:
        items = []
    render_test_ui("模型", test_service, items, "model", optimize_service)


def create_entity_page():
    """创建实体页面 - 通过自然语言创建Agent/Skill/Team/Tool/Workflow"""
    st.header("✨ 智能创建")
    st.markdown("使用自然语言描述您的需求，系统将自动创建对应的实体")
    
    if unified_creator is None:
        st.error("❌ 创建服务未初始化，请检查API服务器是否运行")
        return
    
    # 示例提示
    with st.expander("💡 查看示例"):
        st.markdown("""
        - "创建一个数据分析助手agent"
        - "创建一个负责天气查询的skill"
        - "做一个团队，包含数据分析、报表生成的agent"
        - "创建一个可以调用外部API的工具"
        """)
    
    # 输入区域
    description = st.text_area(
        "📝 输入您的需求",
        height=100,
        placeholder="例如：创建一个能分析CSV文件并生成图表的Agent"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_only = st.checkbox("仅分析", value=False, help="只分析需求，不创建实体")
    with col2:
        if st.button("🚀 开始创建", type="primary", use_container_width=True):
            if not description:
                st.warning("请输入需求描述")
            else:
                with st.spinner("正在分析并创建..."):
                    try:
                        import asyncio
                        
                        if analyze_only:
                            # 仅分析
                            result = unified_creator.analyze_intent(description)
                            st.success(f"✅ 分析完成")
                            st.json({
                                "entity_type": result.entity_type.value,
                                "confidence": result.confidence,
                                "description": result.description,
                                "suggested_name": result.suggested_name
                            })
                        else:
                            # 创建实体
                            result = asyncio.run(unified_creator.create_from_natural_language(description))
                            
                            if result.success:
                                st.success(f"✅ {result.message}")
                                
                                # 显示详情
                                with st.expander("📋 详细信息", expanded=True):
                                    st.json({
                                        "entity_type": result.entity_type,
                                        "entity_id": result.entity_id,
                                        "entity_name": result.entity_name,
                                        "details": result.details
                                    })
                                    
                                # 提供后续操作
                                st.markdown("---")
                                st.markdown("### 📌 后续操作")
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.info("1. 前往对应管理页面查看")
                                with col_b:
                                    st.info("2. 进行测试验证")
                                with col_c:
                                    st.info("3. 如需要则优化")
                            else:
                                st.error(f"❌ 创建失败: {result.error}")
                                
                    except Exception as e:
                        st.error(f"❌ 执行错误: {str(e)}")
    
    # 显示支持的实体类型
    st.markdown("---")
    st.subheader("📦 支持的实体类型")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/create/supported-types", timeout=5)
        if response.status_code == 200:
            data = response.json()
            cols = st.columns(len(data.get("entity_types", [])))
            for idx, et in enumerate(data.get("entity_types", [])):
                with cols[idx]:
                    st.markdown(f"**{et['name']}**")
                    st.caption(et['description'])
    except:
        st.info("API服务器未运行，无法获取实体类型列表")


def test_center_page():
    """Unified Test Center - Combines test discovery, evaluation, and coverage"""
    
    tab1, tab2, tab3 = st.tabs(["🧪 测试与评估", "📊 覆盖率报告", "🔍 维度详情"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🧪 测试")
            try:
                test_items = discover_tests()
            except:
                test_items = []
            
            if test_items:
                for item in test_items:
                    with st.expander(f"📦 {item.get('name', 'Unknown')}"):
                        st.write(f"**类型**: {item.get('type', 'unknown')}")
                        st.write(f"**描述**: {item.get('description', 'N/A')}")
                        st.write(f"**来源**: {item.get('source', 'N/A')}")
            else:
                st.info("未发现测试文件")
        
        with col2:
            st.subheader("📝 评估")
            try:
                eval_items = discover_evaluations()
            except:
                eval_items = []
            
            if eval_items:
                for item in eval_items:
                    with st.expander(f"📊 {item.get('name', 'Unknown')}"):
                        st.write(f"**类型**: {item.get('type', 'unknown')}")
                        st.write(f"**描述**: {item.get('description', 'N/A')}")
                        st.write(f"**来源**: {item.get('source', 'N/A')}")
            else:
                st.info("未发现评估文件")
    
    with tab2:
        if generate_coverage_report is None:
            st.error("测试框架未正确加载")
            return
        
        with st.spinner("正在分析测试覆盖率..."):
            report = generate_coverage_report()
        
        total_dims = sum(c.total_dimensions for c in report.values())
        total_tested = sum(c.tested_dimensions for c in report.values())
        overall_coverage = (total_tested / total_dims * 100) if total_dims > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总维度数", total_dims)
        with col2:
            st.metric("已测试维度", total_tested)
        with col3:
            st.metric("覆盖率", f"{overall_coverage:.1f}%", delta=f"{overall_coverage-50:.1f}%", delta_color="normal")
        
        st.markdown("---")
        
        for entity_type, coverage in report.items():
            with st.expander(f"**{entity_type.upper()}** - {coverage.coverage_percentage:.1f}%"):
                cols = st.columns([1, 1, 2])
                with cols[0]:
                    st.metric("总维度", coverage.total_dimensions)
                with cols[1]:
                    st.metric("已测试", coverage.tested_dimensions)
                with cols[2]:
                    dim_list = [d.dimension_key for d in coverage.dimensions]
                    st.write("维度:", ", ".join(dim_list))
    
    with tab3:
        st.subheader("🔍 各维度详情")
        
        entity_type = st.selectbox(
            "选择实体类型",
            options=list(report.keys()) if 'report' in dir() else ["system_module", "agent", "tool", "skill", "team", "workflow", "service"]
        )
        
        if generate_coverage_report:
            coverage = analyze_coverage(entity_type)
            
            for dim in coverage.dimensions:
                with st.expander(f"{dim.dimension_key}: {dim.dimension_name} (权重: {dim.weight})"):
                    st.write(f"**测试函数**: {dim.test_function or '未映射'}")
                    st.write(f"**状态**: {dim.status.value}")


# Keep legacy pages for backward compatibility (will be removed later)
def test_page():
    st.info("测试功能已整合到「🧪 测试中心」页面")
    test_center_page()


def evaluation_page():
    st.info("评估功能已整合到「🧪 测试中心」页面")
    test_center_page()


def coverage_page():
    st.header("📊 测试覆盖率")
    
    if generate_coverage_report is None:
        st.error("测试框架未正确加载")
        return
    
    with st.spinner("正在分析测试覆盖率..."):
        report = generate_coverage_report()
    
    total_dims = sum(c.total_dimensions for c in report.values())
    total_tested = sum(c.tested_dimensions for c in report.values())
    overall_coverage = (total_tested / total_dims * 100) if total_dims > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总维度数", total_dims)
    with col2:
        st.metric("已测试维度", total_tested)
    with col3:
        st.metric("覆盖率", f"{overall_coverage:.1f}%")
    
    st.markdown("---")
    st.subheader("各实体类型覆盖率")
    
    for entity_type, coverage in report.items():
        with st.expander(f"{entity_type.upper()} - {coverage.coverage_percentage:.1f}%"):
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.write(f"**总维度**: {coverage.total_dimensions}")
                st.write(f"**已测试**: {coverage.tested_dimensions}")
            with col_b:
                if coverage.dimensions:
                    dim_list = [d.dimension_key for d in coverage.dimensions]
                    st.write("维度列表:", ", ".join(dim_list))


# ========== Main Entry ==========
def main():
    st.set_page_config(
        page_title="AI中台管理系统",
        page_icon="🖥️",
        layout="wide"
    )
    
    pages = {
        "✨ 智能创建": create_entity_page,
        "🧩 系统模块": system_module_page,
        "🤖 Agent管理": agent_page,
        "🌐 Gateway": gateway_page,
        "🔧 Tool管理": tool_page,
        "👥 Team管理": team_page,
        "🔀 Workflow": workflow_page,
        "🛠️ Service": service_page,
        "⚙️ 配置管理": config_page,
        "🧠 模型管理": model_page,
        "🧪 测试中心": test_center_page,
    }
    
    with st.sidebar:
        st.title("🖥️ AI中台管理")
        st.markdown("---")
        selected_page = st.radio("选择页面", list(pages.keys()), index=0)
    
    pages[selected_page]()


if __name__ == "__main__":
    main()
