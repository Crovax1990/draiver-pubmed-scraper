# Asynchronous PubMed Scraper

## Quick Start

Requires [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Run with inline keywords
uv run pubmed-scraper --keywords "cancer,diabetes" --pages 5 --start 2020 --stop 2024

# Or with a keywords file (one keyword per line)
echo -e "cancer\ndiabetes" > keywords.txt
uv run pubmed-scraper --pages 5 --start 2020 --stop 2024
```

## Usage

```
uv run pubmed-scraper --help

options:
  --keywords "a,b,c"         Comma-separated keywords (alternative to keywords.txt)
  --keywords-file PATH       Path to keywords file (default: keywords.txt)
  --pages N                  Number of pages per keyword (10 articles/page, default: all)
  --start YEAR               Start year for date range (default: 2019)
  --stop YEAR                Stop year for date range (default: 2020)
  --output FILE              Output CSV filename (default: articles.csv)
```

At least one of `--keywords` or `keywords.txt` must be provided.

## Example Usage and Data

Collects at ~13 articles/second: url, title, abstract, authors, affiliations, journal, keywords, date.

![CLI usage example](https://raw.githubusercontent.com/IliaZenkov/async-pubmed-scraper/master/example/cli_usage_example.JPG)
![Data example](https://raw.githubusercontent.com/IliaZenkov/async-pubmed-scraper/master/example/data_example.JPG)

## What it does

This script asynchronously scrapes PubMed — an open-access database of scholarly research articles —
and saves the data to a pandas DataFrame which is then written to a CSV for further processing.

## Why scrape when there's an API? Why asynchronous?

PubMed's NCBI Entrez API allows only 3 requests/second (10/second with API key).
This scraper uses `asyncio` + `aiohttp` to send thousands of requests in parallel,
achieving ~10x speedup over synchronous scraping.

## Development

```bash
uv sync --extra dev

# Run tests
uv run pytest
uv run pytest tests/test_scraper.py::test_extract_by_article -v  # single test

# Lint (if ruff is added)
uv run ruff check .
uv run ruff format .
```

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/IliaZenkov/async-pubmed-scraper/blob/master/LICENSE)
