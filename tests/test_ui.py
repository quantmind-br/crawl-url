"""Tests for PyTermGUI user interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from crawl_url.core.ui import CrawlerApp
from crawl_url.core.models import CrawlConfig, CrawlResult


class TestCrawlerApp:
    """Test CrawlerApp class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = CrawlerApp()
    
    def test_app_initialization(self):
        """Test app initialization sets default values."""
        assert self.app.current_config is None
        assert self.app.current_result is None
        assert self.app.current_mode == "main"
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_check_pytermgui_availability_success(self, mock_ptg):
        """Test PyTermGUI availability check when available."""
        mock_ptg.WindowManager = MagicMock()
        
        result = self.app._check_pytermgui_availability()
        
        assert result is True
    
    @patch('crawl_url.core.ui.pytermgui', side_effect=ImportError())
    def test_check_pytermgui_availability_import_error(self, mock_ptg):
        """Test PyTermGUI availability check when import fails."""
        result = self.app._check_pytermgui_availability()
        
        assert result is False
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_check_pytermgui_availability_windows_error(self, mock_ptg):
        """Test PyTermGUI availability check when Windows initialization fails."""
        mock_manager = MagicMock()
        mock_manager.__enter__.side_effect = Exception("Windows terminal error")
        mock_ptg.WindowManager.return_value = mock_manager
        
        result = self.app._check_pytermgui_availability()
        
        assert result is False
    
    @patch('crawl_url.core.ui.CrawlerService')
    @patch('crawl_url.core.ui.SitemapService')
    @patch('crawl_url.core.ui.StorageManager')
    def test_start_crawl_sitemap_mode(self, mock_storage_manager, mock_sitemap_service, mock_crawler_service):
        """Test starting crawl in sitemap mode."""
        # Setup config
        config = CrawlConfig(
            url="https://example.com/sitemap.xml",
            mode="sitemap"
        )
        self.app.current_config = config
        
        # Mock sitemap service
        mock_service_instance = Mock()
        mock_sitemap_service.return_value = mock_service_instance
        
        mock_result = CrawlResult(
            success=True,
            urls=["https://example.com/page1", "https://example.com/page2"],
            count=2,
            message="Successfully processed sitemap"
        )
        mock_service_instance.process_sitemap_url.return_value = mock_result
        
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("output.txt")
        
        self.app._start_crawl()
        
        # Verify sitemap service was called
        mock_service_instance.process_sitemap_url.assert_called_once()
        
        # Verify result was saved
        assert self.app.current_result == mock_result
    
    @patch('crawl_url.core.ui.CrawlerService')
    @patch('crawl_url.core.ui.SitemapService')
    @patch('crawl_url.core.ui.StorageManager')
    def test_start_crawl_crawler_mode(self, mock_storage_manager, mock_sitemap_service, mock_crawler_service):
        """Test starting crawl in crawler mode."""
        # Setup config
        config = CrawlConfig(
            url="https://example.com",
            mode="crawl"
        )
        self.app.current_config = config
        
        # Mock crawler service
        mock_service_instance = Mock()
        mock_crawler_service.return_value = mock_service_instance
        
        mock_result = CrawlResult(
            success=True,
            urls=["https://example.com/", "https://example.com/page1"],
            count=2,
            message="Successfully crawled website"
        )
        mock_service_instance.crawl_url.return_value = mock_result
        
        # Mock storage manager
        mock_storage_instance = Mock()
        mock_storage_manager.return_value = mock_storage_instance
        mock_storage_instance.save_urls.return_value = Path("output.txt")
        
        self.app._start_crawl()
        
        # Verify crawler service was called
        mock_service_instance.crawl_url.assert_called_once()
        
        # Verify result was saved
        assert self.app.current_result == mock_result
    
    @patch('crawl_url.core.ui.CrawlerService')
    @patch('crawl_url.core.ui.StorageManager')
    def test_start_crawl_handles_exception(self, mock_storage_manager, mock_crawler_service):
        """Test crawl handles exceptions gracefully."""
        config = CrawlConfig(url="https://example.com", mode="crawl")
        self.app.current_config = config
        
        # Mock crawler service to raise exception
        mock_service_instance = Mock()
        mock_crawler_service.return_value = mock_service_instance
        mock_service_instance.crawl_url.side_effect = Exception("Network error")
        
        self.app._start_crawl()
        
        # Should create error result
        assert self.app.current_result is not None
        assert self.app.current_result.success is False
        assert "Error during crawling" in self.app.current_result.message
    
    def test_auto_detect_mode_sitemap_url(self):
        """Test auto mode detection for sitemap URLs."""
        sitemap_urls = [
            "https://example.com/sitemap.xml",
            "https://example.com/sitemap.xml.gz",
            "https://example.com/sitemapindex.xml",
            "https://example.com/sitemap_index.xml"
        ]
        
        for url in sitemap_urls:
            mode = self.app._auto_detect_mode(url)
            assert mode == "sitemap", f"Failed for URL: {url}"
    
    def test_auto_detect_mode_regular_url(self):
        """Test auto mode detection for regular URLs."""
        regular_urls = [
            "https://example.com",
            "https://example.com/",
            "https://example.com/page.html",
            "https://example.com/about"
        ]
        
        for url in regular_urls:
            mode = self.app._auto_detect_mode(url)
            assert mode == "crawl", f"Failed for URL: {url}"
    
    def test_validate_url_valid_urls(self):
        """Test URL validation for valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com:8080/page"
        ]
        
        for url in valid_urls:
            is_valid, error = self.app._validate_url(url)
            assert is_valid is True, f"URL should be valid: {url}"
            assert error is None
    
    def test_validate_url_invalid_urls(self):
        """Test URL validation for invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",
            "javascript:void(0)",
            "mailto:test@example.com"
        ]
        
        for url in invalid_urls:
            is_valid, error = self.app._validate_url(url)
            assert is_valid is False, f"URL should be invalid: {url}"
            assert error is not None
    
    def test_create_progress_callback(self):
        """Test progress callback creation."""
        callback = self.app._create_progress_callback()
        
        # Should be callable
        assert callable(callback)
        
        # Should handle progress updates without error
        callback("Processing", 50, 100)
        callback("Complete", 100, 100)
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_create_main_window(self, mock_ptg):
        """Test main window creation."""
        # Mock PyTermGUI components
        mock_window = MagicMock()
        mock_ptg.Window.return_value = mock_window
        mock_ptg.Label.return_value = MagicMock()
        mock_ptg.InputField.return_value = MagicMock()
        mock_ptg.Button.return_value = MagicMock()
        mock_ptg.Container.return_value = MagicMock()
        
        window = self.app._create_main_window()
        
        # Verify window was created
        mock_ptg.Window.assert_called_once()
        assert window == mock_window
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_create_progress_window(self, mock_ptg):
        """Test progress window creation."""
        # Mock PyTermGUI components
        mock_window = MagicMock()
        mock_ptg.Window.return_value = mock_window
        mock_ptg.Label.return_value = MagicMock()
        mock_ptg.ProgressBar.return_value = MagicMock()
        mock_ptg.Button.return_value = MagicMock()
        
        window = self.app._create_progress_window()
        
        # Verify window was created
        mock_ptg.Window.assert_called_once()
        assert window == mock_window
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_create_results_window(self, mock_ptg):
        """Test results window creation."""
        # Setup a mock result
        self.app.current_result = CrawlResult(
            success=True,
            urls=["https://example.com/page1", "https://example.com/page2"],
            count=2,
            message="Success"
        )
        
        # Mock PyTermGUI components
        mock_window = MagicMock()
        mock_ptg.Window.return_value = mock_window
        mock_ptg.Label.return_value = MagicMock()
        mock_ptg.Button.return_value = MagicMock()
        mock_ptg.Container.return_value = MagicMock()
        
        window = self.app._create_results_window()
        
        # Verify window was created
        mock_ptg.Window.assert_called_once()
        assert window == mock_window
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_create_help_window(self, mock_ptg):
        """Test help window creation."""
        # Mock PyTermGUI components
        mock_window = MagicMock()
        mock_ptg.Window.return_value = mock_window
        mock_ptg.Label.return_value = MagicMock()
        mock_ptg.Button.return_value = MagicMock()
        
        window = self.app._create_help_window()
        
        # Verify window was created
        mock_ptg.Window.assert_called_once()
        assert window == mock_window
    
    @patch.object(CrawlerApp, '_run_console_mode')
    @patch.object(CrawlerApp, '_check_pytermgui_availability')
    def test_run_fallback_to_console_mode(self, mock_check_ptg, mock_console_mode):
        """Test app falls back to console mode when PyTermGUI unavailable."""
        mock_check_ptg.return_value = False  # PyTermGUI not available
        
        self.app.run()
        
        # Should fall back to console mode
        mock_console_mode.assert_called_once()
    
    @patch.object(CrawlerApp, '_run_tui_mode')
    @patch.object(CrawlerApp, '_check_pytermgui_availability')
    def test_run_uses_tui_mode(self, mock_check_ptg, mock_tui_mode):
        """Test app uses TUI mode when PyTermGUI is available."""
        mock_check_ptg.return_value = True  # PyTermGUI available
        
        self.app.run()
        
        # Should use TUI mode
        mock_tui_mode.assert_called_once()
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch.object(CrawlerApp, '_start_crawl')
    def test_console_mode_basic_flow(self, mock_start_crawl, mock_print, mock_input):
        """Test console mode basic user interaction flow."""
        # Mock user inputs
        mock_input.side_effect = [
            "https://example.com",  # URL input
            "1",                    # Mode selection (auto)
            "3",                    # Max depth
            "1.0",                  # Delay
            "",                     # No filter
            "txt",                  # Output format
            "q"                     # Quit
        ]
        
        # Mock crawl result
        self.app.current_result = CrawlResult(
            success=True,
            urls=["https://example.com/page1"],
            count=1,
            message="Success"
        )
        
        self.app._run_console_mode()
        
        # Verify crawl was started
        mock_start_crawl.assert_called_once()
        
        # Verify some output was printed
        mock_print.assert_called()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_console_mode_invalid_url(self, mock_print, mock_input):
        """Test console mode handles invalid URL input."""
        mock_input.side_effect = [
            "invalid-url",          # Invalid URL
            "https://example.com",  # Valid URL
            "q"                     # Quit
        ]
        
        self.app._run_console_mode()
        
        # Should print error message for invalid URL
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_messages = [msg for msg in print_calls if "invalid" in msg.lower() or "error" in msg.lower()]
        assert len(error_messages) > 0
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_console_mode_help_display(self, mock_print, mock_input):
        """Test console mode displays help when requested."""
        mock_input.side_effect = [
            "h",  # Help command
            "q"   # Quit
        ]
        
        self.app._run_console_mode()
        
        # Should print help information
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        help_messages = [msg for msg in print_calls if "help" in msg.lower() or "commands" in msg.lower()]
        assert len(help_messages) > 0
    
    @patch('crawl_url.core.ui.pytermgui')
    def test_tui_mode_window_manager_setup(self, mock_ptg):
        """Test TUI mode sets up window manager correctly."""
        # Mock WindowManager context manager
        mock_manager = MagicMock()
        mock_manager.__enter__ = Mock(return_value=mock_manager)
        mock_manager.__exit__ = Mock(return_value=None)
        mock_ptg.WindowManager.return_value = mock_manager
        
        # Mock window creation methods
        mock_main_window = MagicMock()
        with patch.object(self.app, '_create_main_window', return_value=mock_main_window):
            with patch.object(self.app, '_update_layout'):
                self.app._run_tui_mode()
        
        # Verify window manager was used
        mock_ptg.WindowManager.assert_called_once()
        mock_manager.__enter__.assert_called_once()
    
    def test_update_layout_main_mode(self):
        """Test layout update for main mode."""
        self.app.current_mode = "main"
        
        with patch.object(self.app, '_create_main_window') as mock_create_main:
            mock_window = MagicMock()
            mock_create_main.return_value = mock_window
            
            self.app.manager = MagicMock()  # Mock window manager
            
            self.app._update_layout()
            
            # Verify main window was created and added
            mock_create_main.assert_called_once()
    
    def test_update_layout_progress_mode(self):
        """Test layout update for progress mode."""
        self.app.current_mode = "progress"
        
        with patch.object(self.app, '_create_progress_window') as mock_create_progress:
            mock_window = MagicMock()
            mock_create_progress.return_value = mock_window
            
            self.app.manager = MagicMock()  # Mock window manager
            
            self.app._update_layout()
            
            # Verify progress window was created and added
            mock_create_progress.assert_called_once()
    
    def test_switch_to_mode(self):
        """Test mode switching functionality."""
        self.app.manager = MagicMock()  # Mock window manager
        
        with patch.object(self.app, '_update_layout') as mock_update:
            self.app._switch_to_mode("results")
            
            assert self.app.current_mode == "results"
            mock_update.assert_called_once()
    
    @patch.object(CrawlerApp, '_start_crawl')
    def test_handle_start_crawl_button(self, mock_start_crawl):
        """Test handling start crawl button click."""
        # Mock input fields
        self.app.url_input = MagicMock()
        self.app.url_input.value = "https://example.com"
        
        self.app.mode_dropdown = MagicMock()
        self.app.mode_dropdown.selected_index = 0  # Auto mode
        
        self.app.depth_input = MagicMock()
        self.app.depth_input.value = "3"
        
        self.app.delay_input = MagicMock()
        self.app.delay_input.value = "1.0"
        
        self.app.filter_input = MagicMock()
        self.app.filter_input.value = ""
        
        self.app.format_dropdown = MagicMock()
        self.app.format_dropdown.selected_index = 0  # txt format
        
        with patch.object(self.app, '_switch_to_mode') as mock_switch:
            self.app._handle_start_crawl()
            
            # Should create config and start crawl
            assert self.app.current_config is not None
            mock_start_crawl.assert_called_once()
            mock_switch.assert_called_with("progress")
    
    def test_handle_start_crawl_invalid_input(self):
        """Test handling start crawl with invalid input."""
        # Mock input fields with invalid data
        self.app.url_input = MagicMock()
        self.app.url_input.value = "invalid-url"
        
        self.app.error_label = MagicMock()
        
        self.app._handle_start_crawl()
        
        # Should not create config due to invalid URL
        assert self.app.current_config is None
        
        # Should set error message
        self.app.error_label.value = "Invalid URL format. Please use http:// or https://"