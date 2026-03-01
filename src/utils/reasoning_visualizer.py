from typing import Dict, List, Any, Optional
import json

class ReasoningVisualizer:
    """推理过程可视化生成器 (Phase 2)
    
    将 ReasoningResult 转换为 Graphviz DOT 格式，
    展示从 Query -> Steps -> Evidence -> Answer 的动态过程。
    """
    
    @staticmethod
    def generate_graphviz(result: Any) -> str:
        """生成 Graphviz DOT 代码 - 展示核心系统节点流程 (LangGraph Style)"""
        dot = ['digraph ReasoningGraph {']
        dot.append('  rankdir=TD;')  # 自顶向下布局，更像流程图
        dot.append('  node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10];')
        dot.append('  edge [fontname="Arial", fontsize=9];')
        
        # 定义核心节点样式
        dot.append('  start [label="START", shape=circle, fillcolor="#4CAF50", fontcolor="white", width=0.8];')
        dot.append('  end [label="END", shape=doublecircle, fillcolor="#F44336", fontcolor="white", width=0.8];')
        
        # 定义功能节点
        dot.append('  analyze [label="Complexity Analysis\n(System 1)", fillcolor="#BBDEFB"];')
        dot.append('  fast_path [label="Fast Path\n(Phi-3)", fillcolor="#C8E6C9"];')
        dot.append('  planner [label="Planner\n(System 2)", fillcolor="#FFF9C4"];')
        dot.append('  deep_loop [label="Deep Reasoning Loop", fillcolor="#FFE0B2"];')
        dot.append('  verify [label="Verification", fillcolor="#D1C4E9"];')
        
        # 提取执行数据
        reasoning_type = getattr(result, 'reasoning_type', 'unknown')
        steps = getattr(result, 'reasoning_steps', [])
        
        # 构建流程连线
        dot.append('  start -> analyze;')
        
        if reasoning_type == "phi3_direct" or reasoning_type == "fast_path":
            # Fast Path 流程
            dot.append('  analyze -> fast_path [label="simple query", color="#4CAF50", penwidth=2];')
            dot.append('  analyze -> planner [label="complex query", style=dashed, color="gray"];') # 未走路径
            dot.append('  fast_path -> verify;')
            dot.append('  verify -> end;')
        else:
            # Deep Path 流程
            dot.append('  analyze -> fast_path [label="simple query", style=dashed, color="gray"];') # 未走路径
            dot.append('  analyze -> planner [label="complex query", color="#FF9800", penwidth=2];')
            dot.append('  planner -> deep_loop;')
            
            # 在 Deep Loop 内部展开具体的步骤
            # 创建子图 cluster
            dot.append('  subgraph cluster_loop {')
            dot.append('    label = "Execution Steps";')
            dot.append('    style = dashed;')
            dot.append('    color = "#FFB74D";')
            dot.append('    bgcolor = "#FFF3E0";')
            
            if steps:
                for i, step in enumerate(steps):
                    step_id = f"step_{i}"
                    # 简化描述，只取前20个字符
                    if isinstance(step, dict):
                        desc = step.get('sub_query') or step.get('description') or f'Step {i+1}'
                        step_type = step.get('type', 'process')
                    else:
                        desc = getattr(step, 'description', f'Step {i+1}')
                        step_type = getattr(step, 'step_type', 'process')
                    
                    label = f"{step_type}\\n{desc[:20]}..."
                    dot.append(f'    {step_id} [label="{label}", fillcolor="white"];')
                    
                    if i > 0:
                        dot.append(f'    step_{i-1} -> {step_id};')
                
                # 连接 Deep Loop 入口和出口
                dot.append(f'    deep_loop -> step_0 [lhead=cluster_loop];')
                dot.append(f'    step_{len(steps)-1} -> verify [ltail=cluster_loop];')
            else:
                dot.append('    deep_loop -> verify;')
            
            dot.append('  }')
            
            dot.append('  verify -> end;')

        dot.append('}')
        return "\n".join(dot)
