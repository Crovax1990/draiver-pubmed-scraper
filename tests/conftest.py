"""Shared test fixtures for pubmed_scraper tests."""

import pytest


@pytest.fixture
def sample_article_html() -> str:
    """HTML of a PubMed article page with all fields populated."""
    return """
    <html>
    <head>
        <meta name="citation_title" content="Test Article Title">
        <meta name="citation_journal_title" content="Test Journal">
    </head>
    <body>
        <div class="abstract-content selected">
            <p>This is the first paragraph of the abstract.</p>
            <p>This is the second paragraph of the abstract.</p>
        </div>
        <div class="authors-list">
            <a class="full-name">John Doe</a>
            <a class="full-name">Jane Smith</a>
        </div>
        <ul class="item-list">
            <li>University of Example, Department of Biology</li>
            <li>Example Research Institute</li>
        </ul>
        <div class="abstract">
            <strong class="sub-title">Background:</strong>
            <p>Some background text</p>
            <strong class="sub-title">Keywords:</strong>
            <p>Keywords:cancer, genomics, bioinformatics</p>
        </div>
        <time class="citation-year">2023</time>
    </body>
    </html>
    """


@pytest.fixture
def sample_article_html_minimal() -> str:
    """HTML of a PubMed article page with minimal/missing fields."""
    return """
    <html>
    <head></head>
    <body>
        <div class="content">
            <p>Just some content, no structured data.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_search_html() -> str:
    """HTML of a PubMed search results page with PMIDs."""
    return """
    <html>
    <head>
        <meta name="log_displayeduids" content="12345678,23456789,34567890">
    </head>
    <body>
        <span class="total-pages">5</span>
        <div class="search-results">
            <div class="docsum-content"><a href="/12345678">Article 1</a></div>
            <div class="docsum-content"><a href="/23456789">Article 2</a></div>
            <div class="docsum-content"><a href="/34567890">Article 3</a></div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_aiohttp_session(sample_article_html):
    """Create a mock aiohttp session that returns sample article HTML."""
    from unittest.mock import AsyncMock, MagicMock
    import contextlib

    session = MagicMock()

    # Mock response
    response = AsyncMock()
    response.text = AsyncMock(return_value=sample_article_html)

    # session.get() returns an async context manager
    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=response)
    mock_get.__aexit__ = AsyncMock(return_value=False)
    session.get.return_value = mock_get

    return session


@pytest.fixture
def mock_aiohttp_session_search(sample_search_html):
    """Create a mock aiohttp session that returns search results HTML."""
    from unittest.mock import AsyncMock, MagicMock

    session = MagicMock()

    response = AsyncMock()
    response.text = AsyncMock(return_value=sample_search_html)

    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=response)
    mock_get.__aexit__ = AsyncMock(return_value=False)
    session.get.return_value = mock_get

    return session
