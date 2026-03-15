#!/usr/bin/env python3
"""
系统集成优化器
促进各统一中心之间的协作和智能化水平提升
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.unified_intelligent_quality_center import get_unified_intelligent_quality_center
from src.utils.unified_learning_center import get_unified_learning_center
from src.utils.unified_answer_center import get_unified_answer_center
from src.utils.unified_cache_center import get_unified_cache_center
from src.utils.unified_security_center import get_unified_security_center
from src.utils.unified_data_center import get_unified_data_center
from src.utils.unified_identity_center import get_unified_identity_center
from src.utils.unified_context_engineering_center import get_unified_context_engineering_center

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CenterIntegrationStatus:
    """中心集成状态"""
    center_name: str
    integration_score: float
    collaboration_count: int
    issues_count: int
    improvement_potential: float

class SystemIntegrationOptimizer:
    """系统集成优化器"""
    
    def __init__(self):
        """初始化优化器"""
        self.quality_center = get_unified_intelligent_quality_center()
        self.learning_center = get_unified_learning_center()
        self.answer_center = get_unified_answer_center()
        self.cache_center = get_unified_cache_center()
        self.security_center = get_unified_security_center()
        self.data_center = get_unified_data_center()
        self.identity_center = get_unified_identity_center()
        self.context_center = get_unified_context_engineering_center()
        
        # 中心映射
        self.centers = {
            'quality': self.quality_center,
            'learning': self.learning_center,
            'answer': self.answer_center,
            'cache': self.cache_center,
            'security': self.security_center,
            'data': self.data_center,
            'identity': self.identity_center,
            'context': self.context_center
        }
        
        # 中心文件路径
        self.center_files = {
            'quality': 'src/utils/unified_intelligent_quality_center.py',
            'learning': 'src/utils/unified_learning_center.py',
            'answer': 'src/utils/unified_answer_center.py',
            'cache': 'src/utils/unified_cache_center.py',
            'security': 'src/utils/unified_security_center.py',
            'data': 'src/utils/unified_data_center.py',
            'identity': 'src/utils/unified_identity_center.py',
            'context': 'src/utils/unified_context_engineering_center.py'
        }
    
    def analyze_integration_status(self) -> List[CenterIntegrationStatus]:
        """分析各中心的集成状态"""
        logger.info("分析各中心集成状态...")
        
        status_list = []
        
        for center_name, center_file in self.center_files.items():
            try:
                # 检测问题
                issues = self.quality_center.detect_issues(center_file)
                issues_count = len(issues)
                
                # 计算集成分数
                integration_score = self._calculate_integration_score(center_name, issues)
                
                # 计算协作次数
                collaboration_count = self._count_collaborations(center_name)
                
                # 计算改进潜力
                improvement_potential = self._calculate_improvement_potential(issues)
                
                status = CenterIntegrationStatus(
                    center_name=center_name,
                    integration_score=integration_score,
                    collaboration_count=collaboration_count,
                    issues_count=issues_count,
                    improvement_potential=improvement_potential
                )
                
                status_list.append(status)
                
            except Exception as e:
                logger.error(f"分析中心 {center_name} 失败: {e}")
                continue
        
        return status_list
    
    def _calculate_integration_score(self, center_name: str, issues: List[Any]) -> float:
        """计算集成分数"""
        try:
            # 基础分数
            base_score = 100.0
            
            # 根据问题类型扣分
            for issue in issues:
                if issue.issue_type.value == 'underutilized_learning_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_answer_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_cache_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_data_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_identity_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_context_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_security_center':
                    base_score -= 5.0
                elif issue.issue_type.value == 'underutilized_quality_center':
                    base_score -= 5.0
            
            # 根据中心类型加分
            if center_name == 'quality':
                base_score += 10.0  # 质量中心是核心
            elif center_name == 'learning':
                base_score += 8.0   # 学习中心很重要
            elif center_name == 'answer':
                base_score += 7.0   # 答案中心很重要
            
            return max(0.0, min(100.0, base_score))
            
        except Exception as e:
            logger.error(f"计算集成分数失败: {e}")
            return 50.0
    
    def _count_collaborations(self, center_name: str) -> int:
        """计算协作次数"""
        try:
            center_file = self.center_files[center_name]
            
            # 读取文件内容
            with open(center_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计其他中心的引用次数
            collaboration_count = 0
            for other_center in self.centers.keys():
                if other_center != center_name:
                    # 统计导入语句
                    import_patterns = [
                        f'from src.utils.unified_{other_center}_center',
                        f'import unified_{other_center}_center',
                        f'unified_{other_center}_center',
                        f'{other_center}_center'
                    ]
                    
                    for pattern in import_patterns:
                        collaboration_count += content.count(pattern)
            
            return collaboration_count
            
        except Exception as e:
            logger.error(f"计算协作次数失败: {e}")
            return 0
    
    def _calculate_improvement_potential(self, issues: List[Any]) -> float:
        """计算改进潜力"""
        try:
            if not issues:
                return 0.0
            
            # 根据问题类型计算改进潜力
            potential = 0.0
            for issue in issues:
                if issue.issue_type.value == 'simplified_logic':
                    potential += 3.0
                elif issue.issue_type.value == 'hardcoded_value':
                    potential += 2.0
                elif issue.issue_type.value.startswith('underutilized_'):
                    potential += 4.0
                elif issue.issue_type.value == 'cheating_behavior':
                    potential += 5.0
            
            return min(100.0, potential)
            
        except Exception as e:
            logger.error(f"计算改进潜力失败: {e}")
            return 0.0
    
    def generate_integration_recommendations(self, status_list: List[CenterIntegrationStatus]) -> List[str]:
        """生成集成建议"""
        logger.info("生成集成建议...")
        
        recommendations = []
        
        # 按改进潜力排序
        sorted_status = sorted(status_list, key=lambda x: x.improvement_potential, reverse=True)
        
        for status in sorted_status:
            if status.improvement_potential > 20:
                recommendations.append(f"🔧 {status.center_name}中心: 改进潜力{status.improvement_potential:.1f}% - 建议优先优化")
            
            if status.integration_score < 60:
                recommendations.append(f"🔗 {status.center_name}中心: 集成分数{status.integration_score:.1f} - 建议增强协作")
            
            if status.collaboration_count < 3:
                recommendations.append(f"🤝 {status.center_name}中心: 协作次数{status.collaboration_count} - 建议增加中心间协作")
        
        return recommendations
    
    def optimize_system_integration(self) -> Dict[str, Any]:
        """优化系统集成"""
        logger.info("开始系统集成优化...")
        
        # 分析集成状态
        status_list = self.analyze_integration_status()
        
        # 生成建议
        recommendations = self.generate_integration_recommendations(status_list)
        
        # 计算总体指标
        total_issues = sum(status.issues_count for status in status_list)
        avg_integration_score = sum(status.integration_score for status in status_list) / len(status_list)
        avg_collaboration_count = sum(status.collaboration_count for status in status_list) / len(status_list)
        total_improvement_potential = sum(status.improvement_potential for status in status_list)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_issues': total_issues,
            'avg_integration_score': avg_integration_score,
            'avg_collaboration_count': avg_collaboration_count,
            'total_improvement_potential': total_improvement_potential,
            'center_status': [
                {
                    'center_name': status.center_name,
                    'integration_score': status.integration_score,
                    'collaboration_count': status.collaboration_count,
                    'issues_count': status.issues_count,
                    'improvement_potential': status.improvement_potential
                }
                for status in status_list
            ],
            'recommendations': recommendations
        }
    
    def print_optimization_report(self, results: Dict[str, Any]):
        """打印优化报告"""
        print("=" * 80)
        print("🚀 系统集成优化报告")
        print("=" * 80)
        
        print(f"📊 总体指标:")
        print(f"  总问题数: {results['total_issues']}")
        print(f"  平均集成分数: {results['avg_integration_score']:.1f}")
        print(f"  平均协作次数: {results['avg_collaboration_count']:.1f}")
        print(f"  总改进潜力: {results['total_improvement_potential']:.1f}%")
        
        print(f"\n📈 各中心状态:")
        for status in results['center_status']:
            print(f"  {status['center_name']:12} | 集成:{status['integration_score']:5.1f} | 协作:{status['collaboration_count']:2d} | 问题:{status['issues_count']:3d} | 潜力:{status['improvement_potential']:5.1f}%")
        
        print(f"\n💡 优化建议:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i:2d}. {rec}")
        
        print("=" * 80)

def main():
    """主函数"""
    try:
        optimizer = SystemIntegrationOptimizer()
        results = optimizer.optimize_system_integration()
        optimizer.print_optimization_report(results)
        
        # 判断优化效果
        if results['total_issues'] < 200:
            print("\n✅ 系统集成状态良好")
        elif results['total_issues'] < 300:
            print("\n🟡 系统集成状态一般，需要改进")
        else:
            print("\n❌ 系统集成状态较差，需要大幅优化")
            
    except Exception as e:
        logger.error(f"系统集成优化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
