#!/usr/bin/env python3
"""
协作架构演示脚本
展示新的模块协作机制和智能工作流
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.unified_collaboration_interface import (
    get_unified_collaboration_interface,
    create_collaboration_context,
    CollaborationContext
)
from src.utils.module_collaboration_manager import (
    get_module_collaboration_manager,
    register_collaboration_module
)
from src.utils.intelligent_workflow_coordinator import (
    get_intelligent_workflow_coordinator,
    execute_workflow,
    get_workflow_status,
    WorkflowPriority
)
from src.agents.enhanced_reasoning_agent import DefaultIntelligentScorer
from src.utils.feature_extractor import get_feature_extractor

class CollaborationArchitectureDemo:
    """协作架构演示类"""
    
    def __init__(self):
        self.collaboration_interface = get_unified_collaboration_interface()
        self.collaboration_manager = get_module_collaboration_manager()
        self.workflow_coordinator = get_intelligent_workflow_coordinator()
        
        self._setup_modules()
    
    def _setup_modules(self):
        """设置协作模块"""
        try:
            # 注册特征提取器
            feature_extractor = get_feature_extractor()
            register_collaboration_module('feature_extractor', feature_extractor)
            print("✅ 特征提取器注册成功")
            
            # 注册智能评分器
            intelligent_scorer = DefaultIntelligentScorer()
            register_collaboration_module('intelligent_scorer', intelligent_scorer, 
                                       dependencies=['feature_extractor'])
            print("✅ 智能评分器注册成功")
            
        except Exception as e:
            print(f"⚠️ 模块注册失败: {e}")
    
    def demonstrate_basic_collaboration(self):
        """演示基础协作功能"""
        print("\n" + "="*60)
        print("🚀 基础协作功能演示")
        print("="*60)
        
        # 创建协作上下文
        context = create_collaboration_context(
            session_id=f"demo_session_{int(time.time())}",
            domain="technology",
            priority="high",
            processing_mode="standard"
        )
        
        # 测试文本
        test_text = "人工智能在医疗领域的应用前景如何？"
        print(f"📝 测试文本: {test_text}")
        
        # 执行协作分析
        print("\n🔄 执行协作分析...")
        start_time = time.time()
        
        try:
            result = self.collaboration_interface.analyze_text_with_collaboration(test_text, context)
            processing_time = time.time() - start_time
            
            print(f"✅ 协作分析完成，耗时: {processing_time:.2f}秒")
            print(f"📊 分析结果: {result.get('success', False)}")
            
            if result.get('success'):
                analysis_summary = result.get('analysis_summary', {})
                print(f"   - 文本长度: {analysis_summary.get('text_length', 0)}")
                print(f"   - 特征数量: {analysis_summary.get('feature_count', 0)}")
                print(f"   - 质量评分: {analysis_summary.get('quality_score', 0):.3f}")
                print(f"   - 相关性评分: {analysis_summary.get('relevance_score', 0):.3f}")
                print(f"   - 置信度评分: {analysis_summary.get('confidence_score', 0):.3f}")
            
        except Exception as e:
            print(f"❌ 协作分析失败: {e}")
    
    def demonstrate_workflow_coordination(self):
        """演示工作流协调功能"""
        print("\n" + "="*60)
        print("🎯 智能工作流协调演示")
        print("="*60)
        
        # 获取可用工作流
        available_workflows = self.workflow_coordinator.get_available_workflows()
        print(f"📋 可用工作流: {', '.join(available_workflows)}")
        
        # 执行智能分析工作流
        print("\n🔄 执行智能分析工作流...")
        input_data = {
            'text': '深度学习在自然语言处理中的最新进展',
            'domain': 'artificial_intelligence',
            'priority': 'high'
        }
        
        try:
            execution_id = execute_workflow('intelligent_analysis', input_data, WorkflowPriority.HIGH)
            print(f"✅ 工作流启动成功，执行ID: {execution_id}")
            
            # 监控工作流状态
            print("\n📊 监控工作流状态...")
            for i in range(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))):  # 最多等待10次
                status = get_workflow_status(execution_id)
                if status:
                    print(f"   状态: {status['status']}, 完成步骤: {len(status['completed_steps'])}/{len(status['pending_steps'])}")
                    
                    if status['status'] in ['completed', 'failed', 'cancelled']:
                        break
                
                time.sleep(1)  # 等待1秒
            
            # 获取最终结果
            final_status = get_workflow_status(execution_id)
            if final_status:
                print(f"\n🎉 工作流执行完成!")
                print(f"   最终状态: {final_status['status']}")
                print(f"   完成步骤: {len(final_status['completed_steps'])}")
                print(f"   错误数量: {len(final_status['errors'])}")
                
                if final_status['errors']:
                    print(f"   错误详情: {final_status['errors']}")
            
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
    
    def demonstrate_performance_monitoring(self):
        """演示性能监控功能"""
        print("\n" + "="*60)
        print("📈 性能监控演示")
        print("="*60)
        
        # 获取协作性能指标
        try:
            collaboration_performance = self.collaboration_interface.get_collaboration_performance()
            print("🔍 协作性能指标:")
            print(f"   - 总会话数: {collaboration_performance.get('total_sessions', 0)}")
            print(f"   - 最近会话数: {collaboration_performance.get('recent_sessions', 0)}")
            print(f"   - 平均处理时间: {collaboration_performance.get('avg_processing_time', 0):.3f}秒")
            print(f"   - 成功率: {collaboration_performance.get('success_rate', 0):.1%}")
            print(f"   - 性能趋势: {collaboration_performance.get('performance_trend', 'unknown')}")
            
        except Exception as e:
            print(f"⚠️ 获取协作性能指标失败: {e}")
        
        # 获取模块性能指标
        try:
            module_performance = self.collaboration_manager.get_overall_performance()
            print("\n🔍 模块性能指标:")
            print(f"   - 总模块数: {module_performance.get('total_modules', 0)}")
            print(f"   - 总调用数: {module_performance.get('total_calls', 0)}")
            print(f"   - 整体成功率: {module_performance.get('overall_success_rate', 0):.1%}")
            print(f"   - 平均响应时间: {module_performance.get('overall_avg_response_time', 0):.3f}秒")
            
        except Exception as e:
            print(f"⚠️ 获取模块性能指标失败: {e}")
        
        # 获取工作流性能指标
        try:
            workflow_performance = self.workflow_coordinator.get_workflow_performance()
            print("\n🔍 工作流性能指标:")
            print(f"   - 总执行数: {workflow_performance.get('total_executions', 0)}")
            print(f"   - 成功执行数: {workflow_performance.get('successful_executions', 0)}")
            print(f"   - 成功率: {workflow_performance.get('success_rate', 0):.1%}")
            print(f"   - 平均执行时间: {workflow_performance.get('avg_execution_time', 0):.3f}秒")
            print(f"   - 性能趋势: {workflow_performance.get('performance_trend', 'unknown')}")
            
        except Exception as e:
            print(f"⚠️ 获取工作流性能指标失败: {e}")
    
    def demonstrate_advanced_features(self):
        """演示高级功能"""
        print("\n" + "="*60)
        print("🚀 高级功能演示")
        print("="*60)
        
        # 演示批量处理
        print("📦 批量处理演示...")
        test_texts = [
            "机器学习的基本原理是什么？",
            "深度学习与传统机器学习的区别？",
            "人工智能在金融领域的应用"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"   处理文本 {i}: {text[:30]}...")
            context = create_collaboration_context(
                session_id=f"batch_demo_{i}_{int(time.time())}",
                domain="technology",
                priority="normal"
            )
            
            try:
                result = self.collaboration_interface.analyze_text_with_collaboration(text, context)
                if result.get('success'):
                    quality_score = result.get('analysis_summary', {}).get('quality_score', 0)
                    print(f"     ✅ 质量评分: {quality_score:.3f}")
                else:
                    print(f"     ❌ 处理失败")
            except Exception as e:
                print(f"     ❌ 异常: {e}")
        
        # 演示自定义工作流
        print("\n🔧 自定义工作流演示...")
        try:
            from src.utils.intelligent_workflow_coordinator import WorkflowStep
            
            custom_steps = [
                WorkflowStep(
                    step_id='custom_analysis',
                    step_name='自定义分析',
                    module_name='intelligent_scorer',
                    timeout=15.0
                )
            ]
            
            self.workflow_coordinator.create_custom_workflow('custom_analysis', custom_steps)
            print("   ✅ 自定义工作流创建成功")
            
            # 执行自定义工作流
            execution_id = execute_workflow('custom_analysis', {'text': '测试文本'})
            print(f"   ✅ 自定义工作流执行启动，ID: {execution_id}")
            
        except Exception as e:
            print(f"   ❌ 自定义工作流创建失败: {e}")
    
    def run_demo(self):
        """运行完整演示"""
        print("🎉 RANGEN 协作架构演示")
        print("="*60)
        print("本演示将展示以下功能:")
        print("1. 基础协作功能")
        print("2. 智能工作流协调")
        print("3. 性能监控")
        print("4. 高级功能")
        print("="*60)
        
        try:
            # 基础协作演示
            self.demonstrate_basic_collaboration()
            
            # 工作流协调演示
            self.demonstrate_workflow_coordination()
            
            # 性能监控演示
            self.demonstrate_performance_monitoring()
            
            # 高级功能演示
            self.demonstrate_advanced_features()
            
            print("\n" + "="*60)
            print("🎊 演示完成!")
            print("="*60)
            print("协作架构特点:")
            print("✅ 模块职责明确，避免功能重复")
            print("✅ 统一协作接口，标准化数据格式")
            print("✅ 智能工作流编排，动态优化")
            print("✅ 实时性能监控，自适应调整")
            print("✅ 支持并行处理和批量操作")
            
        except Exception as e:
            print(f"\n❌ 演示过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    demo = CollaborationArchitectureDemo()
    demo.run_demo()

if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
