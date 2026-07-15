"""
Test suite per src/fetcher.py

Copre le funzioni helper pure (nessuna rete, nessun DB):
  - _clean: normalizzazione testo
  - _strip_html: rimozione tag HTML e entities
  - _extract_excerpt: priorità summary > description > content
  - _parse_date: estrazione data da entry RSS
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from src.fetcher import (
    MAX_ARTICLE_URL_CHARS,
    MAX_ENTRIES_PER_FEED,
    MAX_TITLE_CHARS,
    _clean,
    _extract_excerpt,
    _parse_date,
    _strip_html,
    fetch_feed,
)
from src.models import FeedSource

# ── _clean ─────────────────────────────────────────────────────


def test_clean_spazi_multipli():
    assert _clean("testo   con   spazi") == "testo con spazi"


def test_clean_newline_e_tab():
    assert _clean("testo\ncon\ttab") == "testo con tab"


def test_clean_strip_bordi():
    assert _clean("  testo  ") == "testo"


def test_clean_stringa_vuota():
    assert _clean("") == ""


def test_clean_testo_normale():
    assert _clean("Hub digitale a Cosenza") == "Hub digitale a Cosenza"


# ── _strip_html ────────────────────────────────────────────────


def test_strip_html_tag_semplici():
    assert _strip_html("<p>Testo</p>") == "Testo"


def test_strip_html_tag_multipli():
    result = _strip_html("<h1>Titolo</h1><p>Paragrafo</p>")
    assert "Titolo" in result
    assert "Paragrafo" in result
    assert "<" not in result


def test_strip_html_entities():
    result = _strip_html("Testo &amp; altro &nbsp; contenuto")
    assert "&amp;" not in result
    assert "&nbsp;" not in result


def test_strip_html_tag_con_attributi():
    result = _strip_html('<a href="https://example.com">Link</a>')
    assert "Link" in result
    assert "<a" not in result
    assert "href" not in result


def test_strip_html_testo_pulito():
    """Testo senza HTML rimane invariato."""
    result = _strip_html("Testo già pulito")
    assert result == "Testo già pulito"


def test_strip_html_stringa_vuota():
    assert _strip_html("") == ""


# ── _extract_excerpt ───────────────────────────────────────────


def test_extract_excerpt_da_summary():
    """Priorità 1: usa summary se disponibile."""
    entry = SimpleNamespace(
        summary="Testo dal summary",
        description="Testo dalla description",
    )
    result = _extract_excerpt(entry)
    assert result == "Testo dal summary"


def test_extract_excerpt_da_description_se_no_summary():
    """Priorità 2: usa description se summary assente."""
    entry = SimpleNamespace(
        summary="",
        description="Testo dalla description",
    )
    result = _extract_excerpt(entry)
    assert result == "Testo dalla description"


def test_extract_excerpt_da_content():
    """Priorità 3: usa content se summary e description assenti."""
    entry = SimpleNamespace(
        summary="",
        description="",
        content=[{"value": "Testo dal content"}],
    )
    result = _extract_excerpt(entry)
    assert result == "Testo dal content"


def test_extract_excerpt_nessuna_fonte():
    """Nessuna fonte disponibile → None."""
    entry = SimpleNamespace(summary="", description="")
    result = _extract_excerpt(entry)
    assert result is None


def test_extract_excerpt_troncato_a_500():
    """Excerpt lungo viene troncato a 500 chars."""
    entry = SimpleNamespace(
        summary="Parola " * 200,  # ~1400 chars
        description="",
    )
    result = _extract_excerpt(entry)
    assert result is not None
    assert len(result) <= 500


def test_extract_excerpt_strip_html_da_summary():
    """HTML nel summary viene rimosso."""
    entry = SimpleNamespace(
        summary="<p>Testo <b>importante</b></p>",
        description="",
    )
    result = _extract_excerpt(entry)
    assert "<p>" not in result
    assert "Testo" in result
    assert "importante" in result


# ── _parse_date ────────────────────────────────────────────────


def test_parse_date_da_published_parsed():
    """Data da published_parsed → datetime corretto."""
    entry = SimpleNamespace(
        published_parsed=(2026, 3, 13, 10, 30, 0, 4, 72, 0),
        updated_parsed=None,
    )
    result = _parse_date(entry)
    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 13


def test_parse_date_da_updated_parsed_se_no_published():
    """Fallback su updated_parsed se published_parsed assente."""
    entry = SimpleNamespace(
        published_parsed=None,
        updated_parsed=(2026, 3, 10, 8, 0, 0, 1, 69, 0),
    )
    result = _parse_date(entry)
    assert isinstance(result, datetime)
    assert result.day == 10


def test_parse_date_nessuna_data():
    """Nessun attributo data → None."""
    entry = SimpleNamespace(
        published_parsed=None,
        updated_parsed=None,
    )
    result = _parse_date(entry)
    assert result is None


def test_parse_date_attributo_assente():
    """Entry senza attributi data → None senza eccezioni."""
    entry = SimpleNamespace()
    result = _parse_date(entry)
    assert result is None


def test_parse_date_data_malformata():
    """Data malformata → None senza eccezioni."""
    entry = SimpleNamespace(
        published_parsed=(9999, 99, 99, 99, 99, 99),  # valori impossibili
        updated_parsed=None,
    )
    result = _parse_date(entry)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_feed_applies_entry_and_field_limits(monkeypatch) -> None:
    long_title = "T" * (MAX_TITLE_CHARS + 100)
    long_url = "https://example.com/" + "x" * MAX_ARTICLE_URL_CHARS
    items = [
        f"<item><title>{long_title}</title><link>https://example.com/ok</link></item>",
        f"<item><title>URL troppo lungo</title><link>{long_url}</link></item>",
    ] + [
        f"<item><title>Articolo {index}</title><link>https://example.com/{index}</link></item>"
        for index in range(MAX_ENTRIES_PER_FEED + 10)
    ]
    body = ("<rss><channel>" + "".join(items) + "</channel></rss>").encode()
    response = httpx.Response(
        200,
        content=body,
        request=httpx.Request("GET", "https://example.com/rss"),
    )
    monkeypatch.setattr(
        "src.fetcher.get_public_feed", AsyncMock(return_value=response)
    )
    source = FeedSource(
        id=1,
        name="Test",
        url="https://example.com/rss",
        level=2,
        category="tech",
        active=True,
    )

    _, articles, error = await fetch_feed(AsyncMock(), source)

    assert error is None
    assert len(articles) == MAX_ENTRIES_PER_FEED - 1
    assert len(articles[0]["title"]) == MAX_TITLE_CHARS
    assert all(len(article["url"]) <= MAX_ARTICLE_URL_CHARS for article in articles)
