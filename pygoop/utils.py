"""
Utility functions for the PyGoop library.
"""

import logging
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import validators
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with proper formatting.
    
    Args:
        name: The name of the logger.
        level: The logging level.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Only add handler if not already added to avoid duplicate logs
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: The URL to check.
        
    Returns:
        True if the URL is valid, False otherwise.
    """
    if not url:
        return False
        
    # Check if URL starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
        
    # Use validators library for validation
    return validators.url(url)

def clean_url(url: str) -> str:
    """
    Clean and normalize a URL.
    
    Args:
        url: The URL to clean.
        
    Returns:
        A cleaned and normalized URL.
    """
    # Parse the URL
    parsed = urlparse(url)
    
    # Extract the query parameters
    query_params = parse_qs(parsed.query)
    
    # Sort the query parameters and reconstruct the query string
    sorted_query = urlencode(sorted(query_params.items()), doseq=True) if query_params else ""
    
    # Reconstruct the URL
    clean = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        sorted_query,
        ""  # Remove fragment
    ))
    
    # Ensure URL ends with / if it's a domain root
    if parsed.path == "":
        clean = f"{clean}/"
        
    return clean

def get_domain(url: str) -> Optional[str]:
    """
    Extract the domain from a URL.
    
    Args:
        url: The URL to extract the domain from.
        
    Returns:
        The domain name or None if the URL is invalid.
    """
    if not is_valid_url(url):
        return None
        
    parsed = urlparse(url)
    return parsed.netloc

def get_base_url(url: str) -> Optional[str]:
    """
    Extract the base URL (scheme and domain) from a URL.
    
    Args:
        url: The URL to extract the base URL from.
        
    Returns:
        The base URL or None if the URL is invalid.
    """
    if not is_valid_url(url):
        return None
        
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.
    
    Args:
        url1: The first URL.
        url2: The second URL.
        
    Returns:
        True if both URLs belong to the same domain, False otherwise.
    """
    domain1 = get_domain(url1)
    domain2 = get_domain(url2)
    
    if domain1 is None or domain2 is None:
        return False
        
    return domain1 == domain2
