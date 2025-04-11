"""
PyGoop - Python OpenLLM Proxy
=============================

PyGoop is a Python implementation of the Golang 'goop' project.
It provides a reverse proxy for integrating multiple LLM providers
(OpenAI, Azure OpenAI, Vertex AI, Bedrock) into a single interface.

Features:
---------
- Proxies multiple LLM providers at the network level
- Dynamic routing based on URL prefixes
- Common OpenAI-compatible interface for all providers
- Support for pre and post-response hooks
- Non-blocking streaming support (SSE)
- Audit logging for requests and responses

Basic usage:
-----------

```python
from pygoop.proxy import create_app

# Create the proxy app
app = create_app()

# Run the app
app.run(host='0.0.0.0', port=8000)
```
"""
