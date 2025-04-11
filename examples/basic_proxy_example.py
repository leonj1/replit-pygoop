"""
Basic usage example for the PyGoop LLM proxy.

This script demonstrates how to use PyGoop as a reverse proxy for LLM APIs.
It includes a simple example for setting up and running the proxy server.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pygoop.proxy import create_app
from pygoop.utils import setup_logger
import logging

# Set up logger
logger = setup_logger("pygoop_example", logging.INFO)

def run_proxy_server():
    """
    Run the PyGoop proxy server.
    """
    print("Starting PyGoop LLM Proxy Server...")
    
    # Create the app
    app = create_app()
    
    # Run the app
    port = int(os.environ.get("PORT", 5000))
    print(f"Server running at http://localhost:{port}")
    print("Available endpoints:")
    print("- /openai/...")
    print("- /azure/...")
    print("- /bedrock/...")
    print("- /vertex/...")
    print("- /openai-proxy/...")
    print("\nPress Ctrl+C to stop the server.")
    
    # Run the server
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    print("PyGoop Basic Proxy Example")
    print("========================\n")
    
    # Check if API keys are set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("OpenAI API calls will fail without a valid API key.")
        print("Set the OPENAI_API_KEY environment variable to use OpenAI endpoints.")
        print()
    
    # Run the proxy server
    run_proxy_server()