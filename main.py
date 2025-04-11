import os
import logging
from pygoop.proxy import create_app, PROVIDER_ENDPOINTS
from pygoop.utils import setup_logger

# Set up logger
logger = setup_logger("pygoop", logging.INFO)

# Create the app
app = create_app()

if __name__ == '__main__':
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
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True)