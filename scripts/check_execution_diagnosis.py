#!/usr/bin/env python3
"""
访问诊断端点查看执行记录的详细信息
"""
import sys
import json
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def check_executions():
    """检查所有执行记录"""
    base_url = "http://localhost:8080"
    
    print("=" * 80)
    print("检查执行记录")
    print("=" * 80)
    
    try:
        # 1. 获取所有执行记录
        print("\n📋 步骤1: 获取所有执行记录...")
        response = requests.get(f"{base_url}/api/executions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            executions = data.get("executions", [])
            count = data.get("count", 0)
            print(f"✅ 找到 {count} 条执行记录")
            
            if count == 0:
                print("❌ 没有执行记录")
                return
            
            # 按开始时间排序，最新的在前
            executions_sorted = sorted(
                executions,
                key=lambda x: x.get("start_time", 0),
                reverse=True
            )
            
            # 显示最近的执行记录
            print("\n📊 最近的执行记录:")
            for i, exec_data in enumerate(executions_sorted[:5], 1):
                exec_id = exec_data.get("id") or exec_data.get("execution_id", "unknown")
                status = exec_data.get("status", "unknown")
                has_final_result = "final_result" in exec_data
                has_answer = bool(exec_data.get("final_result", {}).get("answer"))
                nodes_count = len(exec_data.get("nodes", []))
                
                print(f"\n  {i}. Execution ID: {exec_id}")
                print(f"     状态: {status}")
                print(f"     节点数: {nodes_count}")
                print(f"     有 final_result: {has_final_result}")
                print(f"     有答案: {has_answer}")
                
                # 如果有诊断信息，显示它
                if "diagnosis" in exec_data:
                    diag = exec_data["diagnosis"]
                    print(f"     诊断信息:")
                    print(f"       - 答案长度: {diag.get('answer_length', 0)}")
                    print(f"       - 可用字段: {', '.join(diag.get('available_fields', []))}")
            
            # 2. 诊断最新的执行记录
            if executions_sorted:
                latest_exec = executions_sorted[0]
                exec_id = latest_exec.get("id") or latest_exec.get("execution_id", "unknown")
                
                print("\n" + "=" * 80)
                print(f"🔍 步骤2: 诊断执行记录: {exec_id}")
                print("=" * 80)
                
                response = requests.get(f"{base_url}/api/diagnose/execution/{exec_id}", timeout=5)
                if response.status_code == 200:
                    diagnosis = response.json()
                    
                    print(f"\n执行ID: {diagnosis.get('execution_id')}")
                    print(f"状态: {diagnosis.get('status')}")
                    
                    print(f"\n📊 final_result 信息:")
                    final_result_info = diagnosis.get("final_result_info", {})
                    print(f"  存在: {final_result_info.get('exists', False)}")
                    print(f"  有答案: {final_result_info.get('has_answer', False)}")
                    if final_result_info.get('answer'):
                        answer = final_result_info.get('answer', '')
                        print(f"  答案: {answer[:100]}...")
                    print(f"  答案长度: {final_result_info.get('answer_length', 0)}")
                    print(f"  成功: {final_result_info.get('success', False)}")
                    print(f"  有错误: {final_result_info.get('has_error', False)}")
                    if final_result_info.get('error'):
                        print(f"  错误: {final_result_info.get('error')}")
                    
                    print(f"\n📊 节点信息:")
                    nodes_info = diagnosis.get("nodes_info", {})
                    print(f"  节点总数: {nodes_info.get('count', 0)}")
                    print(f"  已完成节点数: {nodes_info.get('completed_count', 0)}")
                    print(f"  节点中有答案: {nodes_info.get('has_answer_in_nodes', False)}")
                    if nodes_info.get('nodes_with_answer'):
                        print(f"  包含答案的节点:")
                        for node in nodes_info.get('nodes_with_answer', []):
                            print(f"    - {node.get('name')}: 答案长度={node.get('answer_length')}")
                    
                    print(f"\n📊 state_history 信息:")
                    state_history_info = diagnosis.get("state_history_info", {})
                    print(f"  历史记录数: {state_history_info.get('count', 0)}")
                    print(f"  历史中有答案: {state_history_info.get('has_answer_in_history', False)}")
                    if state_history_info.get('history_with_answer'):
                        print(f"  包含答案的历史记录:")
                        for hist in state_history_info.get('history_with_answer', [])[:3]:
                            print(f"    - 索引 {hist.get('index')}: 答案长度={hist.get('answer_length')}")
                    
                    print(f"\n⚠️ 问题:")
                    issues = diagnosis.get("issues", [])
                    if issues:
                        for issue in issues:
                            print(f"  - {issue}")
                    else:
                        print(f"  - 无")
                    
                    print(f"\n💡 建议:")
                    recommendations = diagnosis.get("recommendations", [])
                    if recommendations:
                        for rec in recommendations:
                            print(f"  - {rec}")
                    else:
                        print(f"  - 无")
                    
                    # 保存完整诊断信息到文件
                    output_file = project_root / "execution_diagnosis.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(diagnosis, f, indent=2, ensure_ascii=False)
                    print(f"\n✅ 完整诊断信息已保存到: {output_file}")
                else:
                    print(f"❌ 诊断失败: HTTP {response.status_code}")
                    print(f"   响应: {response.text}")
        else:
            print(f"❌ 获取执行记录失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器 (http://localhost:8080)")
        print("   请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_executions()

