# PyGoop - Python OpenLLM Proxy

PyGoop is a Python-based reverse proxy for LLM APIs inspired by the Golang 'goop' project. It provides a single interface for multi-cloud LLM deployments and SaaS API integrations.

## Features

- Proxies multiple LLM providers at the network level
- Dynamic routing based on URL prefixes to different LLM engines:
  - `/openai` for OpenAI API
  - `/azure` for Azure OpenAI API
  - `/bedrock` for AWS Bedrock API
  - `/vertex` for Google Vertex AI API
  - `/openai-proxy` for OpenAI-compatible interface for all providers
- Common OpenAI-compatible interface for all providers
- Support for pre and post-response hooks for monitoring and logging
- Proper handling of streaming responses (SSE)
- Audit logging of requests and responses
- OpenTelemetry instrumentation for metrics and monitoring

## Installation

```bash
pip install pygoop
```

## Quick Start

### Running the Proxy Server

```python
from pygoop.proxy import create_app

# Create the app
app = create_app()

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Using OpenAI via the Proxy

```python
import requests
import json
import os

# Set your API keys as environment variables
os.environ["OPENAI_API_KEY"] = "your-api-key"

# Make a request to OpenAI via the proxy
response = requests.post(
    "http://localhost:5000/openai/chat/completions",
    headers={
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    }
)

print(json.dumps(response.json(), indent=2))
```

### Using AWS Bedrock via the OpenAI-compatible Interface

```python
import requests
import json
import os

# Set your AWS credentials as environment variables
os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"

# Make a request to Bedrock via the OpenAI-compatible proxy
response = requests.post(
    "http://localhost:5000/openai-proxy/chat/completions",
    headers={
        "Content-Type": "application/json"
    },
    json={
        "model": "bedrock/anthropic.claude-3-sonnet-20240229",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of Germany?"}
        ]
    }
)

print(json.dumps(response.json(), indent=2))
```

## Architecture

This reverse proxy integrates multiple LLM providers using a modular and efficient approach:

### Engine Network Interface

Each LLM provider is proxied at the network level, allowing upstream clients to use their native SDKs seamlessly. This allows infrastructure changes to happen independently of the application layer.

### Dynamic Engine Routing

Middleware dynamically routes requests based on URL prefixes to the appropriate engine.

### Pre and Post-Response Hooks

Engines integrate with the audit package to log inline hooks on raw request/response structs. The proxy supports non-blocking SSE/streaming, and the post-response hook is triggered only after the client connection is closed.

### Metrics and Monitoring with OpenTelemetry

PyGoop includes OpenTelemetry instrumentation for collecting and exporting metrics:

- Request counts by provider and endpoint
- Request durations with detailed breakdowns
- Success and error rates
- Streaming vs. non-streaming request tracking

Metrics are exposed via a Prometheus endpoint (default: http://localhost:8081/metrics) and can be visualized using tools like Grafana.

#### Enabling OpenTelemetry

```python
from pygoop.proxy import create_app

# Create the app with telemetry enabled (default)
app = create_app(enable_telemetry=True, prometheus_port=8081)

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

You can also configure OpenTelemetry via environment variables:
- `ENABLE_TELEMETRY`: Set to "false" to disable telemetry (default: "true")
- `PROMETHEUS_PORT`: Port for the Prometheus metrics endpoint (default: 8081)
