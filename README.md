# Draiver PubMed Scraper

Asynchronous Python tool that scrapes [PubMed](https://pubmed.ncbi.nlm.nih.gov/) for scholarly article metadata and saves results to CSV.

Built with `aiohttp`, `asyncio`, and `BeautifulSoup` for fast concurrent HTTP scraping.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
uv sync
uv sync --extra dev   # include pytest
```

## Usage

```bash
# Inline keywords
uv run pubmed-scraper --keywords "cancer,diabetes" --pages 10 --start 2019 --stop 2020

# Keywords from file
uv run pubmed-scraper --keywords-file my_keywords.txt --pages 10

# Custom output path
uv run pubmed-scraper --keywords "mRNA" --output results/vaccines.csv

# Help
uv run pubmed-scraper --help
```

Output is saved to `data/articles.csv` by default.

## CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--keywords` | — | Comma-separated search keywords |
| `--keywords-file` | `keywords.txt` | Path to file with one keyword per line |
| `--pages` | all | Number of pages to scrape per keyword (10 articles/page) |
| `--start` | 2019 | Start year for publication date range |
| `--stop` | 2020 | Stop year for publication date range |
| `--output` | `data/articles.csv` | Output CSV filename |

## Testing

```bash
uv run pytest
uv run pytest tests/test_scraper.py -v
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
