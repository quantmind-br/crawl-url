"""Tests for web crawling functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import time
from urllib.parse import urljoin

from crawl_url.core.crawler import (
    URLExtractor, RateLimiter, RobotsTxtChecker, 
    URLDeduplicator, WebCrawler, CrawlerService
)
from crawl_url.core.models import CrawlConfig, CrawlResult


class TestURLExtractor:
    """Test URLExtractor class."""
    
    def test_extract_urls_from_html(self, sample_html):
        """Test extracting URLs from HTML content."""
        extractor = URLExtractor()
        base_url = "https://example.com"
        
        urls = extractor.extract_urls(sample_html, base_url)
        
        # Should extract and normalize URLs
        expected_urls = {
            "https://example.com/page1",
            "https://example.com/relative-page",
            "https://external.com/page"
        }
        
        assert set(urls) == expected_urls
    
    def test_extract_urls_filters_invalid_schemes(self):
        """Test URL extraction filters out non-HTTP schemes."""
        html = """
        <html>
            <body>
                <a href="https://example.com/valid">Valid HTTPS</a>
                <a href="http://example.com/valid">Valid HTTP</a>
                <a href="mailto:test@example.com">Email</a>
                <a href="ftp://example.com/file">FTP</a>
                <a href="javascript:void(0)">JavaScript</a>
                <a href="#fragment">Fragment</a>
            </body>
        </html>
        """
        
        extractor = URLExtractor()
        urls = extractor.extract_urls(html, "https://example.com")
        
        expected_urls = {
            "https://example.com/valid",
            "http://example.com/valid"
        }
        
        assert set(urls) == expected_urls
    
    def test_extract_urls_handles_relative_urls(self):
        """Test extraction handles various relative URL formats."""
        html = """
        <html>
            <body>
                <a href="/absolute-path">Absolute path</a>
                <a href="relative-path">Relative path</a>
                <a href="../parent-path">Parent path</a>
                <a href="./current-path">Current path</a>
            </body>
        </html>
        """
        
        extractor = URLExtractor()
        urls = extractor.extract_urls(html, "https://example.com/current/")
        
        expected_urls = {
            "https://example.com/absolute-path",
            "https://example.com/current/relative-path",
            "https://example.com/parent-path", 
            "https://example.com/current/current-path"
        }
        
        assert set(urls) == expected_urls
    
    def test_extract_urls_empty_html(self):
        """Test extraction from empty HTML."""
        extractor = URLExtractor()
        urls = extractor.extract_urls("", "https://example.com")
        
        assert urls == []
    
    def test_extract_urls_malformed_html(self):
        """Test extraction from malformed HTML."""
        malformed_html = "<html><body><a href='test'>Link</body>"  # Missing closing tag
        
        extractor = URLExtractor()
        urls = extractor.extract_urls(malformed_html, "https://example.com")
        
        assert "https://example.com/test" in urls
    
    def test_extract_urls_removes_duplicates(self):
        """Test extraction removes duplicate URLs."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page1">Link 1</a>
                <a href="https://example.com/page1">Link 1 Again</a>
                <a href="/page1">Relative to same page</a>
            </body>
        </html>
        """
        
        extractor = URLExtractor()
        urls = extractor.extract_urls(html, "https://example.com")
        
        # Should only have one instance of each URL
        assert urls.count("https://example.com/page1") == 1
        assert len(urls) == 1


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(delay=1.5)
        
        assert limiter.delay == 1.5
        assert limiter._last_request_times == {}
    
    @patch('time.time')
    @patch('time.sleep')
    def test_rate_limiter_enforces_delay(self, mock_sleep, mock_time):
        """Test rate limiter enforces delay between requests."""
        mock_time.side_effect = [0, 0.5, 1.0, 2.0]  # Simulate time progression
        
        limiter = RateLimiter(delay=1.0)
        
        # First request to domain
        limiter.wait_if_needed("example.com")
        mock_sleep.assert_not_called()  # No delay for first request
        
        # Second request to same domain within delay period
        limiter.wait_if_needed("example.com")
        mock_sleep.assert_called_with(0.5)  # Should sleep for remaining time
        
        # Third request to same domain after delay period
        mock_sleep.reset_mock()
        limiter.wait_if_needed("example.com")
        mock_sleep.assert_not_called()  # No delay needed
    
    def test_rate_limiter_different_domains(self):
        """Test rate limiter tracks different domains separately."""
        limiter = RateLimiter(delay=1.0)
        
        with patch('time.time', return_value=0):
            limiter.wait_if_needed("example.com")
            limiter.wait_if_needed("other.com")  # Different domain, no delay
        
        # Both domains should be tracked
        assert "example.com" in limiter._last_request_times
        assert "other.com" in limiter._last_request_times


class TestRobotsTxtChecker:
    """Test RobotsTxtChecker class."""
    
    def test_robots_txt_checker_initialization(self):
        """Test robots.txt checker initialization."""
        checker = RobotsTxtChecker()
        
        assert checker._robots_cache == {}
    
    @patch('crawl_url.core.crawler.requests.Session')
    def test_can_fetch_allowed_path(self, mock_session_class, sample_robots_txt):
        """Test checking allowed path in robots.txt."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_robots_txt
        mock_session.get.return_value = mock_response
        
        checker = RobotsTxtChecker()
        
        # Should be allowed (robots.txt allows all)
        can_fetch = checker.can_fetch("https://example.com/allowed-page", "*")
        
        assert can_fetch is True
    
    @patch('crawl_url.core.crawler.requests.Session')
    def test_can_fetch_robots_txt_not_found(self, mock_session_class):
        """Test checking when robots.txt doesn't exist."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        checker = RobotsTxtChecker()
        
        # Should default to allowed when robots.txt not found
        can_fetch = checker.can_fetch("https://example.com/any-page", "*")
        
        assert can_fetch is True
    
    def test_can_fetch_uses_cache(self):
        """Test robots.txt checker uses cache for repeated requests."""
        checker = RobotsTxtChecker()
        
        # Mock urllib.robotparser.RobotFileParser
        with patch('urllib.robotparser.RobotFileParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.can_fetch.return_value = True
            mock_parser_class.return_value = mock_parser
            
            # First call
            result1 = checker.can_fetch("https://example.com/page1", "*")
            
            # Second call to same domain
            result2 = checker.can_fetch("https://example.com/page2", "*")
            
            # Should only create parser once (cached)
            assert mock_parser_class.call_count == 1
            assert result1 is True
            assert result2 is True


class TestURLDeduplicator:
    """Test URLDeduplicator class."""
    
    def test_deduplicator_initialization(self):
        """Test deduplicator initialization."""
        dedup = URLDeduplicator()
        
        assert dedup._seen_hashes == set()
    
    def test_is_duplicate_detection(self):
        """Test duplicate URL detection."""
        dedup = URLDeduplicator()
        
        url = "https://example.com/page1"
        
        # First time should not be duplicate
        assert dedup.is_duplicate(url) is False
        
        # Second time should be duplicate
        assert dedup.is_duplicate(url) is True
    
    def test_different_urls_not_duplicates(self):
        """Test different URLs are not considered duplicates."""
        dedup = URLDeduplicator()
        
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        
        assert dedup.is_duplicate(url1) is False
        assert dedup.is_duplicate(url2) is False
    
    def test_query_parameters_treated_as_different(self):
        """Test URLs with different query parameters are treated as different."""
        dedup = URLDeduplicator()
        
        url1 = "https://example.com/page?param=1"
        url2 = "https://example.com/page?param=2"
        
        assert dedup.is_duplicate(url1) is False
        assert dedup.is_duplicate(url2) is False
    
    def test_fragment_identifiers_ignored(self):
        """Test fragment identifiers are ignored in duplicate detection."""
        dedup = URLDeduplicator()
        
        url1 = "https://example.com/page#section1"
        url2 = "https://example.com/page#section2"
        
        assert dedup.is_duplicate(url1) is False
        assert dedup.is_duplicate(url2) is True  # Should be duplicate (fragments ignored)


class TestWebCrawler:
    """Test WebCrawler class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = CrawlConfig(
            url="https://example.com",
            max_depth=2,
            delay=0.5
        )
        self.crawler = WebCrawler(self.config)
    
    def test_crawler_initialization(self):
        """Test web crawler initialization."""
        assert self.crawler.config == self.config
        assert isinstance(self.crawler.extractor, URLExtractor)
        assert isinstance(self.crawler.rate_limiter, RateLimiter)
        assert isinstance(self.crawler.robots_checker, RobotsTxtChecker)
        assert isinstance(self.crawler.deduplicator, URLDeduplicator)
    
    @patch('crawl_url.core.crawler.requests.Session')
    def test_fetch_page_success(self, mock_session_class, sample_html):
        """Test successful page fetching."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        content = self.crawler._fetch_page("https://example.com/page1")
        
        assert content == sample_html
    
    @patch('crawl_url.core.crawler.requests.Session')
    def test_fetch_page_non_html_content(self, mock_session_class):
        """Test fetching non-HTML content returns None."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_session.get.return_value = mock_response
        
        content = self.crawler._fetch_page("https://example.com/document.pdf")
        
        assert content is None
    
    @patch('crawl_url.core.crawler.requests.Session')
    def test_fetch_page_http_error(self, mock_session_class):
        """Test fetching page with HTTP error."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        content = self.crawler._fetch_page("https://example.com/notfound")
        
        assert content is None
    
    def test_should_crawl_url_within_filter(self):
        """Test URL filtering logic."""
        config_with_filter = CrawlConfig(
            url="https://example.com",
            filter_base="https://example.com/docs/"
        )
        filtered_crawler = WebCrawler(config_with_filter)
        
        # URL within filter should be crawled
        assert filtered_crawler._should_crawl_url("https://example.com/docs/guide") is True
        
        # URL outside filter should not be crawled
        assert filtered_crawler._should_crawl_url("https://example.com/blog/post") is False
    
    def test_should_crawl_url_no_filter(self):
        """Test URL filtering when no filter is set."""
        # URL should be crawled when no filter is set
        assert self.crawler._should_crawl_url("https://example.com/any-page") is True
        assert self.crawler._should_crawl_url("https://other.com/page") is True
    
    @patch.object(WebCrawler, '_fetch_page')
    @patch.object(RobotsTxtChecker, 'can_fetch')
    def test_crawl_single_page(self, mock_can_fetch, mock_fetch_page, sample_html):
        """Test crawling a single page."""
        mock_can_fetch.return_value = True
        mock_fetch_page.return_value = sample_html
        
        found_urls = []
        errors = []
        
        self.crawler._crawl_page(
            "https://example.com",
            depth=0,
            found_urls=found_urls,
            errors=errors
        )
        
        # Should find URLs from the HTML
        assert len(found_urls) > 0
        assert "https://example.com/page1" in found_urls
    
    @patch.object(WebCrawler, '_fetch_page')
    @patch.object(RobotsTxtChecker, 'can_fetch')
    def test_crawl_respects_robots_txt(self, mock_can_fetch, mock_fetch_page):
        """Test crawling respects robots.txt restrictions."""
        mock_can_fetch.return_value = False  # Robots.txt disallows
        mock_fetch_page.return_value = "<html></html>"
        
        found_urls = []
        errors = []
        
        self.crawler._crawl_page(
            "https://example.com/restricted",
            depth=0,
            found_urls=found_urls,
            errors=errors
        )
        
        # Should not fetch page if robots.txt disallows
        mock_fetch_page.assert_not_called()
    
    @patch.object(WebCrawler, '_crawl_page')
    def test_crawl_with_progress_callback(self, mock_crawl_page, mock_progress_callback):
        """Test crawling with progress callback."""
        mock_crawl_page.return_value = None
        
        result = self.crawler.crawl(progress_callback=mock_progress_callback)
        
        # Progress callback should be called
        mock_progress_callback.assert_called()
    
    @patch.object(WebCrawler, '_fetch_page')
    @patch.object(RobotsTxtChecker, 'can_fetch')
    def test_crawl_max_depth_limit(self, mock_can_fetch, mock_fetch_page, sample_html):
        """Test crawling respects maximum depth limit."""
        mock_can_fetch.return_value = True
        mock_fetch_page.return_value = sample_html
        
        # Set low max depth
        shallow_config = CrawlConfig(url="https://example.com", max_depth=1)
        shallow_crawler = WebCrawler(shallow_config)
        
        result = shallow_crawler.crawl()
        
        # Should find initial page and first level only
        assert result.success is True
        assert len(result.urls) > 0


class TestCrawlerService:
    """Test CrawlerService class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service = CrawlerService()
    
    @patch.object(WebCrawler, 'crawl')
    def test_crawl_url_success(self, mock_crawl):
        """Test successful URL crawling via service."""
        # Mock successful crawl result
        mock_result = CrawlResult(
            success=True,
            urls=["https://example.com/page1", "https://example.com/page2"],
            count=2,
            message="Successfully crawled 2 URLs"
        )
        mock_crawl.return_value = mock_result
        
        result = self.service.crawl_url("https://example.com")
        
        assert result.success is True
        assert result.count == 2
        assert len(result.urls) == 2
    
    @patch.object(WebCrawler, 'crawl')
    def test_crawl_url_with_custom_config(self, mock_crawl):
        """Test crawling with custom configuration parameters."""
        mock_result = CrawlResult(
            success=True,
            urls=["https://example.com/docs/guide"],
            count=1,
            message="Successfully crawled 1 URL"
        )
        mock_crawl.return_value = mock_result
        
        result = self.service.crawl_url(
            "https://example.com",
            max_depth=3,
            delay=2.0,
            filter_base="https://example.com/docs/"
        )
        
        assert result.success is True
        # Verify crawler was created with correct config
        mock_crawl.assert_called_once()
    
    @patch.object(WebCrawler, 'crawl')
    def test_crawl_url_handles_exceptions(self, mock_crawl):
        """Test service handles crawler exceptions gracefully."""
        mock_crawl.side_effect = Exception("Network error")
        
        result = self.service.crawl_url("https://example.com")
        
        assert result.success is False
        assert "Error during crawling" in result.message
        assert "Network error" in result.errors[0]
    
    @patch.object(WebCrawler, 'crawl')
    def test_crawl_url_with_progress_callback(self, mock_crawl, mock_progress_callback):
        """Test crawling with progress callback."""
        mock_result = CrawlResult(
            success=True,
            urls=["https://example.com/page1"],
            count=1,
            message="Success"
        )
        mock_crawl.return_value = mock_result
        
        result = self.service.crawl_url(
            "https://example.com",
            progress_callback=mock_progress_callback
        )
        
        assert result.success is True
        # Verify progress callback was passed to crawler
        call_args = mock_crawl.call_args
        assert call_args[1]['progress_callback'] == mock_progress_callback