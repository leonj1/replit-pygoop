"""
Proxy module for the PyGoop library.

This module contains the proxy functionality that routes requests
to the appropriate LLM provider.
"""

import os
import json
import logging
import requests
from flask import Flask, request, Response, jsonify, stream_with_context
from typing import Dict, Any, Callable, Tuple, Optional

from .utils import (
    setup_logger,
    generate_request_id,
    filter_sensitive_data,
    get_provider_from_url,
    transform_openai_to_bedrock,
    transform_openai_to_vertex,
    transform_bedrock_to_openai,
    transform_vertex_to_openai
)
from .audit import AuditLogger, create_audit_middleware

# Set up logging
logger = setup_logger(__name__)

# Default endpoints for providers
PROVIDER_ENDPOINTS = {
    'openai': os.environ.get('OPENAI_ENDPOINT', 'https://api.openai.com/v1'),
    'azure': os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://your-resource-name.openai.azure.com'),
    'bedrock': os.environ.get('AWS_BEDROCK_ENDPOINT', 'https://bedrock-runtime.us-west-2.amazonaws.com'),
    'vertex': os.environ.get('VERTEX_AI_ENDPOINT', 'https://us-central1-aiplatform.googleapis.com/v1'),
}

def create_app() -> Flask:
    """
    Create a Flask application for the PyGoop proxy.
    
    Returns:
        A Flask application instance.
    """
    app = Flask(__name__)
    audit_logger = AuditLogger()
    
    @app.route('/')
    def index():
        """
        Root endpoint that returns information about the proxy.
        
        Returns:
            JSON response with proxy information.
        """
        return jsonify({
            "name": "PyGoop OpenLLM Proxy",
            "version": "0.1.0",
            "description": "A reverse proxy for integrating multiple LLM providers",
            "endpoints": list(PROVIDER_ENDPOINTS.keys()) + ["openai-proxy"],
            "status": "running"
        })
    
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    def proxy(path: str) -> Response:
        """
        Proxy endpoint that handles all requests and routes them to the appropriate provider.
        
        Args:
            path: The URL path.
            
        Returns:
            The proxied response.
        """
        request_id = generate_request_id()
        provider = get_provider_from_url(path)
        
        if not provider:
            return jsonify({
                'error': f"Invalid provider. URL path must start with one of: {', '.join(PROVIDER_ENDPOINTS.keys())}"
            }), 400
            
        # Determine the target endpoint and request details
        target_url, method, headers, data = prepare_request(provider, path, request)
        
        if provider == 'openai-proxy':
            # Handle routing through the common OpenAI-compatible interface
            return handle_openai_proxy_request(request_id, path, request)
        
        logger.info(f"Proxying {method} request to {target_url}")
        
        # Audit the request
        audit_logger.log_request(
            request_id=request_id,
            provider=provider,
            endpoint=path,
            method=method,
            data=filter_sensitive_data(data)
        )
        
        try:
            # Check if it's a streaming request
            is_streaming = check_streaming_request(data)
            
            if is_streaming:
                return handle_streaming_request(request_id, provider, path, target_url, method, headers, data)
            else:
                return handle_standard_request(request_id, provider, path, target_url, method, headers, data)
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error proxying request to {target_url}: {error_message}")
            
            # Audit the error
            audit_logger.log_error(
                request_id=request_id,
                provider=provider,
                endpoint=path,
                error_message=error_message
            )
            
            return jsonify({
                'error': error_message
            }), 500
    
    def prepare_request(provider: str, path: str, flask_request) -> Tuple[str, str, Dict[str, str], Dict[str, Any]]:
        """
        Prepare the request details for proxying.
        
        Args:
            provider: The LLM provider.
            path: The URL path.
            flask_request: The Flask request object.
            
        Returns:
            A tuple of (target_url, method, headers, data).
        """
        # Remove the provider from the path
        if '/' in path:
            _, path_without_provider = path.split('/', 1)
        else:
            path_without_provider = ''
            
        # Build the target URL
        base_url = PROVIDER_ENDPOINTS.get(provider)
        target_url = f"{base_url}/{path_without_provider}"
        
        # Get the request method
        method = flask_request.method
        
        # Copy the headers
        headers = dict(flask_request.headers)
        
        # Provider-specific header modifications
        if provider == 'openai':
            if 'OPENAI_API_KEY' in os.environ:
                headers['Authorization'] = f"Bearer {os.environ['OPENAI_API_KEY']}"
        elif provider == 'azure':
            if 'AZURE_OPENAI_API_KEY' in os.environ:
                headers['api-key'] = os.environ['AZURE_OPENAI_API_KEY']
            if 'AZURE_OPENAI_API_VERSION' in os.environ:
                headers['api-version'] = os.environ['AZURE_OPENAI_API_VERSION']
        elif provider == 'bedrock':
            # AWS credentials are handled at the request level
            pass
        elif provider == 'vertex':
            # Google credentials are handled at the request level
            pass
        
        # Forward the Content-Type header if present
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
            
        # Parse the request data
        data = {}
        if flask_request.data:
            try:
                data = json.loads(flask_request.data)
            except json.JSONDecodeError:
                data = {'raw': flask_request.data.decode('utf-8')}
        
        return target_url, method, headers, data
    
    def check_streaming_request(data: Dict[str, Any]) -> bool:
        """
        Check if the request is for streaming.
        
        Args:
            data: The request data.
            
        Returns:
            True if the request is for streaming, False otherwise.
        """
        return data.get('stream', False)
    
    def handle_standard_request(
        request_id: str,
        provider: str,
        path: str,
        target_url: str,
        method: str,
        headers: Dict[str, str],
        data: Dict[str, Any]
    ) -> Response:
        """
        Handle a standard (non-streaming) request.
        
        Args:
            request_id: The request ID.
            provider: The LLM provider.
            path: The URL path.
            target_url: The target URL for the request.
            method: The HTTP method.
            headers: The request headers.
            data: The request data.
            
        Returns:
            The proxied response.
        """
        # Make the request to the provider
        response = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            json=data if headers.get('Content-Type') == 'application/json' else None,
            data=data if headers.get('Content-Type') != 'application/json' else None,
            stream=False
        )
        
        # Parse the response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {'raw': response.text}
            
        # Audit the response
        audit_logger.log_response(
            request_id=request_id,
            provider=provider,
            endpoint=path,
            status_code=response.status_code,
            data=filter_sensitive_data(response_data)
        )
        
        # Return the response
        return Response(
            json.dumps(response_data),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
    
    def handle_streaming_request(
        request_id: str,
        provider: str,
        path: str,
        target_url: str,
        method: str,
        headers: Dict[str, str],
        data: Dict[str, Any]
    ) -> Response:
        """
        Handle a streaming request.
        
        Args:
            request_id: The request ID.
            provider: The LLM provider.
            path: The URL path.
            target_url: The target URL for the request.
            method: The HTTP method.
            headers: The request headers.
            data: The request data.
            
        Returns:
            The proxied streaming response.
        """
        # Make the request to the provider
        response = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            json=data if headers.get('Content-Type') == 'application/json' else None,
            data=data if headers.get('Content-Type') != 'application/json' else None,
            stream=True
        )
        
        # Define the generator function for streaming
        def generate():
            for chunk in response.iter_lines(decode_unicode=True):
                if chunk:
                    # Yield the chunk
                    yield f"data: {chunk}\n\n"
                    
                    # Try to parse the chunk for audit logging
                    try:
                        chunk_data = json.loads(chunk.replace('data: ', ''))
                        # Audit the chunk (could be batched for performance)
                        audit_logger.log_response(
                            request_id=request_id,
                            provider=provider,
                            endpoint=path,
                            status_code=response.status_code,
                            data=filter_sensitive_data(chunk_data)
                        )
                    except (json.JSONDecodeError, ValueError):
                        # Just log the raw chunk if can't parse
                        pass
            
            # End the stream
            yield 'data: [DONE]\n\n'
        
        # Return the streaming response
        return Response(
            stream_with_context(generate()),
            status=response.status_code,
            content_type='text/event-stream'
        )
    
    def handle_openai_proxy_request(
        request_id: str,
        path: str,
        flask_request
    ) -> Response:
        """
        Handle a request through the OpenAI-compatible proxy interface.
        
        Args:
            request_id: The request ID.
            path: The URL path.
            flask_request: The Flask request object.
            
        Returns:
            The proxied response.
        """
        logger.info(f"Handling OpenAI-compatible proxy request for {path}")
        
        # Parse the request data
        data = {}
        if flask_request.data:
            try:
                data = json.loads(flask_request.data)
            except json.JSONDecodeError:
                return jsonify({
                    'error': 'Invalid JSON in request body'
                }), 400
        
        # Extract the model parameter to determine the target provider
        model = data.get('model', '')
        
        # Route based on the model prefix
        if model.startswith('bedrock/'):
            # Route to AWS Bedrock
            bedrock_data = transform_openai_to_bedrock(data)
            
            # Remove the provider from the path
            if '/' in path:
                _, path_without_provider = path.split('/', 1)
            else:
                path_without_provider = ''
                
            # Build the target URL (simplified for example)
            target_url = f"{PROVIDER_ENDPOINTS['bedrock']}/{path_without_provider}"
            
            # Make the request to Bedrock (simplified)
            response = requests.post(
                url=target_url,
                headers={'Content-Type': 'application/json'},
                json=bedrock_data
            )
            
            # Transform the response back to OpenAI format
            try:
                bedrock_response = response.json()
                openai_response = transform_bedrock_to_openai(bedrock_response)
                
                return jsonify(openai_response)
            except Exception as e:
                return jsonify({
                    'error': f"Error transforming Bedrock response: {str(e)}"
                }), 500
                
        elif model.startswith('vertex/'):
            # Route to Google Vertex AI
            vertex_data = transform_openai_to_vertex(data)
            
            # Remove the provider from the path
            if '/' in path:
                _, path_without_provider = path.split('/', 1)
            else:
                path_without_provider = ''
                
            # Build the target URL (simplified for example)
            target_url = f"{PROVIDER_ENDPOINTS['vertex']}/{path_without_provider}"
            
            # Make the request to Vertex AI (simplified)
            response = requests.post(
                url=target_url,
                headers={'Content-Type': 'application/json'},
                json=vertex_data
            )
            
            # Transform the response back to OpenAI format
            try:
                vertex_response = response.json()
                openai_response = transform_vertex_to_openai(vertex_response)
                
                return jsonify(openai_response)
            except Exception as e:
                return jsonify({
                    'error': f"Error transforming Vertex AI response: {str(e)}"
                }), 500
                
        else:
            # Default to OpenAI
            # Remove the provider from the path
            if '/' in path:
                _, path_without_provider = path.split('/', 1)
            else:
                path_without_provider = ''
                
            # Build the target URL
            target_url = f"{PROVIDER_ENDPOINTS['openai']}/{path_without_provider}"
            
            # Copy the headers
            headers = dict(flask_request.headers)
            
            # Add the OpenAI API key
            if 'OPENAI_API_KEY' in os.environ:
                headers['Authorization'] = f"Bearer {os.environ['OPENAI_API_KEY']}"
            
            # Make the request to OpenAI
            response = requests.post(
                url=target_url,
                headers=headers,
                json=data
            )
            
            # Return the response directly
            try:
                openai_response = response.json()
                return jsonify(openai_response)
            except json.JSONDecodeError:
                return Response(
                    response.text,
                    status=response.status_code,
                    content_type=response.headers.get('Content-Type', 'application/json')
                )
    
    return app


def main():
    """
    Main entry point for the PyGoop proxy server.
    """
    port = int(os.environ.get("PORT", 5000))
    
    # Print startup information
    print("\nPyGoop OpenLLM Proxy Server")
    print("==========================\n")
    print(f"Server running at: http://localhost:{port}")
    print("\nAvailable Endpoints:")
    for provider, endpoint in PROVIDER_ENDPOINTS.items():
        print(f"  /{provider}/... -> {endpoint}")
    print(f"  /openai-proxy/... -> OpenAI-compatible interface for all providers")
    
    # API key warnings
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nWarning: OPENAI_API_KEY environment variable is not set.")
        print("OpenAI API calls will fail unless using a mock server.")
    
    print("\nUse examples/test_proxy.py to test the proxy server.\n")
    
    # Create and run the app
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()