#!/bin/bash

# 轻量级评测脚本 - 快速验证性能监控功能
echo "🚀 启动轻量级评测模式..."

# 设置评测参数
LIGHTWEIGHT_SAMPLE_COUNT=2
EVALUATION_TIMEOUT=60

# 创建轻量级评测配置
mkdir -p config
cat > config/lightweight_evaluation_config.json << 'EOF'
{
    "evaluation_mode": "lightweight",
    "sample_count": 2,
    "timeout_seconds": 60,
    "max_reasoning_steps": 2,
    "skip_complex_reasoning": true
}
EOF

echo "✅ 轻量级评测配置已创建"

# 运行轻量级评测
python3 -c "
import asyncio
import json
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

from utils.enhanced_performance_example import start_evaluation, end_evaluation, ModulePerformanceContext
from unified_research_system import UnifiedResearchSystem

async def lightweight_eval():
    print('🧪 开始轻量级评测...')
    
    # 开始性能监控
    evaluation_id = f'lightweight_eval_{int(time.time())}'
    start_evaluation(evaluation_id)
    print(f'📊 性能监控评测ID: {evaluation_id}')
    
    # 使用简单的测试查询
    queries = [
        'What is 2+2?',
        'What is the capital of France?'
    ]
    
    results = []
    
    # 初始化系统
    print('🔧 初始化系统...')
    with ModulePerformanceContext('system_initialization', 'main'):
        system = UnifiedResearchSystem()
        await system.initialize()
        print('✅ 系统初始化完成')
    
    # 处理查询
    for i, query in enumerate(queries, 1):
        print(f'🔍 处理查询 {i}/{len(queries)}: {query}')
        
        try:
            with ModulePerformanceContext(f'query_{i}', 'main') as ctx:
                # 设置较短的超时时间
                from unified_research_system import ResearchRequest
                request = ResearchRequest(query=query)
                result = await asyncio.wait_for(
                    system.execute_research(request),
                    timeout=30
                )
                
                if result and isinstance(result, dict):
                    results.append({
                        'query': query,
                        'status': 'success',
                        'answer': result.get('answer', '无答案'),
                        'execution_time': 0.0  # 由性能监控自动记录
                    })
                    print(f'✅ 查询 {i} 成功')
                else:
                    results.append({
                        'query': query,
                        'status': 'no_result',
                        'answer': '无结果',
                        'execution_time': 0.0
                    })
                    print(f'⚠️ 查询 {i} 无结果')
                    
        except asyncio.TimeoutError:
            results.append({
                'query': query,
                'status': 'timeout',
                'answer': '查询超时',
                'execution_time': 30.0
            })
            print(f'⏰ 查询 {i} 超时')
        except Exception as e:
            results.append({
                'query': query,
                'status': 'error',
                'answer': f'执行失败: {str(e)}',
                'execution_time': 0.0
            })
            print(f'❌ 查询 {i} 失败: {e}')
    
    # 结束性能监控并获取报告
    print('\\n📊 生成性能监控报告...')
    performance_report = end_evaluation()
    
    if performance_report:
        print('✅ 性能监控报告生成成功!')
        
        # 保存详细结果
        output_file = 'comprehensive_eval_results/lightweight_evaluation_results.json'
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        detailed_results = {
            'evaluation_mode': 'lightweight',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'evaluation_id': performance_report.evaluation_id,
            'total_queries': len(queries),
            'successful_queries': len([r for r in results if r['status'] == 'success']),
            'results': results,
            'performance_monitoring': {
                'evaluation_id': performance_report.evaluation_id,
                'total_duration': performance_report.total_duration,
                'quality_score': performance_report.quality_score,
                'execution_paths': performance_report.execution_paths_summary,
                'bottlenecks': performance_report.bottlenecks,
                'recommendations': performance_report.recommendations,
                'modules_performance': {
                    name: {
                        'execution_time': trace.execution_time,
                        'execution_path': trace.execution_path,
                        'success': trace.success,
                        'sub_modules': trace.sub_modules,
                        'exception_type': trace.exception_type,
                        'fallback_reason': trace.fallback_reason
                    }
                    for name, trace in performance_report.modules_performance.items()
                }
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        
        print(f'📁 详细结果已保存到: {output_file}')
        
        # 显示性能监控摘要
        print(f'\\n📊 性能监控摘要:')
        print(f'  评测ID: {performance_report.evaluation_id}')
        print(f'  总耗时: {performance_report.total_duration:.3f}秒')
        print(f'  模块数量: {len(performance_report.modules_performance)}')
        print(f'  质量分数: {performance_report.quality_score:.1f}/100')
        
        # 显示执行路径统计
        if performance_report.execution_paths_summary:
            print(f'  执行路径统计:')
            for path, count in performance_report.execution_paths_summary.items():
                print(f'    {path}: {count}次')
        
        # 显示详细模块性能
        print(f'\\n🔍 详细模块性能:')
        for module_name, trace in performance_report.modules_performance.items():
            print(f'  {module_name}:')
            print(f'    执行时间: {trace.execution_time:.3f}秒')
            print(f'    执行路径: {trace.execution_path}')
            print(f'    执行状态: {\"成功\" if trace.success else \"失败\"}')
            if trace.sub_modules:
                print(f'    子模块执行时间:')
                for sub_name, sub_time in trace.sub_modules.items():
                    print(f'      {sub_name}: {sub_time:.3f}秒')
            if trace.exception_type:
                print(f'    异常类型: {trace.exception_type}')
            if trace.fallback_reason:
                print(f'    回退原因: {trace.fallback_reason}')
            print()
        
        return True
    else:
        print('❌ 性能监控报告生成失败')
        return False

# 运行轻量级评测
success = asyncio.run(lightweight_eval())
if success:
    print('\\n🎉 轻量级评测完成!')
else:
    print('\\n💥 轻量级评测失败!')
    sys.exit(1)
"

echo "📊 轻量级评测完成！"
echo "📁 结果文件: comprehensive_eval_results/lightweight_evaluation_results.json"
