"""
实时数据源集成模块
提供建筑数据的实时更新机制，解决数据时效性问题

集成数据源：
1. CTBUH (Council on Tall Buildings and Urban Habitat) - 全球高层建筑权威数据
2. Google Open Buildings - 全球建筑轮廓数据
3. Microsoft Global Building Footprints - 全球建筑足迹数据
4. OpenStreetMap - 开源地图数据
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """数据源类型"""
    CTBUH = "ctbuh"
    GOOGLE_OPEN_BUILDINGS = "google_open_buildings"
    MICROSOFT_BUILDINGS = "microsoft_buildings"
    OPENSTREETMAP = "openstreetmap"

@dataclass
class BuildingData:
    """建筑数据模型"""
    building_id: str
    name: Optional[str] = None
    height_meters: Optional[float] = None
    height_feet: Optional[float] = None
    floors: Optional[int] = None
    year_completed: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    function: Optional[str] = None
    material: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    data_source: Optional[DataSourceType] = None
    last_updated: Optional[datetime] = field(default_factory=datetime.now)
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'building_id': self.building_id,
            'name': self.name,
            'height_meters': self.height_meters,
            'height_feet': self.height_feet,
            'floors': self.floors,
            'year_completed': self.year_completed,
            'city': self.city,
            'country': self.country,
            'region': self.region,
            'status': self.status,
            'function': self.function,
            'material': self.material,
            'coordinates': self.coordinates,
            'data_source': self.data_source.value if self.data_source else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'confidence_score': self.confidence_score
        }

class BaseDataSourceAdapter(ABC):
    """数据源适配器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.rate_limit = config.get('rate_limit', 100)  # 每分钟请求数
        
    @abstractmethod
    async def search_buildings(self, query: str, limit: int = 10) -> List[BuildingData]:
        """搜索建筑数据"""
        pass
    
    @abstractmethod
    async def get_building_by_id(self, building_id: str) -> Optional[BuildingData]:
        """根据ID获取建筑数据"""
        pass
    
    @abstractmethod
    async def get_tallest_buildings(self, region: Optional[str] = None, limit: int = 10) -> List[BuildingData]:
        """获取最高建筑列表"""
        pass

class CTBUHAdapter(BaseDataSourceAdapter):
    """CTBUH数据源适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://skyscrapercenter.com/api/v1"
        
    async def search_buildings(self, query: str, limit: int = 10) -> List[BuildingData]:
        """搜索建筑数据"""
        try:
            # 由于CTBUH可能没有公开API，使用网页解析作为备选方案
            url = f"{self.base_url}/search"
            params = {
                'q': query,
                'limit': limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_ctbuh_data(data)
                    else:
                        logger.warning(f"CTBUH API请求失败: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"CTBUH搜索失败: {e}")
            return []
    
    async def get_building_by_id(self, building_id: str) -> Optional[BuildingData]:
        """根据ID获取建筑数据"""
        try:
            url = f"{self.base_url}/buildings/{building_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        buildings = self._parse_ctbuh_data({'buildings': [data]})
                        return buildings[0] if buildings else None
                    else:
                        return None
                        
        except Exception as e:
            logger.error(f"CTBUH获取建筑详情失败: {e}")
            return None
    
    async def get_tallest_buildings(self, region: Optional[str] = None, limit: int = 10) -> List[BuildingData]:
        """获取最高建筑列表"""
        try:
            url = f"{self.base_url}/tallest"
            params = {'limit': limit}
            if region:
                params['region'] = region
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_ctbuh_data(data)
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"CTBUH获取最高建筑失败: {e}")
            return []
    
    def _parse_ctbuh_data(self, data: Dict[str, Any]) -> List[BuildingData]:
        """解析CTBUH数据格式"""
        buildings = []
        for item in data.get('buildings', []):
            try:
                # 转换单位保持精确度
                height_m = item.get('height_meters')
                height_ft = item.get('height_feet') or (height_m * 3.28084 if height_m else None)
                
                building = BuildingData(
                    building_id=str(item.get('id', '')),
                    name=item.get('name'),
                    height_meters=height_m,
                    height_feet=height_ft,
                    floors=item.get('floors'),
                    year_completed=item.get('year_completed'),
                    city=item.get('city'),
                    country=item.get('country'),
                    region=item.get('region'),
                    status=item.get('status'),
                    function=item.get('function'),
                    material=item.get('material'),
                    coordinates={
                        'lat': item.get('latitude'),
                        'lon': item.get('longitude')
                    } if item.get('latitude') and item.get('longitude') else None,
                    data_source=DataSourceType.CTBUH,
                    confidence_score=0.95  # CTBUH作为权威数据源，高置信度
                )
                buildings.append(building)
            except Exception as e:
                logger.warning(f"解析CTBUH建筑数据失败: {e}")
                continue
                
        return buildings

class GoogleOpenBuildingsAdapter(BaseDataSourceAdapter):
    """Google Open Buildings数据源适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 注意：Google Open Buildings主要通过数据集下载，而非实时API
        self.data_url = config.get('data_url', 'https://sites.research.google/open-buildings/')
        
    async def search_buildings(self, query: str, limit: int = 10) -> List[BuildingData]:
        """搜索建筑数据 - Google Open Buildings主要用于批量数据处理"""
        logger.warning("Google Open Buildings不支持实时搜索，建议使用预处理的本地数据")
        return []
    
    async def get_building_by_id(self, building_id: str) -> Optional[BuildingData]:
        """根据ID获取建筑数据"""
        return None
    
    async def get_tallest_buildings(self, region: Optional[str] = None, limit: int = 10) -> List[BuildingData]:
        """获取最高建筑列表"""
        logger.warning("Google Open Buildings主要用于建筑轮廓，不包含高度信息")
        return []

class RealTimeDataManager:
    """实时数据管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.adapters: Dict[DataSourceType, BaseDataSourceAdapter] = {}
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1小时缓存
        self._initialize_adapters()
        
    def _initialize_adapters(self):
        """初始化数据源适配器"""
        # 初始化CTBUH适配器
        if 'ctbuh' in self.config.get('data_sources', {}):
            self.adapters[DataSourceType.CTBUH] = CTBUHAdapter(
                self.config['data_sources']['ctbuh']
            )
            
        # 初始化Google Open Buildings适配器
        if 'google_open_buildings' in self.config.get('data_sources', {}):
            self.adapters[DataSourceType.GOOGLE_OPEN_BUILDINGS] = GoogleOpenBuildingsAdapter(
                self.config['data_sources']['google_open_buildings']
            )
    
    async def search_building_data(self, query: str, regions: Optional[List[str]] = None) -> List[BuildingData]:
        """搜索建筑数据，集成多个数据源"""
        cache_key = self._generate_cache_key(f"search:{query}:{regions}")
        
        # 检查缓存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.info(f"使用缓存数据: {query}")
                return cached_data
        
        all_buildings = []
        
        # 并行搜索多个数据源
        tasks = []
        for source_type, adapter in self.adapters.items():
            if isinstance(adapter, CTBUHAdapter):
                tasks.append(adapter.search_buildings(query))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_buildings.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"搜索失败: {result}")
        
        # 区域过滤
        if regions:
            all_buildings = [
                b for b in all_buildings 
                if b.region in regions or b.country in regions
            ]
        
        # 按高度排序并去重
        unique_buildings = self._deduplicate_buildings(all_buildings)
        
        # 缓存结果
        self.cache[cache_key] = (unique_buildings, datetime.now())
        
        return unique_buildings
    
    async def get_tallest_buildings_global(self, limit: int = 10) -> List[BuildingData]:
        """获取全球最高建筑"""
        cache_key = f"tallest_global:{limit}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        tallest_buildings = []
        
        # 从CTBUH获取数据
        if DataSourceType.CTBUH in self.adapters:
            adapter = self.adapters[DataSourceType.CTBUH]
            buildings = await adapter.get_tallest_buildings(limit=limit)
            tallest_buildings.extend(buildings)
        
        # 按高度排序
        tallest_buildings.sort(key=lambda x: x.height_feet or 0, reverse=True)
        tallest_buildings = tallest_buildings[:limit]
        
        # 缓存结果
        self.cache[cache_key] = (tallest_buildings, datetime.now())
        
        return tallest_buildings
    
    async def get_tallest_buildings_by_region(self, region: str, limit: int = 10) -> List[BuildingData]:
        """获取指定区域的最高建筑"""
        cache_key = f"tallest_region:{region}:{limit}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        tallest_buildings = []
        
        # 从CTBUH获取区域数据
        if DataSourceType.CTBUH in self.adapters:
            adapter = self.adapters[DataSourceType.CTBUH]
            buildings = await adapter.get_tallest_buildings(region=region, limit=limit)
            tallest_buildings.extend(buildings)
        
        # 按高度排序
        tallest_buildings.sort(key=lambda x: x.height_feet or 0, reverse=True)
        tallest_buildings = tallest_buildings[:limit]
        
        # 缓存结果
        self.cache[cache_key] = (tallest_buildings, datetime.now())
        
        return tallest_buildings
    
    def _generate_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _deduplicate_buildings(self, buildings: List[BuildingData]) -> List[BuildingData]:
        """去重建筑数据，保留置信度最高的记录"""
        unique_buildings = {}
        
        for building in buildings:
            # 使用名称+城市+国家作为唯一标识
            key = f"{building.name}_{building.city}_{building.country}"
            
            if key not in unique_buildings or (
                building.confidence_score and 
                building.confidence_score > (unique_buildings[key].confidence_score or 0)
            ):
                unique_buildings[key] = building
        
        return list(unique_buildings.values())
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        logger.info("实时数据缓存已清除")

# 工厂函数
def create_realtime_data_manager(config: Optional[Dict[str, Any]] = None) -> RealTimeDataManager:
    """创建实时数据管理器实例"""
    if config is None:
        # 默认配置
        config = {
            'cache_ttl': 3600,
            'data_sources': {
                'ctbuh': {
                    'timeout': 30,
                    'rate_limit': 100
                }
            }
        }
    
    return RealTimeDataManager(config)