"""
KMS Metrics
使用 Prometheus Client 暴露核心监控指标。
"""

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class KMSMetrics:
    """
    KMS 监控指标集
    """
    
    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE
        if not self.enabled:
            return
            
        # 1. 延迟指标
        self.import_latency = Histogram(
            'kms_import_latency_seconds', 
            'Time spent importing knowledge',
            ['modality']
        )
        self.retrieval_latency = Histogram(
            'kms_retrieval_latency_seconds',
            'Time spent retrieving knowledge',
            ['strategy']
        )
        
        # 2. 资源指标
        self.vector_index_size = Gauge(
            'kms_vector_index_size',
            'Number of vectors in FAISS index'
        )
        self.model_cache_hits = Counter(
            'kms_model_cache_hits_total',
            'Number of times model was found in memory cache'
        )
        self.model_cache_misses = Counter(
            'kms_model_cache_misses_total',
            'Number of times model had to be loaded'
        )
        
        # 3. 业务指标
        self.api_fallback_count = Counter(
            'kms_api_fallback_total',
            'Number of times local model failed and fell back to API'
        )
        self.transaction_rollback_count = Counter(
            'kms_transaction_rollback_total',
            'Number of failed transactions that were rolled back'
        )

# 全局单例
_metrics_instance = None

def get_metrics() -> KMSMetrics:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = KMSMetrics()
    return _metrics_instance
