"""Pytest configuration and fixtures for crawl-url tests."""

import pytest
from pathlib import Path
from typing import List
from unittest.mock import Mock, MagicMock
import tempfile


@pytest.fixture
def sample_html() -> str:
    """Provide sample HTML content for testing."""
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Website</h1>
            <a href="https://example.com/page1">Page 1</a>
            <a href="/relative-page">Relative Page</a>
            <a href="mailto:test@example.com">Email Link</a>
            <a href="#fragment">Fragment Link</a>
            <a href="https://external.com/page">External Page</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_sitemap_xml() -> str:
    """Provide sample sitemap XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2023-01-15</lastmod>
            <changefreq>weekly</changefreq>
            <priority>0.8</priority>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
            <lastmod>2023-01-20</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.9</priority>
        </url>
        <url>
            <loc>https://example.com/page3</loc>
        </url>
    </urlset>"""


@pytest.fixture
def sample_sitemap_index_xml() -> str:
    """Provide sample sitemap index XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://example.com/sitemap1.xml</loc>
            <lastmod>2023-01-15T10:30:00+00:00</lastmod>
        </sitemap>
        <sitemap>
            <loc>https://example.com/sitemap2.xml</loc>
            <lastmod>2023-01-20T15:45:00+00:00</lastmod>
        </sitemap>
    </sitemapindex>"""


@pytest.fixture
def sample_robots_txt() -> str:
    """Provide sample robots.txt content for testing."""
    return """User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap2.xml

Crawl-delay: 1
"""


@pytest.fixture
def temp_output_file(tmp_path: Path) -> Path:
    """Provide a temporary output file for testing."""
    return tmp_path / "test_output.txt"


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Provide a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def mock_requests_session() -> Mock:
    """Provide a mocked requests session."""
    session = Mock()
    
    # Mock response object
    response = Mock()
    response.status_code = 200
    response.headers = {'content-type': 'text/html'}
    response.raise_for_status.return_value = None
    
    session.get.return_value = response
    session.head.return_value = response
    
    return session


@pytest.fixture
def mock_progress_callback() -> Mock:
    """Provide a mock progress callback function."""
    return Mock()


@pytest.fixture
def sample_urls() -> List[str]:
    """Provide sample URLs for testing."""
    return [
        "https://example.com/",
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/blog/post1",
        "https://example.com/blog/post2",
        "https://docs.example.com/guide",
        "https://api.example.com/docs",
    ]


@pytest.fixture
def filtered_urls() -> List[str]:
    """Provide filtered URLs for testing."""
    return [
        "https://docs.example.com/guide",
        "https://docs.example.com/api",
        "https://docs.example.com/tutorial",
    ]


@pytest.fixture
def mock_pytermgui():
    """Mock PyTermGUI components to avoid TUI launch during tests."""
    mock_ptg = MagicMock()
    
    # Mock WindowManager
    mock_manager = MagicMock()
    mock_manager.__enter__ = Mock(return_value=mock_manager)
    mock_manager.__exit__ = Mock(return_value=None)
    mock_ptg.WindowManager.return_value = mock_manager
    
    # Mock Window
    mock_window = MagicMock()
    mock_window.center.return_value = mock_window
    mock_ptg.Window.return_value = mock_window
    
    # Mock common widgets
    mock_ptg.Label.return_value = MagicMock()
    mock_ptg.InputField.return_value = MagicMock()
    mock_ptg.Button.return_value = MagicMock()
    mock_ptg.Container.return_value = MagicMock()
    
    # Mock boxes
    mock_ptg.boxes.SINGLE = "SINGLE"
    mock_ptg.boxes.DOUBLE = "DOUBLE"
    mock_ptg.boxes.EMPTY = "EMPTY"
    
    return mock_ptg


@pytest.fixture
def sample_crawl_config():
    """Provide sample crawl configuration for testing."""
    from crawl_url.core.models import CrawlConfig
    
    return CrawlConfig(
        url="https://example.com",
        mode="auto",
        max_depth=2,
        delay=1.0,
        filter_base=None,
        output_format="txt"
    )


@pytest.fixture
def sample_crawl_result():
    """Provide sample crawl result for testing."""
    from crawl_url.core.models import CrawlResult
    
    return CrawlResult(
        success=True,
        urls=[
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ],
        count=3,
        message="Successfully crawled 3 URLs"
    )


@pytest.fixture(autouse=True)
def mock_time_sleep(monkeypatch):
    """Mock time.sleep to speed up tests."""
    def mock_sleep(duration):
        pass  # Do nothing, don't actually sleep
    
    monkeypatch.setattr("time.sleep", mock_sleep)


@pytest.fixture
def capture_logs(caplog):
    """Capture logs during testing."""
    import logging
    caplog.set_level(logging.INFO)
    return caplog