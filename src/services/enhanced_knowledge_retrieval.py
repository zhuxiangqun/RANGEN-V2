"""
增强的知识检索服务集成模块
集成实时数据、多地域覆盖、数值精确度和质量验证功能
"""

import logging
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime

from .knowledge_retrieval_service import KnowledgeRetrievalService, AgentResult
from .realtime_data_integration import create_realtime_data_manager, RealTimeDataManager
from .regional_data_integration import create_regional_integrator, RegionalDataIntegrator, Region
from .numeric_precision_processor import get_numeric_processor, process_text_with_precision
from .data_quality_validator import create_data_quality_monitor, DataQualityMonitor

logger = logging.getLogger(__name__)

class EnhancedKnowledgeRetrievalService:
    """增强的知识检索服务
    
    集成以下功能：
    1. 实时数据更新机制
    2. 多地域数据库覆盖
    3. 数值精确度处理
    4. 数据质量监控
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化核心组件
        self.base_service = KnowledgeRetrievalService()
        self.realtime_manager = create_realtime_data_manager(
            self.config.get('realtime_data_integration', {})
        )
        self.regional_integrator = create_regional_integrator(
            self.realtime_manager,
            self.config.get('regional_data_integration', {})
        )
        self.numeric_processor = get_numeric_processor()
        self.quality_monitor = create_data_quality_monitor(
            self.config.get('data_quality', {})
        )
        
        # 功能开关
        self.enable_realtime_data = self.config.get('enable_realtime_data', True)
        self.enable_regional_coverage = self.config.get('enable_regional_coverage', True)
        self.enable_precision_processing = self.config.get('enable_precision_processing', True)
        self.enable_quality_monitoring = self.config.get('enable_quality_monitoring', True)
        
        logger.info("增强知识检索服务初始化完成")
    
    async def execute_with_enhancements(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行增强的知识检索"""
        start_time = datetime.now()
        
        try:
            # 1. 数值精确度处理
            precision_info = {}
            if self.enable_precision_processing:
                precision_info = process_text_with_precision(query, context)
                logger.info(f"数值精确度分析完成: 发现 {precision_info['numbers_found']} 个数值")
            
            # 2. 检测查询类型（建筑相关？）
            is_building_query = self._detect_building_query(query)
            
            # 3. 并行执行基础检索和增强检索
            tasks = []
            
            # 基础检索任务
            tasks.append(self._execute_base_retrieval(query, context))
            
            # 增强检索任务（仅对建筑查询）
            if is_building_query:
                enhancement_tasks = []
                
                if self.enable_realtime_data:
                    enhancement_tasks.append(self._search_realtime_data(query))
                
                if self.enable_regional_coverage:
                    enhancement_tasks.append(self._search_regional_data(query))
                
                if enhancement_tasks:
                    tasks.extend(enhancement_tasks)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 4. 合并结果
            merged_result = await self._merge_retrieval_results(results, precision_info)
            
            # 5. 质量评估
            quality_info = {}
            if self.enable_quality_monitoring and is_building_query:
                quality_info = await self._assess_data_quality(merged_result)
            
            # 6. 构建最终响应
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_result = {
                'query': query,
                'processing_time': processing_time,
                'success': True,
                'data_sources': merged_result.get('data_sources', []),
                'results': merged_result.get('results', []),
                'enhancements': {
                    'precision_processing': precision_info,
                    'realtime_data': merged_result.get('realtime_data', {}),
                    'regional_coverage': merged_result.get('regional_data', {}),
                    'quality_assessment': quality_info
                },
                'metadata': {
                    'query_type': 'building_enhanced' if is_building_query else 'standard',
                    'enhancement_level': self._calculate_enhancement_level(merged_result),
                    'data_freshness': self._assess_data_freshness(merged_result),
                    'regional_balance': self._assess_regional_balance(merged_result)
                }
            }
            
            logger.info(f"增强检索完成: 处理时间 {processing_time:.2f}s, 数据源 {len(final_result['data_sources'])} 个")
            return final_result
            
        except Exception as e:
            logger.error(f"增强检索失败: {e}")
            return {
                'query': query,
                'success': False,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_base_retrieval(self, query: str, context: Optional[Dict[str, Any]]) -> Any:
        """执行基础检索"""
        try:
            return await self.base_service.execute(query, context)
        except Exception as e:
            logger.warning(f"基础检索失败: {e}")
            return {'success': False, 'error': str(e), 'source': 'base_service'}
    
    async def _search_realtime_data(self, query: str) -> Dict[str, Any]:
        """搜索实时数据"""
        try:
            # 提取可能的区域关键词
            regions = self._extract_regions_from_query(query)
            
            buildings = await self.realtime_manager.search_building_data(query, regions)
            
            return {
                'success': True,
                'source': 'realtime_data',
                'buildings_found': len(buildings),
                'buildings': [building.to_dict() for building in buildings],
                'data_freshness': datetime.now().isoformat(),
                'regions_searched': regions or ['global']
            }
        except Exception as e:
            logger.warning(f"实时数据搜索失败: {e}")
            return {'success': False, 'error': str(e), 'source': 'realtime_data'}
    
    async def _search_regional_data(self, query: str) -> Dict[str, Any]:
        """搜索区域数据"""
        try:
            # 确定相关区域
            target_regions = self._determine_target_regions(query)
            
            if not target_regions:
                # 如果没有特定区域，获取全球均衡数据
                buildings = self.regional_integrator.find_buildings_with_balance()
                target_regions = ['global_balanced']
            else:
                buildings = []
                for region in target_regions:
                    regional_buildings = self.regional_integrator.get_tallest_buildings_by_region(region, 10)
                    buildings.extend(regional_buildings)
            
            coverage_summary = self.regional_integrator.get_regional_coverage_summary()
            quality_metrics = self.regional_integrator.get_data_quality_metrics()
            
            return {
                'success': True,
                'source': 'regional_data',
                'buildings_found': len(buildings),
                'buildings': [building.to_dict() for building in buildings],
                'regions_covered': target_regions,
                'regional_coverage': coverage_summary,
                'quality_metrics': quality_metrics
            }
        except Exception as e:
            logger.warning(f"区域数据搜索失败: {e}")
            return {'success': False, 'error': str(e), 'source': 'regional_data'}
    
    async def _merge_retrieval_results(self, results: List[Any], precision_info: Dict[str, Any]) -> Dict[str, Any]:
        """合并检索结果"""
        merged = {
            'results': [],
            'data_sources': [],
            'realtime_data': {},
            'regional_data': {},
            'precision_issues': []
        }
        
        for result in results:
            if isinstance(result, Exception):
                continue
                
            if not isinstance(result, dict):
                continue
            
            # 提取基础检索结果
            if result.get('success') and 'data' in result:
                if isinstance(result['data'], dict) and 'sources' in result['data']:
                    merged['results'].extend(result['data'].get('sources', []))
                    merged['data_sources'].append('knowledge_base')
            
            # 提取实时数据结果
            if result.get('source') == 'realtime_data' and result.get('success'):
                merged['realtime_data'] = result
                merged['data_sources'].append('realtime_data')
                
                # 应用数值精确度处理
                if self.enable_precision_processing and precision_info.get('height_dimensions'):
                    merged['precision_issues'].extend([
                        "发现可能存在精度损失的建筑高度数据"
                    ])
            
            # 提取区域数据结果
            if result.get('source') == 'regional_data' and result.get('success'):
                merged['regional_data'] = result
                merged['data_sources'].append('regional_data')
        
        # 去重和排序
        merged['results'] = self._deduplicate_and_rank(merged['results'])
        
        return merged
    
    async def _assess_data_quality(self, merged_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        try:
            # 收集所有建筑数据
            all_buildings = []
            
            realtime_data = merged_result.get('realtime_data', {})
            if realtime_data.get('buildings'):
                from .realtime_data_integration import BuildingData
                for building_dict in realtime_data['buildings']:
                    # 重建BuildingData对象
                    building = BuildingData(
                        building_id=building_dict['building_id'],
                        name=building_dict.get('name'),
                        height_feet=building_dict.get('height_feet'),
                        height_meters=building_dict.get('height_meters'),
                        city=building_dict.get('city'),
                        country=building_dict.get('country'),
                        confidence_score=building_dict.get('confidence_score')
                    )
                    all_buildings.append(building)
            
            if not all_buildings:
                return {'status': 'no_data_to_assess'}
            
            # 执行质量监控
            quality_report = await self.quality_monitor.monitor_data_quality(
                all_buildings, 
                self.regional_integrator
            )
            
            return quality_report
            
        except Exception as e:
            logger.warning(f"数据质量评估失败: {e}")
            return {'status': 'assessment_failed', 'error': str(e)}
    
    def _detect_building_query(self, query: str) -> bool:
        """检测是否为建筑相关查询"""
        building_keywords = [
            'building', 'skyscraper', 'tower', 'height', 'tall', 'feet', 'meters',
            'architecture', 'construction', 'floor', 'story', '建筑', '高楼', '高度',
            'ctbuh', 'skyscraper center'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in building_keywords)
    
    def _extract_regions_from_query(self, query: str) -> Optional[List[str]]:
        """从查询中提取区域信息"""
        region_keywords = {
            'asia': ['asia', 'asian', 'china', 'japan', 'india', 'asia'],
            'europe': ['europe', 'european', 'uk', 'britain', 'france', 'germany'],
            'north_america': ['north america', 'usa', 'united states', 'canada', 'america'],
            'middle_east': ['middle east', 'dubai', 'saudi', 'uae', 'qatar'],
            'africa': ['africa', 'african', 'egypt', 'south africa', 'nigeria'],
            'south_america': ['south america', 'brazil', 'argentina', 'chile'],
            'oceania': ['oceania', 'australia', 'new zealand']
        }
        
        query_lower = query.lower()
        found_regions = []
        
        for region, keywords in region_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_regions.append(region)
        
        return found_regions if found_regions else None
    
    def _determine_target_regions(self, query: str) -> List[Region]:
        """确定目标区域"""
        extracted = self._extract_regions_from_query(query)
        
        if not extracted:
            return []
        
        region_mapping = {
            'asia': Region.ASIA,
            'europe': Region.EUROPE,
            'north_america': Region.NORTH_AMERICA,
            'middle_east': Region.MIDDLE_EAST,
            'africa': Region.AFRICA,
            'south_america': Region.SOUTH_AMERICA,
            'oceania': Region.OCEANIA
        }
        
        target_regions = []
        for region_name in extracted:
            if region_name in region_mapping:
                target_regions.append(region_mapping[region_name])
        
        return target_regions
    
    def _deduplicate_and_rank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和排序结果"""
        # 简单的去重逻辑
        seen = set()
        unique_results = []
        
        for result in results:
            # 使用内容哈希去重
            content = str(result.get('content', ''))
            if content and content not in seen:
                seen.add(content)
                unique_results.append(result)
        
        # 按相关性排序（这里简化处理）
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique_results
    
    def _calculate_enhancement_level(self, merged_result: Dict[str, Any]) -> str:
        """计算增强级别"""
        enhancements = []
        
        if merged_result.get('realtime_data', {}).get('success'):
            enhancements.append('realtime')
        
        if merged_result.get('regional_data', {}).get('success'):
            enhancements.append('regional')
        
        if merged_result.get('precision_issues'):
            enhancements.append('precision')
        
        if len(enhancements) >= 2:
            return 'high'
        elif len(enhancements) == 1:
            return 'medium'
        else:
            return 'low'
    
    def _assess_data_freshness(self, merged_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据新鲜度"""
        freshness_info = {'overall': 'unknown', 'sources': {}}
        
        realtime_data = merged_result.get('realtime_data', {})
        if realtime_data.get('data_freshness'):
            freshness_info['sources']['realtime_data'] = 'fresh'
            freshness_info['overall'] = 'fresh'
        
        regional_data = merged_result.get('regional_data', {})
        if regional_data.get('quality_metrics', {}).get('regional_coverage_rate'):
            coverage_rate = regional_data['quality_metrics']['regional_coverage_rate']
            freshness_info['sources']['regional_data'] = 'fresh' if coverage_rate > 0.7 else 'stale'
        
        return freshness_info
    
    def _assess_regional_balance(self, merged_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估区域平衡性"""
        balance_info = {'overall': 'unknown', 'regions_covered': 0}
        
        regional_data = merged_result.get('regional_data', {})
        if regional_data.get('regions_covered'):
            regions = regional_data['regions_covered']
            balance_info['regions_covered'] = len(regions)
            
            if len(regions) >= 5:
                balance_info['overall'] = 'excellent'
            elif len(regions) >= 3:
                balance_info['overall'] = 'good'
            elif len(regions) >= 1:
                balance_info['overall'] = 'limited'
        
        return balance_info
    
    async def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_status': 'healthy'
        }
        
        # 检查各组件状态
        try:
            # 实时数据管理器
            health['components']['realtime_data'] = {
                'status': 'healthy' if self.enable_realtime_data else 'disabled',
                'cache_size': len(self.realtime_manager.cache) if self.realtime_manager else 0
            }
            
            # 区域数据集成器
            health['components']['regional_data'] = {
                'status': 'healthy' if self.enable_regional_coverage else 'disabled',
                'regions_loaded': len(self.regional_integrator.regional_data) if self.regional_integrator else 0
            }
            
            # 数值处理器
            health['components']['numeric_processor'] = {
                'status': 'healthy' if self.enable_precision_processing else 'disabled'
            }
            
            # 质量监控器
            health['components']['quality_monitor'] = {
                'status': 'healthy' if self.enable_quality_monitoring else 'disabled',
                'history_size': len(self.quality_monitor.quality_history) if self.quality_monitor else 0
            }
            
            # 确定总体状态
            component_statuses = [comp['status'] for comp in health['components'].values()]
            if all(status == 'healthy' for status in component_statuses):
                health['overall_status'] = 'healthy'
            elif any(status == 'disabled' for status in component_statuses):
                health['overall_status'] = 'partial'
            else:
                health['overall_status'] = 'unhealthy'
                
        except Exception as e:
            health['overall_status'] = 'error'
            health['error'] = str(e)
        
        return health

# 工厂函数
def create_enhanced_knowledge_service(config: Optional[Dict[str, Any]] = None) -> EnhancedKnowledgeRetrievalService:
    """创建增强知识检索服务实例"""
    return EnhancedKnowledgeRetrievalService(config)