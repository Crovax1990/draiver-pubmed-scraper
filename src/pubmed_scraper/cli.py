"""
Async PubMed Scraper — CLI entry point.

Handles argument parsing, keyword resolution, and orchestrates the scraping pipeline.
"""

import argparse
import asyncio
import os
import socket
import sys
import time

import aiohttp
import pandas as pd

from pubmed_scraper import scraper


def resolve_keywords(args: argparse.Namespace) -> list[str]:
    """Resolve keywords from --keywords flag or keywords file.

    :param args: parsed CLI arguments
    :return: list of keyword strings
    :raises SystemExit: if no keyword source is available
    """
    if args.keywords:
        return [k.strip() for k in args.keywords.split(",") if k.strip()]

    if os.path.exists(args.keywords_file):
        with open(args.keywords_file) as f:
            return [line.strip() for line in f if line.strip()]

    sys.exit(
        f"Error: no keywords provided. Use --keywords 'a,b,c' or ensure "
        f"'{args.keywords_file}' exists."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asynchronous PubMed Scraper")
    parser.add_argument(
        "--keywords",
        type=str,
        default=None,
        help='Comma-separated keywords, e.g. "cancer,diabetes"',
    )
    parser.add_argument(
        "--keywords-file",
        type=str,
        default="keywords.txt",
        help="Path to keywords file (one per line). Default: keywords.txt",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="Number of pages to scrape per keyword (10 articles/page). Default: all",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=2019,
        help="Start year for publication date range. Default: 2019",
    )
    parser.add_argument(
        "--stop",
        type=int,
        default=2020,
        help="Stop year for publication date range. Default: 2020",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="articles.csv",
        help='Output CSV filename. Default: "articles.csv"',
    )
    return parser


async def run_scraper(args: argparse.Namespace, keywords: list[str]) -> None:
    """Execute the async scraping pipeline.

    :param args: parsed CLI arguments
    :param keywords: list of resolved keywords
    """
    start_time = time.time()

    if not args.output.endswith(".csv"):
        args.output += ".csv"

    semaphore = asyncio.BoundedSemaphore(100)
    articles_data: list[dict] = []
    urls: list[str] = []
    scraped_urls: set[str] = set()

    headers = scraper.make_header()
    connector = aiohttp.TCPConnector(family=socket.AF_INET)

    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        print(f"\nFinding PubMed article URLs for {len(keywords)} keyword(s)\n")

        await scraper.build_article_urls(
            keywords, session, semaphore, urls, args.start, args.stop, args.pages
        )

        print(
            f"Scraping initiated for {len(urls)} article URLs "
            f"from {args.start} to {args.stop}\n"
        )

        await scraper.get_article_data(
            urls, session, semaphore, articles_data, scraped_urls
        )

    columns = [
        "title",
        "abstract",
        "affiliations",
        "authors",
        "journal",
        "date",
        "keywords",
        "url",
    ]
    articles_df = pd.DataFrame(articles_data, columns=columns)

    print("Preview of scraped article data:\n")
    print(articles_df.head(5))

    articles_df.to_csv(args.output)
    elapsed = time.time() - start_time
    print(
        f"\nIt took {elapsed:.1f} seconds to find {len(urls)} articles; "
        f"{len(scraped_urls)} unique articles were saved to {args.output}"
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    keywords = resolve_keywords(args)
    asyncio.run(run_scraper(args, keywords))


if __name__ == "__main__":
    main()
