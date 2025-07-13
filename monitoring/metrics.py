import time
from collections import defaultdict, deque
from typing import Dict, Any
from utils.logger import logger
import config

class MetricsCollector:
    """Metrics collection without external dependencies"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(deque)
        self.start_time = time.time()
        
        # Keep only last 5000 entries for each metric
        self.max_history = 5000
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        key = self._make_key(name, labels)
        hist = self.histograms[key]
        hist.append(value)
        
        # Keep only recent values
        while len(hist) > self.max_history:
            hist.popleft()
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a key from metric name and labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        summary = {
            "uptime_seconds": time.time() - self.start_time,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }
        
        # Calculate histogram statistics
        for key, values in self.histograms.items():
            if values:
                sorted_values = sorted(values)
                count = len(sorted_values)
                summary["histograms"][key] = {
                    "count": count,
                    "sum": sum(sorted_values),
                    "avg": sum(sorted_values) / count,
                    "min": sorted_values[0],
                    "max": sorted_values[-1],
                    "p50": sorted_values[int(count * 0.5)],
                    "p95": sorted_values[int(count * 0.95)],
                    "p99": sorted_values[int(count * 0.99)]
                }
        
        return summary
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()

# Global metrics instance
metrics = MetricsCollector()

async def log_vector_search_metrics(
    user_id: str, 
    latency_ms: float,
    num_candidates: int,
    result_score: float,
    cache_hit: bool
):
    """Log vector search metrics for monitoring"""

    
    # Update metrics
    metrics.increment_counter("cache_requests", labels={
        "user_id": user_id,
        "hit": str(cache_hit)
    })
    
    metrics.record_histogram("query_latency_ms", latency_ms)
    metrics.record_histogram("similarity_score", result_score)
    metrics.set_gauge("candidates", num_candidates,labels={
        "user_id": user_id})
    
    # Log the metrics
    if config.LOG_VECTOR_METRICS:
        logger.info(
            f"user={user_id} latency={latency_ms:.2f}ms "
            f"score={result_score:.3f} candidates={num_candidates} "
            f"hit={cache_hit}"
        )

def get_metrics() -> Dict[str, Any]:
    """Get current metrics summary"""
    return metrics.get_metrics_summary()