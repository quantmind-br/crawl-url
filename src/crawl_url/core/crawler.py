"""Web crawling implementation for crawl-url application."""

import hashlib
import logging
import time
import urllib.robotparser
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, RequestException, Timeout
from urllib3.util.retry import Retry

from .models import CrawlResult


class URLExtractor:
    """Extract and validate URLs from web pages."""
    
    def __init__(self, allowed_domains: Optional[Set[str]] = None, url_filter_base: Optional[str] = None) -> None:
        """Initialize URL extractor with filtering options."""
        self.allowed_domains = set(allowed_domains or [])
        self.url_filter_base = url_filter_base
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'crawl-url/1.0 (Compatible Web Crawler)'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def extract_urls_from_page(self, url: str, timeout: int = 10) -> Set[str]:
        """Extract all URLs from a single page."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            if not self._is_html_content(response):
                return set()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = set()
            
            # Extract from anchor tags
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if self._is_valid_url(absolute_url):
                    urls.add(self._normalize_url(absolute_url))
            
            return urls
            
        except requests.RequestException as e:
            logging.warning(f"Error fetching {url}: {e}")
            return set()
    
    def _is_html_content(self, response: requests.Response) -> bool:
        """Check if response contains HTML content."""
        content_type = response.headers.get('content-type', '').lower()
        return 'text/html' in content_type
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate and filter URLs."""
        try:
            parsed = urlparse(url)
            
            # Basic validation
            if not (parsed.scheme and parsed.netloc):
                return False
            
            # Domain filtering
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                return False
            
            # Base URL filtering
            if self.url_filter_base:
                if not url.startswith(self.url_filter_base):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments."""
        parsed = urlparse(url)
        # Remove fragment (anchor)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc, 
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized


class RateLimiter:
    """Implement respectful rate limiting for web crawling."""
    
    def __init__(self, default_delay: float = 1.0) -> None:
        """Initialize rate limiter with default delay."""
        self.default_delay = default_delay
        self.domain_delays: Dict[str, float] = defaultdict(lambda: default_delay)
        self.last_request_time: Dict[str, float] = defaultdict(float)
    
    def wait_if_needed(self, url: str) -> None:
        """Implement respectful delay based on domain."""
        domain = urlparse(url).netloc
        current_time = time.time()
        time_since_last = current_time - self.last_request_time[domain]
        
        delay_needed = self.domain_delays[domain] - time_since_last
        if delay_needed > 0:
            time.sleep(delay_needed)
        
        self.last_request_time[domain] = time.time()
    
    def set_domain_delay(self, domain: str, delay: float) -> None:
        """Set custom delay for specific domain."""
        self.domain_delays[domain] = delay


class RobotsTxtChecker:
    """Check robots.txt compliance for URLs."""
    
    def __init__(self, user_agent: str = '*') -> None:
        """Initialize robots.txt checker."""
        self.user_agent = user_agent
        self.robots_cache: Dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url not in self.robots_cache:
                robots_url = urljoin(base_url, '/robots.txt')
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_cache[base_url] = rp
                except Exception:
                    # If robots.txt can't be read, allow crawling
                    self.robots_cache[base_url] = None
            
            robots_parser = self.robots_cache[base_url]
            if robots_parser is None:
                return True
            
            # Fix for Python robotparser bug: when there are no Disallow rules
            # for a user-agent, it should default to allowing all URLs
            try:
                result = robots_parser.can_fetch(self.user_agent, url)
                
                # Check if this is the robotparser bug where no rules exist
                # but it returns False anyway
                if not result:
                    # Check if there are any disallow rules for this user agent
                    has_disallow_rules = False
                    if robots_parser.default_entry:
                        for rule in robots_parser.default_entry.rulelines:
                            if not rule.allowance:  # Disallow rule
                                has_disallow_rules = True
                                break
                    
                    # If no disallow rules exist, allow access
                    if not has_disallow_rules:
                        return True
                
                return result
            except Exception:
                # If there's any error with robots parsing, be permissive
                return True
                
        except Exception:
            return True  # Allow if robots.txt can't be checked


class URLDeduplicator:
    """Memory-efficient URL deduplication using hashes."""
    
    def __init__(self, max_memory_hashes: int = 100000) -> None:
        """Initialize URL deduplicator."""
        self.url_hashes: Set[str] = set()
        self.max_memory_hashes = max_memory_hashes
        
    def is_duplicate(self, url: str) -> bool:
        """Check if URL has been seen before using memory-efficient hashing."""
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        if url_hash in self.url_hashes:
            return True
            
        # Prevent unlimited memory growth
        if len(self.url_hashes) >= self.max_memory_hashes:
            # Remove oldest 20% of hashes (simple cleanup)
            hashes_list = list(self.url_hashes)
            self.url_hashes = set(hashes_list[len(hashes_list)//5:])
        
        self.url_hashes.add(url_hash)
        return False


class WebCrawler:
    """Recursive web crawler with respectful crawling policies."""
    
    def __init__(
        self, 
        max_depth: int = 3, 
        delay: float = 1.0, 
        max_urls: int = 1000,
        progress_callback: Optional[callable] = None
    ) -> None:
        """Initialize web crawler with configuration."""
        self.max_depth = max_depth
        self.delay = delay
        self.max_urls = max_urls
        self.progress_callback = progress_callback
        
        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque()
        self.rate_limiter = RateLimiter(delay)
        self.extractor = URLExtractor()
        self.robots_checker = RobotsTxtChecker()
        self.deduplicator = URLDeduplicator()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def crawl_website(self, start_url: str, filter_base: Optional[str] = None) -> CrawlResult:
        """Main crawling method with progress reporting."""
        try:
            # Configure extractor with filter
            if filter_base:
                self.extractor.url_filter_base = filter_base
            
            self.url_queue.append((start_url, 0))  # (url, depth)
            all_urls = []
            errors = []
            
            while self.url_queue and len(all_urls) < self.max_urls:
                current_url, depth = self.url_queue.popleft()
                
                if (current_url in self.visited_urls or 
                    depth > self.max_depth or
                    self.deduplicator.is_duplicate(current_url)):
                    continue
                
                # Progress callback for UI updates
                if self.progress_callback:
                    self.progress_callback(f"Crawling: {self._shorten_url(current_url)}", len(all_urls))
                
                # Respectful crawling checks
                if not self.robots_checker.can_fetch(current_url):
                    self.logger.info(f"Robots.txt disallows crawling: {current_url}")
                    continue
                    
                self.rate_limiter.wait_if_needed(current_url)
                
                # Extract URLs from current page
                try:
                    urls = self.extractor.extract_urls_from_page(current_url)
                    all_urls.extend(list(urls))
                    self.visited_urls.add(current_url)
                    
                    # Add new URLs to queue for next depth level
                    if depth < self.max_depth:
                        for url in list(urls)[:50]:  # Limit to prevent explosion
                            if url not in self.visited_urls:
                                self.url_queue.append((url, depth + 1))
                                
                except Exception as e:
                    error_msg = f"Error crawling {current_url}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            return CrawlResult(
                success=True,
                urls=all_urls,
                count=len(all_urls),
                message=f'Successfully crawled {len(all_urls)} URLs',
                errors=errors
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                urls=[],
                count=0,
                message=f'Crawling failed: {str(e)}',
                errors=[str(e)]
            )
    
    def _shorten_url(self, url: str, max_length: int = 50) -> str:
        """Shorten URL for display purposes."""
        if len(url) <= max_length:
            return url
        return url[:max_length-3] + "..."


class CrawlerService:
    """Service class to integrate web crawler with terminal app."""
    
    def __init__(self, progress_callback: Optional[callable] = None) -> None:
        """Initialize crawler service."""
        self.progress_callback = progress_callback
        
    def crawl_url(
        self, 
        url: str, 
        max_depth: int = 3, 
        delay: float = 1.0, 
        filter_base: Optional[str] = None
    ) -> CrawlResult:
        """Main crawling service method."""
        try:
            crawler = WebCrawler(
                max_depth=max_depth,
                delay=delay,
                progress_callback=self.progress_callback
            )
            
            return crawler.crawl_website(url, filter_base)
            
        except Exception as e:
            return CrawlResult(
                success=False,
                urls=[],
                count=0,
                message=f'Crawling service failed: {str(e)}',
                errors=[str(e)]
            )