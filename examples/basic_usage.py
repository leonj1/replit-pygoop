"""
Basic usage examples for the PyGoop library.
"""

import os
import sys

# Add the parent directory to the Python path so we can import pygoop
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygoop.crawler import Crawler

def simple_crawl():
    """
    Simple crawl example.
    """
    print("Simple crawl example:")
    
    # Create a crawler instance with default settings
    crawler = Crawler()
    
    # Start crawling from a URL
    results = crawler.crawl("https://example.com")
    
    # Process the results
    print(f"Crawled {len(results)} pages:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result.url} - {result.title}")
        
    print("\n")

def extract_content():
    """
    Extract content with CSS selectors example.
    """
    print("Extract content example:")
    
    # Create a crawler instance
    crawler = Crawler()
    
    # Fetch a single URL
    result = crawler._fetch_url("https://example.com")
    
    if result.status_code == 200:
        # Extract paragraphs
        paragraphs = crawler.parser.extract_content(result.content, "p")
        print(f"Found {len(paragraphs)} paragraphs:")
        for i, p in enumerate(paragraphs[:3]):  # Show first 3
            print(f"{i+1}. {p[:100]}...")
            
        # Extract all links
        links = crawler.parser.extract_attributes(result.content, "a", "href")
        print(f"\nFound {len(links)} links:")
        for i, link in enumerate(links[:5]):  # Show first 5
            print(f"{i+1}. {link}")
    else:
        print(f"Failed to fetch URL: {result.error}")
        
    print("\n")

def limit_depth_crawl():
    """
    Crawl with limited depth example.
    """
    print("Limited depth crawl example:")
    
    # Create a crawler instance with limited depth
    crawler = Crawler(max_depth=1, max_urls=10)
    
    # Start crawling from a URL
    results = crawler.crawl("https://example.com")
    
    # Process the results
    print(f"Crawled {len(results)} pages with max_depth=1:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result.url} - {result.title}")
        
    print("\n")

if __name__ == "__main__":
    print("PyGoop Basic Usage Examples")
    print("==========================\n")
    
    simple_crawl()
    extract_content()
    limit_depth_crawl()
