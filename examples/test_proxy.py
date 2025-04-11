"""
Test example for the PyGoop LLM proxy.

This script demonstrates how to make requests to the PyGoop LLM proxy.
"""

import os
import sys
import json
import requests

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pygoop.utils import setup_logger
import logging

# Set up logger
logger = setup_logger("pygoop_test", logging.INFO)

# The base URL for the PyGoop proxy
PROXY_BASE_URL = "http://localhost:5000"

def test_openai_request():
    """
    Test making a request to OpenAI via the proxy.
    """
    print("\nTesting OpenAI API request via proxy:")
    
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("This test will fail without a valid API key.")
        print("Set the OPENAI_API_KEY environment variable to run this test.")
        return
    
    # Define the request payload
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
    try:
        response = requests.post(
            f"{PROXY_BASE_URL}/openai/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(f"Model: {result.get('model', 'unknown')}")
            for choice in result.get("choices", []):
                content = choice.get("message", {}).get("content", "")
                print(f"Content: {content}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_proxy_health():
    """
    Test if the proxy server is running and responding to requests.
    """
    print("\nTesting proxy server health:")
    
    try:
        response = requests.get(f"{PROXY_BASE_URL}/", timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.RequestException as e:
        print(f"Error connecting to the proxy server: {str(e)}")
        print("Make sure the proxy server is running on port 5000.")

if __name__ == "__main__":
    print("PyGoop Proxy Test")
    print("================\n")
    
    print("Testing connection to the PyGoop proxy server at http://localhost:5000")
    
    # Test if the proxy server is running
    test_proxy_health()
    
    # Test a request to OpenAI
    test_openai_request()