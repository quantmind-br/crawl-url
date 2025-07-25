"""
Crawl-URL: A powerful terminal application for URL crawling.
"""

__version__ = "1.0.0"
__author__ = "Crawl-URL Team"
__email__ = "crawl-url@example.com"
__description__ = "A powerful terminal application for crawling and extracting URLs from websites"

# Make key classes available at package level
from .core.crawler import CrawlerService
from .core.sitemap_parser import SitemapService
from .core.ui import CrawlerApp
from .utils.storage import StorageManager

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "CrawlerService",
    "SitemapService", 
    "CrawlerApp",
    "StorageManager",
]