"""Sitemap parsing implementation for crawl-url application."""

import gzip
import logging
from io import BytesIO
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import lxml.etree as etree
import requests

from .models import CrawlResult, SitemapEntry


class SitemapParser:
    """Memory-efficient sitemap parser using lxml."""
    
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        """Initialize sitemap parser with optional session."""
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'crawl-url/1.0 (Sitemap Parser)'
        })
        
    def parse_sitemap_efficiently(
        self, 
        file_source: Union[str, BytesIO], 
        is_compressed: bool = False
    ) -> List[SitemapEntry]:
        """
        Memory-efficient sitemap parsing using iterparse.
        
        Args:
            file_source: File path, URL, or file-like object
            is_compressed: Whether the file is gzip compressed
            
        Returns:
            List of SitemapEntry objects
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
                        if current_url.get('loc'):
                            entry = SitemapEntry(
                                loc=current_url.get('loc', ''),
                                lastmod=current_url.get('lastmod'),
                                changefreq=current_url.get('changefreq'),
                                priority=current_url.get('priority')
                            )
                            entries.append(entry)
                        current_url = {}
                        
                    elif tag_name in ('loc', 'lastmod', 'changefreq', 'priority'):
                        if element.text:
                            current_url[tag_name] = element.text.strip()
                    
                    # Memory cleanup - critical for large files
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]
            
            if hasattr(file_obj, 'close'):
                file_obj.close()
            return entries
            
        except etree.XMLSyntaxError as e:
            logging.error(f"XML syntax error in sitemap: {e}")
            return []
        except Exception as e:
            logging.error(f"Error parsing sitemap: {e}")
            return []

    def parse_sitemap_index(self, index_source: Union[str, BytesIO]) -> List[Dict[str, str]]:
        """Parse sitemap index and return list of sitemap URLs."""
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
                        if element.text:
                            current_sitemap[tag_name] = element.text.strip()
                    
                    # Memory cleanup
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]
            
            if hasattr(file_obj, 'close'):
                file_obj.close()
            return sitemaps
            
        except Exception as e:
            logging.error(f"Error parsing sitemap index: {e}")
            return []

    def discover_sitemaps(self, base_url: str) -> List[str]:
        """Discover sitemap URLs from robots.txt and common locations."""
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

    def _fetch_sitemap_content(self, url: str) -> BytesIO:
        """Fetch sitemap content from URL with compression handling."""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        # The requests library automatically decompresses gzip content when
        # Content-Encoding: gzip is present, so we don't need to decompress again
        # Only manually decompress if the URL ends with .gz (indicating a gzipped file)
        if url.endswith('.gz'):
            try:
                # Try to decompress if it's actually gzipped
                content = gzip.decompress(response.content)
                return BytesIO(content)
            except gzip.BadGzipFile:
                # If decompression fails, use content as-is (already decompressed by requests)
                return BytesIO(response.content)
        else:
            # For regular XML files, use content directly
            return BytesIO(response.content)

    def _open_local_file(self, file_path: str, is_compressed: bool) -> Union[gzip.GzipFile, open]:
        """Open local file with optional compression handling."""
        if is_compressed or file_path.endswith('.gz'):
            return gzip.open(file_path, 'rb')
        else:
            return open(file_path, 'rb')

    def _get_sitemaps_from_robots(self, base_url: str) -> List[str]:
        """Extract sitemap URLs from robots.txt."""
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

    def _check_sitemap_exists(self, sitemap_url: str) -> bool:
        """Check if sitemap exists at URL."""
        try:
            response = self.session.head(sitemap_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False


class SitemapService:
    """Complete sitemap processing service for crawl-url application."""
    
    def __init__(self, progress_callback: Optional[callable] = None) -> None:
        """Initialize sitemap service with optional progress callback."""
        self.parser = SitemapParser()
        self.progress_callback = progress_callback
        
    def process_sitemap_url(self, sitemap_url: str, filter_base: Optional[str] = None) -> CrawlResult:
        """
        Process sitemap URL and return all URLs.
        Handles both regular sitemaps and sitemap indexes.
        """
        try:
            # First, try to determine if it's an index or regular sitemap
            if self._is_sitemap_index(sitemap_url):
                return self._process_sitemap_index(sitemap_url, filter_base)
            else:
                return self._process_single_sitemap(sitemap_url, filter_base)
                
        except Exception as e:
            return CrawlResult(
                success=False,
                urls=[],
                count=0,
                message=f'Error processing sitemap: {str(e)}',
                errors=[str(e)]
            )
    
    def process_base_url(self, base_url: str, filter_base: Optional[str] = None) -> CrawlResult:
        """Discover and process sitemaps from base URL."""
        try:
            if self.progress_callback:
                self.progress_callback("Discovering sitemaps...", 0)
            
            discovered_sitemaps = self.parser.discover_sitemaps(base_url)
            
            if not discovered_sitemaps:
                return CrawlResult(
                    success=False,
                    urls=[],
                    count=0,
                    message='No sitemaps found for this domain'
                )
            
            all_urls = []
            for i, sitemap_url in enumerate(discovered_sitemaps):
                if self.progress_callback:
                    self.progress_callback(
                        f"Processing sitemap {i+1}/{len(discovered_sitemaps)}", 
                        len(all_urls)
                    )
                
                result = self.process_sitemap_url(sitemap_url, filter_base)
                if result.success:
                    all_urls.extend(result.urls)
            
            return CrawlResult(
                success=True,
                urls=all_urls,
                count=len(all_urls),
                message=f'Successfully extracted {len(all_urls)} URLs from {len(discovered_sitemaps)} sitemaps'
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                urls=[],
                count=0,
                message=f'Error processing base URL: {str(e)}',
                errors=[str(e)]
            )
    
    def _is_sitemap_index(self, sitemap_url: str) -> bool:
        """Quickly check if sitemap is an index by sampling content."""
        try:
            # Fetch first few KB to check
            response = self.parser.session.get(
                sitemap_url, 
                headers={'Range': 'bytes=0-2048'}, 
                timeout=10
            )
            content = response.content.decode('utf-8', errors='ignore')
            return '<sitemapindex' in content.lower()
        except Exception:
            return False
    
    def _process_sitemap_index(self, index_url: str, filter_base: Optional[str]) -> CrawlResult:
        """Process sitemap index and all contained sitemaps."""
        sitemaps = self.parser.parse_sitemap_index(index_url)
        all_urls = []
        errors = []
        
        for i, sitemap_info in enumerate(sitemaps):
            if self.progress_callback:
                self.progress_callback(
                    f"Processing sitemap {i+1}/{len(sitemaps)}", 
                    len(all_urls)
                )
            
            try:
                sitemap_url = sitemap_info['loc']
                entries = self.parser.parse_sitemap_efficiently(sitemap_url)
                urls = self._extract_and_filter_urls(entries, filter_base)
                all_urls.extend(urls)
            except Exception as e:
                error_msg = f"Error processing sitemap {sitemap_info.get('loc', 'unknown')}: {e}"
                errors.append(error_msg)
                logging.error(error_msg)
        
        return CrawlResult(
            success=True,
            urls=all_urls,
            count=len(all_urls),
            message=f'Processed {len(sitemaps)} sitemaps from index',
            errors=errors
        )
    
    def _process_single_sitemap(self, sitemap_url: str, filter_base: Optional[str]) -> CrawlResult:
        """Process a single sitemap file."""
        try:
            entries = self.parser.parse_sitemap_efficiently(sitemap_url)
            urls = self._extract_and_filter_urls(entries, filter_base)
            
            return CrawlResult(
                success=True,
                urls=urls,
                count=len(urls),
                message=f'Extracted {len(urls)} URLs from sitemap'
            )
        except Exception as e:
            return CrawlResult(
                success=False,
                urls=[],
                count=0,
                message=f'Error processing sitemap: {str(e)}',
                errors=[str(e)]
            )
    
    def _extract_and_filter_urls(self, entries: List[SitemapEntry], filter_base: Optional[str]) -> List[str]:
        """Extract URLs from entries and apply filtering."""
        urls = []
        for entry in entries:
            if entry.loc:
                if filter_base:
                    if entry.loc.startswith(filter_base):
                        urls.append(entry.loc)
                else:
                    urls.append(entry.loc)
        return urls