"""
LLM proxy examples for the PyGoop library.

This script demonstrates how to use PyGoop as a reverse proxy for LLM APIs.
It includes examples for:
1. Making requests to OpenAI via PyGoop
2. Making requests to Bedrock via PyGoop using OpenAI-compatible format
3. Making requests to Vertex AI via PyGoop using OpenAI-compatible format
"""

import os
import json
import requests
import sys
from typing import Dict, Any, List

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PyGoop utilities
from pygoop.utils import setup_logger

# Set up logger
logger = setup_logger("pygoop_example")

# Base URL for the PyGoop proxy
PROXY_BASE_URL = "http://localhost:5000"


def make_openai_request(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make a request to OpenAI via the PyGoop proxy.
    
    Args:
        endpoint: The API endpoint (e.g., "chat/completions").
        payload: The request payload.
        
    Returns:
        The API response.
    """
    url = f"{PROXY_BASE_URL}/openai/{endpoint}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return {"error": response.text}


def make_bedrock_request_via_openai_proxy(model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Make a request to AWS Bedrock via the PyGoop proxy using OpenAI-compatible format.
    
    Args:
        model: The Bedrock model ID (prefixed with "bedrock/").
        messages: The messages in OpenAI chat format.
        
    Returns:
        The API response in OpenAI format.
    """
    url = f"{PROXY_BASE_URL}/openai-proxy/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return {"error": response.text}


def make_vertex_request_via_openai_proxy(model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Make a request to Google Vertex AI via the PyGoop proxy using OpenAI-compatible format.
    
    Args:
        model: The Vertex AI model ID (prefixed with "vertex/").
        messages: The messages in OpenAI chat format.
        
    Returns:
        The API response in OpenAI format.
    """
    url = f"{PROXY_BASE_URL}/openai-proxy/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return {"error": response.text}


def openai_example():
    """
    Example of using the PyGoop proxy to make requests to OpenAI.
    """
    print("OpenAI Example via PyGoop proxy:")
    
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set. This example will fail.")
        print("Please set OPENAI_API_KEY to your OpenAI API key to run this example.")
        return
    
    # Define the payload
    payload = {
        "model": "gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    # Make the request
    response = make_openai_request("chat/completions", payload)
    
    # Process the response
    if "error" in response:
        print(f"Error: {response['error']}")
    else:
        print("Response:")
        print(f"Model: {response.get('model', 'unknown')}")
        for choice in response.get("choices", []):
            content = choice.get("message", {}).get("content", "")
            print(f"Content: {content}")
    
    print("\n")


def bedrock_example():
    """
    Example of using the PyGoop proxy to make requests to AWS Bedrock via OpenAI-compatible interface.
    """
    print("AWS Bedrock Example via PyGoop proxy:")
    
    # Check if AWS credentials are set
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        print("Warning: AWS credentials not set. This example will fail.")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to your AWS credentials to run this example.")
        return
    
    # Define the messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of Germany?"}
    ]
    
    # Make the request
    response = make_bedrock_request_via_openai_proxy("bedrock/anthropic.claude-3-sonnet-20240229", messages)
    
    # Process the response
    if "error" in response:
        print(f"Error: {response['error']}")
    else:
        print("Response:")
        print(f"Model: {response.get('model', 'unknown')}")
        for choice in response.get("choices", []):
            content = choice.get("message", {}).get("content", "")
            print(f"Content: {content}")
    
    print("\n")


def vertex_example():
    """
    Example of using the PyGoop proxy to make requests to Google Vertex AI via OpenAI-compatible interface.
    """
    print("Google Vertex AI Example via PyGoop proxy:")
    
    # Check if Google credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set. This example will fail.")
        print("Please set GOOGLE_APPLICATION_CREDENTIALS to your Google credentials file path to run this example.")
        return
    
    # Define the messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of Italy?"}
    ]
    
    # Make the request
    response = make_vertex_request_via_openai_proxy("vertex/chat-bison", messages)
    
    # Process the response
    if "error" in response:
        print(f"Error: {response['error']}")
    else:
        print("Response:")
        print(f"Model: {response.get('model', 'unknown')}")
        for choice in response.get("choices", []):
            content = choice.get("message", {}).get("content", "")
            print(f"Content: {content}")
    
    print("\n")


if __name__ == "__main__":
    print("PyGoop LLM Proxy Examples")
    print("========================\n")
    
    print("These examples assume that the PyGoop proxy server is running at http://localhost:5000")
    print("Start the server with: python main.py\n")
    
    openai_example()
    bedrock_example()
    vertex_example()