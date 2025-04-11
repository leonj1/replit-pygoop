"""
Test example for the PyGoop LLM proxy with a mock server.

This script demonstrates how to test the PyGoop LLM proxy with a mock server.
"""

import os
import sys
import json
import requests
import threading
import time
from mock_proxy_example import create_mock_server

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pygoop.utils import setup_logger
import logging

# Set up logger
logger = setup_logger("pygoop_mock_test", logging.INFO)

# The base URL for the mock server
MOCK_SERVER_URL = "http://localhost:8000"
# The base URL for the PyGoop proxy
PROXY_BASE_URL = "http://localhost:5000"

def start_mock_server():
    """
    Start the mock server in a separate thread.
    """
    print("Starting mock server...")
    app = create_mock_server()
    
    # Run the server in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000, debug=False)).start()
    
    # Wait for the server to start
    time.sleep(1)
    
    # Check if the server is running
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/")
        if response.status_code == 200:
            print("Mock server is running.")
        else:
            print(f"Mock server returned status code {response.status_code}.")
    except requests.RequestException as e:
        print(f"Error connecting to mock server: {str(e)}")

def test_with_mock_server():
    """
    Test making a request to the mock server via the proxy.
    """
    print("\nTesting mock server directly:")
    
    # Define the request payload
    payload = {
        "model": "mock-model",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    # Make the request directly to the mock server
    try:
        response = requests.post(
            f"{MOCK_SERVER_URL}/v1/chat/completions",
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
    
    # Update the OPENAI_API_KEY environment variable to point to our mock server
    os.environ["OPENAI_API_KEY"] = "mock-api-key"
    # Update the OpenAI endpoint in the proxy to point to our mock server
    os.environ["OPENAI_ENDPOINT"] = MOCK_SERVER_URL
    
    print("\nTesting proxy with mock server:")
    
    # Make the request through the proxy
    try:
        response = requests.post(
            f"{PROXY_BASE_URL}/openai/v1/chat/completions",
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

if __name__ == "__main__":
    print("PyGoop Mock Proxy Test")
    print("=====================\n")
    
    print("This test will start a mock server on port 8000 and use the PyGoop proxy on port 5000.")
    print("Make sure the PyGoop proxy server is running on port 5000.")
    
    # Start the mock server
    start_mock_server()
    
    # Test with the mock server
    test_with_mock_server()