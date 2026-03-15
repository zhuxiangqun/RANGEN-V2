#!/usr/bin/env python3
"""
深度对象分析 - 详细分析45万+对象的具体构成
"""

import gc
import sys
import psutil
import time
import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import tracemalloc
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入研究系统
from src.unified_research_system import UnifiedResearchSystem, ResearchRequest

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepObjectAnalyzer:
    """深度对象分析器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.analysis_results = {}
        
    def analyze_object_types(self) -> Dict[str, Any]:
        """分析对象类型分布"""
        logger.info("🔍 开始分析对象类型分布...")
        
        objects = gc.get_objects()
        type_counter = Counter()
        type_sizes = defaultdict(int)
        type_instances = defaultdict(list)
        
        for obj in objects:
            obj_type = type(obj)
            type_name = obj_type.__name__
            type_module = obj_type.__module__
            full_name = f"{type_module}.{type_name}"
            
            type_counter[full_name] += 1
            
            try:
                size = sys.getsizeof(obj)
                type_sizes[full_name] += size
                
                # 收集一些实例用于详细分析
                if len(type_instances[full_name]) < 5:
                    type_instances[full_name].append({
                        'id': id(obj),
                        'size': size,
                        'repr': repr(obj)[:get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))] if hasattr(obj, '__repr__') else str(type(obj))
                    })
            except Exception as e:
                logger.debug(f"无法获取对象大小: {e}")
        
        # 按数量排序
        top_types_by_count = type_counter.most_common(50)
        
        # 按大小排序
        top_types_by_size = sorted(type_sizes.items(), key=lambda x: x[1], reverse=True)[:50]
        
        result = {
            'total_objects': len(objects),
            'unique_types': len(type_counter),
            'top_types_by_count': top_types_by_count,
            'top_types_by_size': top_types_by_size,
            'type_instances': dict(type_instances)
        }
        
        logger.info(f"📊 对象类型分析完成: 总计 {len(objects):,} 个对象, {len(type_counter)} 种类型")
        return result
    
    def analyze_module_objects(self) -> Dict[str, Any]:
        """分析模块相关的对象"""
        logger.info("🔍 开始分析模块相关对象...")
        
        objects = gc.get_objects()
        module_counter = defaultdict(int)
        module_sizes = defaultdict(int)
        
        for obj in objects:
            obj_type = type(obj)
            module_name = obj_type.__module__
            
            module_counter[module_name] += 1
            
            try:
                size = sys.getsizeof(obj)
                module_sizes[module_name] += size
            except:
                pass
        
        # 按数量排序
        top_modules_by_count = sorted(module_counter.items(), key=lambda x: x[1], reverse=True)[:30]
        
        # 按大小排序
        top_modules_by_size = sorted(module_sizes.items(), key=lambda x: x[1], reverse=True)[:30]
        
        result = {
            'total_modules': len(module_counter),
            'top_modules_by_count': top_modules_by_count,
            'top_modules_by_size': top_modules_by_size
        }
        
        logger.info(f"📊 模块分析完成: {len(module_counter)} 个模块")
        return result
    
    def analyze_large_objects(self, min_size: int = 1024) -> Dict[str, Any]:
        """分析大对象"""
        logger.info(f"🔍 开始分析大对象 (>{min_size}字节)...")
        
        objects = gc.get_objects()
        large_objects = []
        
        for obj in objects:
            try:
                size = sys.getsizeof(obj)
                if size >= min_size:
                    large_objects.append({
                        'type': type(obj).__name__,
                        'module': type(obj).__module__,
                        'size': size,
                        'id': id(obj),
                        'repr': repr(obj)[:200] if hasattr(obj, '__repr__') else str(type(obj))
                    })
            except:
                pass
        
        # 按大小排序
        large_objects.sort(key=lambda x: x['size'], reverse=True)
        
        result = {
            'total_large_objects': len(large_objects),
            'total_size': sum(obj['size'] for obj in large_objects),
            'top_large_objects': large_objects[:50]
        }
        
        logger.info(f"📊 大对象分析完成: {len(large_objects)} 个大对象, 总大小 {result['total_size']/1024/1024:.1f}MB")
        return result
    
    def analyze_circular_references(self) -> Dict[str, Any]:
        """分析循环引用"""
        logger.info("🔍 开始分析循环引用...")
        
        # 启用调试模式
        gc.set_debug(gc.DEBUG_SAVEALL)
        
        # 收集垃圾
        collected = gc.collect()
        
        # 获取垃圾收集器中的对象
        garbage = gc.garbage
        
        # 重置调试模式
        gc.set_debug(0)
        
        result = {
            'collected_objects': collected,
            'garbage_objects': len(garbage),
            'garbage_types': Counter(type(obj).__name__ for obj in garbage).most_common(20)
        }
        
        logger.info(f"📊 循环引用分析完成: 收集了 {collected} 个对象, {len(garbage)} 个垃圾对象")
        return result
    
    def analyze_memory_regions(self) -> Dict[str, Any]:
        """分析内存区域"""
        logger.info("🔍 开始分析内存区域...")
        
        # 使用tracemalloc分析内存使用
        tracemalloc.start()
        
        # 获取当前内存快照
        snapshot = tracemalloc.take_snapshot()
        
        # 按大小排序的统计信息
        top_stats = snapshot.statistics('lineno')
        
        # 按内存使用量排序
        memory_stats = []
        for stat in top_stats[:50]:
            memory_stats.append({
                'filename': stat.traceback.format()[0] if stat.traceback.format() else 'Unknown',
                'size': stat.size,
                'count': stat.count,
                'size_mb': stat.size / 1024 / 1024
            })
        
        tracemalloc.stop()
        
        result = {
            'total_memory_traced': sum(stat.size for stat in top_stats),
            'top_memory_usage': memory_stats
        }
        
        logger.info(f"📊 内存区域分析完成: 追踪了 {result['total_memory_traced']/1024/1024:.1f}MB")
        return result
    
    def analyze_research_system_objects(self) -> Dict[str, Any]:
        """分析研究系统相关的对象"""
        logger.info("🔍 开始分析研究系统相关对象...")
        
        objects = gc.get_objects()
        research_objects = defaultdict(int)
        research_sizes = defaultdict(int)
        
        # 定义研究系统相关的模块前缀
        research_modules = [
            'src.unified_research_system',
            'src.agents',
            'src.utils',
            'src.memory',
            'src.knowledge',
            'transformers',
            'torch',
            'faiss',
            'sentence_transformers',
            'wikipediaapi'
        ]
        
        for obj in objects:
            obj_type = type(obj)
            module_name = obj_type.__module__
            
            # 检查是否属于研究系统相关模块
            for research_module in research_modules:
                if module_name.startswith(research_module):
                    research_objects[module_name] += 1
                    
                    try:
                        size = sys.getsizeof(obj)
                        research_sizes[module_name] += size
                    except:
                        pass
                    break
        
        # 按数量排序
        top_research_by_count = sorted(research_objects.items(), key=lambda x: x[1], reverse=True)
        
        # 按大小排序
        top_research_by_size = sorted(research_sizes.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'total_research_objects': sum(research_objects.values()),
            'total_research_size': sum(research_sizes.values()),
            'top_research_by_count': top_research_by_count,
            'top_research_by_size': top_research_by_size
        }
        
        logger.info(f"📊 研究系统对象分析完成: {result['total_research_objects']:,} 个对象, {result['total_research_size']/1024/1024:.1f}MB")
        return result
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """运行综合分析"""
        logger.info("🚀 开始深度对象分析...")
        
        # 初始快照
        initial_objects = len(gc.get_objects())
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        logger.info(f"📸 初始状态: {initial_objects:,} 个对象, {initial_memory:.1f}MB")
        
        # 运行各种分析
        results = {
            'initial_state': {
                'object_count': initial_objects,
                'memory_mb': initial_memory
            },
            'object_types': self.analyze_object_types(),
            'module_objects': self.analyze_module_objects(),
            'large_objects': self.analyze_large_objects(),
            'circular_references': self.analyze_circular_references(),
            'memory_regions': self.analyze_memory_regions(),
            'research_system_objects': self.analyze_research_system_objects()
        }
        
        # 最终快照
        final_objects = len(gc.get_objects())
        final_memory = self.process.memory_info().rss / 1024 / 1024
        
        results['final_state'] = {
            'object_count': final_objects,
            'memory_mb': final_memory
        }
        
        logger.info(f"📸 最终状态: {final_objects:,} 个对象, {final_memory:.1f}MB")
        
        return results
    
    def print_analysis_summary(self, results: Dict[str, Any]):
        """打印分析摘要"""
        logger.info("\n" + "="*80)
        logger.info("📊 深度对象分析结果摘要")
        logger.info("="*80)
        
        # 基本统计
        initial = results['initial_state']
        final = results['final_state']
        
        logger.info(f"\n📈 基本统计:")
        logger.info(f"  初始对象数: {initial['object_count']:,}")
        logger.info(f"  最终对象数: {final['object_count']:,}")
        logger.info(f"  对象增长: {final['object_count'] - initial['object_count']:,}")
        logger.info(f"  初始内存: {initial['memory_mb']:.1f}MB")
        logger.info(f"  最终内存: {final['memory_mb']:.1f}MB")
        logger.info(f"  内存增长: {final['memory_mb'] - initial['memory_mb']:.1f}MB")
        
        # 对象类型分析
        obj_types = results['object_types']
        logger.info(f"\n🔍 对象类型分析:")
        logger.info(f"  总对象数: {obj_types['total_objects']:,}")
        logger.info(f"  唯一类型数: {obj_types['unique_types']:,}")
        
        logger.info(f"\n📊 数量最多的对象类型 (前10):")
        for i, (type_name, count) in enumerate(obj_types['top_types_by_count'][:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
            percentage = count / obj_types['total_objects'] * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
            logger.info(f"  {i:2d}. {type_name}: {count:,} ({percentage:.1f}%)")
        
        logger.info(f"\n💾 占用内存最多的对象类型 (前10):")
        for i, (type_name, size) in enumerate(obj_types['top_types_by_size'][:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
            size_mb = size / 1024 / 1024
            logger.info(f"  {i:2d}. {type_name}: {size_mb:.1f}MB")
        
        # 模块分析
        module_analysis = results['module_objects']
        logger.info(f"\n📦 模块分析:")
        logger.info(f"  总模块数: {module_analysis['total_modules']}")
        
        logger.info(f"\n📊 对象数量最多的模块 (前10):")
        for i, (module_name, count) in enumerate(module_analysis['top_modules_by_count'][:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
            percentage = count / obj_types['total_objects'] * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
            logger.info(f"  {i:2d}. {module_name}: {count:,} ({percentage:.1f}%)")
        
        # 大对象分析
        large_objects = results['large_objects']
        logger.info(f"\n🔍 大对象分析:")
        logger.info(f"  大对象数量: {large_objects['total_large_objects']:,}")
        logger.info(f"  大对象总大小: {large_objects['total_size']/1024/1024:.1f}MB")
        
        if large_objects['top_large_objects']:
            logger.info(f"\n💾 最大的对象 (前5):")
            for i, obj in enumerate(large_objects['top_large_objects'][:5], 1):
                size_mb = obj['size'] / 1024 / 1024
                logger.info(f"  {i}. {obj['type']} ({obj['module']}): {size_mb:.1f}MB")
        
        # 研究系统对象分析
        research_objects = results['research_system_objects']
        logger.info(f"\n🤖 研究系统相关对象:")
        logger.info(f"  研究系统对象数: {research_objects['total_research_objects']:,}")
        logger.info(f"  研究系统对象大小: {research_objects['total_research_size']/1024/1024:.1f}MB")
        
        logger.info(f"\n📊 研究系统模块对象分布 (前10):")
        for i, (module_name, count) in enumerate(research_objects['top_research_by_count'][:get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))], 1):
            percentage = count / research_objects['total_research_objects'] * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
            logger.info(f"  {i:2d}. {module_name}: {count:,} ({percentage:.1f}%)")
        
        # 循环引用分析
        circular_refs = results['circular_references']
        logger.info(f"\n🔄 循环引用分析:")
        logger.info(f"  收集的对象数: {circular_refs['collected_objects']}")
        logger.info(f"  垃圾对象数: {circular_refs['garbage_objects']}")
        
        if circular_refs['garbage_types']:
            logger.info(f"\n🗑️ 垃圾对象类型 (前5):")
            for i, (type_name, count) in enumerate(circular_refs['garbage_types'][:5], 1):
                logger.info(f"  {i}. {type_name}: {count}")
        
        logger.info("\n" + "="*80)

def main():
    """主函数"""
    logger.info("🔍 深度对象分析工具启动...")
    
    analyzer = DeepObjectAnalyzer()
    results = analyzer.run_comprehensive_analysis()
    analyzer.print_analysis_summary(results)
    
    # 保存详细结果到文件
    import json
    output_file = "object_analysis_results.json"
    
    # 转换不可序列化的对象
    serializable_results = {}
    for key, value in results.items():
        try:
            json.dumps(value)
            serializable_results[key] = value
        except:
            serializable_results[key] = str(value)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 详细分析结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
