# Sitemap Parsing Implementation Guide for Crawl-URL

## Overview
This guide provides production-ready patterns for parsing sitemap.xml files efficiently using lxml, including support for compressed sitemaps, sitemap indexes, and various edge cases.

## Core Libraries and Setup
```python
import lxml.etree as etree
import gzip
import requests
from urllib.parse import urljoin, urlparse
from collections import namedtuple
from io import BytesIO
import logging
from pathlib import Path
```

## Essential Data Structure
```python
from collections import namedtuple
from datetime import datetime
from typing import List, Optional, Union

SitemapEntry = namedtuple('SitemapEntry', [
    'loc',          # URL location (required)
    'lastmod',      # Last modification date (optional)
    'changefreq',   # Change frequency (optional)
    'priority'      # Priority 0.0-1.0 (optional)
])

class SitemapIndex:
    def __init__(self):
        self.sitemaps = []  # List of sitemap URLs
        
class SitemapParser:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'crawl-url/1.0 (Sitemap Parser)'
        })
```

## Memory-Efficient XML Parsing Pattern
```python
def parse_sitemap_efficiently(self, file_source, is_compressed=False):
    """
    Memory-efficient sitemap parsing using iterparse
    file_source can be: file path, URL, or file-like object
    """
    try:
        # Handle different source types
        if isinstance(file_source, str):
            if file_source.startswith(('http://', 'https://')):
                file_obj = self._fetch_sitemap_content(file_source)
            else:
                file_obj = self._open_local_file(file_source, is_compressed)
        else:
            file_obj = file_source
        
        entries = []
        context = etree.iterparse(file_obj, events=('start', 'end'))
        
        # Skip root element
        context = iter(context)
        event, root = next(context)
        
        current_url = {}
        
        for event, element in context:
            if event == 'end':
                tag_name = element.tag.split('}')[-1]  # Remove namespace
                
                if tag_name == 'url':
                    # Create entry from collected data
                    entry = SitemapEntry(
                        loc=current_url.get('loc'),
                        lastmod=current_url.get('lastmod'),
                        changefreq=current_url.get('changefreq'),
                        priority=current_url.get('priority')
                    )
                    if entry.loc:  # Only add if URL exists
                        entries.append(entry)
                    current_url = {}
                    
                elif tag_name in ('loc', 'lastmod', 'changefreq', 'priority'):
                    current_url[tag_name] = element.text
                
                # Memory cleanup - critical for large files
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]
        
        file_obj.close()
        return entries
        
    except etree.XMLSyntaxError as e:
        logging.error(f"XML syntax error in sitemap: {e}")
        return []
    except Exception as e:
        logging.error(f"Error parsing sitemap: {e}")
        return []

def _fetch_sitemap_content(self, url):
    """Fetch sitemap content from URL with compression handling"""
    response = self.session.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    # Handle compressed content
    if (url.endswith('.gz') or 
        response.headers.get('content-encoding') == 'gzip'):
        content = gzip.decompress(response.content)
        return BytesIO(content)
    else:
        return BytesIO(response.content)

def _open_local_file(self, file_path, is_compressed):
    """Open local file with optional compression handling"""
    if is_compressed or file_path.endswith('.gz'):
        return gzip.open(file_path, 'rb')
    else:
        return open(file_path, 'rb')
```

## Sitemap Index Parsing Pattern
```python
def parse_sitemap_index(self, index_source):
    """Parse sitemap index and return list of sitemap URLs"""
    try:
        if isinstance(index_source, str) and index_source.startswith(('http://', 'https://')):
            file_obj = self._fetch_sitemap_content(index_source)
        else:
            file_obj = self._open_local_file(index_source, False)
        
        sitemaps = []
        context = etree.iterparse(file_obj, events=('start', 'end'))
        current_sitemap = {}
        
        for event, element in context:
            if event == 'end':
                tag_name = element.tag.split('}')[-1]
                
                if tag_name == 'sitemap':
                    if current_sitemap.get('loc'):
                        sitemaps.append(current_sitemap.copy())
                    current_sitemap = {}
                elif tag_name in ('loc', 'lastmod'):
                    current_sitemap[tag_name] = element.text
                
                # Memory cleanup
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]
        
        file_obj.close()
        return sitemaps
        
    except Exception as e:
        logging.error(f"Error parsing sitemap index: {e}")
        return []
```

## Sitemap Discovery Pattern
```python
def discover_sitemaps(self, base_url):
    """Discover sitemap URLs from robots.txt and common locations"""
    discovered_sitemaps = []
    
    # 1. Check robots.txt
    robots_sitemaps = self._get_sitemaps_from_robots(base_url)
    discovered_sitemaps.extend(robots_sitemaps)
    
    # 2. Check common locations if nothing found in robots.txt
    if not discovered_sitemaps:
        common_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps/sitemap.xml',
            '/xml-sitemaps/sitemap.xml'
        ]
        
        for location in common_locations:
            sitemap_url = urljoin(base_url, location)
            if self._check_sitemap_exists(sitemap_url):
                discovered_sitemaps.append(sitemap_url)
                break  # Stop at first found
    
    return discovered_sitemaps

def _get_sitemaps_from_robots(self, base_url):
    """Extract sitemap URLs from robots.txt"""
    robots_url = urljoin(base_url, '/robots.txt')
    sitemaps = []
    
    try:
        response = self.session.get(robots_url, timeout=10)
        if response.status_code == 200:
            for line in response.text.split('\n'):
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemaps.append(sitemap_url)
    except Exception as e:
        logging.warning(f"Could not fetch robots.txt from {robots_url}: {e}")
    
    return sitemaps

def _check_sitemap_exists(self, sitemap_url):
    """Check if sitemap exists at URL"""
    try:
        response = self.session.head(sitemap_url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False
```

## Complete Sitemap Processing Service
```python
class SitemapService:
    """Complete sitemap processing service for crawl-url application"""
    
    def __init__(self, progress_callback=None):
        self.parser = SitemapParser()
        self.progress_callback = progress_callback
        
    def process_sitemap_url(self, sitemap_url, filter_base=None):
        """
        Process sitemap URL and return all URLs
        Handles both regular sitemaps and sitemap indexes
        """
        try:
            # First, try to determine if it's an index or regular sitemap
            if self._is_sitemap_index(sitemap_url):
                return self._process_sitemap_index(sitemap_url, filter_base)
            else:
                return self._process_single_sitemap(sitemap_url, filter_base)
                
        except Exception as e:
            return {
                'success': False,
                'urls': [],
                'count': 0,
                'message': f'Error processing sitemap: {str(e)}'
            }
    
    def process_base_url(self, base_url, filter_base=None):
        """
        Discover and process sitemaps from base URL
        """
        try:
            if self.progress_callback:
                self.progress_callback("Discovering sitemaps...", 0)
            
            discovered_sitemaps = self.parser.discover_sitemaps(base_url)
            
            if not discovered_sitemaps:
                return {
                    'success': False,
                    'urls': [],
                    'count': 0,
                    'message': 'No sitemaps found for this domain'
                }
            
            all_urls = []
            for i, sitemap_url in enumerate(discovered_sitemaps):
                if self.progress_callback:
                    self.progress_callback(f"Processing sitemap {i+1}/{len(discovered_sitemaps)}", 
                                         len(all_urls))
                
                result = self.process_sitemap_url(sitemap_url, filter_base)
                if result['success']:
                    all_urls.extend(result['urls'])
            
            return {
                'success': True,
                'urls': all_urls,
                'count': len(all_urls),
                'message': f'Successfully extracted {len(all_urls)} URLs from {len(discovered_sitemaps)} sitemaps'
            }
            
        except Exception as e:
            return {
                'success': False,
                'urls': [],
                'count': 0,
                'message': f'Error processing base URL: {str(e)}'
            }
    
    def _is_sitemap_index(self, sitemap_url):
        """Quickly check if sitemap is an index by sampling content"""
        try:
            # Fetch first few KB to check
            response = self.session.get(sitemap_url, headers={'Range': 'bytes=0-2048'}, timeout=10)
            content = response.content.decode('utf-8', errors='ignore')
            return '<sitemapindex' in content.lower()
        except Exception:
            return False
    
    def _process_sitemap_index(self, index_url, filter_base):
        """Process sitemap index and all contained sitemaps"""
        sitemaps = self.parser.parse_sitemap_index(index_url)
        all_urls = []
        
        for i, sitemap_info in enumerate(sitemaps):
            if self.progress_callback:
                self.progress_callback(f"Processing sitemap {i+1}/{len(sitemaps)}", 
                                     len(all_urls))
            
            sitemap_url = sitemap_info['loc']
            entries = self.parser.parse_sitemap_efficiently(sitemap_url)
            urls = self._extract_and_filter_urls(entries, filter_base)
            all_urls.extend(urls)
        
        return {
            'success': True,
            'urls': all_urls,
            'count': len(all_urls),
            'message': f'Processed {len(sitemaps)} sitemaps from index'
        }
    
    def _process_single_sitemap(self, sitemap_url, filter_base):
        """Process a single sitemap file"""
        entries = self.parser.parse_sitemap_efficiently(sitemap_url)
        urls = self._extract_and_filter_urls(entries, filter_base)
        
        return {
            'success': True,
            'urls': urls,
            'count': len(urls),
            'message': f'Extracted {len(urls)} URLs from sitemap'
        }
    
    def _extract_and_filter_urls(self, entries, filter_base):
        """Extract URLs from entries and apply filtering"""
        urls = []
        for entry in entries:
            if entry.loc:
                if filter_base:
                    if entry.loc.startswith(filter_base):
                        urls.append(entry.loc)
                else:
                    urls.append(entry.loc)
        return urls
```

## Alternative Text Sitemap Support
```python
def parse_text_sitemap(self, sitemap_url):
    """Parse text-based sitemap (one URL per line)"""
    try:
        response = self.session.get(sitemap_url, timeout=30)
        response.raise_for_status()
        
        urls = []
        for line in response.text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip comments
                # Basic URL validation
                if line.startswith(('http://', 'https://')):
                    urls.append(line)
        
        return urls
        
    except Exception as e:
        logging.error(f"Error parsing text sitemap: {e}")
        return []
```

## Error Handling and Validation
```python
def validate_sitemap_urls(self, urls):
    """Validate and clean up extracted URLs"""
    clean_urls = []
    for url in urls:
        try:
            parsed = urlparse(url)
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                clean_urls.append(url)
        except Exception:
            continue  # Skip invalid URLs
    
    return clean_urls

def handle_malformed_xml(self, sitemap_url):
    """Fallback handler for malformed XML using BeautifulSoup"""
    try:
        from bs4 import BeautifulSoup
        import requests
        
        response = requests.get(sitemap_url, timeout=30)
        soup = BeautifulSoup(response.content, 'xml')
        
        urls = []
        for loc in soup.find_all('loc'):
            if loc.text:
                urls.append(loc.text.strip())
        
        return urls
        
    except Exception as e:
        logging.error(f"Fallback parsing also failed: {e}")
        return []
```

## Performance Optimization for Large Sitemaps
```python
def parse_large_sitemap_streaming(self, sitemap_url, batch_size=1000):
    """Stream processing for very large sitemaps"""
    try:
        file_obj = self._fetch_sitemap_content(sitemap_url)
        context = etree.iterparse(file_obj, events=('start', 'end'))
        
        batch = []
        current_url = {}
        
        for event, element in context:
            if event == 'end':
                tag_name = element.tag.split('}')[-1]
                
                if tag_name == 'url':
                    if current_url.get('loc'):
                        batch.append(current_url['loc'])
                    current_url = {}
                    
                    # Yield batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        
                elif tag_name == 'loc':
                    current_url['loc'] = element.text
                
                # Critical memory cleanup
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]
        
        # Yield remaining URLs
        if batch:
            yield batch
            
        file_obj.close()
        
    except Exception as e:
        logging.error(f"Error in streaming parse: {e}")
        yield []
```

## Integration Pattern for Terminal App
```python
class SitemapCrawlerService:
    """Main service class for sitemap-based crawling in terminal app"""
    
    def __init__(self, progress_callback=None):
        self.sitemap_service = SitemapService(progress_callback)
        self.progress_callback = progress_callback
    
    def crawl_sitemap(self, sitemap_input, filter_base=None):
        """
        Main method for sitemap crawling
        sitemap_input can be: sitemap URL or base domain URL
        """
        try:
            # Determine input type
            if sitemap_input.endswith(('.xml', '.xml.gz')):
                # Direct sitemap URL
                return self.sitemap_service.process_sitemap_url(sitemap_input, filter_base)
            else:
                # Base URL - discover sitemaps
                return self.sitemap_service.process_base_url(sitemap_input, filter_base)
                
        except Exception as e:
            return {
                'success': False,
                'urls': [],
                'count': 0,
                'message': f'Sitemap crawling failed: {str(e)}'
            }
```

## Critical Performance and Compatibility Notes

1. **Memory Management**: Always use `iterparse()` and clear elements to handle large sitemaps (50MB+)
2. **Compression**: Automatically handle .gz compressed sitemaps
3. **Error Handling**: Implement fallback parsing with BeautifulSoup for malformed XML
4. **Timeout Handling**: Use reasonable timeouts (30s) for large sitemap downloads
5. **Respectful Processing**: Include User-Agent headers and reasonable delays
6. **XML Namespaces**: Strip namespaces when processing tag names
7. **Validation**: Always validate extracted URLs before adding to results

## Testing Pattern
```python
def test_sitemap_parsing():
    """Test sitemap parsing with sample XML"""
    sample_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2023-01-01</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.8</priority>
        </url>
    </urlset>"""
    
    # Test with BytesIO
    from io import BytesIO
    parser = SitemapParser()
    entries = parser.parse_sitemap_efficiently(BytesIO(sample_sitemap.encode()))
    
    assert len(entries) == 1
    assert entries[0].loc == "https://example.com/page1"
```

This comprehensive guide provides all the patterns needed to implement robust sitemap parsing functionality for the crawl-url application.