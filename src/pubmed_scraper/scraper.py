"""
Async PubMed Scraper — scraping logic.

Extracts article metadata from PubMed search results asynchronously using
aiohttp + BeautifulSoup.
"""

import asyncio
import random

import aiohttp
import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
]

ROOT_PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov"


def make_header() -> dict:
    """Construct HTTP headers with a random user agent."""
    return {"User-Agent": random.choice(USER_AGENTS)}


async def extract_by_article(
    url: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    results: list[dict],
) -> None:
    """Extract all data from a single article.

    :param url: URL to a single PubMed article
    :param session: shared aiohttp session
    :param semaphore: concurrency limiter
    :param results: list to append article data dict to
    """
    async with semaphore, session.get(url) as response:
        data = await response.text()
        soup = BeautifulSoup(data, "lxml")

        abstract = _extract_abstract(soup)
        affiliations = _extract_affiliations(soup)
        keywords = _extract_keywords(soup)
        title = _extract_title(soup)
        authors = _extract_authors(soup)
        journal = _extract_journal(soup)
        date = _extract_date(soup)

        article_data = {
            "url": url,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "affiliations": affiliations,
            "journal": journal,
            "keywords": keywords,
            "date": date,
        }
        results.append(article_data)


def _extract_abstract(soup: BeautifulSoup) -> str:
    try:
        abstract_raw = soup.find(
            "div", {"class": "abstract-content selected"}
        ).find_all("p")
        return " ".join(p.text.strip() for p in abstract_raw)
    except (AttributeError, TypeError):
        return "NO_ABSTRACT"


def _extract_affiliations(soup: BeautifulSoup) -> list[str] | str:
    try:
        all_affiliations = soup.find("ul", {"class": "item-list"}).find_all("li")
        return [aff.get_text().strip() for aff in all_affiliations]
    except (AttributeError, TypeError):
        return "NO_AFFILIATIONS"


def _extract_keywords(soup: BeautifulSoup) -> str:
    try:
        has_keywords = soup.find_all("strong", {"class": "sub-title"})[-1].text.strip()
        if has_keywords == "Keywords:":
            kw = soup.find("div", {"class": "abstract"}).find_all("p")[-1].get_text()
            return kw.replace("Keywords:", "\n").strip()
        return "NO_KEYWORDS"
    except (AttributeError, TypeError, IndexError):
        return "NO_KEYWORDS"


def _extract_title(soup: BeautifulSoup) -> str:
    try:
        return soup.find("meta", {"name": "citation_title"})["content"].strip("[]")
    except (AttributeError, TypeError, KeyError):
        return "NO_TITLE"


def _extract_authors(soup: BeautifulSoup) -> str:
    try:
        authors = ""
        for author in soup.find("div", {"class": "authors-list"}).find_all(
            "a", {"class": "full-name"}
        ):
            authors += author.text + ", "
        return authors
    except (AttributeError, TypeError):
        return "NO_AUTHOR"


def _extract_journal(soup: BeautifulSoup) -> str:
    try:
        return soup.find("meta", {"name": "citation_journal_title"})["content"]
    except (AttributeError, TypeError, KeyError):
        return "NO_JOURNAL"


def _extract_date(soup: BeautifulSoup) -> str:
    try:
        return soup.find("time", {"class": "citation-year"}).text
    except (AttributeError, TypeError):
        return "NO_DATE"


def get_num_pages(keyword: str, max_pages: int | None = None) -> int:
    """Get total number of pages returned by search results for keyword.

    :param keyword: search keyword
    :param max_pages: if set, return this value instead of querying PubMed
    :return: number of result pages
    """
    if max_pages is not None:
        return max_pages

    headers = make_header()
    search_url = f"{ROOT_PUBMED_URL}/?term={keyword}"
    response = requests.get(search_url, headers=headers)
    data = response.text
    soup = BeautifulSoup(data, "lxml")
    total_pages_elem = soup.find("span", {"class": "total-pages"})
    if total_pages_elem is None:
        return 1
    num_pages = int(total_pages_elem.get_text().replace(",", ""))
    return num_pages


async def get_pmids(
    page: int,
    keyword: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    urls: list[str],
    start_year: int,
    stop_year: int,
) -> None:
    """Extract PMIDs from a single page of search results.

    :param page: current page number
    :param keyword: search keyword
    :param session: shared aiohttp session
    :param semaphore: concurrency limiter
    :param urls: list to append article URLs to
    :param start_year: start year for date range filter
    :param stop_year: stop year for date range filter
    """
    pubmed_url = f"{ROOT_PUBMED_URL}/?term={start_year}%3A{stop_year}%5Bdp%5D"
    page_url = f"{pubmed_url}+{keyword}+&page={page}"
    async with semaphore, session.get(page_url) as response:
        data = await response.text()
        soup = BeautifulSoup(data, "lxml")
        pmids = soup.find("meta", {"name": "log_displayeduids"})["content"]
        for pmid in pmids.split(","):
            url = f"{ROOT_PUBMED_URL}/{pmid}"
            urls.append(url)


async def build_article_urls(
    keywords: list[str],
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    urls: list[str],
    start_year: int,
    stop_year: int,
    max_pages: int | None = None,
) -> None:
    """Build list of article URLs for all keywords.

    :param keywords: list of search keywords
    :param session: shared aiohttp session
    :param semaphore: concurrency limiter
    :param urls: list to append article URLs to
    :param start_year: start year for date range
    :param stop_year: stop year for date range
    :param max_pages: optional limit on pages per keyword
    """
    tasks = []
    for keyword in keywords:
        num_pages = get_num_pages(keyword, max_pages)
        for page in range(1, num_pages + 1):
            task = asyncio.create_task(
                get_pmids(
                    page, keyword, session, semaphore, urls, start_year, stop_year
                )
            )
            tasks.append(task)

    await asyncio.gather(*tasks)


async def get_article_data(
    urls: list[str],
    session: aiohttp.ClientSession,
    semaphore: asyncio.BoundedSemaphore,
    results: list[dict],
    scraped: set[str],
) -> None:
    """Scrape data from each article URL.

    :param urls: list of PubMed article URLs
    :param session: shared aiohttp session
    :param semaphore: concurrency limiter
    :param results: list to append article data dicts to
    :param scraped: set of already-scraped URLs (deduplication)
    """
    tasks = []
    for url in urls:
        if url not in scraped:
            task = asyncio.create_task(
                extract_by_article(url, session, semaphore, results)
            )
            tasks.append(task)
            scraped.add(url)

    await asyncio.gather(*tasks)
