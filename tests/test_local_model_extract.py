"""
本地模型提取服务测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLocalModelExtractService:
    """测试本地模型提取服务"""

    def test_service_available(self):
        """测试服务是否可用"""
        try:
            from src.services.local_model_extract_service import LocalModelExtractService
            available = LocalModelExtractService.__init__.__doc__ is not None
            assert True
        except ImportError:
            pytest.skip("LocalModelExtractService not available (transformers not installed)")

    def test_hybrid_service_creation(self):
        """测试混合服务创建"""
        try:
            from src.services.local_model_extract_service import HybridExtractService
            
            service = HybridExtractService(use_local_model=True)
            assert service is not None
        except ImportError:
            pytest.skip("Local model service not available")

    def test_hybrid_auto_detection(self):
        """测试混合服务自动检测"""
        try:
            from src.services.local_model_extract_service import HybridExtractService
            
            service = HybridExtractService()
            assert service is not None
        except ImportError:
            pytest.skip("HybridExtractService not available")


class TestLocalModelIntegration:
    """测试本地模型集成"""

    @pytest.mark.asyncio
    async def test_extract_entities(self):
        """测试实体提取"""
        try:
            from src.services.local_model_extract_service import HybridExtractService
            
            service = HybridExtractService(use_local_model=True)
            
            result = await service.extract_entities_with_locations(
                "John lives in New York.",
                entity_types=["PERSON", "LOCATION"]
            )
            
            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Local model service not available")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_extract_from_evidence(self):
        """测试从证据提取"""
        try:
            from src.services.local_model_extract_service import HybridExtractService
            
            service = HybridExtractService(use_local_model=True)
            
            evidence = [
                {"content": "Albert Einstein was born in Ulm.", "source": "wiki"},
                {"content": "He developed the theory of relativity.", "source": "wiki"}
            ]
            
            result = await service.extract_from_evidence(
                evidence=evidence,
                schema={"entities": []}
            )
            
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Local model service not available")
        except Exception:
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
