"""
Knowledge Query App (Powered by RANGEN V2 Core)
一个基于 Streamlit 的智能问答系统，利用 RANGEN V2 的核心推理引擎回答问题。
"""

import warnings
import numpy as np
import logging
import sys

# 获取根日志记录器
root_logger = logging.getLogger()

# 防止 Streamlit 重复加载时添加多个 handler
if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in root_logger.handlers):
    # 移除所有现有的 handler
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # 配置日志格式
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

# 避免 basicConfig 的副作用
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     force=True  # 强制重新配置，覆盖Streamlit的默认配置
# )

# 抑制 FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning, module="keras")
warnings.filterwarnings("ignore", category=FutureWarning, module="tensorflow")

import streamlit as st
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.real_reasoning_engine import RealReasoningEngine
from src.utils.reasoning_visualizer import ReasoningVisualizer
from knowledge_management_system.core.vector_index_builder import VectorIndexBuilder

def main():
    st.set_page_config(page_title="RANGEN Intelligent Query", page_icon="🧠")
    
    st.title("🧠 RANGEN 智能问答系统")
    st.markdown("此系统使用 **RANGEN V2 核心引擎**，具备**双脑智能**和**动态推理**能力。")
    
    # 初始化组件
    @st.cache_resource
    def load_engine():
        # 🚀 Force reload to clear memory cache (Fixed Chinese Academy issue)
        return RealReasoningEngine()

    @st.cache_resource
    def load_vib():
        return VectorIndexBuilder("data/knowledge_management/vector_index.bin")

    try:
        engine = load_engine()
        vib = load_vib()
        
        # 侧边栏：状态监控
        with st.sidebar:
            st.header("📊 系统状态")
            if vib.ensure_index_ready():
                st.metric("📚 知识库规模", f"{vib.entry_count} 条向量")
            else:
                st.error("知识库索引未就绪")
            
            st.divider()
            st.markdown("### 🧠 核心能力")
            st.markdown("- **Fast Path**: Phi-3 (本地)")
            st.markdown("- **Deep Path**: DeepSeek R1 (云端)")
            st.markdown("- **DDL**: 动态难度加载")

        # 主界面：查询输入
        # 🚀 优化：使用 chat_input 实现连续对话体验
        # query = st.text_input("请输入您的问题：", placeholder="例如：RANGEN V2 是如何实现动态路由的？")
        
        # 初始化会话历史
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 展示历史消息
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 接受新输入
        if query := st.chat_input("请输入您的问题..."):
            # 添加用户消息到历史
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            # 生成回复
            with st.chat_message("assistant"):
                # 使用 st.status 创建状态容器，替代简单的 spinner
                status_container = st.status("🤔 RANGEN 正在启动...", expanded=True)
                
                # 定义回调函数来更新状态
                callbacks = {
                    "on_start": lambda q: status_container.update(label=f"🚀 开始分析: {q[:20]}...", state="running"),
                    "on_fast_path_success": lambda a: status_container.update(label="⚡ Fast Path 快速响应完成", state="complete", expanded=False),
                    "on_planning_start": lambda: status_container.write("📅 正在规划推理步骤..."),
                    "on_planning_end": lambda plan: status_container.write(f"✅ 规划完成，共 {len(plan)} 个步骤"),
                    "on_deep_reasoning_start": lambda: status_container.update(label="🧠 进入深度推理模式...", state="running"),
                    "on_step_start": lambda step: status_container.write(f"🔄 执行步骤: {step.get('sub_query') or step.get('description', '正在处理...')}"),
                    "on_end": lambda res: status_container.update(label="✅ 推理完成", state="complete", expanded=False)
                }

                try:
                    result = asyncio.run(engine.reason(query, context={}, callbacks=callbacks))
                    
                    if result:
                        # 0. 展示警告信息 (如果存在)
                        if getattr(result, 'warnings', None):
                            with st.expander("⚠️ 系统运行警告", expanded=True):
                                for warning in result.warnings:
                                    st.warning(warning)

                        # 1. 展示最终答案
                        st.markdown("### 💡 智能回答")
                        st.success(result.final_answer)
                        
                        # 添加助手消息到历史（仅保存文本答案）
                        st.session_state.messages.append({"role": "assistant", "content": result.final_answer})
                        
                        # 2. 展示推理过程 (透明化)
                        with st.expander("🔍 查看推理过程 (Thinking Process)", expanded=False):
                            st.markdown(f"**推理策略:** `{result.reasoning_type}`")
                            st.markdown(f"**执行来源:** `{result.answer_source}`")
                            st.markdown(f"**置信度:** `{result.total_confidence:.2f}`")
                            st.markdown(f"**耗时:** `{result.processing_time:.2f}s`")
                            
                            # 🚀 Phase 2: 可视化
                            # 使用 Tabs 分离推理图和文本步骤
                            tab_graph, tab_steps = st.tabs(["🗺️ 推理路径图", "📝 详细步骤"])
                            
                            with tab_graph:
                                st.markdown("#### 推理路径可视化:")
                                try:
                                    dot_code = ReasoningVisualizer.generate_graphviz(result)
                                    st.graphviz_chart(dot_code)
                                except Exception as e:
                                    st.warning(f"无法生成可视化图表: {e}")
                            
                            with tab_steps:
                                if result.reasoning_steps:
                                    st.markdown("#### 推理步骤:")
                                    for step in result.reasoning_steps:
                                        # 只显示sub_query或description，避免显示原始字典
                                        step_desc = step.get('sub_query') or step.get('description') or str(step)
                                        # 如果有结果摘要，也显示一部分
                                        if step.get('result'):
                                            step_result = step['result'][:100] + "..." if len(step['result']) > 100 else step['result']
                                            st.markdown(f"- **{step_desc}**\n  > 结果: {step_result}")
                                        else:
                                            st.markdown(f"- {step_desc}")
                        
                        # 3. 展示参考证据
                        if result.evidence_chain:
                            with st.expander(f"📚 参考证据 ({len(result.evidence_chain)} 条)", expanded=False):
                                for i, ev in enumerate(result.evidence_chain):
                                    relevance = ev.relevance_score if hasattr(ev, 'relevance_score') else 0.0
                                    st.markdown(f"**证据 {i+1}** (Relevance: {relevance:.2f})")
                                    content = ev.content if hasattr(ev, 'content') else str(ev)
                                    st.text(content[:500] + "..." if len(content) > 500 else content)
                    else:
                        st.error("推理引擎未返回结果。")
                        
                except Exception as e:
                    st.error(f"推理过程中发生错误: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    
    except Exception as e:
        st.error(f"系统初始化失败: {e}")
        st.code(str(e))

if __name__ == "__main__":
    main()
