import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import sys
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import PyGoop components
from pygoop.crawler import Crawler
from pygoop.utils import is_valid_url

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pygoop-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def index():
    """Home page of the PyGoop web interface."""
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    """Handle crawl requests."""
    url = request.form.get('url', '')
    max_urls = int(request.form.get('max_urls', 10))
    max_depth = int(request.form.get('max_depth', 2))
    follow_external = request.form.get('follow_external') == 'on'
    
    if not is_valid_url(url):
        return jsonify({
            'error': 'Invalid URL. Please enter a valid URL starting with http:// or https://'
        }), 400
    
    try:
        # Configure crawler
        crawler = Crawler(
            max_urls=max_urls,
            max_depth=max_depth,
            follow_external_links=follow_external
        )
        
        # Start crawling
        results = crawler.crawl(url)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'url': result.url,
                'title': result.title,
                'status_code': result.status_code,
                'content_length': len(result.content),
                'links_count': len(result.links),
                'error': result.error
            })
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': formatted_results
        })
    
    except Exception as e:
        logger.exception(f"Error while crawling: {str(e)}")
        return jsonify({
            'error': f'Error while crawling: {str(e)}'
        }), 500

@app.route('/extract', methods=['POST'])
def extract():
    """Handle content extraction requests."""
    url = request.form.get('url', '')
    selector = request.form.get('selector', '')
    
    if not url or not selector:
        return jsonify({
            'error': 'URL and CSS selector are required'
        }), 400
    
    if not is_valid_url(url):
        return jsonify({
            'error': 'Invalid URL. Please enter a valid URL starting with http:// or https://'
        }), 400
    
    try:
        # Create crawler
        crawler = Crawler()
        
        # Extract content
        result = crawler._fetch_url(url)
        
        if result.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch URL: {result.error}'
            }), 400
        
        # Extract content using the selector
        extracted = crawler.parser.extract_content(result.content, selector)
        
        return jsonify({
            'success': True,
            'count': len(extracted),
            'results': extracted
        })
    
    except Exception as e:
        logger.exception(f"Error while extracting content: {str(e)}")
        return jsonify({
            'error': f'Error while extracting content: {str(e)}'
        }), 500

@app.route('/run_example')
def run_example():
    """Run a PyGoop example and return the results."""
    example_type = request.args.get('type', 'simple')
    
    try:
        # Create a crawler instance
        crawler = Crawler(max_urls=5, max_depth=2)
        
        if example_type == 'simple':
            # Simple crawl example
            results = crawler.crawl("https://example.com")
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'url': result.url,
                    'title': result.title,
                    'status_code': result.status_code
                })
            
            return jsonify({
                'example_type': 'Simple Crawl',
                'results': formatted_results
            })
            
        elif example_type == 'extract':
            # Extract content example
            result = crawler._fetch_url("https://example.com")
            
            if result.status_code != 200:
                return jsonify({
                    'error': f'Failed to fetch URL: {result.error}'
                }), 400
            
            # Extract paragraphs
            paragraphs = crawler.parser.extract_content(result.content, "p")
            
            return jsonify({
                'example_type': 'Extract Content',
                'paragraphs': paragraphs[:3]  # First 3 paragraphs
            })
            
        else:
            return jsonify({
                'error': 'Invalid example type'
            }), 400
    
    except Exception as e:
        logger.exception(f"Error running example: {str(e)}")
        return jsonify({
            'error': f'Error running example: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)