"""
AI中台能力评估系统 - 重组版

两种评估模式：
1. E2E集成测试 (--mode=e2e): 调用真实API测试24个维度
2. 静态代码分析 (--mode=static): 分析源码结构检查2个维度
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 测试模式配置
# ============================================================================

# 端到端集成测试维度 (24个)
E2E_DIMENSIONS = [
    # A. 基础能力 (4个)
    'orchestration',           # 编排能力
    'agent_completeness',      # Agent完备性
    'prompt_engineering',      # 提示词工程
    'context_engineering',     # 上下文工程
    
    # B. 智能能力 (7个)
    'response_quality',        # 回答质量
    'routing',                # 路由准确率
    'reasoning',               # 推理深度
    'knowledge_recall',       # 知识召回
    'tool_calling',           # 工具调用
    'multi_turn',             # 多轮对话
    'self_learning',          # 自学习能力
    
    # C. 架构能力 (4个)
    'harness',                # Harness能力
    'observability',          # 可观测性
    'monitoring',             # 监控告警
    'self_healing',           # 故障自愈
    'rollout',                # 灰度发布
    
    # D. 数据能力 (4个)
    'data_source',            # 数据源接入
    'knowledge_mgmt',         # 知识管理
    'vector_mgmt',            # 向量管理
    'data_lineage',           # 数据血缘
    
    # E. 平台能力 (3个)
    'app_support',            # 应用支撑
    'cost_control',           # 成本控制
    'integration',            # 集成扩展
    
    # S. 安全能力 (1个)
    'security',               # 安全能力
]

# 静态代码分析维度 (2个)
STATIC_DIMENSIONS = [
    'architecture',           # 架构合理性
    'code_quality',           # 代码质量
]

# 维度元数据
DIMENSION_META = {
    # A. 基础能力
    'orchestration': {'name': '编排能力', 'category': 'A', 'weight': 0.08, 'e2e': True},
    'agent_completeness': {'name': 'Agent完备性', 'category': 'A', 'weight': 0.06, 'e2e': True},
    'prompt_engineering': {'name': '提示词工程', 'category': 'A', 'weight': 0.06, 'e2e': True},
    'context_engineering': {'name': '上下文工程', 'category': 'A', 'weight': 0.05, 'e2e': True},
    
    # B. 智能能力
    'response_quality': {'name': '回答质量', 'category': 'B', 'weight': 0.18, 'e2e': True},
    'routing': {'name': '路由准确率', 'category': 'B', 'weight': 0.08, 'e2e': True},
    'reasoning': {'name': '推理深度', 'category': 'B', 'weight': 0.07, 'e2e': True},
    'knowledge_recall': {'name': '知识召回', 'category': 'B', 'weight': 0.06, 'e2e': True},
    'tool_calling': {'name': '工具调用', 'category': 'B', 'weight': 0.06, 'e2e': True},
    'multi_turn': {'name': '多轮对话', 'category': 'B', 'weight': 0.05, 'e2e': True},
    'self_learning': {'name': '自学习能力', 'category': 'B', 'weight': 0.05, 'e2e': True},
    
    # C. 架构能力
    'harness': {'name': 'Harness能力', 'category': 'C', 'weight': 0.06, 'e2e': True},
    'architecture': {'name': '架构合理性', 'category': 'C', 'weight': 0.05, 'e2e': False},
    'observability': {'name': '可观测性', 'category': 'C', 'weight': 0.05, 'e2e': True},
    'monitoring': {'name': '监控告警', 'category': 'C', 'weight': 0.04, 'e2e': True},
    'self_healing': {'name': '故障自愈', 'category': 'C', 'weight': 0.04, 'e2e': True},
    'rollout': {'name': '灰度发布', 'category': 'C', 'weight': 0.04, 'e2e': True},
    
    # D. 数据能力
    'data_source': {'name': '数据源接入', 'category': 'D', 'weight': 0.04, 'e2e': True},
    'knowledge_mgmt': {'name': '知识管理', 'category': 'D', 'weight': 0.03, 'e2e': True},
    'vector_mgmt': {'name': '向量管理', 'category': 'D', 'weight': 0.02, 'e2e': True},
    'data_lineage': {'name': '数据血缘', 'category': 'D', 'weight': 0.01, 'e2e': True},
    
    # E. 平台能力
    'app_support': {'name': '应用支撑', 'category': 'E', 'weight': 0.03, 'e2e': True},
    'cost_control': {'name': '成本控制', 'category': 'E', 'weight': 0.02, 'e2e': True},
    'integration': {'name': '集成扩展', 'category': 'E', 'weight': 0.02, 'e2e': True},
    
    # S. 安全能力
    'security': {'name': '安全能力', 'category': 'S', 'weight': 0.05, 'e2e': True},
    
    # Q. 代码质量
    'code_quality': {'name': '代码质量', 'category': 'Q', 'weight': 0.03, 'e2e': False},
}

CATEGORY_INFO = {
    'A': {'name': '基础能力', 'weight': 0.25},
    'B': {'name': '智能能力', 'weight': 0.30},
    'C': {'name': '架构能力', 'weight': 0.28},
    'D': {'name': '数据能力', 'weight': 0.10},
    'E': {'name': '平台能力', 'weight': 0.07},
    'S': {'name': '安全能力', 'weight': 0.00},  # 独立计算
    'Q': {'name': '代码质量', 'weight': 0.00},  # 独立计算
}


# ============================================================================
# 主评估器
# ============================================================================

class RANGENEvaluator:
    """RANGEN系统统一评估器"""
    
    def __init__(self, mode: str = 'all', config: Dict = None):
        """
        初始化评估器
        
        Args:
            mode: 评估模式 ('e2e', 'static', 'all')
            config: 配置参数
        """
        self.mode = mode
        self.config = config or {}
        self.source_path = self.config.get('source_path', '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src')
        self.system_url = self.config.get('system_url', 'http://localhost:8000')
        self.max_sample_count = self.config.get('max_sample_count', 10)
        self.max_concurrent = self.config.get('max_concurrent', 4)
        
        # 确定要评估的维度
        if mode == 'e2e':
            self.dimensions_to_eval = E2E_DIMENSIONS
        elif mode == 'static':
            self.dimensions_to_eval = STATIC_DIMENSIONS
        else:  # 'all'
            self.dimensions_to_eval = E2E_DIMENSIONS + STATIC_DIMENSIONS
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """运行评估"""
        results = {
            'mode': self.mode,
            'dimensions_tested': len(self.dimensions_to_eval),
            'dimension_results': {},
            'category_scores': {},
            'overall_score': 0.0,
            'summary': {}
        }
        
        if self.mode in ['e2e', 'all']:
            e2e_results = await self._run_e2e_evaluation()
            results['dimension_results'].update(e2e_results)
        
        if self.mode in ['static', 'all']:
            static_results = await self._run_static_evaluation()
            results['dimension_results'].update(static_results)
        
        # 计算各类别得分
        results['category_scores'] = self._calculate_category_scores(results['dimension_results'])
        
        # 计算总分
        results['overall_score'] = self._calculate_overall_score(results['category_scores'])
        
        # 生成摘要
        results['summary'] = self._generate_summary(results)
        
        return results
    
    async def _run_e2e_evaluation(self) -> Dict[str, Any]:
        """运行端到端集成测试"""
        from .e2e import E2EEvaluator
        
        results = {}
        evaluator = E2EEvaluator(self.config)
        
        logger.info(f"=" * 60)
        logger.info(f"📡 E2E端到端集成测试 ({len(E2E_DIMENSIONS)}个维度)")
        logger.info(f"=" * 60)
        
        for dimension in E2E_DIMENSIONS:
            logger.info(f"测试维度: {dimension}")
            try:
                result = await evaluator.evaluate(dimension)
                results[dimension] = result
                logger.info(f"  ✓ {dimension}: {result.get('score', 0):.2f}")
            except Exception as e:
                logger.error(f"  ✗ {dimension}: {e}")
                results[dimension] = {
                    'score': 0.0,
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    async def _run_static_evaluation(self) -> Dict[str, Any]:
        """运行静态代码分析"""
        from .static import StaticEvaluator
        
        results = {}
        evaluator = StaticEvaluator(self.config)
        
        logger.info(f"=" * 60)
        logger.info(f"🔍 静态代码分析 ({len(STATIC_DIMENSIONS)}个维度)")
        logger.info(f"=" * 60)
        
        for dimension in STATIC_DIMENSIONS:
            logger.info(f"分析维度: {dimension}")
            try:
                result = await evaluator.evaluate(dimension)
                results[dimension] = result
                logger.info(f"  ✓ {dimension}: {result.get('score', 0):.2f}")
            except Exception as e:
                logger.error(f"  ✗ {dimension}: {e}")
                results[dimension] = {
                    'score': 0.0,
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def _calculate_category_scores(self, dimension_results: Dict) -> Dict:
        """计算各类别得分"""
        category_scores = {}
        
        for dim_id, result in dimension_results.items():
            if dim_id not in DIMENSION_META:
                continue
            
            meta = DIMENSION_META[dim_id]
            category = meta['category']
            
            if category not in category_scores:
                category_scores[category] = {
                    'name': CATEGORY_INFO[category]['name'],
                    'weight': CATEGORY_INFO[category]['weight'],
                    'score': 0.0,
                    'dimensions': []
                }
            
            category_scores[category]['dimensions'].append({
                'id': dim_id,
                'name': meta['name'],
                'score': result.get('score', 0.0)
            })
            category_scores[category]['score'] += result.get('score', 0.0) * meta['weight']
        
        return category_scores
    
    def _calculate_overall_score(self, category_scores: Dict) -> float:
        """计算总分"""
        total_score = 0.0
        total_weight = 0.0
        
        for cat_id, cat_info in category_scores.items():
            if cat_info['weight'] > 0:
                total_score += cat_info['score']
                total_weight += cat_info['weight']
        
        if total_weight > 0:
            return total_score / total_weight
        return 0.0
    
    def _generate_summary(self, results: Dict) -> Dict:
        """生成摘要"""
        summary = {
            'total_dimensions': len(self.dimensions_to_eval),
            'passed': sum(1 for d in self.dimensions_to_eval 
                         if results['dimension_results'].get(d, {}).get('score', 0) >= 0.7),
            'failed': sum(1 for d in self.dimensions_to_eval 
                         if results['dimension_results'].get(d, {}).get('score', 0) < 0.5),
            'mode': self.mode
        }
        
        # 按类别统计
        category_summary = {}
        for cat_id, cat_info in results['category_scores'].items():
            category_summary[cat_id] = {
                'name': cat_info['name'],
                'score': cat_info['score'],
                'status': 'excellent' if cat_info['score'] >= 0.9 else 
                          'good' if cat_info['score'] >= 0.7 else
                          'fair' if cat_info['score'] >= 0.5 else 'poor'
            }
        summary['categories'] = category_summary
        
        return summary


# ============================================================================
# 命令行入口
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="RANGEN AI中台能力评估系统")
    parser.add_argument('--mode', choices=['e2e', 'static', 'all'], default='all',
                       help='评估模式: e2e=端到端测试, static=静态分析, all=全部')
    parser.add_argument('--sample-count', type=int, default=10,
                       help='每个维度的测试样本数 (默认: 10)')
    parser.add_argument('--max-concurrent', type=int, default=4,
                       help='最大并发数 (默认: 4)')
    parser.add_argument('--output', type=str, default=None,
                       help='输出结果文件路径')
    parser.add_argument('--verbose', action='store_true',
                       help='详细输出')
    return parser.parse_args()


async def main():
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建评估器
    config = {
        'max_sample_count': args.sample_count,
        'max_concurrent': args.max_concurrent,
    }
    
    evaluator = RANGENEvaluator(mode=args.mode, config=config)
    
    # 运行评估
    print(f"\n{'=' * 70}")
    print(f"🤖 RANGEN AI中台能力评估系统")
    print(f"评估模式: {args.mode}")
    print(f"维度数量: {len(evaluator.dimensions_to_eval)}")
    print(f"{'=' * 70}\n")
    
    results = await evaluator.run_evaluation()
    
    # 输出结果
    print(f"\n{'=' * 70}")
    print(f"📊 评估结果")
    print(f"{'=' * 70}")
    
    # 类别得分
    for cat_id, cat_info in results['category_scores'].items():
        if cat_info['weight'] > 0:
            status_icon = '🟢' if cat_info['score'] >= 0.7 else '🟡' if cat_info['score'] >= 0.5 else '🔴'
            print(f"{status_icon} {cat_info['name']} [{cat_id}]: {cat_info['score']:.2f} (权重: {cat_info['weight']:.0%})")
            for dim in cat_info.get('dimensions', []):
                dim_icon = '✓' if dim['score'] >= 0.7 else '○' if dim['score'] >= 0.5 else '✗'
                print(f"    {dim_icon} {dim['name']}: {dim['score']:.2f}")
    
    # 总分
    print(f"\n{'=' * 70}")
    print(f"📈 总分: {results['overall_score']:.2f}")
    print(f"{'=' * 70}")
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n结果已保存到: {output_path}")
    
    return results


if __name__ == '__main__':
    asyncio.run(main())
