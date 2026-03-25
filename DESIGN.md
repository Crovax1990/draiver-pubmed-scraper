# Design: Modernizzazione Async PubMed Scraper

## Understanding Summary

- **Cosa**: Modernizzare `async_pubmed_scraper.py` in un progetto `uv` Python 3.12 con package minimale, `--keywords` CLI, console_scripts e test
- **Perché**: Codice datato (2020), mancano test e gestione moderna delle dipendenze
- **Per chi**: Lo sviluppatore che mantiene/usa lo scraper
- **Vincoli chiave**:
  - `uv` come project manager
  - Python 3.12
  - `--keywords "a,b,c"` come alternativa a `keywords.txt`
  - Errore se nessuna sorgente keywords presente
  - Struttura: `pyproject.toml` + `src/pubmed_scraper/` + `tests/`
  - Aggiornare versioni librerie esistenti (no sostituzione)
  - Unit test con mock HTTP (pytest + pytest-asyncio)
  - Entry point: `uv run pubmed-scraper` (console_scripts)
- **Non-obiettivi**: No httpx, no moduli separati, no cambio formato output CSV

## Assumptions

- CLI resta retrocompatibile (`--pages`, `--start`, `--stop`, `--output`)
- Test con `pytest` + `unittest.mock` per HTTP
- `nest_asyncio` rimosso
- `asyncio.get_event_loop()` sostituito con `asyncio.run()`

## Decision Log

| # | Deciso | Alternative considerate | Motivo |
|---|--------|------------------------|--------|
| 1 | `uv` come project manager | pip, poetry, pdm | Richiesto dall'utente, gestione più moderna e veloce |
| 2 | Package minimale (`src/` + `tests/`) | Script singolo + tests, package completo con moduli | Bilancia semplicità e testabilità |
| 3 | `--keywords "a,b,c"` comma-separated | Argomenti ripetibili, JSON | Scelto dall'utente, più intuitivo |
| 4 | `--keywords` ha priorità su `--keywords-file` | Fallback silenzioso, merge | Comportamento prevedibile, esplicito |
| 5 | Errore se nessuna keyword disponibile | Default vuoto, warning | Evita esecuzioni inutili |
| 6 | Aggiornare versioni lib | Sostituire requests/httpx | Minore rischio, zero riscrittura logica |
| 7 | Eliminare globals, stato come parametri | Classe Scraper, context dict | Testabilità alta, cambi minimi |
| 8 | Argparse resta | click, typer | Zero dipendenze aggiuntive, già funziona |
| 9 | `asyncio.run()` | Mantenere `get_event_loop()` | Deprecato in Python 3.10+, `asyncio.run()` è lo standard |
| 10 | `hatchling` come build backend | setuptools, flit | Default di uv, zero config |
| 11 | Unit test con `pytest-asyncio` + mock | Solo sync test, integration test | Copre la logica async senza rete reale |
| 12 | `nest_asyncio` rimosso | Mantenere commentato | Non serve in CLI, rimuovi codice morto |

## Rischi chiave

- **Breaking change struttura**: l'utente che esegue `python async_pubmed_scraper.py` diretto dovrà usare `uv run pubmed-scraper` — mitigato da README aggiornato
- **PubMed HTML changes**: i selettori BeautifulSoup potrebbero rompersi se PubMed cambia markup — rischio preesistente, i test con HTML mock aiutano a rilevarlo
- **Compatibilità librerie aggiornate**: pandas 2.x ha breaking changes minori — il codice usa `DataFrame(lista_dict)` che è compatibile

---

## Final Design

### Struttura del Progetto

```
async-pubmed-scraper/
├── pyproject.toml
├── src/
│   └── pubmed_scraper/
│       ├── __init__.py
│       ├── scraper.py          # Logica di scraping refactorizzata
│       └── cli.py              # Entry point CLI, argparse, main()
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py         # Test scraping con mock HTTP
│   ├── test_cli.py             # Test CLI args, keywords resolution
│   └── conftest.py             # Fixtures condivise
├── keywords.txt                # (opzionale, retrocompatibile)
├── example/                    # (invariato)
├── README.md
├── AGENTS.md
└── .gitignore
```

### pyproject.toml

```toml
[project]
name = "async-pubmed-scraper"
version = "2.0.0"
description = "Asynchronous PubMed article scraper"
requires-python = ">=3.12"
dependencies = [
    "aiohttp>=3.11,<4",
    "beautifulsoup4>=4.12,<5",
    "lxml>=5.1,<6",
    "pandas>=2.2,<3",
    "requests>=2.32,<3",
    "numpy>=1.26,<3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pytest-asyncio>=0.24,<1",
]

[project.scripts]
pubmed-scraper = "pubmed_scraper.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pubmed_scraper"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Refactoring scraper.py

**Eliminazione globals** — lo stato viene passato come parametri:

```python
# PRIMA (globals)
global articles_data
articles_data.append(article_data)

# DOPO (stato esplicito)
async def extract_by_article(
    url: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    results: list[dict],
) -> None:
    ...
    results.append(article_data)
```

**Sessione condivisa** — creata una volta e passata a tutte le funzioni:

```python
async def get_article_data(
    urls: list[str],
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    results: list[dict],
    scraped: set[str],
) -> None:
    tasks = []
    for url in urls:
        if url not in scraped:
            task = asyncio.create_task(
                extract_by_article(url, session, semaphore, results)
            )
            tasks.append(task)
            scraped.add(url)
    await asyncio.gather(*tasks)
```

**Entry point con `asyncio.run()`**:

```python
# In cli.py main()
semaphore = asyncio.BoundedSemaphore(100)
results = []
async with aiohttp.ClientSession(headers=headers) as session:
    await build_article_urls(keywords, session, semaphore, urls)
    await get_article_data(urls, session, semaphore, results, set())
```

### CLI + Risoluzione Keywords

```python
# cli.py
def resolve_keywords(args) -> list[str]:
    if args.keywords:
        return [k.strip() for k in args.keywords.split(',') if k.strip()]
    if os.path.exists(args.keywords_file):
        with open(args.keywords_file) as f:
            return [line.strip() for line in f if line.strip()]
    sys.exit("Error: provide --keywords or ensure keywords.txt exists.")

def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--keywords', type=str, default=None,
                        help='Comma-separated keywords, e.g. "cancer,diabetes"')
    parser.add_argument('--keywords-file', type=str, default='keywords.txt',
                        help='Path to keywords file (default: keywords.txt)')
    # ... existing args (--pages, --start, --stop, --output)
    args = parser.parse_args()
    keywords = resolve_keywords(args)
    # ...
```

### Strategia di Testing

**Fixtures (`conftest.py`):**
- `sample_article_html` — HTML fittizio pagina PubMed con abstract, autori, keywords
- `sample_search_html` — HTML fittizio pagina risultati con PMIDs
- Mock `aiohttp.ClientSession` che restituisce HTML fittizio

**Test scraper (`test_scraper.py`):**
- `test_extract_by_article` — estrazione corretta di tutti i campi
- `test_extract_by_article_missing_fields` — gestione campi mancanti (sentinel strings)
- `test_get_pmids` — estrazione PMIDs e costruzione URL
- `test_get_num_pages_with_arg` — ritorna `args.pages` se specificato
- `test_get_num_pages_from_html` — estrae total-pages da HTML

**Test CLI (`test_cli.py`):**
- `test_resolve_keywords_from_flag` — `--keywords "a,b,c"` → `["a", "b", "c"]`
- `test_resolve_keywords_from_file` — lettura da file
- `test_resolve_keywords_error` — sys.exit se nessuna sorgente
- `test_output_csv_extension` — aggiunge `.csv` se mancante

## Comandi per sviluppo

```bash
# Inizializzazione
uv sync
uv sync --extra dev

# Esecuzione
uv run pubmed-scraper --keywords "cancer,diabetes" --pages 5 --start 2020 --stop 2024
uv run pubmed-scraper --keywords-file my_keywords.txt --pages 3

# Test
uv run pytest
uv run pytest tests/test_scraper.py::test_extract_by_article -v

# Lint (se si aggiunge ruff)
uv run ruff check .
uv run ruff format .
```
