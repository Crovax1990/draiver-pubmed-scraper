"""Tests for pubmed_scraper.cli module."""

import os
import tempfile

import pytest

from pubmed_scraper.cli import build_parser, resolve_keywords


class TestResolveKeywords:
    """Tests for keyword resolution logic."""

    def test_from_flag(self):
        """--keywords flag takes priority."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", "cancer,diabetes,alzheimer"])
        keywords = resolve_keywords(args)
        assert keywords == ["cancer", "diabetes", "alzheimer"]

    def test_from_flag_strips_whitespace(self):
        """Whitespace around comma-separated keywords is stripped."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", " cancer , diabetes , "])
        keywords = resolve_keywords(args)
        assert keywords == ["cancer", "diabetes"]

    def test_from_flag_single_keyword(self):
        """Single keyword without commas works."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", "cancer"])
        keywords = resolve_keywords(args)
        assert keywords == ["cancer"]

    def test_from_file(self, tmp_path):
        """Keywords are read from file when --keywords not provided."""
        kw_file = tmp_path / "keywords.txt"
        kw_file.write_text("cancer\ndiabetes\nalzheimer\n")

        parser = build_parser()
        args = parser.parse_args(["--keywords-file", str(kw_file)])
        keywords = resolve_keywords(args)
        assert keywords == ["cancer", "diabetes", "alzheimer"]

    def test_from_file_skips_blank_lines(self, tmp_path):
        """Blank lines in keywords file are skipped."""
        kw_file = tmp_path / "keywords.txt"
        kw_file.write_text("cancer\n\ndiabetes\n  \nalzheimer\n")

        parser = build_parser()
        args = parser.parse_args(["--keywords-file", str(kw_file)])
        keywords = resolve_keywords(args)
        assert keywords == ["cancer", "diabetes", "alzheimer"]

    def test_flag_takes_priority_over_file(self, tmp_path):
        """--keywords flag takes priority over keywords file."""
        kw_file = tmp_path / "keywords.txt"
        kw_file.write_text("from_file\n")

        parser = build_parser()
        args = parser.parse_args(
            ["--keywords", "from_flag", "--keywords-file", str(kw_file)]
        )
        keywords = resolve_keywords(args)
        assert keywords == ["from_flag"]

    def test_error_when_no_source(self, tmp_path):
        """SystemExit when no keywords source is available."""
        nonexistent = tmp_path / "does_not_exist.txt"

        parser = build_parser()
        args = parser.parse_args(["--keywords-file", str(nonexistent)])

        with pytest.raises(SystemExit):
            resolve_keywords(args)


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_defaults(self):
        """Default values for all arguments."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", "test"])
        assert args.keywords == "test"
        assert args.keywords_file == "keywords.txt"
        assert args.pages is None
        assert args.start == 2019
        assert args.stop == 2020
        assert args.output == "data/articles.csv"

    def test_pages_is_int(self):
        """--pages accepts an integer."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", "test", "--pages", "10"])
        assert args.pages == 10

    def test_output_csv_extension(self):
        """Output filename handling (tested in integration, just verify arg parsing)."""
        parser = build_parser()
        args = parser.parse_args(["--keywords", "test", "--output", "my_data.csv"])
        assert args.output == "my_data.csv"

    def test_date_range(self):
        """--start and --stop accept integers."""
        parser = build_parser()
        args = parser.parse_args(
            ["--keywords", "test", "--start", "2018", "--stop", "2024"]
        )
        assert args.start == 2018
        assert args.stop == 2024
