#!/usr/bin/env python3
"""
分析研究系统运行时的对象增长 - 找出45万+对象的来源
"""

import asyncio
import gc
import sys
import psutil
import time
import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入研究系统
from src.unified_research_system import UnifiedResearchSystem, ResearchRequest

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchSystemObjectAnalyzer:
    """研究系统对象分析器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.snapshots = []
        
    def take_snapshot(self, label: str) -> Dict[str, Any]:
        """拍摄对象快照"""
        objects = gc.get_objects()
        type_counter = Counter()
        module_counter = defaultdict(int)
        
        for obj in objects:
            obj_type = type(obj)
            type_name = obj_type.__name__
            module_name = obj_type.__module__
            full_name = f"{module_name}.{type_name}"
            
            type_counter[full_name] += 1
            module_counter[module_name] += 1
        
        snapshot = {
            'label': label,
            'timestamp': time.time(),
            'object_count': len(objects),
            'memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'type_distribution': dict(type_counter.most_common(20)),
            'module_distribution': dict(sorted(module_counter.items(), key=lambda x: x[1], reverse=True)[:20])
        }
        
        self.snapshots.append(snapshot)
        logger.info(f"📸 快照 '{label}': {snapshot['object_count']:,} 个对象, {snapshot['memory_mb']:.1f}MB")
        
        return snapshot
    
    def analyze_growth(self, snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> Dict[str, Any]:
        """分析两个快照之间的增长"""
        growth = {
            'object_growth': snapshot2['object_count'] - snapshot1['object_count'],
            'memory_growth': snapshot2['memory_mb'] - snapshot1['memory_mb'],
            'type_growth': {},
            'module_growth': {}
        }
        
        # 分析类型增长
        for type_name, count2 in snapshot2['type_distribution'].items():
            count1 = snapshot1['type_distribution'].get(type_name, 0)
            if count2 > count1:
                growth['type_growth'][type_name] = count2 - count1
        
        # 分析模块增长
        for module_name, count2 in snapshot2['module_distribution'].items():
            count1 = snapshot1['module_distribution'].get(module_name, 0)
            if count2 > count1:
                growth['module_growth'][module_name] = count2 - count1
        
        return growth
    
    async def analyze_research_system_lifecycle(self):
        """分析研究系统生命周期中的对象增长"""
        logger.info("🚀 开始分析研究系统生命周期...")
        
        # 1. 初始状态
        snapshot1 = self.take_snapshot("初始状态")
        
        # 2. 导入研究系统后
        logger.info("📦 导入研究系统...")
        snapshot2 = self.take_snapshot("导入研究系统后")
        
        # 3. 创建研究系统实例后
        logger.info("🔧 创建研究系统实例...")
        research_system = UnifiedResearchSystem(max_concurrent_queries=1)
        snapshot3 = self.take_snapshot("创建研究系统实例后")
        
        # 4. 执行第一个查询后
        logger.info("🔍 执行第一个查询...")
        request = ResearchRequest(
            query="What is the capital of France?",
            timeout=30.0
        )
        
        try:
            result = await asyncio.wait_for(
                research_system.execute_research(request),
                timeout=30.0
            )
            logger.info(f"✅ 第一个查询完成: {result.answer[:50]}...")
        except Exception as e:
            logger.error(f"❌ 第一个查询失败: {e}")
        
        snapshot4 = self.take_snapshot("执行第一个查询后")
        
        # 5. 执行第二个查询后
        logger.info("🔍 执行第二个查询...")
        request2 = ResearchRequest(
            query="Who wrote Romeo and Juliet?",
            timeout=30.0
        )
        
        try:
            result2 = await asyncio.wait_for(
                research_system.execute_research(request2),
                timeout=30.0
            )
            logger.info(f"✅ 第二个查询完成: {result2.answer[:50]}...")
        except Exception as e:
            logger.error(f"❌ 第二个查询失败: {e}")
        
        snapshot5 = self.take_snapshot("执行第二个查询后")
        
        # 6. 执行第三个查询后
        logger.info("🔍 执行第三个查询...")
        request3 = ResearchRequest(
            query="What is the largest planet in our solar system?",
            timeout=30.0
        )
        
        try:
            result3 = await asyncio.wait_for(
                research_system.execute_research(request3),
                timeout=30.0
            )
            logger.info(f"✅ 第三个查询完成: {result3.answer[:50]}...")
        except Exception as e:
            logger.error(f"❌ 第三个查询失败: {e}")
        
        snapshot6 = self.take_snapshot("执行第三个查询后")
        
        # 分析增长
        logger.info("\n" + "="*80)
        logger.info("📊 研究系统生命周期对象增长分析")
        logger.info("="*80)
        
        snapshots = [snapshot1, snapshot2, snapshot3, snapshot4, snapshot5, snapshot6]
        
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]
            growth = self.analyze_growth(prev, curr)
            
            logger.info(f"\n📈 {prev['label']} -> {curr['label']}:")
            logger.info(f"  对象增长: {growth['object_growth']:,}")
            logger.info(f"  内存增长: {growth['memory_growth']:+.1f}MB")
            
            if growth['type_growth']:
                logger.info(f"  主要类型增长:")
                sorted_types = sorted(growth['type_growth'].items(), key=lambda x: x[1], reverse=True)
                for type_name, count in sorted_types[:5]:
                    logger.info(f"    {type_name}: +{count:,}")
            
            if growth['module_growth']:
                logger.info(f"  主要模块增长:")
                sorted_modules = sorted(growth['module_growth'].items(), key=lambda x: x[1], reverse=True)
                for module_name, count in sorted_modules[:5]:
                    logger.info(f"    {module_name}: +{count:,}")
        
        # 总体分析
        total_growth = self.analyze_growth(snapshot1, snapshot6)
        logger.info(f"\n🎯 总体增长分析:")
        logger.info(f"  总对象增长: {total_growth['object_growth']:,}")
        logger.info(f"  总内存增长: {total_growth['memory_growth']:+.1f}MB")
        
        # 找出增长最多的类型和模块
        if total_growth['type_growth']:
            logger.info(f"\n🔍 增长最多的对象类型 (前10):")
            sorted_types = sorted(total_growth['type_growth'].items(), key=lambda x: x[1], reverse=True)
            for i, (type_name, count) in enumerate(sorted_types[:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
                percentage = count / total_growth['object_growth'] * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
                logger.info(f"  {i:2d}. {type_name}: +{count:,} ({percentage:.1f}%)")
        
        if total_growth['module_growth']:
            logger.info(f"\n📦 增长最多的模块 (前10):")
            sorted_modules = sorted(total_growth['module_growth'].items(), key=lambda x: x[1], reverse=True)
            for i, (module_name, count) in enumerate(sorted_modules[:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
                percentage = count / total_growth['object_growth'] * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
                logger.info(f"  {i:2d}. {module_name}: +{count:,} ({percentage:.1f}%)")
        
        return {
            'snapshots': snapshots,
            'total_growth': total_growth
        }
    
    def analyze_specific_objects(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """分析特定类型的对象"""
        logger.info("🔍 分析特定类型的对象...")
        
        objects = gc.get_objects()
        specific_analysis = {
            'functions': [],
            'classes': [],
            'instances': [],
            'modules': [],
            'large_objects': []
        }
        
        for obj in objects:
            obj_type = type(obj)
            type_name = obj_type.__name__
            module_name = obj_type.__module__
            
            try:
                size = sys.getsizeof(obj)
                
                if type_name == 'function':
                    specific_analysis['functions'].append({
                        'name': getattr(obj, '__name__', 'unknown'),
                        'module': getattr(obj, '__module__', 'unknown'),
                        'size': size
                    })
                elif type_name == 'type':
                    specific_analysis['classes'].append({
                        'name': getattr(obj, '__name__', 'unknown'),
                        'module': getattr(obj, '__module__', 'unknown'),
                        'size': size
                    })
                elif type_name == 'module':
                    specific_analysis['modules'].append({
                        'name': getattr(obj, '__name__', 'unknown'),
                        'size': size
                    })
                elif size > 1024:  # 大于1KB的对象
                    specific_analysis['large_objects'].append({
                        'type': type_name,
                        'module': module_name,
                        'size': size,
                        'repr': repr(obj)[:get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))] if hasattr(obj, '__repr__') else str(type(obj))
                    })
            except:
                pass
        
        # 排序
        specific_analysis['functions'].sort(key=lambda x: x['size'], reverse=True)
        specific_analysis['classes'].sort(key=lambda x: x['size'], reverse=True)
        specific_analysis['modules'].sort(key=lambda x: x['size'], reverse=True)
        specific_analysis['large_objects'].sort(key=lambda x: x['size'], reverse=True)
        
        return specific_analysis

async def main():
    """主函数"""
    logger.info("🔍 研究系统对象分析工具启动...")
    
    analyzer = ResearchSystemObjectAnalyzer()
    results = await analyzer.analyze_research_system_lifecycle()
    
    # 分析最终状态的特定对象
    final_snapshot = results['snapshots'][-1]
    specific_analysis = analyzer.analyze_specific_objects(final_snapshot)
    
    logger.info(f"\n🔍 特定对象分析:")
    logger.info(f"  函数数量: {len(specific_analysis['functions'])}")
    logger.info(f"  类数量: {len(specific_analysis['classes'])}")
    logger.info(f"  模块数量: {len(specific_analysis['modules'])}")
    logger.info(f"  大对象数量: {len(specific_analysis['large_objects'])}")
    
    if specific_analysis['large_objects']:
        logger.info(f"\n💾 最大的对象 (前5):")
        for i, obj in enumerate(specific_analysis['large_objects'][:5], 1):
            size_mb = obj['size'] / 1024 / 1024
            logger.info(f"  {i}. {obj['type']} ({obj['module']}): {size_mb:.1f}MB")
    
    # 保存结果
    import json
    output_file = "research_system_object_analysis.json"
    
    # 转换不可序列化的对象
    serializable_results = {
        'snapshots': results['snapshots'],
        'total_growth': results['total_growth'],
        'specific_analysis': {
            'functions_count': len(specific_analysis['functions']),
            'classes_count': len(specific_analysis['classes']),
            'modules_count': len(specific_analysis['modules']),
            'large_objects_count': len(specific_analysis['large_objects']),
            'top_large_objects': specific_analysis['large_objects'][:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))]
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 详细分析结果已保存到: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
