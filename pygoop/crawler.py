"""
Crawler module for the PyGoop library.

This module contains the main Crawler class that handles
the web crawling functionality.
"""

import time
import logging
import requests
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import validators
from typing import List, Dict, Set, Optional, Union, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from .parser import Parser
from .utils import setup_logger, clean_url, is_valid_url

# Set up logging
logger = setup_logger(__name__)

@dataclass
class CrawlResult:
    """Class to store the result of a crawl for a single URL."""
    url: str
    status_code: int
    title: str = ""
    content: str = ""
    links: List[str] = None
    headers: Dict[str, str] = None
    error: str = ""
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.headers is None:
            self.headers = {}

class Crawler:
    """
    Main crawler class for PyGoop.
    
    This class handles crawling websites, respecting robots.txt rules,
    rate limiting, and extracting content based on CSS selectors.
    """
    
    def __init__(
        self,
        user_agent: str = "PyGoop/0.1.0 (+https://github.com/pygoop)",
        delay: float = 1.0,
        max_depth: int = 3,
        max_urls: int = 100,
        timeout: int = 30,
        respect_robots_txt: bool = True,
        follow_external_links: bool = False,
        headers: Optional[Dict[str, str]] = None,
        concurrent_requests: int = 1
    ):
        """
        Initialize a new Crawler instance.
        
        Args:
            user_agent: String to use as the User-Agent header.
            delay: Time in seconds to wait between requests to the same domain.
            max_depth: Maximum depth to crawl.
            max_urls: Maximum number of URLs to crawl.
            timeout: Request timeout in seconds.
            respect_robots_txt: Whether to respect robots.txt rules.
            follow_external_links: Whether to follow links to external domains.
            headers: Additional headers to include in requests.
            concurrent_requests: Number of concurrent requests to make.
        """
        self.user_agent = user_agent
        self.delay = delay
        self.max_depth = max_depth
        self.max_urls = max_urls
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt
        self.follow_external_links = follow_external_links
        self.concurrent_requests = concurrent_requests
        
        self.default_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if headers:
            self.default_headers.update(headers)
            
        self.parser = Parser()
        self.robots_cache = {}  # Cache for robots.txt parsers
        self.last_request_time = {}  # Track last request time per domain
        
    def _get_robots_parser(self, url: str) -> RobotFileParser:
        """
        Get or create a robots.txt parser for the given URL's domain.
        
        Args:
            url: The URL to get the robots parser for.
            
        Returns:
            A RobotFileParser instance for the domain.
        """
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        robots_url = f"{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        try:
            parser.read()
            self.robots_cache[domain] = parser
            logger.debug(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Error reading robots.txt from {robots_url}: {e}")
            # Create an empty parser that allows everything
            parser = RobotFileParser()
            self.robots_cache[domain] = parser
            
        return parser
    
    def _can_fetch(self, url: str) -> bool:
        """
        Check if a URL can be fetched according to robots.txt rules.
        
        Args:
            url: The URL to check.
            
        Returns:
            True if the URL can be fetched, False otherwise.
        """
        if not self.respect_robots_txt:
            return True
            
        try:
            parser = self._get_robots_parser(url)
            return parser.can_fetch(self.user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow if there's an error checking
    
    def _respect_rate_limit(self, url: str):
        """
        Ensure we respect the rate limit for a domain.
        This method will sleep if needed to maintain the minimum delay
        between requests to the same domain.
        
        Args:
            url: The URL being requested.
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s for domain {domain}")
                time.sleep(sleep_time)
                
        self.last_request_time[domain] = time.time()
    
    def _fetch_url(self, url: str) -> CrawlResult:
        """
        Fetch a single URL and return the result.
        
        Args:
            url: The URL to fetch.
            
        Returns:
            A CrawlResult object containing the response data.
        """
        if not is_valid_url(url):
            return CrawlResult(
                url=url,
                status_code=0,
                error="Invalid URL"
            )
            
        if not self._can_fetch(url):
            return CrawlResult(
                url=url,
                status_code=0,
                error="Blocked by robots.txt"
            )
        
        self._respect_rate_limit(url)
        
        try:
            response = requests.get(
                url,
                headers=self.default_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            result = CrawlResult(
                url=response.url,  # Use the final URL after redirects
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            if response.status_code == 200:
                # Only parse content if it's HTML
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    result.title = self.parser.extract_title(response.text)
                    result.content = self.parser.extract_text(response.text)
                    result.links = self.parser.extract_links(response.text, url)
                else:
                    result.error = f"Not an HTML page (Content-Type: {content_type})"
            else:
                result.error = f"HTTP error: {response.status_code}"
                
            return result
            
        except requests.exceptions.Timeout:
            return CrawlResult(
                url=url,
                status_code=0,
                error="Request timed out"
            )
        except requests.exceptions.ConnectionError:
            return CrawlResult(
                url=url,
                status_code=0,
                error="Connection error"
            )
        except Exception as e:
            return CrawlResult(
                url=url,
                status_code=0,
                error=f"Error: {str(e)}"
            )
    
    def crawl(self, start_url: str, css_selector: str = None) -> List[CrawlResult]:
        """
        Crawl a website starting from the given URL.
        
        Args:
            start_url: The URL to start crawling from.
            css_selector: Optional CSS selector to extract specific content.
            
        Returns:
            A list of CrawlResult objects.
        """
        if not is_valid_url(start_url):
            logger.error(f"Invalid start URL: {start_url}")
            return []
            
        # Clean and normalize the start URL
        start_url = clean_url(start_url)
        
        # Initialize the crawler state
        results = []
        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        
        # Store the base domain for checking external links
        base_domain = urlparse(start_url).netloc
        
        while to_visit and len(results) < self.max_urls:
            if self.concurrent_requests > 1:
                # Process multiple URLs concurrently
                batch = []
                batch_depths = []
                
                # Get a batch of URLs to process
                while to_visit and len(batch) < self.concurrent_requests:
                    url, depth = to_visit.pop(0)
                    if url not in visited:
                        batch.append(url)
                        batch_depths.append(depth)
                        visited.add(url)
                
                if not batch:
                    continue
                    
                # Process the batch concurrently
                with ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
                    batch_results = list(executor.map(self._fetch_url, batch))
                    
                # Process the results and add new URLs to visit
                for result, depth in zip(batch_results, batch_depths):
                    results.append(result)
                    
                    # If we reached max_urls, stop adding new URLs
                    if len(results) >= self.max_urls:
                        break
                        
                    # Only follow links if we haven't reached max_depth
                    if depth < self.max_depth and result.links:
                        for link in result.links:
                            link_domain = urlparse(link).netloc
                            
                            # Check if we should follow this link
                            if link not in visited and (
                                self.follow_external_links or link_domain == base_domain
                            ):
                                to_visit.append((link, depth + 1))
            else:
                # Process one URL at a time
                url, depth = to_visit.pop(0)
                
                if url in visited:
                    continue
                    
                visited.add(url)
                result = self._fetch_url(url)
                results.append(result)
                
                # If we reached max_urls, stop adding new URLs
                if len(results) >= self.max_urls:
                    break
                    
                # Only follow links if we haven't reached max_depth
                if depth < self.max_depth and result.links:
                    for link in result.links:
                        link_domain = urlparse(link).netloc
                        
                        # Check if we should follow this link
                        if link not in visited and (
                            self.follow_external_links or link_domain == base_domain
                        ):
                            to_visit.append((link, depth + 1))
                            
        return results
    
    def extract(self, url: str, css_selector: str) -> List[str]:
        """
        Extract content from a single URL using a CSS selector.
        
        Args:
            url: The URL to extract content from.
            css_selector: The CSS selector to use for extraction.
            
        Returns:
            A list of extracted content strings.
        """
        result = self._fetch_url(url)
        
        if result.status_code != 200:
            logger.error(f"Failed to fetch {url}: {result.error}")
            return []
            
        return self.parser.extract_content(result.content, css_selector)
