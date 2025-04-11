"""
Proxy module for the PyGoop library.

This module contains the main proxy functionality for routing
requests to different LLM providers.
"""

import os
import logging
from flask import Flask, request, Response, jsonify, stream_with_context
import requests
from functools import wraps

logger = logging.getLogger(__name__)

class LLMEngine:
    """Base class for LLM provider engines."""
    
    def __init__(self, base_url, api_key=None):
        """Initialize an LLM engine.
        
        Args:
            base_url: The base URL for the LLM provider API.
            api_key: The API key for authenticating with the provider.
        """
        self.base_url = base_url
        self.api_key = api_key
        
    def get_headers(self):
        """Get the headers for making requests to the LLM provider.
        
        Returns:
            A dictionary of headers.
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        return headers
        
    def proxy_request(self, path, method, headers=None, data=None, stream=False):
        """Proxy a request to the LLM provider.
        
        Args:
            path: The path to append to the base URL.
            method: The HTTP method to use.
            headers: Additional headers to include.
            data: The request data.
            stream: Whether to stream the response.
            
        Returns:
            The response from the LLM provider.
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        
        request_headers = self.get_headers()
        if headers:
            # Copy specific headers from the original request
            for header in ['Content-Type', 'Accept']:
                if header in headers:
                    request_headers[header] = headers[header]
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                json=data,
                stream=stream
            )
            
            return response
        except Exception as e:
            logger.exception(f"Error proxying request to {url}: {str(e)}")
            return None
            
class OpenAIEngine(LLMEngine):
    """Engine for OpenAI API."""
    
    def __init__(self, api_key=None):
        super().__init__("https://api.openai.com/v1", api_key)


class AzureOpenAIEngine(LLMEngine):
    """Engine for Azure OpenAI API."""
    
    def __init__(self, endpoint, api_key=None):
        super().__init__(endpoint, api_key)
        
    def get_headers(self):
        headers = super().get_headers()
        # Azure uses a different header for authentication
        if self.api_key:
            headers.pop('Authorization', None)
            headers['api-key'] = self.api_key
        return headers


class BedrockEngine(LLMEngine):
    """Engine for AWS Bedrock API."""
    
    def __init__(self, aws_region="us-east-1", aws_access_key=None, aws_secret_key=None):
        super().__init__(f"https://bedrock-runtime.{aws_region}.amazonaws.com/", None)
        self.aws_region = aws_region
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        
    def proxy_request(self, path, method, headers=None, data=None, stream=False):
        """Override to add AWS authentication."""
        # In a real implementation, we would use AWS SDK for authentication
        # For this example, we'll just pass through the request
        return super().proxy_request(path, method, headers, data, stream)


class VertexAIEngine(LLMEngine):
    """Engine for Google Vertex AI API."""
    
    def __init__(self, project_id, location="us-central1"):
        super().__init__(f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}", None)
        self.project_id = project_id
        self.location = location
        
    def proxy_request(self, path, method, headers=None, data=None, stream=False):
        """Override to add Google authentication."""
        # In a real implementation, we would use Google SDK for authentication
        # For this example, we'll just pass through the request
        return super().proxy_request(path, method, headers, data, stream)


class OpenAIProxyEngine(LLMEngine):
    """Engine for providing OpenAI-compatible interface for other LLM providers."""
    
    def __init__(self, provider_engines):
        super().__init__("", None)
        self.provider_engines = provider_engines
        
    def proxy_request(self, path, method, headers=None, data=None, stream=False):
        """Route request to the appropriate provider based on the model parameter."""
        if not data or 'model' not in data:
            return Response(
                response='{"error": "model parameter is required"}',
                status=400,
                mimetype='application/json'
            )
            
        model = data['model']
        
        # Route based on model prefix
        if model.startswith('bedrock/'):
            # Extract the actual model ID
            model_id = model.split('/', 1)[1]
            
            # Update data with provider-specific format
            bedrock_data = {
                # Convert OpenAI format to Bedrock format
                "modelId": model_id,
                "prompt": data.get('prompt', data.get('messages', [])),
                "max_tokens": data.get('max_tokens', 100),
                "temperature": data.get('temperature', 0.7),
                # Add other parameters as needed
            }
            
            return self.provider_engines['bedrock'].proxy_request(
                path=f"model/{model_id}/invoke",
                method=method,
                headers=headers,
                data=bedrock_data,
                stream=stream
            )
            
        elif model.startswith('vertex/'):
            # Extract the actual model ID
            model_id = model.split('/', 1)[1]
            
            # Update data with provider-specific format
            vertex_data = {
                # Convert OpenAI format to Vertex AI format
                "instances": [{
                    "prompt": data.get('prompt', ''),
                    "messages": data.get('messages', [])
                }],
                "parameters": {
                    "maxOutputTokens": data.get('max_tokens', 100),
                    "temperature": data.get('temperature', 0.7),
                    # Add other parameters as needed
                }
            }
            
            return self.provider_engines['vertex'].proxy_request(
                path=f"publishers/google/models/{model_id}:predict",
                method=method,
                headers=headers,
                data=vertex_data,
                stream=stream
            )
            
        elif model.startswith('azure/'):
            # Extract the actual model ID
            model_id = model.split('/', 1)[1]
            
            # For Azure, typically retain the OpenAI format but route to Azure endpoint
            return self.provider_engines['azure'].proxy_request(
                path=f"openai/deployments/{model_id}/chat/completions",
                method=method,
                headers=headers,
                data=data,
                stream=stream
            )
            
        else:
            # Assume it's a standard OpenAI model
            return self.provider_engines['openai'].proxy_request(
                path=f"chat/completions",  # or the appropriate endpoint
                method=method,
                headers=headers,
                data=data,
                stream=stream
            )


def create_audit_middleware():
    """Create a middleware function for request/response auditing."""
    
    def audit_middleware(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Pre-request hook
            logger.info(f"Request: {request.method} {request.path}")
            if request.is_json:
                logger.debug(f"Request data: {request.get_json()}")
                
            # Execute the view function
            response = f(*args, **kwargs)
            
            # Post-response hook
            logger.info(f"Response status: {response.status_code}")
            
            return response
        return decorated_function
    
    return audit_middleware


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)
    
    # Configure engines
    openai_engine = OpenAIEngine(api_key=os.environ.get('OPENAI_API_KEY'))
    
    azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    azure_engine = AzureOpenAIEngine(
        endpoint=azure_endpoint if azure_endpoint else "https://example.openai.azure.com/",
        api_key=os.environ.get('AZURE_OPENAI_API_KEY')
    )
    
    bedrock_engine = BedrockEngine(
        aws_region=os.environ.get('AWS_REGION', 'us-east-1'),
        aws_access_key=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    
    vertex_engine = VertexAIEngine(
        project_id=os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    )
    
    openai_proxy_engine = OpenAIProxyEngine({
        'openai': openai_engine,
        'azure': azure_engine,
        'bedrock': bedrock_engine,
        'vertex': vertex_engine
    })
    
    # Apply middleware
    audit_middleware = create_audit_middleware()
    
    @app.route('/')
    def index():
        """Home page showing the API status."""
        return jsonify({
            'status': 'ok',
            'message': 'PyGoop - Python OpenLLM Proxy',
            'endpoints': [
                '/openai/...',
                '/azure/...',
                '/bedrock/...',
                '/vertex/...',
                '/openai-proxy/...'
            ]
        })
    
    @app.route('/openai/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @audit_middleware
    def openai_proxy(subpath):
        """Proxy requests to OpenAI API."""
        response = openai_engine.proxy_request(
            path=subpath,
            method=request.method,
            headers=request.headers,
            data=request.get_json() if request.is_json else None,
            stream=request.headers.get('Accept') == 'text/event-stream'
        )
        
        if not response:
            return jsonify({'error': 'Failed to proxy request to OpenAI API'}), 500
            
        if response.headers.get('Content-Type') == 'text/event-stream':
            # Handle streaming response
            def generate():
                for chunk in response.iter_lines():
                    if chunk:
                        yield chunk + b'\n'
                        
            return Response(
                stream_with_context(generate()),
                status=response.status_code,
                content_type='text/event-stream'
            )
        else:
            # Regular response
            return Response(
                response=response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )
    
    @app.route('/azure/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @audit_middleware
    def azure_proxy(subpath):
        """Proxy requests to Azure OpenAI API."""
        response = azure_engine.proxy_request(
            path=subpath,
            method=request.method,
            headers=request.headers,
            data=request.get_json() if request.is_json else None,
            stream=request.headers.get('Accept') == 'text/event-stream'
        )
        
        if not response:
            return jsonify({'error': 'Failed to proxy request to Azure OpenAI API'}), 500
            
        if response.headers.get('Content-Type') == 'text/event-stream':
            # Handle streaming response
            def generate():
                for chunk in response.iter_lines():
                    if chunk:
                        yield chunk + b'\n'
                        
            return Response(
                stream_with_context(generate()),
                status=response.status_code,
                content_type='text/event-stream'
            )
        else:
            # Regular response
            return Response(
                response=response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )
    
    @app.route('/bedrock/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @audit_middleware
    def bedrock_proxy(subpath):
        """Proxy requests to AWS Bedrock API."""
        response = bedrock_engine.proxy_request(
            path=subpath,
            method=request.method,
            headers=request.headers,
            data=request.get_json() if request.is_json else None,
            stream=request.headers.get('Accept') == 'text/event-stream'
        )
        
        if not response:
            return jsonify({'error': 'Failed to proxy request to AWS Bedrock API'}), 500
            
        # Handle the response similarly to other routes
        return Response(
            response=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
    
    @app.route('/vertex/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @audit_middleware
    def vertex_proxy(subpath):
        """Proxy requests to Google Vertex AI API."""
        response = vertex_engine.proxy_request(
            path=subpath,
            method=request.method,
            headers=request.headers,
            data=request.get_json() if request.is_json else None,
            stream=request.headers.get('Accept') == 'text/event-stream'
        )
        
        if not response:
            return jsonify({'error': 'Failed to proxy request to Google Vertex AI API'}), 500
            
        # Handle the response similarly to other routes
        return Response(
            response=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
    
    @app.route('/openai-proxy/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @audit_middleware
    def openai_compat_proxy(subpath):
        """Proxy requests using OpenAI-compatible interface to other providers."""
        response = openai_proxy_engine.proxy_request(
            path=subpath,
            method=request.method,
            headers=request.headers,
            data=request.get_json() if request.is_json else None,
            stream=request.headers.get('Accept') == 'text/event-stream'
        )
        
        if isinstance(response, Response):
            # The engine already created a Response object
            return response
            
        if not response:
            return jsonify({'error': 'Failed to proxy request'}), 500
            
        if response.headers.get('Content-Type') == 'text/event-stream':
            # Handle streaming response
            def generate():
                for chunk in response.iter_lines():
                    if chunk:
                        yield chunk + b'\n'
                        
            return Response(
                stream_with_context(generate()),
                status=response.status_code,
                content_type='text/event-stream'
            )
        else:
            # Regular response
            return Response(
                response=response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )
    
    return app