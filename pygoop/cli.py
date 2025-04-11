"""
Command-line interface for the PyGoop library.
"""

import sys
import json
import csv
import click
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

from .crawler import Crawler, CrawlResult
from .utils import setup_logger, is_valid_url

# Set up logging
logger = setup_logger(__name__)

def write_json(results: List[CrawlResult], output_file: str):
    """
    Write crawl results to a JSON file.
    
    Args:
        results: The crawl results to write.
        output_file: The path to the output file.
    """
    output = []
    
    for result in results:
        output.append({
            "url": result.url,
            "status_code": result.status_code,
            "title": result.title,
            "content_length": len(result.content),
            "links_count": len(result.links),
            "error": result.error
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
def write_csv(results: List[CrawlResult], output_file: str):
    """
    Write crawl results to a CSV file.
    
    Args:
        results: The crawl results to write.
        output_file: The path to the output file.
    """
    fieldnames = ["url", "status_code", "title", "content_length", "links_count", "error"]
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                "url": result.url,
                "status_code": result.status_code,
                "title": result.title,
                "content_length": len(result.content),
                "links_count": len(result.links),
                "error": result.error
            })

def write_links(results: List[CrawlResult], output_file: str):
    """
    Write all links found during crawling to a text file.
    
    Args:
        results: The crawl results to extract links from.
        output_file: The path to the output file.
    """
    all_links = set()
    
    for result in results:
        all_links.update(result.links)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in sorted(all_links):
            f.write(f"{link}\n")

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PyGoop - A Python web crawler and scraping library."""
    pass

@cli.command()
@click.argument('url', required=True)
@click.option('--output', '-o', help='Output file for results')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'links']), default='json',
              help='Output format (default: json)')
@click.option('--depth', '-d', type=int, default=3, help='Maximum crawl depth (default: 3)')
@click.option('--delay', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
@click.option('--max-urls', type=int, default=100, help='Maximum number of URLs to crawl (default: 100)')
@click.option('--user-agent', help='User agent string to use')
@click.option('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
@click.option('--ignore-robots', is_flag=True, help='Ignore robots.txt restrictions')
@click.option('--follow-external', is_flag=True, help='Follow links to external domains')
@click.option('--concurrent', type=int, default=1, help='Number of concurrent requests (default: 1)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def crawl(url, output, format, depth, delay, max_urls, user_agent, timeout, 
          ignore_robots, follow_external, concurrent, verbose):
    """
    Crawl a website starting from the specified URL.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        sys.exit(1)
        
    # Configure the crawler
    crawler_config = {
        "max_depth": depth,
        "delay": delay,
        "max_urls": max_urls,
        "timeout": timeout,
        "respect_robots_txt": not ignore_robots,
        "follow_external_links": follow_external,
        "concurrent_requests": concurrent
    }
    
    if user_agent:
        crawler_config["user_agent"] = user_agent
        
    logger.info(f"Starting crawl of {url} with max depth {depth}, max URLs {max_urls}")
    
    # Create crawler and start crawling
    crawler = Crawler(**crawler_config)
    results = crawler.crawl(url)
    
    # Print summary
    success_count = sum(1 for r in results if r.status_code == 200)
    logger.info(f"Crawl complete. Processed {len(results)} URLs, {success_count} successful.")
    
    # Write output if specified
    if output:
        if format == 'json':
            write_json(results, output)
        elif format == 'csv':
            write_csv(results, output)
        elif format == 'links':
            write_links(results, output)
        logger.info(f"Results written to {output} in {format} format")
    else:
        # Print brief summary to console
        click.echo("\nCrawl Results Summary:")
        click.echo(f"Total URLs processed: {len(results)}")
        click.echo(f"Successful: {success_count}")
        click.echo(f"Failed: {len(results) - success_count}")
        
        # Show first few results
        click.echo("\nSample results:")
        for result in results[:5]:
            status = "✓" if result.status_code == 200 else "✗"
            click.echo(f"{status} {result.url} - {result.title[:50]}")
            
        if len(results) > 5:
            click.echo(f"... and {len(results) - 5} more URLs")

@cli.command()
@click.argument('url', required=True)
@click.argument('selector', required=True)
@click.option('--output', '-o', help='Output file for results')
@click.option('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
@click.option('--user-agent', help='User agent string to use')
def extract(url, selector, output, timeout, user_agent):
    """
    Extract content from a URL using a CSS selector.
    """
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        sys.exit(1)
        
    # Configure the crawler
    crawler_config = {
        "timeout": timeout
    }
    
    if user_agent:
        crawler_config["user_agent"] = user_agent
        
    # Create crawler and extract content
    crawler = Crawler(**crawler_config)
    result = crawler._fetch_url(url)
    
    if result.status_code != 200:
        logger.error(f"Failed to fetch {url}: {result.error}")
        sys.exit(1)
        
    extracted = crawler.parser.extract_content(result.content, selector)
    
    # Output results
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            for item in extracted:
                f.write(f"{item}\n")
        logger.info(f"Extracted {len(extracted)} items to {output}")
    else:
        click.echo(f"Extracted {len(extracted)} items:")
        for item in extracted:
            click.echo(f"- {item}")

if __name__ == '__main__':
    cli()
