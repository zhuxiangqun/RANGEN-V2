"""
多地域建筑数据库集成策略
解决地域偏差问题，提供全球覆盖的建筑数据
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math
from .realtime_data_integration import BuildingData, DataSourceType, RealTimeDataManager

logger = logging.getLogger(__name__)

class Region(Enum):
    """全球区域划分"""
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    EUROPE = "europe"
    AFRICA = "africa"
    ASIA = "asia"
    MIDDLE_EAST = "middle_east"
    OCEANIA = "oceania"
    CENTRAL_AMERICA = "central_america"
    CARIBBEAN = "caribbean"

@dataclass
class RegionalCoverage:
    """区域覆盖统计"""
    region: Region
    total_buildings: int = 0
    buildings_with_height: int = 0
    data_sources: Set[DataSourceType] = field(default_factory=set)
    last_updated: Optional[datetime] = None
    confidence_score: float = 0.0
    
    @property
    def coverage_rate(self) -> float:
        """数据覆盖率"""
        return (self.buildings_with_height / self.total_buildings) if self.total_buildings > 0 else 0.0

class RegionalDataIntegrator:
    """多地域数据集成器"""
    
    def __init__(self, realtime_manager: RealTimeDataManager, config: Dict[str, Any]):
        self.realtime_manager = realtime_manager
        self.config = config
        self.regional_data: Dict[Region, List[BuildingData]] = {}
        self.coverage_stats: Dict[Region, RegionalCoverage] = {}
        self.region_mapping = self._build_region_mapping()
        self._initialize_coverage_stats()
        
    def _build_region_mapping(self) -> Dict[str, Region]:
        """构建国家到区域的映射"""
        return {
            # 北美
            'united states': Region.NORTH_AMERICA,
            'canada': Region.NORTH_AMERICA,
            'mexico': Region.NORTH_AMERICA,
            
            # 南美
            'brazil': Region.SOUTH_AMERICA,
            'argentina': Region.SOUTH_AMERICA,
            'chile': Region.SOUTH_AMERICA,
            'colombia': Region.SOUTH_AMERICA,
            'peru': Region.SOUTH_AMERICA,
            'venezuela': Region.SOUTH_AMERICA,
            
            # 欧洲
            'united kingdom': Region.EUROPE,
            'germany': Region.EUROPE,
            'france': Region.EUROPE,
            'italy': Region.EUROPE,
            'spain': Region.EUROPE,
            'netherlands': Region.EUROPE,
            'switzerland': Region.EUROPE,
            'sweden': Region.EUROPE,
            'norway': Region.EUROPE,
            'denmark': Region.EUROPE,
            'poland': Region.EUROPE,
            'russia': Region.EUROPE,  # 部分在亚洲
            
            # 非洲
            'south africa': Region.AFRICA,
            'egypt': Region.AFRICA,
            'nigeria': Region.AFRICA,
            'kenya': Region.AFRICA,
            'morocco': Region.AFRICA,
            'ghana': Region.AFRICA,
            
            # 亚洲
            'china': Region.ASIA,
            'japan': Region.ASIA,
            'south korea': Region.ASIA,
            'india': Region.ASIA,
            'singapore': Region.ASIA,
            'thailand': Region.ASIA,
            'malaysia': Region.ASIA,
            'indonesia': Region.ASIA,
            'philippines': Region.ASIA,
            'vietnam': Region.ASIA,
            'pakistan': Region.ASIA,
            'bangladesh': Region.ASIA,
            
            # 中东
            'united arab emirates': Region.MIDDLE_EAST,
            'saudi arabia': Region.MIDDLE_EAST,
            'qatar': Region.MIDDLE_EAST,
            'kuwait': Region.MIDDLE_EAST,
            'israel': Region.MIDDLE_EAST,
            'turkey': Region.MIDDLE_EAST,
            'iran': Region.MIDDLE_EAST,
            'iraq': Region.MIDDLE_EAST,
            
            # 大洋洲
            'australia': Region.OCEANIA,
            'new zealand': Region.OCEANIA,
            
            # 中美洲
            'guatemala': Region.CENTRAL_AMERICA,
            'costa rica': Region.CENTRAL_AMERICA,
            'panama': Region.CENTRAL_AMERICA,
            'honduras': Region.CENTRAL_AMERICA,
            'nicaragua': Region.CENTRAL_AMERICA,
            
            # 加勒比
            'cuba': Region.CARIBBEAN,
            'jamaica': Region.CARIBBEAN,
            'dominican republic': Region.CARIBBEAN,
            'puerto rico': Region.CARIBBEAN,
            'trinidad and tobago': Region.CARIBBEAN,
        }
    
    def _initialize_coverage_stats(self):
        """初始化覆盖统计"""
        for region in Region:
            self.coverage_stats[region] = RegionalCoverage(region=region)
    
    def _get_region_for_country(self, country: Optional[str]) -> Optional[Region]:
        """根据国家获取区域"""
        if not country:
            return None
        
        country_lower = country.lower().strip()
        return self.region_mapping.get(country_lower)
    
    async def load_regional_data(self, regions: Optional[List[Region]] = None):
        """加载指定区域的数据"""
        if regions is None:
            regions = list(Region)
        
        logger.info(f"开始加载区域数据: {[r.value for r in regions]}")
        
        # 并行加载各区域数据
        tasks = []
        for region in regions:
            tasks.append(self._load_single_region_data(region))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"加载区域 {regions[i].value} 数据失败: {result}")
            else:
                logger.info(f"成功加载区域 {regions[i].value} 数据: {len(result)} 栋建筑")
        
        await self._update_coverage_stats()
    
    async def _load_single_region_data(self, region: Region) -> List[BuildingData]:
        """加载单个区域的数据"""
        region_buildings = []
        
        # 获取区域内的最高建筑
        try:
            # 对于某些区域，使用国家列表进行查询
            region_countries = self._get_countries_for_region(region)
            
            if region_countries:
                # 并行查询多个国家
                tasks = []
                for country in region_countries[:5]:  # 限制查询数量避免过多请求
                    query = f"tallest buildings {country}"
                    tasks.append(self.realtime_manager.search_building_data(query))
                
                country_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in country_results:
                    if isinstance(result, list):
                        region_buildings.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"查询国家数据失败: {result}")
            else:
                # 对于其他区域，使用通用查询
                query = f"tallest buildings {region.value.replace('_', ' ')}"
                buildings = await self.realtime_manager.search_building_data(query)
                region_buildings.extend(buildings)
                
        except Exception as e:
            logger.error(f"加载区域 {region.value} 数据失败: {e}")
        
        # 按区域过滤建筑
        filtered_buildings = []
        for building in region_buildings:
            building_region = self._get_region_for_country(building.country)
            if building_region == region:
                filtered_buildings.append(building)
        
        # 缓存区域数据
        self.regional_data[region] = filtered_buildings
        
        return filtered_buildings
    
    def _get_countries_for_region(self, region: Region) -> List[str]:
        """获取区域内的主要国家列表"""
        region_countries = {
            Region.NORTH_AMERICA: ['united states', 'canada', 'mexico'],
            Region.SOUTH_AMERICA: ['brazil', 'argentina', 'chile', 'colombia', 'peru'],
            Region.EUROPE: ['united kingdom', 'germany', 'france', 'italy', 'spain', 'netherlands'],
            Region.AFRICA: ['south africa', 'egypt', 'nigeria', 'kenya', 'morocco'],
            Region.ASIA: ['china', 'japan', 'south korea', 'india', 'singapore'],
            Region.MIDDLE_EAST: ['united arab emirates', 'saudi arabia', 'qatar', 'kuwait'],
            Region.OCEANIA: ['australia', 'new zealand'],
            Region.CENTRAL_AMERICA: ['guatemala', 'costa rica', 'panama'],
            Region.CARIBBEAN: ['cuba', 'jamaica', 'dominican republic'],
        }
        return region_countries.get(region, [])
    
    async def _update_coverage_stats(self):
        """更新覆盖统计"""
        for region, buildings in self.regional_data.items():
            stats = self.coverage_stats[region]
            stats.total_buildings = len(buildings)
            stats.buildings_with_height = len([
                b for b in buildings 
                if b.height_feet is not None or b.height_meters is not None
            ])
            
            # 统计数据源
            data_sources = set()
            for building in buildings:
                if building.data_source:
                    data_sources.add(building.data_source)
            stats.data_sources = data_sources
            
            # 计算置信度（基于数据源和数据完整性）
            confidence = 0.0
            if DataSourceType.CTBUH in data_sources:
                confidence += 0.7  # 权威数据源
            if stats.coverage_rate > 0.8:
                confidence += 0.2  # 高覆盖率
            if stats.total_buildings > 50:
                confidence += 0.1  # 数据量充足
            
            stats.confidence_score = min(confidence, 1.0)
            stats.last_updated = datetime.now()
    
    def get_tallest_buildings_by_region(self, region: Region, limit: int = 10) -> List[BuildingData]:
        """获取指定区域的最高建筑"""
        buildings = self.regional_data.get(region, [])
        
        # 按高度排序
        buildings_with_height = [
            b for b in buildings 
            if b.height_feet is not None or b.height_meters is not None
        ]
        
        buildings_with_height.sort(
            key=lambda x: (x.height_feet or 0) or (x.height_meters or 0) * 3.28084,
            reverse=True
        )
        
        return buildings_with_height[:limit]
    
    def get_regional_coverage_summary(self) -> Dict[str, Any]:
        """获取区域覆盖摘要"""
        summary = {}
        
        for region, stats in self.coverage_stats.items():
            summary[region.value] = {
                'total_buildings': stats.total_buildings,
                'buildings_with_height': stats.buildings_with_height,
                'coverage_rate': stats.coverage_rate,
                'data_sources': [ds.value for ds in stats.data_sources],
                'confidence_score': stats.confidence_score,
                'last_updated': stats.last_updated.isoformat() if stats.last_updated else None
            }
        
        return summary
    
    def find_buildings_with_balance(self, min_regions: int = 3, limit: int = 20) -> List[BuildingData]:
        """查找多地区均衡的建筑列表"""
        all_buildings = []
        
        # 收集所有区域的建筑
        for region, buildings in self.regional_data.items():
            for building in buildings:
                if building.height_feet is not None or building.height_meters is not None:
                    all_buildings.append((building, region))
        
        # 按高度排序
        all_buildings.sort(
            key=lambda x: (x[0].height_feet or 0) or (x[0].height_meters or 0) * 3.28084,
            reverse=True
        )
        
        # 选择多地区均衡的建筑
        selected_buildings = []
        region_count = {}
        
        for building, region in all_buildings:
            # 确保地区多样性
            current_regions = len(region_count)
            region_usage = region_count.get(region, 0)
            
            if (current_regions < min_regions or 
                (current_regions >= min_regions and region_usage < min_regions)):
                
                selected_buildings.append(building)
                region_count[region] = region_usage + 1
                
                if len(selected_buildings) >= limit:
                    break
        
        return selected_buildings
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """获取数据质量指标"""
        total_buildings = sum(stats.total_buildings for stats in self.coverage_stats.values())
        total_with_height = sum(stats.buildings_with_height for stats in self.coverage_stats.values())
        regions_with_data = len([
            stats for stats in self.coverage_stats.values() 
            if stats.total_buildings > 0
        ])
        
        avg_confidence = sum(
            stats.confidence_score for stats in self.coverage_stats.values() 
            if stats.confidence_score > 0
        ) / max(regions_with_data, 1)
        
        return {
            'total_buildings': total_buildings,
            'buildings_with_height_data': total_with_height,
            'overall_coverage_rate': (total_with_height / total_buildings) if total_buildings > 0 else 0,
            'regions_covered': regions_with_data,
            'total_regions': len(Region),
            'regional_coverage_rate': regions_with_data / len(Region),
            'average_confidence_score': avg_confidence,
            'data_sources_used': list(set(
                ds for stats in self.coverage_stats.values() for ds in stats.data_sources
            ))
        }
    
    async def refresh_regional_data(self, regions: Optional[List[Region]] = None):
        """刷新区域数据"""
        logger.info("开始刷新区域数据")
        
        # 清除现有缓存
        self.realtime_manager.clear_cache()
        
        # 重新加载数据
        await self.load_regional_data(regions)
        
        logger.info("区域数据刷新完成")

# 工厂函数
def create_regional_integrator(
    realtime_manager: RealTimeDataManager,
    config: Optional[Dict[str, Any]] = None
) -> RegionalDataIntegrator:
    """创建区域数据集成器实例"""
    if config is None:
        config = {
            'max_buildings_per_region': 100,
            'refresh_interval_hours': 24,
            'min_confidence_threshold': 0.5
        }
    
    return RegionalDataIntegrator(realtime_manager, config)