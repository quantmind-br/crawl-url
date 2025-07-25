"""Tests for CLI interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from typer.testing import CliRunner
from crawl_url.cli import app


class TestCLICommands:
    """Test CLI command interface."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_version_command(self):
        """Test version command displays version information."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "crawl-url version" in result.stdout
        assert "1.0.0" in result.stdout
    
    def test_help_command(self):
        """Test help command displays usage information."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "crawl-url" in result.stdout
        assert "interactive" in result.stdout
        assert "crawl" in result.stdout
    
    @patch('crawl_url.cli.CrawlerApp')
    def test_interactive_command_success(self, mock_crawler_app):
        """Test interactive command launches successfully."""
        mock_app_instance = Mock()
        mock_crawler_app.return_value = mock_app_instance
        
        result = self.runner.invoke(app, ["interactive"])
        
        assert result.exit_code == 0
        mock_crawler_app.assert_called_once()
        mock_app_instance.run.assert_called_once()
    
    @patch('crawl_url.cli.CrawlerApp')
    def test_interactive_command_keyboard_interrupt(self, mock_crawler_app):
        """Test interactive command handles keyboard interrupt."""
        mock_app_instance = Mock()
        mock_app_instance.run.side_effect = KeyboardInterrupt()
        mock_crawler_app.return_value = mock_app_instance
        
        result = self.runner.invoke(app, ["interactive"])
        
        assert result.exit_code == 0
        assert "Operation cancelled by user" in result.stdout
    
    @patch('crawl_url.cli.CrawlerApp')
    def test_interactive_command_exception(self, mock_crawler_app):
        """Test interactive command handles exceptions."""
        mock_app_instance = Mock()
        mock_app_instance.run.side_effect = Exception("Test error")
        mock_crawler_app.return_value = mock_app_instance
        
        result = self.runner.invoke(app, ["interactive"])
        
        assert result.exit_code == 1
        assert "Error launching interactive mode: Test error" in result.stdout


class TestCrawlCommand:
    """Test crawl command functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_crawl_command_help(self):
        """Test crawl command help displays all options."""
        result = self.runner.invoke(app, ["crawl", "--help"])
        assert result.exit_code == 0
        assert "--mode" in result.stdout
        assert "--output" in result.stdout
        assert "--format" in result.stdout
        assert "--depth" in result.stdout
        assert "--filter" in result.stdout
        assert "--delay" in result.stdout
    
    def test_crawl_command_missing_url(self):
        """Test crawl command fails without URL argument."""
        result = self.runner.invoke(app, ["crawl"])
        assert result.exit_code == 2  # Missing argument error
        assert "Missing argument" in result.stdout
    
    def test_crawl_command_invalid_mode(self):
        """Test crawl command fails with invalid mode."""
        result = self.runner.invoke(app, ["crawl", "https://example.com", "--mode", "invalid"])
        assert result.exit_code == 2
        assert "Invalid value for '--mode'" in result.stdout
    
    def test_crawl_command_invalid_format(self):
        """Test crawl command fails with invalid format."""
        result = self.runner.invoke(app, ["crawl", "https://example.com", "--format", "xml"])
        assert result.exit_code == 2
        assert "Invalid value for '--format'" in result.stdout
    
    def test_crawl_command_invalid_depth(self):
        """Test crawl command fails with invalid depth."""
        result = self.runner.invoke(app, ["crawl", "https://example.com", "--depth", "0"])
        assert result.exit_code == 2
        
        result = self.runner.invoke(app, ["crawl", "https://example.com", "--depth", "15"])
        assert result.exit_code == 2
    
    def test_crawl_command_invalid_delay(self):
        """Test crawl command fails with invalid delay."""
        result = self.runner.invoke(app, ["crawl", "https://example.com", "--delay", "0.1"])
        assert result.exit_code == 2
    
    @patch('crawl_url.cli.SitemapService')
    @patch('crawl_url.cli.StorageManager')
    def test_crawl_sitemap_mode_success(self, mock_storage_manager, mock_sitemap_service):
        """Test successful sitemap crawling."""
        # Mock sitemap service
        mock_service_instance = Mock()
        mock_sitemap_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.urls = ["https://example.com/page1", "https://example.com/page2"]
        mock_result.count = 2
        mock_result.errors = []
        mock_service_instance.process_sitemap_url.return_value = mock_result
        
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("example_com_20240101_120000.txt")
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, [
                "crawl", 
                "https://example.com/sitemap.xml",
                "--mode", "sitemap"
            ])
        
        assert result.exit_code == 0
        assert "Success!" in result.stdout
        assert "Found 2 URLs" in result.stdout
        mock_service_instance.process_sitemap_url.assert_called_once()
    
    @patch('crawl_url.cli.CrawlerService')
    @patch('crawl_url.cli.StorageManager')
    def test_crawl_website_mode_success(self, mock_storage_manager, mock_crawler_service):
        """Test successful website crawling."""
        # Mock crawler service
        mock_service_instance = Mock()
        mock_crawler_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.urls = ["https://example.com/", "https://example.com/page1"]
        mock_result.count = 2
        mock_result.errors = []
        mock_service_instance.crawl_url.return_value = mock_result
        
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("example_com_20240101_120000.txt")
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, [
                "crawl", 
                "https://example.com",
                "--mode", "crawl",
                "--depth", "2"
            ])
        
        assert result.exit_code == 0
        assert "Success!" in result.stdout
        assert "Found 2 URLs" in result.stdout
        mock_service_instance.crawl_url.assert_called_once()
    
    @patch('crawl_url.cli.SitemapService')
    def test_crawl_sitemap_mode_failure(self, mock_sitemap_service):
        """Test failed sitemap crawling."""
        mock_service_instance = Mock()
        mock_sitemap_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.urls = []
        mock_result.count = 0
        mock_result.message = "No sitemap found"
        mock_result.errors = ["404 Not Found"]
        mock_service_instance.process_sitemap_url.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "crawl", 
            "https://example.com/sitemap.xml",
            "--mode", "sitemap"
        ])
        
        assert result.exit_code == 1
        assert "No sitemap found" in result.stdout
    
    @patch('crawl_url.cli.SitemapService')
    @patch('crawl_url.cli.StorageManager')
    def test_crawl_with_custom_output_file(self, mock_storage_manager, mock_sitemap_service):
        """Test crawling with custom output file."""
        # Mock successful crawl
        mock_service_instance = Mock()
        mock_sitemap_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.urls = ["https://example.com/page1"]
        mock_result.count = 1
        mock_result.errors = []
        mock_service_instance.process_sitemap_url.return_value = mock_result
        
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("custom_output.json")
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, [
                "crawl", 
                "https://example.com/sitemap.xml",
                "--output", "custom_output.json",
                "--format", "json"
            ])
        
        assert result.exit_code == 0
        assert "Success!" in result.stdout
    
    @patch('crawl_url.cli.CrawlerService')
    @patch('crawl_url.cli.StorageManager')
    def test_crawl_with_url_filter(self, mock_storage_manager, mock_crawler_service):
        """Test crawling with URL filter."""
        mock_service_instance = Mock()
        mock_crawler_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.urls = ["https://docs.example.com/guide"]
        mock_result.count = 1
        mock_result.errors = []
        mock_service_instance.crawl_url.return_value = mock_result
        
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("output.txt")
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, [
                "crawl", 
                "https://example.com",
                "--filter", "https://docs.example.com/",
                "--verbose"
            ])
        
        assert result.exit_code == 0
        assert "Success!" in result.stdout
        # Check that crawler was called with filter
        call_args = mock_service_instance.crawl_url.call_args
        assert call_args[1]['filter_base'] == "https://docs.example.com/"
    
    @patch('crawl_url.cli.CrawlerService')
    def test_crawl_keyboard_interrupt(self, mock_crawler_service):
        """Test crawling handles keyboard interrupt."""
        mock_service_instance = Mock()
        mock_service_instance.crawl_url.side_effect = KeyboardInterrupt()
        mock_crawler_service.return_value = mock_service_instance
        
        result = self.runner.invoke(app, ["crawl", "https://example.com"])
        
        assert result.exit_code == 0
        assert "Operation cancelled by user" in result.stdout
    
    @patch('crawl_url.cli.CrawlerService')  
    def test_crawl_unexpected_exception(self, mock_crawler_service):
        """Test crawling handles unexpected exceptions."""
        mock_service_instance = Mock()
        mock_service_instance.crawl_url.side_effect = Exception("Unexpected error")
        mock_crawler_service.return_value = mock_service_instance
        
        result = self.runner.invoke(app, ["crawl", "https://example.com"])
        
        assert result.exit_code == 1
        assert "Unexpected error" in result.stdout
    
    @patch('crawl_url.cli.CrawlerService')
    @patch('crawl_url.cli.StorageManager')
    def test_crawl_with_verbose_output(self, mock_storage_manager, mock_crawler_service):
        """Test crawling with verbose output shows additional information."""
        mock_service_instance = Mock()
        mock_crawler_service.return_value = mock_service_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.urls = ["https://example.com/page1", "https://example.com/page2"]
        mock_result.count = 2
        mock_result.errors = []
        mock_service_instance.crawl_url.return_value = mock_result
        
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("output.txt")
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, [
                "crawl", 
                "https://example.com",
                "--verbose"
            ])
        
        assert result.exit_code == 0
        assert "Crawl Configuration" in result.stdout
        assert "Sample URLs Found" in result.stdout