# CRUSH.md

Project cheat sheet for agentic coding in this repo.

Commands
- Setup: pip install -e ".[dev]"
- Test all: pytest
- Test single file: pytest tests/test_crawler.py -q
- Test single test: pytest tests/test_crawler.py::test_basic -q
- Coverage HTML: pytest --cov=crawl_url --cov-report=html
- Lint: ruff check src/ tests/
- Format check: black --check src/ tests/
- Format apply: black src/ tests/
- Typecheck: mypy src/
- Build: python -m build
- CLI help: crawl-url --help

Code style
- Python 3.8+, Black (88 cols), Ruff rules: E,W,F,I,B,C4,UP; ignore E501,B008; isort via Ruff; MyPy strict settings per pyproject.
- Imports: standard, third-party, local; no relative imports across packages; keep __all__ minimal; prefer from x import y over star.
- Types: mypy strict; no untyped defs; no implicit Optional; use TypedDict/Protocol/NamedTuple/Final where helpful.
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_CASE for constants; module-private with leading underscore.
- Errors: raise specific exceptions; avoid bare except; log with rich/typer context; never swallow exceptions silently.
- CLI: entrypoint crawl_url.cli:main via Typer; keep functions pure and testable; UI uses PyTermGUI with Windows console fallback.
- Tests: pytest, markers unit/integration/slow; prefer fixtures in tests/conftest.py; use -m to select.
- Storage: write outputs via utils.storage; avoid printing raw secrets; respect robots.txt in crawler.
- Performance: respect --delay rate limiting; avoid blocking I/O in tight loops; batch sitemap parsing when possible.

Notes
- Follow pyproject.toml for all tool configs; prefer Windows-safe paths; keep new commands here for future agents.
