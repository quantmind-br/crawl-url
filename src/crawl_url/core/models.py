"""Core data models for crawl-url application."""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class CrawlConfig:
    """Configuration for crawling operations."""
    
    url: str
    mode: str = "auto"  # 'auto', 'sitemap', or 'crawl'
    max_depth: int = 3
    delay: float = 1.0
    filter_base: Optional[str] = None
    output_path: Optional[Path] = None
    output_format: str = "txt"
    verbose: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.mode not in ("auto", "sitemap", "crawl"):
            raise ValueError(
                f"Invalid crawling mode '{self.mode}'. Please choose from:\n"
                f"  • 'auto' - Automatically detect sitemap.xml URLs vs website URLs\n"
                f"  • 'sitemap' - Extract URLs from sitemap.xml files only\n"
                f"  • 'crawl' - Recursively crawl website pages"
            )
        
        if self.max_depth < 1 or self.max_depth > 10:
            raise ValueError(
                f"Invalid crawl depth '{self.max_depth}'. Depth must be between 1 and 10.\n"
                f"  • Use depth 1-2 for quick surface-level crawling\n"
                f"  • Use depth 3-5 for thorough crawling (recommended)\n"
                f"  • Use depth 6-10 for deep crawling (may be slow)"
            )
        
        if self.delay < 0:
            raise ValueError(
                f"Invalid delay '{self.delay}'. Delay must be non-negative (0 or greater).\n"
                f"  • Recommended: 1.0 seconds for respectful crawling\n"
                f"  • Minimum: 0.5 seconds to avoid overwhelming servers\n"
                f"  • Use higher values (2-5 seconds) for conservative crawling"
            )
        
        if self.output_format not in ("txt", "json", "csv"):
            raise ValueError(
                f"Invalid output format '{self.output_format}'. Please choose from:\n"
                f"  • 'txt' - Simple text file with one URL per line\n"
                f"  • 'json' - Structured JSON with metadata and URLs array\n"
                f"  • 'csv' - Comma-separated values with URL, domain, and path columns"
            )


@dataclass
class CrawlResult:
    """Result of a crawling operation."""
    
    success: bool
    urls: List[str]
    count: int
    message: str
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Ensure count matches URL list length."""
        if self.count != len(self.urls):
            self.count = len(self.urls)


@dataclass
class SitemapEntry:
    """Sitemap URL entry with optional metadata."""
    
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate sitemap entry data."""
        if not self.loc:
            raise ValueError(
                "Sitemap entry is missing required location URL. "
                "Each sitemap entry must have a valid <loc> element with a URL."
            )
        
        # Validate changefreq if provided
        valid_changefreq = {
            "always", "hourly", "daily", "weekly", 
            "monthly", "yearly", "never"
        }
        if self.changefreq and self.changefreq not in valid_changefreq:
            valid_options = "', '".join(sorted(valid_changefreq))
            raise ValueError(
                f"Invalid changefreq value '{self.changefreq}' in sitemap entry.\n"
                f"Valid changefreq values are: '{valid_options}'"
            )
        
        # Validate priority if provided
        if self.priority:
            try:
                priority_val = float(self.priority)
                if not (0.0 <= priority_val <= 1.0):
                    raise ValueError(
                        f"Invalid priority value '{self.priority}' in sitemap entry.\n"
                        f"Priority must be a decimal number between 0.0 and 1.0 (e.g., '0.5', '0.8', '1.0')"
                    )
            except ValueError as e:
                if "Priority must be" in str(e):
                    raise
                raise ValueError(
                    f"Invalid priority format '{self.priority}' in sitemap entry.\n"
                    f"Priority must be a valid decimal number between 0.0 and 1.0 (e.g., '0.5', '0.8', '1.0')"
                )