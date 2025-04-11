"""
PyGoop - A Python web crawler and scraping library
================================================

PyGoop is a Python library inspired by the Golang 'goop' project.
It provides a simple interface for crawling websites, extracting data,
and processing the results.

Basic usage:
-----------

```python
from pygoop.crawler import Crawler

# Create a crawler instance
crawler = Crawler()

# Start crawling from a URL
results = crawler.crawl("https://example.com")

# Process the results
for result in results:
    print(f"URL: {result.url}")
    print(f"Title: {result.title}")
    print(f"Content: {result.content[:100]}...")
```
"""
