"""
Parser module for the PyGoop library.

This module handles parsing HTML content, extracting links,
and processing content using CSS selectors.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class Parser:
    """
    HTML parser for PyGoop.
    
    This class handles parsing HTML content, extracting links
    and processing content using CSS selectors.
    """
    
    def __init__(self):
        """
        Initialize a new Parser instance.
        """
        pass
        
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from the HTML content.
        
        Args:
            html: The HTML content to parse.
            base_url: The base URL to resolve relative links.
            
        Returns:
            A list of absolute URLs.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Extract all <a> tags with href attributes
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip empty links and JavaScript links
            if not href or href.startswith(('javascript:', '#')):
                continue
                
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Only include http and https URLs
            if absolute_url.startswith(('http://', 'https://')):
                links.append(absolute_url)
                
        return links
    
    def extract_title(self, html: str) -> str:
        """
        Extract the title from the HTML content.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            The page title or an empty string if not found.
        """
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.title
        
        if title_tag and title_tag.string:
            return title_tag.string.strip()
            
        # Try h1 if title is not available
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.string:
            return h1_tag.string.strip()
            
        return ""
    
    def extract_text(self, html: str) -> str:
        """
        Extract readable text content from the HTML.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            The extracted text content.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link', 'noscript']):
            element.decompose()
            
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up the text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = ' '.join(lines)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_content(self, html: str, css_selector: str) -> List[str]:
        """
        Extract content from HTML using a CSS selector.
        
        Args:
            html: The HTML content to parse.
            css_selector: The CSS selector to use for extraction.
            
        Returns:
            A list of extracted content strings.
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for element in soup.select(css_selector):
            # Get text if it's a text element
            if element.string:
                results.append(element.string.strip())
            else:
                # Otherwise get the HTML content
                results.append(element.get_text(separator=' ', strip=True))
                
        return results
    
    def extract_attributes(self, html: str, css_selector: str, attribute: str) -> List[str]:
        """
        Extract attribute values from elements matching a CSS selector.
        
        Args:
            html: The HTML content to parse.
            css_selector: The CSS selector to use for extraction.
            attribute: The attribute name to extract.
            
        Returns:
            A list of attribute values.
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for element in soup.select(css_selector):
            if element.has_attr(attribute):
                results.append(element[attribute])
                
        return results
