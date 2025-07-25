# crawl-url

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-crawl--url-orange.svg)](https://pypi.org/project/crawl-url/)

A powerful, cross-platform terminal application for extracting URLs from websites. Supports both sitemap.xml parsing and recursive website crawling with an intuitive PyTermGUI interface.

## Features

- **Two Crawling Modes**:
  - **Sitemap Mode**: Fast extraction from sitemap.xml files with automatic discovery
  - **Crawl Mode**: Recursive website crawling with configurable depth limits

- **Interactive Terminal Interface**:
  - Beautiful PyTermGUI interface with progressive disclosure
  - Windows compatibility with automatic console fallback
  - Real-time progress tracking and results display

- **Flexible Output Options**:
  - Multiple formats: TXT, JSON, CSV
  - Automatic filename generation based on domain and timestamp
  - Custom output paths supported

- **Smart URL Filtering**:
  - Filter URLs by base URL pattern
  - Automatic deduplication using efficient hashing
  - Support for relative and absolute URL resolution

- **Respectful Crawling**:
  - Configurable rate limiting with per-domain delays
  - robots.txt compliance checking
  - Memory-efficient parsing for large sitemaps

- **Cross-Platform Compatibility**:
  - Works on Windows and Linux
  - Automatic terminal compatibility detection
  - Console fallback for unsupported environments

## Installation

### From PyPI (Recommended)

```bash
pip install crawl-url
```

### From Source

```bash
git clone https://github.com/your-username/crawl-url.git
cd crawl-url
pip install -e .
```

## Quick Start

### Interactive Mode

Launch the interactive terminal interface:

```bash
crawl-url interactive
```

The interface provides:
- URL input with validation
- Mode selection (auto-detect, sitemap, or crawl)
- Configurable crawling parameters
- Real-time progress tracking
- Results preview and export options

### Command Line Mode

#### Auto-detect Mode
```bash
# Automatically detects sitemap.xml URLs vs regular website URLs
crawl-url crawl https://example.com
crawl-url crawl https://example.com/sitemap.xml
```

#### Sitemap Mode
```bash
# Extract URLs from sitemap.xml
crawl-url crawl https://example.com/sitemap.xml --mode sitemap

# With custom output format
crawl-url crawl https://example.com/sitemap.xml --format json --output results.json
```

#### Website Crawling Mode
```bash
# Recursive website crawling
crawl-url crawl https://example.com --mode crawl --depth 3

# With URL filtering and rate limiting
crawl-url crawl https://example.com --filter "https://example.com/docs/" --delay 2
```

## Command Line Options

```
crawl-url crawl [URL] [OPTIONS]

Arguments:
  URL  The website URL or sitemap.xml URL to process

Options:
  --mode [auto|sitemap|crawl]  Crawling mode (default: auto)
  --output PATH               Custom output file path
  --format [txt|json|csv]     Output format (default: txt)
  --depth INTEGER             Maximum crawl depth 1-10 (default: 3)
  --filter TEXT               Filter URLs by base URL pattern
  --delay FLOAT               Delay between requests in seconds (default: 1.0)
  --verbose                   Show detailed progress information
  --help                      Show help message
```

## Output Formats

### TXT Format
```
https://example.com/page1
https://example.com/page2
https://example.com/blog/post1
```

### JSON Format
```json
{
  "metadata": {
    "crawl_date": "2024-01-15 14:30:00",
    "total_urls": 150,
    "base_url": "https://example.com",
    "format_version": "1.0"
  },
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ]
}
```

### CSV Format
```csv
URL,Domain,Path
https://example.com/page1,example.com,/page1
https://example.com/page2,example.com,/page2
```

## Advanced Usage

### URL Filtering

Filter URLs to extract only specific sections of a website:

```bash
# Only extract documentation URLs
crawl-url crawl https://example.com --filter "https://example.com/docs/"

# Only extract blog posts
crawl-url crawl https://example.com --filter "https://example.com/blog/"
```

### Sitemap Discovery

The tool automatically discovers sitemaps from:
- robots.txt file
- Common locations (`/sitemap.xml`, `/sitemap_index.xml`)
- Sitemap index files with recursive processing

### Rate Limiting

Configure delays to be respectful to target websites:

```bash
# Wait 2 seconds between requests
crawl-url crawl https://example.com --delay 2.0

# Conservative crawling with 5-second delays
crawl-url crawl https://example.com --delay 5.0 --depth 2
```

## Python API

Use crawl-url as a Python library:

```python
from crawl_url import CrawlerService, SitemapService, StorageManager
from crawl_url.core.models import CrawlConfig

# Sitemap processing
sitemap_service = SitemapService()
result = sitemap_service.process_sitemap_url("https://example.com/sitemap.xml")

if result.success:
    print(f"Found {result.count} URLs")
    for url in result.urls[:5]:  # Show first 5 URLs
        print(f"  {url}")

# Website crawling
crawler_service = CrawlerService()
result = crawler_service.crawl_url(
    "https://example.com",
    max_depth=2,
    filter_base="https://example.com/docs/"
)

# Save results
storage_manager = StorageManager()
output_path = storage_manager.save_urls(
    urls=result.urls,
    base_url="https://example.com",
    format_type="json"
)
print(f"Results saved to: {output_path}")
```

## Configuration

### Environment Variables

```bash
# Set default crawl delay
export CRAWL_URL_DEFAULT_DELAY=1.5

# Set default output format
export CRAWL_URL_DEFAULT_FORMAT=json

# Set default max depth
export CRAWL_URL_DEFAULT_DEPTH=3
```

### Configuration File

Create a `.crawl-url.json` configuration file in your home directory:

```json
{
  "default_delay": 1.0,
  "default_format": "txt",
  "default_depth": 3,
  "respect_robots_txt": true,
  "user_agent": "crawl-url/1.0.0"
}
```

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, Linux (most distributions)
- **Memory**: Minimum 512MB RAM (more for large websites)
- **Network**: Internet connection for crawling

### Dependencies

Core dependencies:
- `requests` - HTTP client for web requests
- `beautifulsoup4` - HTML parsing and URL extraction
- `lxml` - Fast XML parsing for sitemaps
- `typer` - Modern CLI framework
- `rich` - Rich text and progress bars

Optional dependencies:
- `pytermgui` - Terminal user interface (auto-installs, falls back to console on failure)

## Platform-Specific Notes

### Windows
- Automatically detects Windows Terminal compatibility
- Falls back to console mode if PyTermGUI fails
- Supports PowerShell, Command Prompt, and Windows Terminal

### Linux
- Full PyTermGUI support on most distributions
- Tested on Ubuntu, Debian, CentOS, and Arch Linux
- Requires terminal with Unicode support for best experience

## Troubleshooting

### Common Issues

**PyTermGUI Interface Won't Start**
```bash
# Force console mode
crawl-url interactive --console-mode

# Or use command-line interface instead
crawl-url crawl https://example.com
```

**Memory Issues with Large Sitemaps**
```bash
# Use streaming mode for large sitemaps
crawl-url crawl https://example.com/sitemap.xml --stream

# Or process in smaller chunks
crawl-url crawl https://example.com --depth 1
```

**Rate Limiting / Blocked Requests**
```bash
# Increase delay between requests
crawl-url crawl https://example.com --delay 3.0

# Use more conservative settings
crawl-url crawl https://example.com --delay 5.0 --depth 2
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
crawl-url crawl https://example.com --verbose
```

This shows:
- Detailed request/response information
- robots.txt checking results
- URL filtering decisions
- Progress updates and timing

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/your-username/crawl-url.git
cd crawl-url

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/ tests/
black --check src/ tests/

# Run type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=crawl_url --cov-report=html

# Run specific test file
pytest tests/test_crawler.py

# Run tests with verbose output
pytest -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 (2024-01-15)
- Initial release
- Interactive PyTermGUI interface with Windows fallback
- Sitemap.xml parsing with automatic discovery
- Recursive website crawling with depth limits
- Multiple output formats (TXT, JSON, CSV)
- URL filtering and deduplication
- Rate limiting and robots.txt compliance
- Cross-platform compatibility (Windows/Linux)

## Support

- **Documentation**: [Full documentation](https://crawl-url.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/your-username/crawl-url/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/crawl-url/discussions)

## Acknowledgments

- Built with [PyTermGUI](https://github.com/bczsalba/pytermgui) for the terminal interface
- Uses [Typer](https://typer.tiangolo.com/) for the modern CLI framework
- XML parsing powered by [lxml](https://lxml.de/)
- HTML parsing with [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)

---

**Made with ❤️ for the web crawling community**