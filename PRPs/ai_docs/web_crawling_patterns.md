# Web Crawling Implementation Patterns for Crawl-URL

## Overview
This guide provides production-ready patterns for implementing web crawling with requests + BeautifulSoup, focusing on URL extraction, respectful crawling, and robust error handling.

## Core Libraries and Setup
```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
from collections import defaultdict, deque
import hashlib
import logging
from pathlib import Path
```

## Essential URL Extraction Pattern
```python
class URLExtractor:
    def __init__(self, allowed_domains=None, url_filter_base=None):
        self.allowed_domains = set(allowed_domains or [])
        self.url_filter_base = url_filter_base
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'crawl-url/1.0 (Compatible Web Crawler)'
        })
    
    def extract_urls_from_page(self, url, timeout=10):
        """Extract all URLs from a single page"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            if not self.is_html_content(response):
                return set()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = set()
            
            # Extract from anchor tags
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if self.is_valid_url(absolute_url):
                    urls.add(self.normalize_url(absolute_url))
            
            return urls
            
        except requests.RequestException as e:
            logging.warning(f"Error fetching {url}: {e}")
            return set()
    
    def is_html_content(self, response):
        """Check if response contains HTML content"""
        content_type = response.headers.get('content-type', '').lower()
        return 'text/html' in content_type
    
    def is_valid_url(self, url):
        """Validate and filter URLs"""
        try:
            parsed = urlparse(url)
            
            # Basic validation
            if not (parsed.scheme and parsed.netloc):
                return False
            
            # Domain filtering
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                return False
            
            # Base URL filtering (for crawl-url's filter feature)
            if self.url_filter_base:
                if not url.startswith(self.url_filter_base):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def normalize_url(self, url):
        """Normalize URL by removing fragments and query params if needed"""
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
```

## Recursive Crawling Pattern
```python
class WebCrawler:
    def __init__(self, max_depth=3, delay=1.0, max_urls=1000):
        self.max_depth = max_depth
        self.delay = delay
        self.max_urls = max_urls
        self.visited_urls = set()
        self.url_queue = deque()
        self.rate_limiter = RateLimiter(delay)
        self.extractor = URLExtractor()
        self.robots_checker = RobotsTxtChecker()
        
    def crawl_website(self, start_url, progress_callback=None):
        """Main crawling method with progress reporting"""
        self.url_queue.append((start_url, 0))  # (url, depth)
        all_urls = []
        
        while self.url_queue and len(all_urls) < self.max_urls:
            current_url, depth = self.url_queue.popleft()
            
            if (current_url in self.visited_urls or 
                depth > self.max_depth):
                continue
            
            # Progress callback for UI updates
            if progress_callback:
                progress_callback(f"Crawling: {current_url}", len(all_urls))
            
            # Respectful crawling checks
            if not self.robots_checker.can_fetch(current_url):
                continue
                
            self.rate_limiter.wait_if_needed(current_url)
            
            # Extract URLs from current page
            urls = self.extractor.extract_urls_from_page(current_url)
            all_urls.extend(urls)
            self.visited_urls.add(current_url)
            
            # Add new URLs to queue for next depth level
            if depth < self.max_depth:
                for url in list(urls)[:50]:  # Limit to prevent explosion
                    if url not in self.visited_urls:
                        self.url_queue.append((url, depth + 1))
        
        return all_urls
```

## Rate Limiting Implementation
```python
import time
from collections import defaultdict
from urllib.parse import urlparse

class RateLimiter:
    def __init__(self, default_delay=1.0):
        self.default_delay = default_delay
        self.domain_delays = defaultdict(lambda: default_delay)
        self.last_request_time = defaultdict(float)
    
    def wait_if_needed(self, url):
        """Implement respectful delay based on domain"""
        domain = urlparse(url).netloc
        current_time = time.time()
        time_since_last = current_time - self.last_request_time[domain]
        
        delay_needed = self.domain_delays[domain] - time_since_last
        if delay_needed > 0:
            time.sleep(delay_needed)
        
        self.last_request_time[domain] = time.time()
    
    def set_domain_delay(self, domain, delay):
        """Set custom delay for specific domain"""
        self.domain_delays[domain] = delay
```

## Robots.txt Compliance
```python
import urllib.robotparser
from urllib.parse import urljoin, urlparse

class RobotsTxtChecker:
    def __init__(self, user_agent='*'):
        self.user_agent = user_agent
        self.robots_cache = {}
    
    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
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
                
            return robots_parser.can_fetch(self.user_agent, url)
            
        except Exception:
            return True  # Allow if robots.txt can't be checked
```

## Memory-Efficient URL Storage
```python
class URLDeduplicator:
    def __init__(self, max_memory_hashes=100000):
        self.url_hashes = set()
        self.max_memory_hashes = max_memory_hashes
        
    def is_duplicate(self, url):
        """Check if URL has been seen before using memory-efficient hashing"""
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
```

## Robust Error Handling Pattern
```python
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError

class RobustCrawler:
    def __init__(self):
        self.setup_logging()
        self.session = requests.Session()
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crawl.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def safe_request(self, url, timeout=10):
        """Make request with comprehensive error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
            
        except Timeout:
            self.logger.warning(f"Timeout accessing {url}")
        except ConnectionError:
            self.logger.warning(f"Connection error for {url}")
        except RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error for {url}: {e}")
        
        return None
```

## URL Storage and Export Patterns
```python
class URLStorage:
    def __init__(self, output_file):
        self.output_file = Path(output_file)
        self.urls = []
    
    def add_urls(self, urls):
        """Add URLs to storage"""
        self.urls.extend(urls)
    
    def save_to_file(self, format='txt'):
        """Save URLs to file in specified format"""
        if format == 'txt':
            self.output_file.write_text('\n'.join(self.urls), encoding='utf-8')
        elif format == 'json':
            import json
            data = {
                'crawl_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_urls': len(self.urls),
                'urls': self.urls
            }
            self.output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        elif format == 'csv':
            import csv
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL'])
                for url in self.urls:
                    writer.writerow([url])
    
    def generate_filename(self, base_url):
        """Generate filename based on domain"""
        domain = urlparse(base_url).netloc
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        return f"{domain}_{timestamp}.txt"
```

## Integration Pattern for Terminal App
```python
class CrawlerService:
    """Service class to integrate with PyTermGUI terminal app"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.crawler = WebCrawler()
        self.storage = None
        
    def crawl_url(self, url, max_depth=3, delay=1.0, filter_base=None):
        """Main crawling service method"""
        try:
            # Configure crawler
            self.crawler.max_depth = max_depth
            self.crawler.delay = delay
            if filter_base:
                self.crawler.extractor.url_filter_base = filter_base
            
            # Start crawling
            urls = self.crawler.crawl_website(url, self.progress_callback)
            
            return {
                'success': True,
                'urls': urls,
                'count': len(urls),
                'message': f'Successfully crawled {len(urls)} URLs'
            }
            
        except Exception as e:
            return {
                'success': False,
                'urls': [],
                'count': 0,
                'message': f'Crawling failed: {str(e)}'
            }
    
    def save_results(self, urls, filename, format='txt'):
        """Save crawling results"""
        storage = URLStorage(filename)
        storage.add_urls(urls)
        storage.save_to_file(format)
```

## Critical Performance Considerations
1. **Rate Limiting**: Always implement delays between requests (minimum 1 second)
2. **Memory Management**: Use generators and limit stored URLs for large crawls
3. **Error Handling**: Implement robust retry logic and timeout handling
4. **Respectful Crawling**: Always check robots.txt and implement proper delays
5. **Progress Reporting**: Provide regular updates for terminal UI integration

## Testing Pattern
```python
def test_url_extraction():
    """Test URL extraction with mock HTML"""
    html_content = """
    <html>
        <body>
            <a href="https://example.com/page1">Page 1</a>
            <a href="/relative-page">Relative Page</a>
            <a href="#fragment">Fragment</a>
        </body>
    </html>
    """
    
    # Test extraction logic
    extractor = URLExtractor()
    # Mock the request to return test HTML
    # Test various URL types and edge cases
```

This guide provides all essential patterns for implementing robust web crawling functionality in the crawl-url application.