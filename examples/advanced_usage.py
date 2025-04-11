"""
Advanced usage examples for the PyGoop library.
"""

import time
import os
import sys

# Add the parent directory to the Python path so we can import pygoop
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygoop.crawler import Crawler
from pygoop.utils import is_valid_url

def concurrent_crawl():
    """
    Concurrent crawling example.
    """
    print("Concurrent crawling example:")
    
    # Time a single-threaded crawl
    start_time = time.time()
    crawler_single = Crawler(max_depth=2, max_urls=20, concurrent_requests=1)
    results_single = crawler_single.crawl("https://example.com")
    single_time = time.time() - start_time
    
    # Time a multi-threaded crawl
    start_time = time.time()
    crawler_multi = Crawler(max_depth=2, max_urls=20, concurrent_requests=5)
    results_multi = crawler_multi.crawl("https://example.com")
    multi_time = time.time() - start_time
    
    print(f"Single-threaded: Crawled {len(results_single)} pages in {single_time:.2f} seconds")
    print(f"Multi-threaded: Crawled {len(results_multi)} pages in {multi_time:.2f} seconds")
    print(f"Speed improvement: {(single_time / multi_time):.2f}x faster")
    print("\n")

def custom_user_agent():
    """
    Custom user agent example.
    """
    print("Custom user agent example:")
    
    # Create a crawler with a custom user agent
    crawler = Crawler(
        user_agent="PyGoopExample/1.0 (+https://example.com/bot)",
        max_urls=5
    )
    
    # Start crawling
    results = crawler.crawl("https://httpbin.org/user-agent")
    
    if results and results[0].status_code == 200:
        print(f"Sent user agent: {crawler.user_agent}")
        print(f"Response content: {results[0].content}")
    else:
        print("Failed to get user agent response")
        
    print("\n")

def follow_external_links():
    """
    Following external links example.
    """
    print("Following external links example:")
    
    # Create a crawler that follows external links
    crawler = Crawler(
        follow_external_links=True,
        max_depth=2,
        max_urls=20
    )
    
    # Start crawling from a URL that contains external links
    results = crawler.crawl("https://example.com")
    
    # Group results by domain
    domains = {}
    for result in results:
        if result.status_code == 200:
            domain = is_valid_url(result.url) and result.url.split('/')[2] or "unknown"
            
            if domain not in domains:
                domains[domain] = 0
            domains[domain] += 1
            
    # Print results
    print(f"Crawled {len(results)} pages across {len(domains)} domains:")
    for domain, count in domains.items():
        print(f"- {domain}: {count} pages")
        
    print("\n")

def extract_specific_content():
    """
    Extract specific content using CSS selectors.
    """
    print("Extract specific content example:")
    
    # Create a crawler instance
    crawler = Crawler()
    
    # Website with clear structured content
    result = crawler._fetch_url("https://news.ycombinator.com/")
    
    if result.status_code == 200:
        # Extract story titles
        titles = crawler.parser.extract_content(result.content, ".titleline > a")
        
        # Extract points
        points = crawler.parser.extract_content(result.content, ".score")
        
        # Print results
        print("Hacker News Top Stories:")
        for i, (title, point) in enumerate(zip(titles[:5], points[:5])):
            print(f"{i+1}. {title} - {point}")
    else:
        print(f"Failed to fetch URL: {result.error}")
        
    print("\n")

if __name__ == "__main__":
    print("PyGoop Advanced Usage Examples")
    print("=============================\n")
    
    concurrent_crawl()
    custom_user_agent()
    follow_external_links()
    extract_specific_content()
