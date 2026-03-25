# AGENTS.md

## Project Overview

Async PubMed Scraper — a Python package that asynchronously scrapes PubMed for
scholarly article metadata and saves results to CSV.
Uses `aiohttp` + `asyncio` + `BeautifulSoup` for concurrent HTTP scraping.
Managed with `uv` (Python 3.12+).

## Repository Structure

```
pyproject.toml                  # uv project config, deps, entry point
src/pubmed_scraper/
    __init__.py
    scraper.py                  # Scraping logic (stateless functions)
    cli.py                      # CLI entry point, argparse, keyword resolution
tests/
    __init__.py
    conftest.py                 # Shared fixtures (HTML mocks)
    test_scraper.py             # Tests for scraping functions
    test_cli.py                 # Tests for CLI and keyword resolution
keywords.txt                    # Optional: search keywords (one per line)
example/                        # Sample CSV output and CLI screenshots
async_pubmed_scraper.py         # Legacy original script (do not modify)
```

## Build / Run / Test Commands

### Install dependencies
```bash
uv sync              # production deps only
uv sync --extra dev  # + pytest, pytest-asyncio
```

### Run the scraper
```bash
# With inline keywords
uv run pubmed-scraper --keywords "cancer,diabetes" --pages 10 --start 2019 --stop 2020

# With keywords file
uv run pubmed-scraper --keywords-file my_keywords.txt --pages 10

# Help
uv run pubmed-scraper --help
```

### Run tests
```bash
uv run pytest                                           # all tests
uv run pytest tests/test_scraper.py -v                  # one file
uv run pytest tests/test_scraper.py::test_extract_by_article -v  # single test
```

### Lint/format (if ruff is added to dev deps)
```bash
uv run ruff check .
uv run ruff format .
```

## Code Style Guidelines

### Language and runtime
- Python 3.12+ (uses `list[str] | str` union syntax, f-strings, `asyncio.run()`)
- Type hints on function signatures (parameters and return types)
- No type checker (mypy/pyright) configured — rely on runtime and tests

### Imports
- Standard library first, then third-party, each group separated by blank line
- Use `from module import x` for frequently used items (e.g. `from bs4 import BeautifulSoup`)
- Module-level imports only — no lazy/conditional imports

### Async patterns
- `async def` / `await` for I/O-bound scraping functions
- `asyncio.create_task()` + `asyncio.gather()` for concurrent execution
- `asyncio.BoundedSemaphore(100)` to rate-limit requests
- `aiohttp.ClientSession` created once in `main()` and passed to all functions
- `requests` for synchronous one-off calls (e.g. `get_num_pages`)
- Use `asyncio.run()` — never `asyncio.get_event_loop()`

### Error handling
- Specific exceptions (`AttributeError`, `TypeError`, `IndexError`, `KeyError`) in scraper helpers
- Sentinel strings on failure: `'NO_ABSTRACT'`, `'NO_TITLE'`, `'NO_AUTHOR'`, etc.
- Missing fields on PubMed articles are normal, not errors
- `sys.exit()` with clear message for CLI input errors (missing keywords)

### State management
- **No globals** — all state passed as function parameters
- `results: list[dict]` accumulates article data, passed through call chain
- `scraped: set[str]` for URL deduplication
- `semaphore` passed explicitly to rate-limiting functions
- `session` (aiohttp.ClientSession) created once and shared

### Naming conventions
- Functions: `snake_case` (e.g., `extract_by_article`, `get_pmids`)
- Variables: `snake_case` (e.g., `article_data`, `search_keywords`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `USER_AGENTS`, `ROOT_PUBMED_URL`)
- Private helpers: `_extract_title`, `_extract_authors` (leading underscore)

### HTML parsing
- `BeautifulSoup` with `"lxml"` parser
- `soup.find()` / `soup.find_all()` with dict attribute selectors
- Extract helpers (`_extract_*`) keep parsing logic isolated and testable

### Output
- Accumulate data as `list[dict]`, convert to `pd.DataFrame` once at end
- Write CSV with `df.to_csv(filename)`

### General style
- Double quotes for strings (modern Python convention)
- Docstrings with `:param` and `:return` annotations
- Keep functions focused: one responsibility each
- Avoid unnecessary dependencies

## When Modifying This Codebase

1. **Keep it simple** — small package, not a framework. Don't over-engineer.
2. **Preserve async semantics** — scraping must stay async for performance.
3. **Run tests** — `uv run pytest` before committing any change.
4. **Respect rate limits** — `BoundedSemaphore(100)` avoids PubMed bans. Don't weaken it.
5. **Maintain backward compatibility** with CLI args (`--pages`, `--start`, `--stop`, `--output`).
6. **Update tests** when changing scraper functions or CLI behavior.
7. **Don't modify** `async_pubmed_scraper.py` (legacy original, kept for reference).
