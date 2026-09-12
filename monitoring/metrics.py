import logging
from prometheus_client import Counter, Histogram, Gauge, Summary
from config.settings import settings

logger = logging.getLogger(__name__)

# Application metrics
app_requests_total = Counter(
    'app_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

app_request_duration_seconds = Histogram(
    'app_request_duration_seconds', 
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

app_active_connections = Gauge(
    'app_active_connections', 
    'Number of active connections'
)

# Prediction metrics
prediction_requests_total = Counter(
    'prediction_requests_total', 
    'Total number of prediction requests',
    ['session_type', 'source']
)

prediction_latency_seconds = Histogram(
    'prediction_latency_seconds', 
    'Prediction generation latency in seconds',
    ['session_type'],
    buckets=settings.PREDICTION_LATENCY_BUCKETS
)

prediction_success_rate = Gauge(
    'prediction_success_rate', 
    'Success rate of prediction requests'
)

# Database metrics
database_queries_total = Counter(
    'database_queries_total', 
    'Total number of database queries',
    ['operation', 'table']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds', 
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=settings.DATABASE_QUERY_LATENCY_BUCKETS
)

database_connections_total = Gauge(
    'database_connections_total', 
    'Total number of database connections'
)

# AI provider metrics
ai_provider_requests_total = Counter(
    'ai_provider_requests_total', 
    'Total number of AI provider requests',
    ['provider', 'status']
)

ai_provider_latency_seconds = Histogram(
    'ai_provider_latency_seconds', 
    'AI provider request latency in seconds',
    ['provider']
)

# System metrics
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent', 
    'System CPU usage percentage'
)

system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes', 
    'System memory usage in bytes'
)

# Custom summary for prediction accuracy
prediction_accuracy_summary = Summary(
    'prediction_accuracy_summary', 
    'Summary of prediction accuracy metrics'
)

# Initialize metrics with default values
if settings.MONITORING_ENABLED:
    logger.info("Monitoring system initialized")
    # Set initial values for gauges
    app_active_connections.set(0)
    database_connections_total.set(0)
    system_cpu_usage_percent.set(0.0)
    system_memory_usage_bytes.set(0)
else:
    logger.info("Monitoring disabled")