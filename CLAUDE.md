# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**crawl-url** is a Python CLI tool for extracting URLs from websites with two modes: sitemap.xml parsing and recursive crawling. Features Windows-compatible console fallback for PyTermGUI issues.

## Development Commands

### Setup and Installation
```bash
# Quick setup (Windows)
python setup.bat

# Quick setup (Unix/Linux/Mac)
./setup-advanced.bat

# Manual setup
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
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

# Run validation test
python final_validation.py
```

## Architecture Overview

### Architecture
Package: `src/crawl_url/` - modular Python CLI tool

**Entry Points:**
- `cli.py:main()` → Typer CLI registration
- `__init__.py:get_version()` → Package metadata

**Core Domain:**
- `models.py` → Config/result validation (pydantic-style)
- `crawler.py` → HTTP crawling + robots.txt + rate limiting
- `sitemap_parser.py` → XML sitemap + sitemap index parsing
- `ui.py` → PyTermGUI with Windows console fallback

**Utilities:**
- `storage.py` → File persistence (TXT/JSON/CSV outputs)
- `validation.py` → URL filtering and validation utilities

### Testing Architecture
- **Unit Tests**: Complete coverage of core modules with extensive mocking
- **Integration Tests**: End-to-end workflow validation
- **Platform Testing**: Windows/Linux compatibility validation
- **Test Fixtures**: Comprehensive test data including HTML, XML, and configuration samples

### Quality Pipeline
- **Format**: `black` (88 chars) → `ruff check` → `mypy --strict`
- **Test**: `pytest` with markers: unit, integration, slow
- **Build**: `python -m build` outputs .whl + .tar.gz

### Operations
**Dual modes in CLI:**
```bash
crawl-url crawl https://example.com          # recursive (depth=3)
crawl-url crawl https://example.com/sitemap  # sitemap mode (auto)
```

**Interactive options from `cli.py`:**
```bash
crawl-url interactive                    # TUI + Windows console fallback
crawl-url crawl <url> --mode sitemap     # Force sitemap parsing
crawl-url crawl <url> --format json      # Change output format
crawl-url crawl <url> --depth 5          # Adjust crawl depth
crawl-url crawl <url> --delay 1.0        # Rate limiting
```

### Platform Specifics
- Windows: Console mode defaults (no PyTermGUI compatibility issues)
- Linux: Full PyTermGUI interface with rich terminal features
- All platforms: robots.txt compliance + user-agent rotation