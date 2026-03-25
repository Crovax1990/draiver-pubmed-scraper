"""Tests for pubmed_scraper.scraper module."""

import asyncio

import pytest
from unittest.mock import patch, MagicMock

from pubmed_scraper import scraper


@pytest.mark.asyncio
async def test_extract_by_article(sample_article_html, mock_aiohttp_session):
    """Test that article data is correctly extracted from HTML."""
    semaphore = asyncio.BoundedSemaphore(10)
    results = []

    await scraper.extract_by_article(
        "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        mock_aiohttp_session,
        semaphore,
        results,
    )

    assert len(results) == 1
    article = results[0]
    assert article["title"] == "Test Article Title"
    assert article["journal"] == "Test Journal"
    assert article["authors"] == "John Doe, Jane Smith, "
    assert "first paragraph" in article["abstract"]
    assert "second paragraph" in article["abstract"]
    assert article["date"] == "2023"
    assert isinstance(article["affiliations"], list)
    assert len(article["affiliations"]) == 2
    assert "University of Example" in article["affiliations"][0]
    assert "cancer" in article["keywords"]


@pytest.mark.asyncio
async def test_extract_by_article_missing_fields(
    sample_article_html_minimal,
    mock_aiohttp_session,
):
    """Test that missing fields return sentinel strings."""
    # Override mock to return minimal HTML
    from unittest.mock import AsyncMock

    response = AsyncMock()
    response.text = AsyncMock(return_value=sample_article_html_minimal)
    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=response)
    mock_get.__aexit__ = AsyncMock(return_value=False)
    mock_aiohttp_session.get.return_value = mock_get

    semaphore = asyncio.BoundedSemaphore(10)
    results = []

    await scraper.extract_by_article(
        "https://pubmed.ncbi.nlm.nih.gov/99999999/",
        mock_aiohttp_session,
        semaphore,
        results,
    )

    assert len(results) == 1
    article = results[0]
    assert article["title"] == "NO_TITLE"
    assert article["abstract"] == "NO_ABSTRACT"
    assert article["authors"] == "NO_AUTHOR"
    assert article["affiliations"] == "NO_AFFILIATIONS"
    assert article["keywords"] == "NO_KEYWORDS"
    assert article["journal"] == "NO_JOURNAL"
    assert article["date"] == "NO_DATE"


@pytest.mark.asyncio
async def test_get_pmids(sample_search_html, mock_aiohttp_session_search):
    """Test that PMIDs are extracted and URLs are built correctly."""
    urls = []
    semaphore = asyncio.BoundedSemaphore(100)

    await scraper.get_pmids(
        page=1,
        keyword="cancer",
        session=mock_aiohttp_session_search,
        semaphore=semaphore,
        urls=urls,
        start_year=2020,
        stop_year=2024,
    )

    assert len(urls) == 3
    assert "https://pubmed.ncbi.nlm.nih.gov/12345678" in urls
    assert "https://pubmed.ncbi.nlm.nih.gov/23456789" in urls
    assert "https://pubmed.ncbi.nlm.nih.gov/34567890" in urls


@patch("pubmed_scraper.scraper.requests.get")
def test_get_num_pages_with_arg(mock_get):
    """Test that max_pages overrides the HTTP request."""
    result = scraper.get_num_pages("cancer", max_pages=5)
    assert result == 5
    mock_get.assert_not_called()


@patch("pubmed_scraper.scraper.requests.get")
def test_get_num_pages_from_html(mock_get, sample_search_html):
    """Test that total pages is extracted from search results HTML."""
    mock_response = MagicMock()
    mock_response.text = sample_search_html
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_get.return_value = mock_response

    result = scraper.get_num_pages("cancer")
    assert result == 5


@pytest.mark.asyncio
async def test_get_article_data_deduplication(mock_aiohttp_session):
    """Test that already-scraped URLs are skipped."""
    semaphore = asyncio.BoundedSemaphore(10)
    results = []
    scraped = set()

    urls = ["https://pubmed.ncbi.nlm.nih.gov/12345678/"] * 3

    await scraper.get_article_data(
        urls, mock_aiohttp_session, semaphore, results, scraped
    )

    # Should only scrape once despite 3 duplicate URLs
    assert len(results) == 1
    assert len(scraped) == 1


def test_make_header():
    """Test that make_header returns a dict with User-Agent."""
    header = scraper.make_header()
    assert isinstance(header, dict)
    assert "User-Agent" in header
    assert len(header["User-Agent"]) > 0


def test_extract_title(sample_article_html):
    """Test title extraction directly."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_article_html, "lxml")
    assert scraper._extract_title(soup) == "Test Article Title"


def test_extract_abstract(sample_article_html):
    """Test abstract extraction directly."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_article_html, "lxml")
    abstract = scraper._extract_abstract(soup)
    assert "first paragraph" in abstract
    assert "second paragraph" in abstract


def test_extract_authors(sample_article_html):
    """Test authors extraction directly."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_article_html, "lxml")
    authors = scraper._extract_authors(soup)
    assert "John Doe" in authors
    assert "Jane Smith" in authors


def test_extract_missing_fields_return_sentinels(sample_article_html_minimal):
    """Test that extract helpers return sentinel strings on empty HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_article_html_minimal, "lxml")
    assert scraper._extract_title(soup) == "NO_TITLE"
    assert scraper._extract_abstract(soup) == "NO_ABSTRACT"
    assert scraper._extract_authors(soup) == "NO_AUTHOR"
    assert scraper._extract_journal(soup) == "NO_JOURNAL"
    assert scraper._extract_date(soup) == "NO_DATE"
    assert scraper._extract_keywords(soup) == "NO_KEYWORDS"
    assert scraper._extract_affiliations(soup) == "NO_AFFILIATIONS"
