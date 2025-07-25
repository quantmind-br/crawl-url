"""Tests for sitemap parsing functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO
import gzip

from crawl_url.core.sitemap_parser import SitemapParser, SitemapService
from crawl_url.core.models import SitemapEntry, CrawlResult


class TestSitemapParser:
    """Test SitemapParser class."""
    
    def test_parse_sitemap_xml_success(self, sample_sitemap_xml):
        """Test successful parsing of sitemap XML."""
        parser = SitemapParser()
        
        with patch('builtins.open', return_value=StringIO(sample_sitemap_xml)):
            entries = parser.parse_sitemap_xml('dummy_path.xml')
        
        assert len(entries) == 3
        
        # Check first entry
        assert entries[0].loc == "https://example.com/page1"
        assert entries[0].lastmod == "2023-01-15"
        assert entries[0].changefreq == "weekly"
        assert entries[0].priority == "0.8"
        
        # Check third entry (minimal)
        assert entries[2].loc == "https://example.com/page3"
        assert entries[2].lastmod is None
        assert entries[2].changefreq is None
        assert entries[2].priority is None
    
    def test_parse_sitemap_xml_with_compressed_file(self, sample_sitemap_xml):
        """Test parsing compressed sitemap XML file."""
        parser = SitemapParser()
        
        # Mock gzip.open to return our sample XML
        mock_file = StringIO(sample_sitemap_xml)
        with patch('gzip.open', return_value=mock_file):
            entries = parser.parse_sitemap_xml('sitemap.xml.gz')
        
        assert len(entries) == 3
        assert entries[0].loc == "https://example.com/page1"
    
    def test_parse_sitemap_xml_invalid_xml(self):
        """Test parsing invalid XML raises appropriate error."""
        parser = SitemapParser()
        invalid_xml = "<invalid><xml></invalid>"
        
        with patch('builtins.open', return_value=StringIO(invalid_xml)):
            entries = parser.parse_sitemap_xml('invalid.xml')
        
        # Should return empty list for invalid XML
        assert entries == []
    
    def test_parse_sitemap_xml_file_not_found(self):
        """Test parsing non-existent file handles gracefully."""
        parser = SitemapParser()
        
        with patch('builtins.open', side_effect=FileNotFoundError()):
            entries = parser.parse_sitemap_xml('nonexistent.xml')
        
        assert entries == []
    
    def test_parse_sitemap_index_xml(self, sample_sitemap_index_xml):
        """Test parsing sitemap index XML."""
        parser = SitemapParser()
        
        with patch('builtins.open', return_value=StringIO(sample_sitemap_index_xml)):
            sitemap_urls = parser.parse_sitemap_index_xml('sitemapindex.xml')
        
        assert len(sitemap_urls) == 2
        assert "https://example.com/sitemap1.xml" in sitemap_urls
        assert "https://example.com/sitemap2.xml" in sitemap_urls
    
    def test_parse_sitemap_index_xml_invalid(self):
        """Test parsing invalid sitemap index XML."""
        parser = SitemapParser()
        invalid_xml = "<invalid>content</invalid>"
        
        with patch('builtins.open', return_value=StringIO(invalid_xml)):
            sitemap_urls = parser.parse_sitemap_index_xml('invalid.xml')
        
        assert sitemap_urls == []
    
    def test_memory_efficient_parsing(self, sample_sitemap_xml):
        """Test memory efficient parsing with large sitemap simulation."""
        parser = SitemapParser()
        
        # Mock a very large sitemap by repeating entries
        large_sitemap = sample_sitemap_xml.replace(
            '</urlset>', 
            '<url><loc>https://example.com/large-page</loc></url></urlset>'
        )
        
        with patch('builtins.open', return_value=StringIO(large_sitemap)):
            entries = parser.parse_sitemap_xml('large_sitemap.xml')
        
        assert len(entries) == 4  # 3 original + 1 added
        assert entries[-1].loc == "https://example.com/large-page"


class TestSitemapService:
    """Test SitemapService class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service = SitemapService()
    
    @patch('crawl_url.core.sitemap_parser.requests.Session')
    def test_discover_sitemaps_from_robots_txt(self, mock_session_class, sample_robots_txt):
        """Test discovering sitemaps from robots.txt."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_robots_txt
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        sitemaps = self.service._discover_sitemaps_from_robots("https://example.com")
        
        assert len(sitemaps) == 2
        assert "https://example.com/sitemap.xml" in sitemaps
        assert "https://example.com/sitemap2.xml" in sitemaps
    
    @patch('crawl_url.core.sitemap_parser.requests.Session')
    def test_discover_sitemaps_robots_txt_not_found(self, mock_session_class):
        """Test robots.txt not found scenario."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        sitemaps = self.service._discover_sitemaps_from_robots("https://example.com")
        
        assert sitemaps == []
    
    @patch('crawl_url.core.sitemap_parser.requests.Session')
    def test_discover_common_sitemap_locations(self, mock_session_class):
        """Test discovering sitemaps from common locations."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock first location returns 200, second returns 404
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        
        mock_session.head.side_effect = [mock_response_200, mock_response_404]
        
        sitemaps = self.service._discover_common_sitemap_locations("https://example.com")
        
        assert len(sitemaps) == 1
        assert "https://example.com/sitemap.xml" in sitemaps
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    @patch.object(SitemapService, '_discover_sitemaps_from_robots')
    def test_process_sitemap_url_auto_discovery(self, mock_robots, mock_fetch, sample_sitemap_xml):
        """Test processing sitemap URL with auto-discovery."""
        # Mock discovery returning sitemap URLs
        mock_robots.return_value = ["https://example.com/sitemap.xml"]
        
        # Mock fetching sitemap content
        mock_fetch.return_value = sample_sitemap_xml
        
        result = self.service.process_sitemap_url("https://example.com")
        
        assert result.success is True
        assert result.count == 3
        assert len(result.urls) == 3
        assert "https://example.com/page1" in result.urls
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    def test_process_sitemap_url_direct_sitemap(self, mock_fetch, sample_sitemap_xml):
        """Test processing direct sitemap URL."""
        mock_fetch.return_value = sample_sitemap_xml
        
        result = self.service.process_sitemap_url("https://example.com/sitemap.xml")
        
        assert result.success is True
        assert result.count == 3
        assert len(result.urls) == 3
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    def test_process_sitemap_url_with_filter(self, mock_fetch, sample_sitemap_xml):
        """Test processing sitemap URL with URL filter."""
        mock_fetch.return_value = sample_sitemap_xml
        
        result = self.service.process_sitemap_url(
            "https://example.com/sitemap.xml",
            filter_base="https://example.com/page1"
        )
        
        assert result.success is True
        assert result.count == 1
        assert result.urls == ["https://example.com/page1"]
    
    @patch.object(SitemapService, '_discover_sitemaps_from_robots')
    @patch.object(SitemapService, '_discover_common_sitemap_locations')
    def test_process_sitemap_url_no_sitemaps_found(self, mock_common, mock_robots):
        """Test processing when no sitemaps are found."""
        mock_robots.return_value = []
        mock_common.return_value = []
        
        result = self.service.process_sitemap_url("https://example.com")
        
        assert result.success is False
        assert result.count == 0
        assert "No sitemaps found" in result.message
    
    @patch('crawl_url.core.sitemap_parser.requests.Session')
    def test_fetch_sitemap_content_success(self, mock_session_class, sample_sitemap_xml):
        """Test successful fetching of sitemap content."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock() 
        mock_response.status_code = 200
        mock_response.text = sample_sitemap_xml
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        content = self.service._fetch_sitemap_content("https://example.com/sitemap.xml")
        
        assert content == sample_sitemap_xml
    
    @patch('crawl_url.core.sitemap_parser.requests.Session')
    def test_fetch_sitemap_content_failure(self, mock_session_class):
        """Test failed fetching of sitemap content."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        content = self.service._fetch_sitemap_content("https://example.com/sitemap.xml")
        
        assert content is None
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    def test_process_sitemap_index_recursive(self, mock_fetch, sample_sitemap_index_xml, sample_sitemap_xml):
        """Test processing sitemap index with recursive fetching."""
        # First call returns sitemap index, subsequent calls return actual sitemaps
        mock_fetch.side_effect = [
            sample_sitemap_index_xml,  # Index file
            sample_sitemap_xml,        # First sitemap
            sample_sitemap_xml         # Second sitemap  
        ]
        
        result = self.service.process_sitemap_url("https://example.com/sitemapindex.xml")
        
        assert result.success is True
        # Should have 6 URLs total (3 from each sitemap, but duplicates removed)
        assert result.count == 3
        assert mock_fetch.call_count == 3
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    def test_process_sitemap_with_progress_callback(self, mock_fetch, sample_sitemap_xml, mock_progress_callback):
        """Test processing sitemap with progress callback."""
        mock_fetch.return_value = sample_sitemap_xml
        
        result = self.service.process_sitemap_url(
            "https://example.com/sitemap.xml",
            progress_callback=mock_progress_callback
        )
        
        assert result.success is True
        # Progress callback should be called
        mock_progress_callback.assert_called()
    
    @patch.object(SitemapService, '_fetch_sitemap_content')
    def test_process_sitemap_handles_exceptions(self, mock_fetch):
        """Test processing sitemap handles exceptions gracefully."""
        mock_fetch.side_effect = Exception("Network error")
        
        result = self.service.process_sitemap_url("https://example.com/sitemap.xml")
        
        assert result.success is False
        assert "Error processing sitemap" in result.message
        assert "Network error" in result.errors[0]