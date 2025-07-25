# Crawl-URL Terminal Application PRP

## Goal

Create a complete Python terminal application called "crawl-url" that extracts URLs from websites through two modes: sitemap.xml parsing and full website crawling. The application must be interactive using PyTermGUI, installable via pip, and work cross-platform (Windows/Linux).

## Why

- **Business Value**: Provides developers, SEO professionals, and system administrators with a powerful tool to analyze website structure and extract URL lists
- **User Impact**: Eliminates manual URL collection processes and provides an intuitive terminal interface for technical users
- **Integration Need**: Creates a standalone tool that can be integrated into larger automation workflows
- **Problem Solved**: Current tools are either too complex (enterprise crawlers) or too simple (basic scripts). This fills the gap with a professional terminal application

## What

A Python CLI application with these specifications:

### Core Features
- **Two Operation Modes**: 
  - Sitemap mode: Parse sitemap.xml URLs directly
  - Crawl mode: Recursively crawl website starting from base URL
- **Interactive Terminal UI**: Built with PyTermGUI for professional user experience
- **URL Filtering**: Filter extracted URLs by base URL pattern (e.g., only URLs starting with https://docs.anthropic.com/en/docs/claude-code)
- **Multiple Output Formats**: Save results as text, JSON, or CSV files
- **Cross-Platform**: Works on Windows and Linux terminals
- **Pip Installable**: `pip install crawl-url` → `crawl-url` command available globally

### Success Criteria

- [ ] Interactive terminal application launches successfully on Windows and Linux
- [ ] Sitemap mode: Successfully parses sitemap.xml files and sitemap indexes
- [ ] Crawl mode: Recursively crawls websites with configurable depth limits
- [ ] URL filtering works correctly when base URL filter is provided
- [ ] Results saved to files named after input site in current working directory
- [ ] Application installable via pip and accessible as `crawl-url` command
- [ ] Handles errors gracefully with user-friendly messages
- [ ] Respects robots.txt and implements rate limiting for ethical crawling

## All Needed Context

### Documentation & References

```yaml
# MUST READ - PyTermGUI Implementation Patterns
- docfile: PRPs/ai_docs/pytermgui_guide.md
  why: Complete implementation patterns, gotchas, and cross-platform considerations for TUI

# MUST READ - Web Crawling Implementation  
- docfile: PRPs/ai_docs/web_crawling_patterns.md
  why: Production-ready crawling patterns with requests+BeautifulSoup, rate limiting, error handling

# MUST READ - Sitemap Parsing Implementation
- docfile: PRPs/ai_docs/sitemap_parsing_guide.md
  why: Memory-efficient XML parsing with lxml, handles compressed sitemaps and indexes

# MUST READ - Modern CLI Packaging
- docfile: PRPs/ai_docs/modern_cli_packaging.md  
  why: Complete pyproject.toml setup, Typer CLI patterns, cross-platform packaging

# Essential External Documentation
- url: https://ptg.bczsalba.com/
  why: Official PyTermGUI documentation for widget usage and TIM markup
  
- url: https://typer.tiangolo.com/
  why: Modern CLI framework documentation for command structure

- url: https://lxml.de/parsing.html
  why: XML parsing performance patterns and memory management

- url: https://requests.readthedocs.io/en/latest/
  why: HTTP client best practices and session management
```

### Current Codebase Tree
```bash
crawl-url/
├── PRPs/
│   ├── README.md
│   ├── scripts/
│   │   └── prp_runner.py
│   ├── templates/
│   │   └── prp_base.md
│   └── ai_docs/
│       ├── pytermgui_guide.md
│       ├── web_crawling_patterns.md
│       ├── sitemap_parsing_guide.md
│       └── modern_cli_packaging.md
```

### Desired Codebase Tree with Files to be Added
```bash
crawl-url/
├── README.md                          # Installation and usage instructions
├── LICENSE                            # MIT license
├── pyproject.toml                     # Modern packaging configuration
├── .gitignore                         # Python gitignore
├── src/
│   └── crawl_url/                     # Main package (underscore not hyphen)
│       ├── __init__.py                # Package metadata and version
│       ├── cli.py                     # Main CLI entry point with Typer
│       ├── core/
│       │   ├── __init__.py
│       │   ├── crawler.py             # Web crawling service (requests+BeautifulSoup)
│       │   ├── sitemap_parser.py      # Sitemap XML parsing service (lxml)
│       │   └── ui.py                  # PyTermGUI interactive interface
│       └── utils/
│           ├── __init__.py
│           └── storage.py             # URL storage and file output utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration and fixtures
│   ├── test_cli.py                    # CLI command testing with Typer
│   ├── test_crawler.py                # Web crawling logic tests
│   ├── test_sitemap_parser.py         # Sitemap parsing tests
│   └── test_ui.py                     # UI component testing (mocked)
└── PRPs/                              # Keep existing PRP structure
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: PyTermGUI Windows compatibility issue
# PyTermGUI import may hang on Windows terminals until key pressed
# Solution: Implement fallback console mode and test thoroughly on Windows

# CRITICAL: lxml memory management for large sitemaps
# Use iterparse() and element.clear() to prevent memory bloat
# Pattern: Always clear processed elements in XML parsing loops

# CRITICAL: Cross-platform path handling
# Use pathlib.Path for all file operations, never os.path
# Ensure UTF-8 encoding is explicitly specified for file operations

# CRITICAL: Rate limiting for ethical crawling  
# Implement minimum 1-second delays between requests
# Check robots.txt compliance before crawling

# CRITICAL: URL normalization and deduplication
# Use urljoin() for relative URL resolution
# Implement hash-based deduplication for memory efficiency

# GOTCHA: Typer CLI argument vs option distinction
# Arguments are positional (URL), Options have --flags
# Use proper type hints for automatic validation

# GOTCHA: PyTermGUI terminal state management
# Always use context managers (with statements) for proper cleanup
# Implement graceful KeyboardInterrupt handling
```

## Implementation Blueprint

### Data Models and Structure

Core data models for type safety and consistency:

```python
# src/crawl_url/core/models.py
from dataclasses import dataclass
from typing import List, Optional, Union
from pathlib import Path

@dataclass
class CrawlConfig:
    """Configuration for crawling operations"""
    url: str
    mode: str  # 'sitemap' or 'crawl'
    max_depth: int = 3
    delay: float = 1.0
    filter_base: Optional[str] = None
    output_path: Optional[Path] = None
    output_format: str = 'txt'

@dataclass  
class CrawlResult:
    """Result of crawling operation"""
    success: bool
    urls: List[str]
    count: int
    message: str
    errors: List[str] = None

@dataclass
class SitemapEntry:
    """Sitemap URL entry"""
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[str] = None
```

### List of Tasks to be Completed in Order

```yaml
Task 1: "Setup Project Structure and Packaging"
CREATE pyproject.toml:
  - COPY pattern from: PRPs/ai_docs/modern_cli_packaging.md
  - MODIFY project name to "crawl-url" 
  - SET entry point: crawl-url = "crawl_url.cli:main"
  - INCLUDE dependencies: requests, beautifulsoup4, lxml, pytermgui, typer, rich

CREATE src/crawl_url/__init__.py:
  - SET __version__ = "1.0.0"
  - EXPORT main classes for package-level imports

CREATE .gitignore:
  - USE standard Python gitignore template
  - ADD common build and IDE directories

Task 2: "Implement Core Data Models" 
CREATE src/crawl_url/core/models.py:
  - DEFINE CrawlConfig, CrawlResult, SitemapEntry dataclasses
  - USE type hints for all fields
  - INCLUDE validation methods where needed

Task 3: "Implement Sitemap Parsing Service"
CREATE src/crawl_url/core/sitemap_parser.py:
  - MIRROR pattern from: PRPs/ai_docs/sitemap_parsing_guide.md
  - IMPLEMENT SitemapService class with iterparse() for memory efficiency
  - HANDLE compressed sitemaps (.gz files) 
  - SUPPORT sitemap indexes (recursive parsing)
  - INCLUDE robots.txt sitemap discovery
  - ADD URL filtering by base URL pattern

Task 4: "Implement Web Crawling Service"  
CREATE src/crawl_url/core/crawler.py:
  - MIRROR pattern from: PRPs/ai_docs/web_crawling_patterns.md
  - IMPLEMENT URLCrawler class with requests+BeautifulSoup
  - ADD recursive crawling with depth limits
  - INCLUDE rate limiting (1+ second delays)
  - IMPLEMENT robots.txt compliance checking
  - ADD URL deduplication with hash-based storage
  - SUPPORT progress callbacks for UI integration

Task 5: "Implement URL Storage Utilities"
CREATE src/crawl_url/utils/storage.py:
  - IMPLEMENT URLStorage class for file output
  - SUPPORT txt, json, csv output formats
  - AUTO-GENERATE filenames from domain + timestamp
  - USE pathlib.Path for cross-platform compatibility
  - EXPLICIT UTF-8 encoding for all file operations

Task 6: "Implement PyTermGUI Interactive Interface"
CREATE src/crawl_url/core/ui.py:
  - MIRROR pattern from: PRPs/ai_docs/pytermgui_guide.md  
  - IMPLEMENT CrawlerApp class with WindowManager
  - CREATE main configuration window with input fields
  - ADD progress display window for crawling operations
  - IMPLEMENT results display with scrollable container
  - INCLUDE error handling with graceful fallback to console mode
  - SUPPORT Windows compatibility testing

Task 7: "Implement Main CLI Entry Point"
CREATE src/crawl_url/cli.py:
  - MIRROR pattern from: PRPs/ai_docs/modern_cli_packaging.md
  - USE Typer for modern CLI with Rich output
  - IMPLEMENT two commands: 'interactive' and 'crawl'
  - ADD comprehensive argument validation and help text
  - INCLUDE progress reporting for non-interactive mode
  - SUPPORT both direct CLI usage and interactive TUI mode

Task 8: "Implement Comprehensive Testing"
CREATE tests/conftest.py:
  - SETUP pytest fixtures for test data and mocking
  - CREATE sample sitemap XML and HTML content
  - PROVIDE temporary file handling utilities

CREATE tests/test_sitemap_parser.py:
  - TEST XML parsing with sample sitemaps
  - VERIFY compressed sitemap handling
  - TEST sitemap index processing
  - VALIDATE URL filtering functionality

CREATE tests/test_crawler.py:
  - MOCK HTTP requests for reliable testing
  - TEST recursive crawling logic
  - VERIFY rate limiting implementation
  - TEST robots.txt compliance checking

CREATE tests/test_cli.py:
  - USE CliRunner from Typer for CLI testing
  - TEST both interactive and direct command modes
  - VERIFY argument parsing and validation
  - TEST output file generation

CREATE tests/test_ui.py:
  - MOCK PyTermGUI components to avoid TUI launch
  - TEST UI logic and state management
  - VERIFY error handling and fallback modes

Task 9: "Add Documentation and Polish"
CREATE README.md:
  - INCLUDE installation instructions (pip install crawl-url)
  - PROVIDE usage examples for both modes
  - ADD screenshots of terminal interface
  - DOCUMENT configuration options and filtering

CREATE LICENSE:
  - USE MIT license for open source distribution

ENHANCE error messages:
  - PROVIDE clear, actionable error messages
  - INCLUDE suggestions for common issues
  - ADD verbose mode for debugging

Task 10: "Cross-Platform Testing and Validation"
TEST Windows compatibility:
  - VERIFY PyTermGUI launches without hanging
  - TEST file path handling with pathlib
  - VALIDATE console encoding and output

TEST Linux compatibility:
  - VERIFY terminal compatibility across distributions
  - TEST package installation and entry point creation
  - VALIDATE permission handling and file operations
```

### Pseudocode for Critical Components

```python
# Task 3: Sitemap Parser Core Logic
class SitemapService:
    def process_sitemap_url(self, sitemap_url: str, filter_base: str = None) -> CrawlResult:
        # PATTERN: Use lxml iterparse for memory efficiency
        entries = []
        for event, element in etree.iterparse(sitemap_url, events=('start', 'end')):
            if event == 'end' and element.tag.endswith('url'):
                # EXTRACT URL from <loc> element
                url = self.extract_url_from_element(element)
                
                # FILTER by base URL if provided
                if not filter_base or url.startswith(filter_base):
                    entries.append(url)
                
                # CRITICAL: Clear element to prevent memory bloat
                element.clear()
                
        return CrawlResult(success=True, urls=entries, count=len(entries))

# Task 4: Web Crawler Core Logic  
class URLCrawler:
    def crawl_website(self, start_url: str, max_depth: int = 3) -> CrawlResult:
        visited = set()
        url_queue = deque([(start_url, 0)])  # (url, depth)
        all_urls = []
        
        while url_queue and len(all_urls) < 10000:  # Prevent infinite loops
            current_url, depth = url_queue.popleft()
            
            if current_url in visited or depth > max_depth:
                continue
                
            # CRITICAL: Rate limiting for ethical crawling
            time.sleep(self.delay)
            
            # CRITICAL: Check robots.txt compliance
            if not self.robots_checker.can_fetch(current_url):
                continue
                
            # EXTRACT URLs from page using BeautifulSoup
            page_urls = self.extract_urls_from_page(current_url)
            all_urls.extend(page_urls)
            visited.add(current_url)
            
            # ADD new URLs to queue for next depth level
            for url in page_urls[:50]:  # Limit to prevent explosion
                if url not in visited:
                    url_queue.append((url, depth + 1))
        
        return CrawlResult(success=True, urls=all_urls, count=len(all_urls))

# Task 6: PyTermGUI Interface Core Logic
class CrawlerApp:
    def create_main_window(self):
        # PATTERN: Use WindowManager context for proper cleanup
        return ptg.Window(
            ptg.Label("[bold]🕷️ Crawl-URL Application[/bold]", centered=True),
            "",
            ptg.InputField("https://", prompt="URL to crawl: "),
            ptg.InputField("auto", prompt="Mode (auto/sitemap/crawl): "),
            ptg.InputField("", prompt="Filter base URL (optional): "),
            "",
            ptg.Container(
                ptg.Button("Start Crawling", self.start_crawl),
                ptg.Button("View Results", self.show_results),
                ptg.Button("Quit", self.quit_app),
                box="EMPTY"
            ),
            width=70,
            box="DOUBLE"
        ).center()
    
    def run(self):
        # CRITICAL: Graceful error handling for Windows compatibility
        try:
            with ptg.WindowManager() as manager:
                manager.add(self.create_main_window())
                manager.run()
        except (ImportError, Exception) as e:
            print(f"TUI mode not available: {e}")
            self.run_console_fallback()

# Task 7: CLI Entry Point Core Logic
@app.command()
def crawl(
    url: str = typer.Argument(..., help="URL to crawl"),
    mode: str = typer.Option("auto", help="Crawling mode"),
    output: Optional[Path] = typer.Option(None, help="Output file"),
):
    # DETERMINE crawling mode based on URL and mode parameter
    if mode == "sitemap" or url.endswith('.xml'):
        service = SitemapService()
        result = service.process_sitemap_url(url)
    else:
        crawler = URLCrawler()
        result = crawler.crawl_website(url)
    
    # SAVE results to file with auto-generated name if needed
    if not output:
        output = generate_output_filename(url)
    
    save_results(result.urls, output, format="txt")
    console.print(f"[green]✅ Found {result.count} URLs, saved to {output}[/green]")
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# CRITICAL: Run these commands in project root before testing
# Install in development mode first
pip install -e .

# Lint and format code
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type checking
mypy src/crawl_url/

# Expected: No errors. If errors occur, read carefully and fix before proceeding.
```

### Level 2: Unit Tests

```python
# CREATE comprehensive test cases covering all components:

def test_sitemap_parsing():
    """Test sitemap XML parsing with sample data"""
    parser = SitemapService()
    # Use sample XML from fixtures
    result = parser.process_sitemap_url("sample_sitemap.xml")
    assert result.success
    assert len(result.urls) > 0

def test_web_crawling():
    """Test web crawling with mocked requests"""
    with mock.patch('requests.Session.get') as mock_get:
        mock_get.return_value.content = b"<html><a href='/page1'>Link</a></html>"
        crawler = URLCrawler()
        result = crawler.crawl_website("https://example.com")
        assert result.success

def test_cli_commands():
    """Test CLI argument parsing and execution"""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "crawl-url version" in result.stdout
```

```bash
# Run tests and iterate until all pass
pytest tests/ -v --cov=crawl_url --cov-report=html

# Expected: All tests pass with >80% coverage
# If failing: Read error messages, understand root cause, fix code, re-run
# NEVER mock just to make tests pass - fix the underlying issue
```

### Level 3: Integration Testing

```bash
# Test package installation and CLI access
pip install -e .

# Verify CLI command is available
crawl-url --version
# Expected: "crawl-url version 1.0.0"

# Test interactive mode (may require manual verification on different terminals)
crawl-url interactive
# Expected: PyTermGUI interface launches or graceful fallback message

# Test sitemap crawling with real URL
crawl-url crawl https://www.sitemaps.org/sitemap.xml --mode sitemap
# Expected: URLs extracted and saved to file

# Test website crawling with depth limit
crawl-url crawl https://example.com --mode crawl --depth 2 --delay 1.0
# Expected: Multiple URLs found and saved, with respectful rate limiting
```

### Level 4: Cross-Platform Validation

```bash
# Windows-specific testing (if on Windows)
# Test in Command Prompt, PowerShell, and Windows Terminal
crawl-url --help  # Should display help without hanging

# Linux-specific testing (if on Linux)  
# Test in various terminals (gnome-terminal, xterm, etc.)
crawl-url interactive  # Should launch TUI interface cleanly

# Both platforms: Test file operations
crawl-url crawl https://example.com/sitemap.xml
# Expected: Output file created in current directory with UTF-8 encoding
# Verify file can be opened and contains valid URLs
```

## Final Validation Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/crawl_url/`
- [ ] CLI command works: `crawl-url --version`
- [ ] Interactive mode launches: `crawl-url interactive`
- [ ] Sitemap mode works: `crawl-url crawl [sitemap-url] --mode sitemap`
- [ ] Crawl mode works: `crawl-url crawl [base-url] --mode crawl`
- [ ] Output files generated with correct content
- [ ] URL filtering works when base filter provided
- [ ] Cross-platform compatibility verified on target systems
- [ ] Error handling graceful with helpful messages
- [ ] Rate limiting respected (1+ second delays observed)
- [ ] Memory usage reasonable for large sitemaps/crawls

---

## Anti-Patterns to Avoid

- ❌ Don't use os.path - always use pathlib.Path for cross-platform compatibility
- ❌ Don't parse XML with BeautifulSoup - use lxml.etree for performance and memory efficiency
- ❌ Don't skip rate limiting - always implement respectful crawling delays
- ❌ Don't ignore robots.txt - implement proper compliance checking
- ❌ Don't hardcode file encodings - always specify UTF-8 explicitly
- ❌ Don't catch all exceptions broadly - be specific about error types
- ❌ Don't create new patterns when the documented patterns work
- ❌ Don't skip the TUI fallback - Windows compatibility requires graceful degradation
- ❌ Don't forget URL normalization - use urljoin() for relative URLs
- ❌ Don't ignore memory management - clear XML elements in parsing loops

## Confidence Level: 9/10

This PRP provides comprehensive context, clear implementation patterns, and thorough validation gates. The extensive research and documentation files give the AI agent everything needed for successful one-pass implementation. The only uncertainty is PyTermGUI's Windows compatibility behavior, but fallback patterns are well-documented.