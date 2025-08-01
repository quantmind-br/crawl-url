# crawl-url

A powerful Python CLI tool for extracting URLs from websites with intelligent mode switching and cross-platform support.

## ✨ Features

**🕷️ URL Discovery**: Extract URLs from websites using two specialized modes
- **Sitemap Mode**: Parse `sitemap.xml` files and sitemap indexes efficiently
- **Crawl Mode**: Recursive website crawling with configurable depth and rate limiting

**🖥️ Platform Support**: Works seamlessly across Windows, Linux, and macOS
- Automatic Windows console fallback (no PyTermGUI issues)
- Full PyTermGUI interface on Linux
- Unicode-safe terminal output everywhere

**⚙️ Configuration**: 
- CLI flags for quick one-liners
- Interactive TUI mode for guided usage
- Configurable rate limiting, depth limits, and URL filtering

## 🚀 Quick Start

### Installation
```bash
# Quick setup (Windows)
python setup.bat

# Quick setup (Unix/Linux/Mac)
./setup-advanced.bat

# Manual installation
pip install crawl-url

# From source
pip install -e ".[dev]"
```

### Basic Usage
```bash
# Extract URLs from any website
crawl-url crawl https://example.com

# Use sitemap mode (faster)
crawl-url crawl https://example.com --mode sitemap

# Customize depth and rate limiting
crawl-url crawl https://example.com --depth 5 --delay 1.0

# Save results
 crawl-url crawl https://example.com --format json > urls.json
```

## 📋 Commands

### CLI Mode
```bash
# Basic crawling
crawl-url crawl <URL> [OPTIONS]

# Interactive mode
crawl-url interactive

# Help and version
crawl-url --help
crawl-url --version
```

### CLI Options
```
--mode [auto|sitemap|crawl]     # Discovery mode (default: auto)
--depth INTEGER                 # Crawl depth 1-10 (default: 3)  
--delay FLOAT                   # Request delay in seconds (default: 1.0)
--format [txt|json|csv]         # Output format (default: txt)
--filter TEXT                   # Substring to filter URLs by
--user-agent TEXT              # Custom user agent string
--timeout INTEGER               # Request timeout in seconds
```

### Interactive Mode
For guided usage with prompts and progress indicators:
```bash
crawl-url interactive
```

## 🎯 Usage Examples

### Sitemap Extraction
```bash
# Extract from sitemap.xml
crawl-url crawl https://example.com --mode sitemap --format json

# Handle sitemap indexes automatically
crawl-url crawl https://example.com/sitemap_index.xml --mode sitemap
```

### Deep Crawling
```bash
# Crawl with depth customization
crawl-url crawl https://blog.example.com --depth 5 --delay 2.0

# Respect robots.txt while crawling
crawl-url crawl https://example.com --user-agent "crawl-url/1.0"
```

### URL Filtering
```bash
# Filter by domain or path
crawl-url crawl https://example.com --filter "/blog/"
crawl-url crawl https://example.com --filter ".pdf"
```

### Output Formats
```bash
# Plain text (default)
crawl-url crawl https://example.com > urls.txt

# JSON for programmatic use
crawl-url crawl https://example.com --format json | jq '.urls[]'

# CSV for spreadsheet analysis
crawl-url crawl https://example.com --format csv > urls.csv
```

## 🛠️ Development

### Setup Development Environment
```bash
# Clone repository
git clone <repository-url>
cd crawl-url

# Install development dependencies
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest                    # All tests
pytest -m unit           # Unit tests only
pytest -v                # Verbose output
pytest --cov-report=html # Coverage report
```

### Code Quality
```bash
# Format and lint
black src/ tests/
ruff check src/ tests/
mypy src/

# Run all quality checks
ruff check src/ tests/ && black --check src/ tests/ && mypy src/ && pytest

# Build package
python -m build
```

### Testing
This project uses pytest with comprehensive test coverage:
- **Unit tests**: Fast, isolated tests with mocks
- **Integration tests**: End-to-end CLI and API testing
- **Platform tests**: Cross-platform compatibility validation
- **Coverage**: HTML reports available in `htmlcov/`

Run test suites:
```bash
pytest -m unit          # 100ms fast tests
pytest -m integration   # End-to-end workflows  
pytest -m "not slow"    # Skip network tests
```

## 🏗️ Architecture

```
crawl-url/
├── src/crawl_url/
│   ├── cli.py              # Typer CLI registration
│   ├── core/
│   │   ├── models.py       # Config/result validation
│   │   ├── crawler.py      # HTTP crawling + rate limiting
│   │   ├── sitemap_parser.py  # XML parsing
│   │   └── ui.py           # PyTermGUI + console fallback
│   └── utils/
│       ├── storage.py      # File I/O (TXT/JSON/CSV)
│       └── validation.py   # URL filtering utilities
└── tests/
    ├── test_*.py          # Unit/integration tests
    └── conftest.py        # Test fixtures and mocks
```

## 🌍 Platform Compatibility

### Windows
- Automatic console mode (PyTermGUI fallback)
- PowerShell/CMD compatibility
- Unicode-safe terminal output

### Linux & Unix
- Full PyTermGUI interface with ncurses
- Rich terminal features and colors
- Bash/Zsh completion

### macOS
- Native terminal support
- Homebrew installation ready

## 📊 Performance

**Sitemap Mode**: O(n) - Direct XML parsing
**Crawl Mode**: O(n²) worst case (depth×links) with configured limits

**Tuning recommends:**
- `--depth 3` for average sites (≤1000 URLs)
- `--delay 1.0` to respect server resources
- `--timeout 30` for slower connections

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-mode`
3. Run quality checks: `ruff check src/ tests/ && black src/ tests/ && mypy src/ && pytest`
4. Submit pull request with clear commit messages

### Development Setup
```bash
# Install pre-commit hooks
pre-commit install

# Run validation test
python final_validation.py

# Package testing
pip install -e .
crawl-url --version
crawl-url crawl https://example.com --depth 1
crawl-url interactive  # Test TUI
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

**Permission Issues on Windows:**
```bash
# Use PowerShell as Administrator
python setup.bat
```

**Python Version Issues:**
- Requires Python 3.8+ (see pyproject.toml)
- Tested on Python 3.8-3.12

**Network Errors:**
- Check internet connectivity
- Verify robots.txt allows crawling
- Use longer `--timeout` for slow connections