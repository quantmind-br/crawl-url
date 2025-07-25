# Modern Python CLI Packaging Guide for Crawl-URL

## Overview
This guide provides the complete setup for creating a modern, installable Python CLI application using pyproject.toml, Typer, and best practices for 2024.

## Essential Project Structure (Src Layout)
```
crawl-url/
├── README.md
├── LICENSE
├── pyproject.toml                    # Modern packaging configuration
├── .gitignore
├── .github/
│   └── workflows/
│       ├── test.yml                  # CI/CD testing
│       └── publish.yml               # PyPI publishing
├── src/
│   └── crawl_url/                    # Main package (note: underscore, not hyphen)
│       ├── __init__.py               # Package version and metadata
│       ├── cli.py                    # Main CLI entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── crawler.py            # Web crawling logic
│       │   ├── sitemap_parser.py     # Sitemap parsing
│       │   └── ui.py                 # PyTermGUI interface
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_crawler.py
│   └── fixtures/
└── requirements-dev.txt (optional)
```

## Complete pyproject.toml Configuration
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crawl-url"
version = "1.0.0"
description = "A powerful terminal application for crawling and extracting URLs from websites"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["cli", "web-crawling", "url", "scraping", "terminal", "sitemap"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: System :: Systems Administration",
    "Topic :: Utilities",
]

# Core dependencies
dependencies = [
    "requests>=2.28.0",
    "beautifulsoup4>=4.11.0",
    "lxml>=4.9.0",
    "pytermgui>=7.4.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

# Optional dependencies
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "twine>=4.0.0",
    "build>=0.10.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
]

# Console script entry points
[project.scripts]
crawl-url = "crawl_url.cli:main"
curl = "crawl_url.cli:main"  # Optional shorter alias

[project.urls]
Homepage = "https://github.com/username/crawl-url"
Repository = "https://github.com/username/crawl-url"
Issues = "https://github.com/username/crawl-url/issues"
Changelog = "https://github.com/username/crawl-url/blob/main/CHANGELOG.md"
Documentation = "https://github.com/username/crawl-url#readme"

# Setuptools-specific configuration
[tool.setuptools.packages.find]
where = ["src"]
include = ["crawl_url*"]

# Black formatting configuration
[tool.black]
line-length = 88
target-version = ["py38", "py39", "py310", "py311", "py312"]
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

# Ruff linting configuration  
[tool.ruff]
target-version = "py38"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

# MyPy type checking configuration
[tool.mypy]
python_version = "3.8"
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=crawl_url",
    "--cov-report=html",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

# Coverage configuration
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Package Version Management
```python
# src/crawl_url/__init__.py
"""
Crawl-URL: A powerful terminal application for URL crawling.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "A powerful terminal application for crawling and extracting URLs from websites"

# Make key classes available at package level
from .core.crawler import URLCrawler
from .core.sitemap_parser import SitemapParser
from .core.ui import CrawlerApp

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "URLCrawler",
    "SitemapParser", 
    "CrawlerApp",
]
```

## Main CLI Entry Point Pattern
```python
# src/crawl_url/cli.py
"""
Main CLI entry point for crawl-url application.
"""

import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.ui import CrawlerApp
from .core.crawler import URLCrawler
from .core.sitemap_parser import SitemapService
from . import __version__, __description__

# Create main Typer app
app = typer.Typer(
    name="crawl-url",
    help=f"🕷️ {__description__}",
    epilog="Made with ❤️ using Typer and PyTermGUI",
    add_completion=True,
    rich_markup_mode="rich"
)

console = Console()

# Version callback
def version_callback(value: bool):
    if value:
        console.print(f"crawl-url version {__version__}")
        raise typer.Exit()

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, 
        "--version", 
        "-V", 
        callback=version_callback,
        help="Show version and exit"
    )
):
    """🕷️ Crawl-URL: A powerful terminal application for URL crawling."""
    pass

@app.command()
def interactive():
    """🖥️ Launch interactive terminal UI mode."""
    try:
        app = CrawlerApp()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error launching interactive mode: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def crawl(
    url: str = typer.Argument(..., help="🌐 URL to crawl"),
    mode: str = typer.Option(
        "auto", 
        "--mode", 
        "-m", 
        help="🔍 Crawling mode",
        click_type=typer.Choice(["auto", "sitemap", "crawl"])
    ),
    output: Optional[Path] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="💾 Output file path"
    ),
    format: str = typer.Option(
        "txt", 
        "--format", 
        "-f", 
        help="📄 Output format",
        click_type=typer.Choice(["txt", "json", "csv"])
    ),
    depth: int = typer.Option(
        3, 
        "--depth", 
        "-d", 
        help="🔍 Maximum crawling depth (crawl mode only)",
        min=1,
        max=10
    ),
    filter_base: Optional[str] = typer.Option(
        None,
        "--filter",
        "-fb",
        help="🎯 Filter URLs by base URL"
    ),
    delay: float = typer.Option(
        1.0, 
        "--delay", 
        help="⏱️ Delay between requests (seconds)",
        min=0.0
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v", 
        help="🔊 Enable verbose output"
    ),
) -> None:
    """🕷️ Crawl a URL and extract URLs (command-line mode)."""
    
    # Determine output filename if not provided
    if output is None:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or "crawl_results"
        timestamp = __import__('time').strftime('%Y%m%d_%H%M%S')
        output = Path(f"{domain}_{timestamp}.{format}")
    
    try:
        if mode == "sitemap" or (mode == "auto" and url.endswith('.xml')):
            # Sitemap mode
            service = SitemapService(progress_callback=_create_progress_callback(verbose))
            if url.endswith('.xml'):
                result = service.process_sitemap_url(url, filter_base)
            else:
                result = service.process_base_url(url, filter_base)
        else:
            # Crawling mode
            crawler = URLCrawler(
                max_depth=depth,
                delay=delay,
                progress_callback=_create_progress_callback(verbose)
            )
            result = crawler.crawl_website(url, filter_base)
        
        if result['success']:
            # Save results
            _save_results(result['urls'], output, format)
            
            console.print(f"[green]✅ Success![/green]")
            console.print(f"📊 Found {result['count']} URLs")
            console.print(f"💾 Saved to: {output}")
            
            if verbose:
                _display_summary_table(result['urls'][:10])  # Show first 10
        else:
            console.print(f"[red]❌ {result['message']}[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)

def _create_progress_callback(verbose: bool):
    """Create progress callback for crawling operations"""
    if not verbose:
        return None
        
    def progress_callback(message: str, count: int):
        console.print(f"[blue]🔄 {message}[/blue] ([cyan]{count}[/cyan] URLs found)")
    
    return progress_callback

def _save_results(urls: List[str], output_path: Path, format: str):
    """Save URLs to file in specified format"""
    if format == "txt":
        output_path.write_text('\n'.join(urls), encoding='utf-8')
    elif format == "json":
        import json
        import time
        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_urls': len(urls),
            'urls': urls
        }
        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    elif format == "csv":
        import csv
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL'])
            for url in urls:
                writer.writerow([url])

def _display_summary_table(urls: List[str]):
    """Display summary table of URLs"""
    table = Table(title="Sample URLs Found")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("URL", style="blue")
    
    for i, url in enumerate(urls, 1):
        table.add_row(str(i), url)
    
    console.print(table)

# Main entry point
def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Development Workflow Setup

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### GitHub Actions CI/CD
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run linting
      run: |
        ruff check src/ tests/
        ruff format --check src/ tests/
    
    - name: Run type checking
      run: mypy src/
    
    - name: Run tests
      run: pytest tests/ -v --cov=crawl_url --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Installation and Distribution Commands

### Development Installation
```bash
# Install in development mode
pip install -e .

# Install with development dependencies  
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Building and Publishing
```bash
# Build the package
python -m build

# Check the built package
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Testing Installation
```bash
# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ crawl-url

# Test the CLI works
crawl-url --version
crawl-url --help
```

## Cross-Platform Compatibility Notes

### Entry Point Creation
- The `[project.scripts]` configuration automatically creates:
  - `crawl-url.exe` on Windows (in Scripts/ directory)  
  - `crawl-url` script on Unix/Linux (in bin/ directory)
- Both call the same `crawl_url.cli:main` function

### Path Handling
```python
# Always use pathlib for cross-platform paths
from pathlib import Path

# User home directory
config_dir = Path.home() / ".config" / "crawl-url"

# Current working directory
output_file = Path.cwd() / "results.txt"
```

### Console Encoding
```python
# Handle console encoding differences
import sys
import locale

def get_console_encoding():
    """Get appropriate console encoding"""
    return getattr(sys.stdout, 'encoding', None) or locale.getpreferredencoding() or 'utf-8'
```

## Testing Patterns for CLI Applications

### CLI Testing with Typer
```python
# tests/test_cli.py
import pytest
from typer.testing import CliRunner
from crawl_url.cli import app

runner = CliRunner()

def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "crawl-url version" in result.stdout

def test_interactive_command():
    """Test interactive command (mocked)."""
    # Mock the CrawlerApp to avoid actual TUI launch
    with patch('crawl_url.cli.CrawlerApp') as mock_app:
        result = runner.invoke(app, ["interactive"])
        assert result.exit_code == 0
        mock_app.assert_called_once()

def test_crawl_command_invalid_url():
    """Test crawl command with invalid URL."""
    result = runner.invoke(app, ["crawl", "invalid-url"])
    assert result.exit_code == 1
    assert "Error" in result.stdout

@pytest.mark.integration  
def test_crawl_command_real_url(tmp_path):
    """Integration test with real URL."""
    output_file = tmp_path / "test_output.txt"
    result = runner.invoke(app, [
        "crawl", 
        "https://example.com",
        "--output", str(output_file),
        "--mode", "sitemap"
    ])
    
    if result.exit_code == 0:
        assert output_file.exists()
        assert output_file.stat().st_size > 0
```

## Key Benefits of This Setup

1. **Modern Standards**: Uses pyproject.toml and src layout (2024 best practices)
2. **Cross-Platform**: Works identically on Windows, Linux, and macOS
3. **Professional Tooling**: Includes linting, formatting, type checking, and testing
4. **Easy Installation**: `pip install crawl-url` creates working CLI command
5. **Rich CLI Experience**: Beautiful output with Rich and Typer
6. **Comprehensive Testing**: Unit tests, integration tests, and CI/CD
7. **Easy Distribution**: Ready for PyPI publishing

This setup provides a complete, professional foundation for the crawl-url CLI application.