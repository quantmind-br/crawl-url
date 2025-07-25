# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**crawl-url** is a Python CLI tool for extracting URLs from websites with two main modes: sitemap.xml parsing and recursive website crawling. It features an interactive PyTermGUI-based terminal interface with Windows compatibility detection and automatic console fallback.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment and install development dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=crawl_url --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run specific test file
pytest tests/test_crawler.py

# Run tests with verbose output
pytest -v
```

### Code Quality
```bash
# Run linting
ruff check src/ tests/

# Run code formatting
black --check src/ tests/

# Apply formatting
black src/ tests/

# Run type checking
mypy src/

# Run all quality checks (recommended before commits)
ruff check src/ tests/ && black --check src/ tests/ && mypy src/ && pytest
```

### Building and Distribution
```bash
# Build package
python -m build

# Install from local build
pip install -e .

# Test CLI installation
crawl-url --help
```

## Architecture Overview

### Core Structure
- **`src/crawl_url/cli.py`**: Main CLI entry point using Typer framework
- **`src/crawl_url/core/`**: Core business logic
  - `models.py`: Data classes (CrawlConfig, CrawlResult, SitemapEntry)
  - `crawler.py`: Web crawling implementation with depth limits and rate limiting
  - `sitemap_parser.py`: XML sitemap parsing with sitemap index support
  - `ui.py`: PyTermGUI interactive interface with Windows compatibility
- **`src/crawl_url/utils/`**: Utility modules for storage and validation

### Key Components

**Dual Operation Modes:**
- **Sitemap Mode**: Efficiently parses sitemap.xml files and sitemap indexes
- **Crawl Mode**: Recursive website crawling with configurable depth (1-10)

**Cross-Platform Compatibility:**
- Windows: Automatic PyTermGUI compatibility detection with console mode fallback
- Linux: Full PyTermGUI interface support
- Platform-specific handling in `ui.py` and CLI commands

**Data Models:**
- `CrawlConfig`: Comprehensive configuration validation with mode, depth, and rate limiting
- `CrawlResult`: Standardized result structure with success status and metadata
- `SitemapEntry`: XML sitemap entry representation

### Testing Architecture
- **Unit Tests**: Complete coverage of core modules with extensive mocking
- **Integration Tests**: End-to-end workflow validation
- **Platform Testing**: Windows/Linux compatibility validation
- **Test Fixtures**: Comprehensive test data including HTML, XML, and configuration samples

## Development Patterns

### Configuration Management
- Uses `pyproject.toml` for modern Python packaging
- Environment variable support for default settings
- Configuration file support (`.crawl-url.json`)

### Error Handling
- Graceful degradation for Windows PyTermGUI compatibility issues
- Comprehensive validation in data models using Pydantic-style patterns
- Rate limiting and robots.txt compliance for ethical crawling

### Testing Patterns
- Extensive use of `pytest-mock` for external dependency mocking
- Separate test markers for unit/integration/slow tests
- Coverage reporting with HTML output for detailed analysis

### Code Quality Standards
- Black formatting with 88-character line length
- Ruff linting with comprehensive rule set
- MyPy strict type checking for Python 3.8+
- Pre-commit hooks available for quality enforcement

## Key Dependencies
- **CLI Framework**: Typer for modern command-line interface
- **TUI Framework**: PyTermGUI for interactive terminal interface
- **Web Requests**: requests library with BeautifulSoup4 for HTML parsing
- **XML Processing**: lxml for fast sitemap.xml parsing
- **Rich Output**: Rich library for progress bars and formatting

## Platform-Specific Notes

### Windows Development
- PyTermGUI may fail on some Windows configurations - automatic console fallback implemented
- Test platform detection in `test_ui.py` for Windows-specific behavior
- Unicode handling considerations for Windows terminals

### Linux Development
- Full PyTermGUI interface support expected
- Terminal compatibility detection for optimal user experience