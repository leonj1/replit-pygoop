"""
Audit module for the PyGoop library.

This module provides functionality for logging and auditing
requests and responses to and from LLM providers.
"""

import logging
import json
import time
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class AuditLogger:
    """Class for audit logging of LLM requests and responses."""
    
    def __init__(self, log_dir='logs', log_level=logging.INFO):
        """Initialize the audit logger.
        
        Args:
            log_dir: Directory to store audit logs.
            log_level: Logging level.
        """
        self.log_dir = log_dir
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler
        self.file_handler = logging.FileHandler(
            os.path.join(log_dir, f'audit_{datetime.now().strftime("%Y%m%d")}.log')
        )
        self.file_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(self.file_handler)
        
    def log_request(self, request_id, provider, endpoint, method, data):
        """Log a request to an LLM provider.
        
        Args:
            request_id: Unique identifier for the request.
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            method: The HTTP method.
            data: The request data.
        """
        log_data = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'endpoint': endpoint,
            'method': method,
            'data': data,
            'type': 'request'
        }
        
        logger.info(f"REQUEST {request_id}: {json.dumps(log_data)}")
        
    def log_response(self, request_id, provider, endpoint, status_code, data,
                    response_time=None):
        """Log a response from an LLM provider.
        
        Args:
            request_id: Unique identifier for the request.
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            status_code: The HTTP status code.
            data: The response data.
            response_time: The time taken to receive the response.
        """
        log_data = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'endpoint': endpoint,
            'status_code': status_code,
            'data': data,
            'response_time': response_time,
            'type': 'response'
        }
        
        logger.info(f"RESPONSE {request_id}: {json.dumps(log_data)}")
        
    def log_error(self, request_id, provider, endpoint, error_message):
        """Log an error from an LLM provider.
        
        Args:
            request_id: Unique identifier for the request.
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            error_message: The error message.
        """
        log_data = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'endpoint': endpoint,
            'error': error_message,
            'type': 'error'
        }
        
        logger.error(f"ERROR {request_id}: {json.dumps(log_data)}")
        
    def get_request_logger(self, provider, endpoint):
        """Get a function for logging requests for a specific provider and endpoint.
        
        Args:
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            
        Returns:
            A function that logs requests.
        """
        def log_request_func(request_id, method, data):
            self.log_request(request_id, provider, endpoint, method, data)
            
        return log_request_func
        
    def get_response_logger(self, provider, endpoint):
        """Get a function for logging responses for a specific provider and endpoint.
        
        Args:
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            
        Returns:
            A function that logs responses.
        """
        def log_response_func(request_id, status_code, data, response_time=None):
            self.log_response(request_id, provider, endpoint, status_code, data,
                             response_time)
            
        return log_response_func
        
    def get_error_logger(self, provider, endpoint):
        """Get a function for logging errors for a specific provider and endpoint.
        
        Args:
            provider: The LLM provider (e.g., 'openai', 'azure').
            endpoint: The API endpoint being called.
            
        Returns:
            A function that logs errors.
        """
        def log_error_func(request_id, error_message):
            self.log_error(request_id, provider, endpoint, error_message)
            
        return log_error_func


class RequestTimer:
    """Class for timing requests to LLM providers."""
    
    def __init__(self):
        """Initialize the request timer."""
        self.start_time = None
        
    def start(self):
        """Start timing a request."""
        self.start_time = time.time()
        
    def end(self):
        """End timing a request and return the elapsed time.
        
        Returns:
            The elapsed time in seconds.
        """
        if self.start_time is None:
            return 0
            
        return time.time() - self.start_time
        
    def __enter__(self):
        """Start timing when used as a context manager."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing when used as a context manager."""
        self.end()


def create_audit_middleware(audit_logger):
    """Create a middleware function for request/response auditing.
    
    Args:
        audit_logger: An instance of AuditLogger.
        
    Returns:
        A middleware function.
    """
    def audit_middleware(provider, endpoint):
        def decorator(f):
            def wrapped(*args, **kwargs):
                # Generate a unique request ID
                request_id = f"{int(time.time())}-{os.urandom(4).hex()}"
                
                # Get loggers for this provider and endpoint
                log_request = audit_logger.get_request_logger(provider, endpoint)
                log_response = audit_logger.get_response_logger(provider, endpoint)
                log_error = audit_logger.get_error_logger(provider, endpoint)
                
                # Log the request
                request_data = kwargs.get('data', {})
                log_request(request_id, kwargs.get('method', 'GET'), request_data)
                
                # Time the request
                timer = RequestTimer()
                timer.start()
                
                try:
                    # Call the original function
                    response = f(*args, **kwargs)
                    
                    # Log the response
                    response_time = timer.end()
                    log_response(
                        request_id,
                        getattr(response, 'status_code', 200),
                        getattr(response, 'data', {}),
                        response_time
                    )
                    
                    return response
                except Exception as e:
                    # Log the error
                    log_error(request_id, str(e))
                    raise
                    
            return wrapped
        return decorator
        
    return audit_middleware