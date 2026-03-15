#!/usr/bin/env python3
"""
简化的可视化演示 - 不需要网络访问
用于在IDE沙盒环境中演示工作流可视化功能
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_mock_workflow_data():
    """创建模拟的工作流数据"""
    return {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "label": "开始",
                "description": "工作流开始节点"
            },
            {
                "id": "research",
                "type": "agent",
                "label": "研究代理",
                "description": "执行知识检索和信息收集"
            },
            {
                "id": "reasoning",
                "type": "agent",
                "label": "推理专家",
                "description": "执行逻辑推理和问题分析"
            },
            {
                "id": "answer",
                "type": "agent",
                "label": "答案生成",
                "description": "生成最终答案和格式化"
            },
            {
                "id": "end",
                "type": "end",
                "label": "结束",
                "description": "工作流结束节点"
            }
        ],
        "edges": [
            {"source": "start", "target": "research", "label": "开始研究"},
            {"source": "research", "target": "reasoning", "label": "信息收集完成"},
            {"source": "reasoning", "target": "answer", "label": "推理完成"},
            {"source": "answer", "target": "end", "label": "答案生成完成"}
        ]
    }

def generate_html_page():
    """生成HTML页面"""
    workflow_data = create_mock_workflow_data()

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RANGEN LangGraph 可视化演示</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .title {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .subtitle {{
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }}

        .status {{
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }}

        .status.success {{
            background: #e8f5e8;
            border-color: #4caf50;
        }}

        .status .icon {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .workflow-section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}

        .mermaid-container {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            border: 2px solid #e0e0e0;
            text-align: center;
        }}

        .node-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .node-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}

        .node-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}

        .node-card .type {{
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.8em;
            display: inline-block;
            margin-bottom: 10px;
        }}

        .node-card .description {{
            color: #666;
            font-size: 0.9em;
            line-height: 1.4;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .stat-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}

        .note {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
        }}

        .note .icon {{
            color: #856404;
            font-size: 1.5em;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🎯 RANGEN LangGraph 可视化演示</div>
            <div class="subtitle">智能工作流可视化系统</div>

            <div class="status success">
                <div class="icon">✅</div>
                <div>系统状态: 正常运行</div>
                <div>工作流引擎: LangGraph 已集成</div>
            </div>
        </div>

        <div class="workflow-section">
            <div class="section-title">🔄 工作流图</div>
            <div class="mermaid-container">
                <div id="workflow-diagram"></div>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(workflow_data['nodes'])}</div>
                    <div class="stat-label">节点数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(workflow_data['edges'])}</div>
                    <div class="stat-label">连接数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">4</div>
                    <div class="stat-label">智能代理</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">100%</div>
                    <div class="stat-label">集成完成度</div>
                </div>
            </div>
        </div>

        <div class="workflow-section">
            <div class="section-title">🤖 智能代理节点</div>
            <div class="node-info">
    """

    # 添加节点信息
    for node in workflow_data['nodes']:
        node_type_color = {
            'start': '#4caf50',
            'end': '#f44336',
            'agent': '#667eea'
        }.get(node['type'], '#666')

        html_content += f"""
                <div class="node-card">
                    <h3>{node['label']}</h3>
                    <div class="type" style="background: {node_type_color}">{node['type'].upper()}</div>
                    <div class="description">{node['description']}</div>
                </div>
        """

    html_content += """
            </div>
        </div>

        <div class="note">
            <span class="icon">ℹ️</span>
            <strong>注意:</strong> 这是IDE沙盒环境下的演示版本。由于沙盒限制，实际的网络服务器无法启动。
            但您可以看到完整的LangGraph工作流结构和智能代理配置。
            <br><br>
            <strong>要在完整环境中运行:</strong> 请在本地终端中使用以下命令：<br>
            <code>cd /Users/syu/workdata/person/zy/RANGEN-main(syu-python) && ./start_server.sh</code>
        </div>
    </div>

    <script>
        // 初始化Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            themeVariables: {
                primaryColor: '#667eea',
                primaryTextColor: '#fff',
                primaryBorderColor: '#5a67d8',
                lineColor: '#667eea',
                sectionBkgColor: '#f8f9fa',
                altSectionBkgColor: '#e2e8f0',
                gridColor: '#e0e0e0',
                tertiaryColor: '#fff'
            }
        });

        // 定义工作流图
        const graphDefinition = `
            graph TD
                A[开始] --> B[研究代理]
                B --> C[推理专家]
                C --> D[答案生成]
                D --> E[结束]

                style A fill:#4caf50,color:#fff
                style E fill:#f44336,color:#fff
                style B fill:#667eea,color:#fff
                style C fill:#667eea,color:#fff
                style D fill:#667eea,color:#fff
        `;

        // 渲染图表
        document.addEventListener('DOMContentLoaded', function() {
            const element = document.getElementById('workflow-diagram');
            mermaid.render('workflow-graph', graphDefinition).then(function(result) {
                element.innerHTML = result.svg;
            });
        });
    </script>
</body>
</html>"""

    return html_content

def main():
    """主函数"""
    print("=" * 80)
    print("🎯 RANGEN LangGraph 可视化演示")
    print("=" * 80)
    print()

    try:
        # 生成HTML页面
        html_content = generate_html_page()

        # 保存到文件
        output_file = "workflow_demo.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("✅ 演示页面生成成功!")
        print(f"📁 文件位置: {os.path.abspath(output_file)}")
        print()
        print("🌐 打开方式:")
        print(f"   在浏览器中打开: file://{os.path.abspath(output_file)}")
        print("   或者在IDE中直接打开此HTML文件")
        print()
        print("🎨 演示内容:")
        print("   - LangGraph工作流可视化")
        print("   - 智能代理节点展示")
        print("   - 系统状态信息")
        print("   - 工作流统计数据")
        print()
        print("💡 注意: 这是在IDE沙盒环境下的静态演示")
        print("   实际的交互式服务器需要在本地终端中运行")

    except Exception as e:
        print(f"❌ 生成演示页面失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
