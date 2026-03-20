"""
AI Design Review UI - Streamlit 可视化设计审查页面

功能:
- 需求输入 → AI 生成设计
- 可视化审查设计
- 一键批准/拒绝
- 查看 HARD-GATE 状态

运行: streamlit run src/ui/design_review_ui.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def init_session_state():
    """初始化 session state"""
    if 'design' not in st.session_state:
        st.session_state.design = None
    if 'requirements' not in st.session_state:
        st.session_state.requirements = ""
    if 'design_generated' not in st.session_state:
        st.session_state.design_generated = False
    if 'approved' not in st.session_state:
        st.session_state.approved = None
    if 'hard_gate_status' not in st.session_state:
        st.session_state.hard_gate_status = None


def render_header():
    """渲染页面头部"""
    st.set_page_config(
        page_title="AI Design Review",
        page_icon="📐",
        layout="wide"
    )
    
    st.title("📐 AI Design Review")
    st.markdown("---")
    
    # 流程说明
    with st.expander("ℹ️ 工作流程说明", expanded=False):
        st.markdown("""
        **完整流程:**
        1. **输入需求** → 描述你想要的功能
        2. **AI 生成设计** → 基于需求生成详细设计方案
        3. **审查设计** → 查看 AI 生成的设计
        4. **批准/拒绝** → 批准后进入实现阶段
        5. **实现** → 在 TDD 强制下编写代码
        """)
    
    st.markdown("")


def render_hard_gate_status():
    """渲染 HARD-GATE 状态"""
    try:
        from src.agents.hard_gate import HARD_GATE
        
        gate = HARD_GATE()
        status = gate.get_status()
        
        st.sidebar.header("🔒 HARD-GATE 状态")
        
        phase = status.get("phase", "unknown")
        can_write = status.get("can_write", False)
        design = status.get("design", {})
        
        # 阶段颜色
        phase_colors = {
            "idle": "gray",
            "brainstorming": "yellow",
            "design_review": "orange",
            "design_approved": "blue",
            "implementing": "green",
            "completed": "violet"
        }
        color = phase_colors.get(phase, "gray")
        
        st.sidebar.markdown(f"**阶段:** :{color}[{phase}]")
        st.sidebar.markdown(f"**可写文件:** {'✅ 是' if can_write else '❌ 否'}")
        
        if design:
            st.sidebar.markdown(f"**设计标题:** {design.get('title', 'N/A')}")
            st.sidebar.markdown(f"**已批准:** {'✅' if design.get('approved') else '⏳ 待批准'}")
        
        # 重置按钮
        if st.sidebar.button("🔄 重置 HARD-GATE"):
            gate.reset()
            st.rerun()
        
        st.sidebar.markdown("---")
        
    except Exception as e:
        st.sidebar.error(f"HARD-GATE 错误: {e}")


def render_requirement_input():
    """渲染需求输入区域"""
    st.header("📝 步骤 1: 输入需求")
    
    requirements = st.text_area(
        "描述你想要实现的功能",
        value=st.session_state.requirements,
        placeholder="例如:\n- 用户注册和登录\n- JWT Token 认证\n- 用户信息管理",
        height=150
    )
    
    st.session_state.requirements = requirements
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        auto_approve = st.checkbox("🤖 自动批准 (跳过审查)", value=False)
    
    with col2:
        generate_btn = st.button("🚀 生成设计", type="primary", use_container_width=True)
    
    return requirements, auto_approve, generate_btn


def generate_design(requirements: str, auto_approve: bool):
    """生成设计"""
    if not requirements.strip():
        st.warning("⚠️ 请输入需求描述")
        return
    
    with st.spinner("🔄 AI 正在生成设计..."):
        try:
            from src.agents.ai_design_generator import AIDesignGenerator
            from src.agents.requirement_discovery import RequirementDiscoveryAgent
            
            # 如果是简单需求，先进行需求发现
            if len(requirements) < 100:
                discovery = RequirementDiscoveryAgent()
                discovered = discovery.discover_requirements(requirements)
                requirements_text = "\n".join([
                    f"- **{r.title}**: {r.description}"
                    for r in discovered.requirements
                ])
            else:
                requirements_text = requirements
            
            # 生成设计
            generator = AIDesignGenerator()
            design = generator.generate_design(requirements_text)
            
            st.session_state.design = design
            st.session_state.design_generated = True
            
            # 如果自动批准
            if auto_approve:
                with st.spinner("🔄 自动批准中..."):
                    generator.submit_to_hard_gate(design, approved_by="ui_auto")
                    st.session_state.approved = True
                    st.session_state.hard_gate_status = "approved"
            
            st.success("✅ 设计生成完成!")
            
        except Exception as e:
            st.error(f"❌ 生成失败: {e}")
            import traceback
            st.code(traceback.format_exc())


def render_design_review():
    """渲染设计审查区域"""
    if not st.session_state.design_generated or not st.session_state.design:
        st.info("👆 请先输入需求并生成设计")
        return
    
    design = st.session_state.design
    
    st.header("📋 步骤 2: 审查设计")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 概览", 
        "🏗️ 架构", 
        "🔗 API", 
        "📁 文件结构",
        "⚠️ 风险"
    ])
    
    with tab1:
        st.subheader("概览")
        if design.overview:
            st.markdown(design.overview)
        else:
            st.info("暂无概览信息")
    
    with tab2:
        st.subheader("架构设计")
        if design.architecture:
            st.markdown(design.architecture)
        else:
            st.info("暂无架构设计信息")
        
        # 显示组件
        if design.components:
            st.subheader("🧩 组件")
            for comp in design.components:
                with st.expander(f"📦 {comp.name}"):
                    st.markdown(f"**描述:** {comp.description}")
                    if comp.files:
                        st.markdown("**文件:**")
                        for f in comp.files:
                            st.code(f)
    
    with tab3:
        st.subheader("API 端点")
        if design.api_endpoints:
            for i, ep in enumerate(design.api_endpoints):
                endpoint = ep.get("endpoint", str(ep))
                st.code(endpoint, language=None)
        else:
            st.info("暂无 API 端点信息")
    
    with tab4:
        st.subheader("文件结构")
        if design.file_structure:
            for f in design.file_structure:
                if f.strip():
                    st.code(f, language=None)
        else:
            st.info("暂无文件结构信息")
    
    with tab5:
        st.subheader("风险评估")
        if design.risks:
            for risk in design.risks:
                risk_desc = risk.get("description", str(risk))
                st.warning(f"⚠️ {risk_desc}")
        else:
            st.success("✅ 暂无已识别风险")


def render_approval_section():
    """渲染批准/拒绝区域"""
    if not st.session_state.design_generated:
        return
    
    st.header("✅ 步骤 3: 批准设计")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        approve_btn = st.button("✅ 批准", type="primary", use_container_width=True)
    
    with col2:
        reject_btn = st.button("❌ 拒绝", use_container_width=True)
    
    with col3:
        if st.session_state.approved is True:
            st.success("🎉 设计已批准！可以开始实现了。")
        elif st.session_state.approved is False:
            st.warning("👎 设计被拒绝，请修改需求后重新生成。")
        else:
            st.info("请审查设计后决定是否批准")
    
    # 处理批准
    if approve_btn:
        try:
            from src.agents.ai_design_generator import AIDesignGenerator
            
            generator = AIDesignGenerator()
            success = generator.submit_to_hard_gate(
                st.session_state.design, 
                approved_by="ui_user"
            )
            
            if success:
                st.session_state.approved = True
                st.session_state.hard_gate_status = "approved"
                st.success("✅ 设计已批准并提交到 HARD-GATE！")
                st.balloons()
            else:
                st.error("❌ 提交失败")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 批准失败: {e}")
    
    # 处理拒绝
    if reject_btn:
        st.session_state.approved = False
        st.warning("👎 设计已拒绝，请修改需求后重新生成。")
        st.rerun()


def render_implementation_guide():
    """渲染实现指南"""
    if st.session_state.hard_gate_status != "approved":
        return
    
    st.header("🚀 实现指南")
    
    st.success("""
    🎉 **设计已批准！** 现在可以开始实现了。
    
    **接下来的步骤:**
    1. 在 `tests/` 目录下创建测试文件 (RED)
    2. 运行测试确认失败
    3. 在 `src/` 下实现功能 (GREEN)
    4. 重构优化 (REFACTOR)
    5. 使用 `BlockingReviewer` 审查代码
    """)
    
    # 显示下一步
    st.subheader("📋 TDD 流程")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 1️⃣ RED
        先写测试
        ```python
        def test_user_register():
            pass  # 先写测试
        ```
        """)
    
    with col2:
        st.markdown("""
        ### 2️⃣ GREEN  
        写最小代码
        ```python
        def register_user(data):
            return User(id=1)
        ```
        """)
    
    with col3:
        st.markdown("""
        ### 3️⃣ REFACTOR
        重构优化
        ```python
        def register_user(data):
            validate(data)
            return User.create(data)
        ```
        """)


def render_history():
    """渲染历史记录"""
    st.header("📜 最近设计")
    
    # TODO: 从文件加载历史
    st.info("历史记录功能开发中...")


def main():
    """主函数"""
    init_session_state()
    
    # 侧边栏
    with st.sidebar:
        render_hard_gate_status()
    
    # 主区域
    render_header()
    
    # 需求输入
    requirements, auto_approve, generate_btn = render_requirement_input()
    
    # 生成设计
    if generate_btn:
        generate_design(requirements, auto_approve)
        st.rerun()
    
    st.markdown("---")
    
    # 设计审查
    render_design_review()
    
    st.markdown("---")
    
    # 批准区域
    render_approval_section()
    
    # 实现指南
    render_implementation_guide()


if __name__ == "__main__":
    main()
