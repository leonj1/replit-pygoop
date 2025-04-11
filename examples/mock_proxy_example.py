"""
Mock example for the PyGoop LLM proxy.

This script demonstrates how to test the PyGoop LLM proxy with mock responses.
"""

import os
import sys
import json
import logging
from flask import Flask, jsonify, request

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pygoop.utils import setup_logger

# Set up logger
logger = setup_logger("pygoop_mock", logging.INFO)

def create_mock_server():
    """
    Create a mock LLM server for testing.
    
    Returns:
        A Flask application instance.
    """
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        """
        Root endpoint.
        """
        return jsonify({
            "name": "Mock LLM API Server",
            "version": "0.1.0",
            "status": "running"
        })
    
    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """
        Mock chat completions endpoint.
        """
        data = request.json
        
        # Extract the user's message
        messages = data.get('messages', [])
        user_message = ""
        for message in messages:
            if message.get('role') == 'user':
                user_message = message.get('content', '')
                break
        
        # Create a mock response
        response = {
            "id": "mock-chat-response-123",
            "object": "chat.completion",
            "created": 1682900000,
            "model": data.get('model', 'mock-model'),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"This is a mock response to: '{user_message}'"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30
            }
        }
        
        # Check if it's a streaming request
        if data.get('stream', False):
            def generate():
                # First chunk with role
                yield f"data: {json.dumps({'id': 'mock-chat-response-123', 'object': 'chat.completion.chunk', 'created': 1682900000, 'model': data.get('model', 'mock-model'), 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
                
                # Split the content into chunks for streaming
                content = f"This is a mock response to: '{user_message}'"
                words = content.split(' ')
                for i in range(0, len(words), 2):
                    chunk = " ".join(words[i:i+2])
                    yield f"data: {json.dumps({'id': 'mock-chat-response-123', 'object': 'chat.completion.chunk', 'created': 1682900000, 'model': data.get('model', 'mock-model'), 'choices': [{'index': 0, 'delta': {'content': chunk}, 'finish_reason': None}]})}\n\n"
                
                # Final chunk with finish reason
                yield f"data: {json.dumps({'id': 'mock-chat-response-123', 'object': 'chat.completion.chunk', 'created': 1682900000, 'model': data.get('model', 'mock-model'), 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                
                # End marker
                yield "data: [DONE]\n\n"
            
            return app.response_class(
                generate(),
                mimetype='text/event-stream'
            )
        
        return jsonify(response)
    
    return app

if __name__ == "__main__":
    print("Starting Mock LLM API Server")
    app = create_mock_server()
    app.run(host='0.0.0.0', port=8000, debug=True)
    print("Mock server running at http://localhost:8000")