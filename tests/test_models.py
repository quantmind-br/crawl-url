"""Tests for core data models."""

import pytest
from pathlib import Path

from crawl_url.core.models import CrawlConfig, CrawlResult, SitemapEntry


class TestCrawlConfig:
    """Test CrawlConfig dataclass."""
    
    def test_valid_config_creation(self):
        """Test creating valid crawl configuration."""
        config = CrawlConfig(
            url="https://example.com",
            mode="crawl",
            max_depth=3,
            delay=1.5,
            filter_base="https://example.com/docs/",
            output_path=Path("output.txt"),
            output_format="json"
        )
        
        assert config.url == "https://example.com"
        assert config.mode == "crawl"
        assert config.max_depth == 3
        assert config.delay == 1.5
        assert config.filter_base == "https://example.com/docs/"
        assert config.output_path == Path("output.txt")
        assert config.output_format == "json"
    
    def test_default_values(self):
        """Test default values are applied correctly."""
        config = CrawlConfig(url="https://example.com")
        
        assert config.mode == "auto"
        assert config.max_depth == 3
        assert config.delay == 1.0
        assert config.filter_base is None
        assert config.output_path is None
        assert config.output_format == "txt"
        assert config.verbose is False
    
    def test_invalid_mode_raises_error(self):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            CrawlConfig(url="https://example.com", mode="invalid")
    
    def test_invalid_depth_raises_error(self):
        """Test invalid depth raises ValueError."""
        with pytest.raises(ValueError, match="max_depth must be between 1 and 10"):
            CrawlConfig(url="https://example.com", max_depth=0)
        
        with pytest.raises(ValueError, match="max_depth must be between 1 and 10"):
            CrawlConfig(url="https://example.com", max_depth=15)
    
    def test_negative_delay_raises_error(self):
        """Test negative delay raises ValueError."""
        with pytest.raises(ValueError, match="delay must be non-negative"):
            CrawlConfig(url="https://example.com", delay=-1.0)
    
    def test_invalid_output_format_raises_error(self):
        """Test invalid output format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid output_format"):
            CrawlConfig(url="https://example.com", output_format="xml")


class TestCrawlResult:
    """Test CrawlResult dataclass."""
    
    def test_successful_result_creation(self):
        """Test creating successful crawl result."""
        urls = ["https://example.com/page1", "https://example.com/page2"]
        result = CrawlResult(
            success=True,
            urls=urls,
            count=2,
            message="Successfully crawled 2 URLs"
        )
        
        assert result.success is True
        assert result.urls == urls
        assert result.count == 2
        assert result.message == "Successfully crawled 2 URLs"
        assert result.errors == []
    
    def test_failed_result_creation(self):
        """Test creating failed crawl result."""
        errors = ["Connection timeout", "Invalid URL"]
        result = CrawlResult(
            success=False,
            urls=[],
            count=0,
            message="Crawl failed",
            errors=errors
        )
        
        assert result.success is False
        assert result.urls == []
        assert result.count == 0
        assert result.message == "Crawl failed"
        assert result.errors == errors
    
    def test_count_auto_correction(self):
        """Test count is automatically corrected to match URL list length."""
        urls = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
        result = CrawlResult(
            success=True,
            urls=urls,
            count=10,  # Incorrect count
            message="Test"
        )
        
        # Count should be corrected to match actual URL list length
        assert result.count == 3


class TestSitemapEntry:
    """Test SitemapEntry dataclass."""
    
    def test_valid_entry_creation(self):
        """Test creating valid sitemap entry."""
        entry = SitemapEntry(
            loc="https://example.com/page1",
            lastmod="2023-01-15",
            changefreq="weekly",
            priority="0.8"
        )
        
        assert entry.loc == "https://example.com/page1"
        assert entry.lastmod == "2023-01-15"
        assert entry.changefreq == "weekly"
        assert entry.priority == "0.8"
    
    def test_minimal_entry_creation(self):
        """Test creating entry with only required fields."""
        entry = SitemapEntry(loc="https://example.com/page1")
        
        assert entry.loc == "https://example.com/page1"
        assert entry.lastmod is None
        assert entry.changefreq is None
        assert entry.priority is None
    
    def test_empty_location_raises_error(self):
        """Test empty location raises ValueError."""
        with pytest.raises(ValueError, match="Sitemap entry must have a location URL"):
            SitemapEntry(loc="")
    
    def test_none_location_raises_error(self):
        """Test None location raises ValueError."""
        with pytest.raises(ValueError, match="Sitemap entry must have a location URL"):
            SitemapEntry(loc=None)
    
    def test_invalid_changefreq_raises_error(self):
        """Test invalid changefreq raises ValueError."""
        with pytest.raises(ValueError, match="Invalid changefreq"):
            SitemapEntry(
                loc="https://example.com/page1",
                changefreq="invalid"
            )
    
    def test_valid_changefreq_values(self):
        """Test all valid changefreq values are accepted."""
        valid_values = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
        
        for value in valid_values:
            entry = SitemapEntry(
                loc="https://example.com/page1",
                changefreq=value
            )
            assert entry.changefreq == value
    
    def test_invalid_priority_range_raises_error(self):
        """Test priority outside 0.0-1.0 range raises ValueError."""
        with pytest.raises(ValueError, match="Priority must be between 0.0 and 1.0"):
            SitemapEntry(
                loc="https://example.com/page1",
                priority="1.5"
            )
        
        with pytest.raises(ValueError, match="Priority must be between 0.0 and 1.0"):
            SitemapEntry(
                loc="https://example.com/page1",
                priority="-0.1"
            )
    
    def test_invalid_priority_format_raises_error(self):
        """Test invalid priority format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid priority format"):
            SitemapEntry(
                loc="https://example.com/page1",
                priority="not_a_number"
            )
    
    def test_valid_priority_values(self):
        """Test valid priority values are accepted."""
        valid_values = ["0.0", "0.5", "1.0", "0.123"]
        
        for value in valid_values:
            entry = SitemapEntry(
                loc="https://example.com/page1",
                priority=value
            )
            assert entry.priority == value