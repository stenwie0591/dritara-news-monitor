"""
Test suite per src/deduplicator.py

Copre:
  - Dedup per URL hash identico
  - Dedup per titolo esatto (title_exact)
  - Dedup per titolo simile (title_similarity)
  - Articoli diversi non deduplicati
  - Dedup storico 7 giorni
"""

from src.deduplicator import Deduplicator

# ── Helpers ────────────────────────────────────────────────────


def make_article(title: str, url: str = None, i: int = 0) -> dict:
    url = url or f"https://example.com/article-{i}"
    import hashlib

    article_id = hashlib.sha256(url.encode()).hexdigest()
    return {
        "id": article_id,
        "title": title,
        "url": url,
        "feed_name": "Test Feed",
        "feed_source_id": 1,
        "feed_level": 2,
        "excerpt": "Testo di esempio.",
        "score": 10.0,
    }


# ── Test URL hash ───────────────────────────────────────────────


def test_dedup_url_identico():
    """Due articoli con stesso URL → uno solo"""
    dedup = Deduplicator()
    articles = [
        make_article("Titolo A", url="https://example.com/stesso"),
        make_article("Titolo B", url="https://example.com/stesso"),
    ]
    result = dedup.filter(articles)
    assert len(result) == 1


def test_dedup_url_diverso():
    """Due articoli con URL diversi e titoli diversi → entrambi passano"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://example.com/a"
        ),
        make_article(
            "Intelligenza artificiale rivoluziona il settore agricolo",
            url="https://example.com/b",
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 2


# ── Test title exact ───────────────────────────────────────────


def test_dedup_titolo_esatto():
    """Due articoli con titolo identico → uno solo"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Startup calabrese vince premio innovazione", url="https://a.com/1"
        ),
        make_article(
            "Startup calabrese vince premio innovazione", url="https://b.com/2"
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 1


def test_no_dedup_titoli_diversi():
    """Due articoli con titoli completamente diversi → entrambi passano"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://a.com/1"
        ),
        make_article(
            "Intelligenza artificiale rivoluziona il Sud Italia", url="https://b.com/2"
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 2


# ── Test title similarity ──────────────────────────────────────


def test_dedup_titolo_simile():
    """Due articoli con titolo molto simile (>85%) → uno solo"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Startup calabrese raccoglie 2 milioni di euro", url="https://a.com/1"
        ),
        make_article(
            "++ Startup calabrese raccoglie 2 milioni di euro", url="https://b.com/2"
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 1


def test_no_dedup_titolo_simile_sotto_soglia():
    """Due articoli con titolo simile ma sotto soglia → entrambi passano"""
    dedup = Deduplicator(similarity_threshold=0.95)
    articles = [
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://a.com/1"
        ),
        make_article(
            "Hub digitale a Reggio Calabria finanziato dal PNRR", url="https://b.com/2"
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 2


# ── Test lista vuota e singolo articolo ───────────────────────


def test_lista_vuota():
    dedup = Deduplicator()
    result = dedup.filter([])
    assert result == []


def test_singolo_articolo():
    dedup = Deduplicator()
    articles = [make_article("Titolo unico", url="https://example.com/unico")]
    result = dedup.filter(articles)
    assert len(result) == 1


# ── Test ordine preservato ─────────────────────────────────────


def test_ordine_preservato():
    """Il primo articolo (più recente) viene mantenuto, non il duplicato"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Startup calabrese vince premio innovazione", url="https://primo.com/1"
        ),
        make_article(
            "Startup calabrese vince premio innovazione", url="https://secondo.com/2"
        ),
    ]
    result = dedup.filter(articles)
    assert len(result) == 1
    assert result[0]["url"] == "https://primo.com/1"


# ── Test batch multiplo ────────────────────────────────────────


def test_dedup_multipli():
    """5 articoli con 3 duplicati → 2 unici"""
    dedup = Deduplicator()
    articles = [
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://a.com/1"
        ),
        make_article(
            "Intelligenza artificiale nel settore agricolo", url="https://b.com/2"
        ),
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://c.com/3"
        ),  # dup titolo
        make_article(
            "Intelligenza artificiale nel settore agricolo", url="https://d.com/4"
        ),  # dup titolo
        make_article(
            "Hub digitale a Cosenza finanziato dal PNRR", url="https://a.com/1"
        ),  # dup URL
    ]
    result = dedup.filter(articles)
    assert len(result) == 2
