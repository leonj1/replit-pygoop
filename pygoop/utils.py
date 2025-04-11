"""
Utility functions for the PyGoop library.
"""

import logging
import uuid
import json
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with proper formatting.
    
    Args:
        name: The name of the logger.
        level: The logging level.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def generate_request_id() -> str:
    """
    Generate a unique request ID.
    
    Returns:
        A string containing a unique ID.
    """
    return str(uuid.uuid4())


def filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter sensitive data from a dictionary.
    
    Args:
        data: The dictionary to filter.
        
    Returns:
        The filtered dictionary.
    """
    if not data:
        return {}
        
    filtered_data = data.copy()
    
    sensitive_keys = [
        'api_key', 'apikey', 'api-key', 'key', 'secret',
        'password', 'token', 'authorization', 'auth'
    ]
    
    for key in list(filtered_data.keys()):
        key_lower = key.lower()
        
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            filtered_data[key] = '[FILTERED]'
        elif isinstance(filtered_data[key], dict):
            filtered_data[key] = filter_sensitive_data(filtered_data[key])
        elif isinstance(filtered_data[key], list):
            filtered_data[key] = [
                filter_sensitive_data(item) if isinstance(item, dict) else item
                for item in filtered_data[key]
            ]
            
    return filtered_data


def get_provider_from_url(url: str) -> Optional[str]:
    """
    Extract the provider name from a URL path.
    
    Args:
        url: The URL path.
        
    Returns:
        The provider name or None if not found.
    """
    if not url:
        return None
        
    parts = url.strip('/').split('/')
    if not parts:
        return None
        
    provider_map = {
        'openai': 'openai',
        'azure': 'azure',
        'bedrock': 'bedrock',
        'vertex': 'vertex',
        'openai-proxy': 'openai-proxy'
    }
    
    return provider_map.get(parts[0])


def format_openai_response(provider_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a provider-specific response to match OpenAI's format.
    
    Args:
        provider_response: The provider-specific response.
        
    Returns:
        The formatted response in OpenAI's format.
    """
    # This would be a more detailed implementation to handle
    # different provider response formats
    return provider_response


def transform_openai_to_bedrock(openai_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an OpenAI-format request to AWS Bedrock format.
    
    Args:
        openai_request: The request in OpenAI format.
        
    Returns:
        The transformed request in Bedrock format.
    """
    bedrock_request = {}
    
    # Extract model information
    model = openai_request.get('model', '')
    model_id = ""
    if model.startswith('bedrock/'):
        model_id = model.split('/', 1)[1]
        bedrock_request['modelId'] = model_id
    
    # Handle different types of requests (chat completions vs text completions)
    if 'messages' in openai_request:
        # This is a chat completion request
        messages = openai_request.get('messages', [])
        
        # Format depends on the specific Bedrock model (Anthropic, AI21, etc.)
        if model_id and 'anthropic' in model_id.lower():
            # Anthropic format
            prompt = "\\n".join([f"{m['role']}: {m['content']}" for m in messages])
            bedrock_request['prompt'] = prompt
        else:
            # Default format (simplified)
            bedrock_request['inputText'] = json.dumps(messages)
    elif 'prompt' in openai_request:
        # This is a text completion request
        bedrock_request['inputText'] = openai_request['prompt']
    
    # Map common parameters
    param_mapping = {
        'max_tokens': 'maxTokens',
        'temperature': 'temperature',
        'top_p': 'topP',
        'top_k': 'topK',
        'stop': 'stopSequences'
    }
    
    for openai_param, bedrock_param in param_mapping.items():
        if openai_param in openai_request:
            bedrock_request[bedrock_param] = openai_request[openai_param]
    
    return bedrock_request


def transform_openai_to_vertex(openai_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an OpenAI-format request to Google Vertex AI format.
    
    Args:
        openai_request: The request in OpenAI format.
        
    Returns:
        The transformed request in Vertex AI format.
    """
    vertex_request = {
        'instances': [],
        'parameters': {}
    }
    
    # Extract model information
    model = openai_request.get('model', '')
    model_id = ""
    if model.startswith('vertex/'):
        model_id = model.split('/', 1)[1]
    
    # Handle different types of requests (chat completions vs text completions)
    if 'messages' in openai_request:
        # This is a chat completion request
        vertex_request['instances'].append({
            'messages': openai_request.get('messages', [])
        })
    elif 'prompt' in openai_request:
        # This is a text completion request
        vertex_request['instances'].append({
            'prompt': openai_request['prompt']
        })
    
    # Map common parameters
    param_mapping = {
        'max_tokens': 'maxOutputTokens',
        'temperature': 'temperature',
        'top_p': 'topP',
        'top_k': 'topK',
        'stop': 'stopSequences'
    }
    
    for openai_param, vertex_param in param_mapping.items():
        if openai_param in openai_request:
            vertex_request['parameters'][vertex_param] = openai_request[openai_param]
    
    return vertex_request


def transform_bedrock_to_openai(bedrock_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform an AWS Bedrock response to OpenAI format.
    
    Args:
        bedrock_response: The response from Bedrock.
        
    Returns:
        The transformed response in OpenAI format.
    """
    openai_response = {
        'id': f"chatcmpl-{generate_request_id()}",
        'object': 'chat.completion',
        'created': int(uuid.uuid1().time // 10000),
        'model': f"bedrock/{bedrock_response.get('modelId', 'unknown')}",
        'choices': [],
        'usage': {
            'prompt_tokens': bedrock_response.get('inputTokenCount', 0),
            'completion_tokens': bedrock_response.get('outputTokenCount', 0),
            'total_tokens': (
                bedrock_response.get('inputTokenCount', 0) +
                bedrock_response.get('outputTokenCount', 0)
            )
        }
    }
    
    # Extract the completion
    if 'completion' in bedrock_response:
        content = bedrock_response['completion']
    elif 'outputText' in bedrock_response:
        content = bedrock_response['outputText']
    else:
        content = ''
    
    # Add to choices
    openai_response['choices'].append({
        'index': 0,
        'message': {
            'role': 'assistant',
            'content': content
        },
        'finish_reason': 'stop'  # Simplified
    })
    
    return openai_response


def transform_vertex_to_openai(vertex_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a Google Vertex AI response to OpenAI format.
    
    Args:
        vertex_response: The response from Vertex AI.
        
    Returns:
        The transformed response in OpenAI format.
    """
    openai_response = {
        'id': f"chatcmpl-{generate_request_id()}",
        'object': 'chat.completion',
        'created': int(uuid.uuid1().time // 10000),
        'model': f"vertex/{vertex_response.get('model', 'unknown')}",
        'choices': [],
        'usage': {
            'prompt_tokens': 0,  # Vertex doesn't always provide token counts
            'completion_tokens': 0,
            'total_tokens': 0
        }
    }
    
    # Handle different response formats
    predictions = vertex_response.get('predictions', [])
    if predictions and len(predictions) > 0:
        prediction = predictions[0]
        
        # PaLM and other models may have different response formats
        if 'candidates' in prediction:
            for i, candidate in enumerate(prediction['candidates']):
                openai_response['choices'].append({
                    'index': i,
                    'message': {
                        'role': 'assistant',
                        'content': candidate.get('content', '')
                    },
                    'finish_reason': 'stop'  # Simplified
                })
        elif 'content' in prediction:
            openai_response['choices'].append({
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': prediction['content']
                },
                'finish_reason': 'stop'  # Simplified
            })
    
    return openai_response