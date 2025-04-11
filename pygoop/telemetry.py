"""
Telemetry module for the PyGoop library.

This module provides functionality for instrumenting the proxy
with OpenTelemetry to collect metrics.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from prometheus_client import start_http_server

from .utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Define metrics
meter = metrics.get_meter("pygoop")

# Request counters
request_counter = meter.create_counter(
    name="requests_total",
    description="Total number of requests",
    unit="requests",
)

# Error counter
error_counter = meter.create_counter(
    name="errors_total",
    description="Total number of errors",
    unit="errors",
)

# Request duration histogram
request_duration = meter.create_histogram(
    name="request_duration_seconds",
    description="Duration of requests in seconds",
    unit="seconds",
)

# Provider request counters
provider_request_counter = meter.create_counter(
    name="provider_requests_total",
    description="Total number of requests by provider",
    unit="requests",
)

# Provider error counters
provider_error_counter = meter.create_counter(
    name="provider_errors_total",
    description="Total number of errors by provider",
    unit="errors",
)

# Streaming request counter
streaming_request_counter = meter.create_counter(
    name="streaming_requests_total",
    description="Total number of streaming requests",
    unit="requests",
)


def setup_telemetry(app, prometheus_port: int = 8081) -> None:
    """
    Set up OpenTelemetry instrumentation for the Flask app.
    
    Args:
        app: The Flask application.
        prometheus_port: The port for the Prometheus metrics endpoint.
    """
    # Create a PrometheusMetricReader
    prometheus_reader = PrometheusMetricReader()
    
    # Set up the meter provider
    provider = MeterProvider(metric_readers=[prometheus_reader])
    metrics.set_meter_provider(provider)
    
    # Start the Prometheus HTTP server
    start_http_server(port=prometheus_port)
    logger.info(f"Prometheus metrics available at http://localhost:{prometheus_port}/metrics")
    
    # Instrument Flask
    FlaskInstrumentor().instrument_app(app)
    logger.info("Flask app instrumented with OpenTelemetry")


class RequestMetrics:
    """Class for tracking metrics for a single request."""
    
    def __init__(self, provider: str, endpoint: str):
        """
        Initialize request metrics.
        
        Args:
            provider: The LLM provider.
            endpoint: The API endpoint.
        """
        self.provider = provider
        self.endpoint = endpoint
        self.start_time = time.time()
        self.is_streaming = False
        self.error = False
        
        # Record the request
        request_counter.add(1, {"provider": provider, "endpoint": endpoint})
        provider_request_counter.add(1, {"provider": provider})
    
    def record_streaming(self) -> None:
        """Record that this is a streaming request."""
        self.is_streaming = True
        streaming_request_counter.add(1, {"provider": self.provider, "endpoint": self.endpoint})
    
    def record_error(self, error_type: str) -> None:
        """
        Record an error.
        
        Args:
            error_type: The type of error.
        """
        self.error = True
        error_counter.add(1, {"provider": self.provider, "endpoint": self.endpoint, "error_type": error_type})
        provider_error_counter.add(1, {"provider": self.provider, "error_type": error_type})
    
    def record_completion(self) -> None:
        """Record the completion of the request and its duration."""
        duration = time.time() - self.start_time
        request_duration.record(
            duration,
            {"provider": self.provider, "endpoint": self.endpoint, "streaming": str(self.is_streaming)}
        )


def create_metrics_middleware(app):
    """
    Create middleware for request/response metrics tracking.
    
    Args:
        app: The Flask application.
        
    Returns:
        A decorator function for wrapping route handlers.
    """
    def metrics_middleware(view_func):
        """
        Middleware function for tracking request metrics.
        
        Args:
            view_func: The view function to wrap.
            
        Returns:
            The wrapped view function.
        """
        def wrapper(*args, **kwargs):
            provider = kwargs.get('provider', 'unknown')
            endpoint = kwargs.get('endpoint', 'unknown')
            
            # Start tracking metrics
            metrics = RequestMetrics(provider, endpoint)
            
            try:
                # Call the original view function
                response = view_func(*args, **kwargs)
                
                # Check if this was a streaming request
                if getattr(response, 'mimetype', '') == 'text/event-stream':
                    metrics.record_streaming()
                
                # Record completion
                metrics.record_completion()
                
                return response
            except Exception as e:
                # Record error
                metrics.record_error(type(e).__name__)
                metrics.record_completion()
                raise
                
        return wrapper
    
    return metrics_middleware