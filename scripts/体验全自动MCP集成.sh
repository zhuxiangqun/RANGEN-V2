#!/bin/bash
# 全自动MCP集成系统体验脚本
# 运行此脚本体验完整的自动发现和集成流程

echo "🚀 RANGEN V2 全自动MCP集成系统体验"
echo "======================================"

# 首先检查服务器是否运行
echo -e "\n🔍 检查后端API服务器状态..."
if curl -s --max-time 2 http://localhost:8000/autodiscovery/health > /dev/null 2>&1; then
    echo "✅ 后端API服务器正在运行 (localhost:8000)"
else
    echo "❌ 后端API服务器未运行"
    echo ""
    echo "请先启动后端服务器:"
    echo "  1. 进入项目目录: cd /Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
    echo "  2. 启动服务器: python3 -m src.api.server"
    echo ""
    echo "或者使用以下命令快速启动:"
    echo "  cd /Users/apple/workdata/person/zy/RANGEN-main(syu-python) && python3 -m src.api.server &"
    echo ""
    echo "⚠️  注意: 如果您担心DeepSeek API费用，可以在启动前修改配置使用本地模型"
    echo "      或者仅测试自动发现功能（不依赖LLM调用）"
    exit 1
fi

# 检查后端服务
echo -e "\n1️⃣  检查后端API服务状态..."
curl -s http://localhost:8000/autodiscovery/health | python3 -m json.tool

echo -e "\n2️⃣  查看自动发现状态..."
curl -s http://localhost:8000/autodiscovery/status | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'状态: {data[\"status\"]}')
print(f'发现目标数: {data[\"target_count\"]}')
print(f'已发现资源数: {data[\"discovered_count\"]}')
print(f'最后发现时间: {data[\"last_discovery\"]}')
"

echo -e "\n3️⃣  查看已发现的资源..."
curl -s http://localhost:8000/autodiscovery/resources | python3 -c "
import json, sys
resources = json.load(sys.stdin)
print(f'共发现 {len(resources)} 个资源:')
for i, res in enumerate(resources, 1):
    print(f'  {i}. {res[\"name\"]} ({res[\"resource_type\"]})')
    print(f'     端点: {res[\"endpoint\"]}')
    print(f'     置信度: {res[\"confidence\"]}')
    print(f'     能力: {res[\"capabilities\"]}')
"

echo -e "\n4️⃣  模拟Agent需求触发自动集成..."
echo "  请求: '帮我写Python代码调试程序'"
curl -X POST -s "http://localhost:8000/autodiscovery/trigger/agent-demand?query=帮我写Python代码调试程序" | python3 -m json.tool

echo -e "\n5️⃣  自动集成已发现的资源..."
curl -X POST -s http://localhost:8000/autodiscovery/auto-integrate | python3 -c "
import json, sys
result = json.load(sys.stdin)
print(f'总资源数: {result[\"total_resources\"]}')
print(f'成功集成: {result[\"integrated_count\"]}')
print('集成结果:')
for res in result['results']:
    status = '✅' if res['integrated'] else '❌'
    print(f'  {status} {res[\"name\"]} ({res[\"type\"]})')
"

echo -e "\n6️⃣  查看路由监控统计..."
curl -s http://localhost:8000/api/routing/statistics | python3 -c "
import json, sys
stats = json.load(sys.stdin)
print(f'总查询数: {stats[\"total_queries\"]}')
print(f'技能路由次数: {stats[\"skill_routing_count\"]}')
print(f'工具路由次数: {stats[\"tool_routing_count\"]}')
print(f'本地资源数: {stats[\"local_resource_count\"]}')
print(f'外部资源数: {stats[\"external_resource_count\"]}')
"

echo -e "\n🎉 体验完成！"
echo -e "\n📋 访问方式:"
echo "  - 后端API: http://localhost:8000/docs (完整API文档)"
echo "  - 前端监控: http://localhost:3000 (路由监控界面)"
echo "  - 路由监控标签页: http://localhost:3000/#/routing"

echo -e "\n🔧 快速测试命令:"
echo "  # 健康检查"
echo "  curl http://localhost:8000/autodiscovery/health"
echo ""
echo "  # 启动新的发现扫描"
echo "  curl -X POST http://localhost:8000/autodiscovery/scan"
echo ""
echo "  # 一键发现并集成"
echo "  curl -X POST http://localhost:8000/autodiscovery/discover-and-integrate"