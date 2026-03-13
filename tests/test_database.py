"""
Test suite per src/database.py

Copre i query helpers su DB in-memory (nessuna dipendenza su file):
  - article_exists
  - get_active_feeds
  - get_active_keywords
  - get_articles_by_date
"""

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.database import (
    article_exists,
    get_active_feeds,
    get_active_keywords,
    get_articles_by_date,
)
from src.models import Article, FeedSource, KeywordConfig

# ── Fixture DB in-memory ───────────────────────────────────────


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ── Helpers ────────────────────────────────────────────────────


def make_feed(name: str, active: bool = True, level: int = 2) -> FeedSource:
    return FeedSource(
        name=name,
        url=f"https://example.com/{name}.xml",
        level=level,
        category="tech",
        active=active,
    )


def make_keyword(word: str, cluster: str = "B", active: bool = True) -> KeywordConfig:
    return KeywordConfig(
        keyword=word,
        cluster=cluster,
        weight=1.5,
        active=active,
    )


def make_article(title: str, digest_date: date, article_id: str = None) -> Article:
    import hashlib

    aid = article_id or hashlib.sha256(title.encode()).hexdigest()
    return Article(
        id=aid,
        feed_source_id=1,
        feed_name="Test Feed",
        feed_level=2,
        title=title,
        url=f"https://example.com/{aid[:8]}",
        digest_date=digest_date,
        score=10.0,
        section="section1",
    )


# ── article_exists ─────────────────────────────────────────────


def test_article_exists_presente(session):
    a = make_article("Articolo esistente", date(2026, 3, 13))
    session.add(a)
    session.commit()
    assert article_exists(session, a.id) is True


def test_article_exists_assente(session):
    assert article_exists(session, "id-inesistente-xyz") is False


def test_article_exists_dopo_inserimento(session):
    """Verifica che article_exists sia False prima e True dopo."""
    a = make_article("Nuovo articolo", date(2026, 3, 13))
    assert article_exists(session, a.id) is False
    session.add(a)
    session.commit()
    assert article_exists(session, a.id) is True


# ── get_active_feeds ───────────────────────────────────────────


def test_get_active_feeds_solo_attivi(session):
    session.add(make_feed("Feed attivo A", active=True))
    session.add(make_feed("Feed attivo B", active=True))
    session.add(make_feed("Feed disattivato", active=False))
    session.commit()

    result = get_active_feeds(session)
    names = [f.name for f in result]
    assert "Feed attivo A" in names
    assert "Feed attivo B" in names
    assert "Feed disattivato" not in names


def test_get_active_feeds_nessuno(session):
    session.add(make_feed("Feed off", active=False))
    session.commit()
    result = get_active_feeds(session)
    assert result == []


def test_get_active_feeds_tutti_attivi(session):
    for i in range(5):
        session.add(make_feed(f"Feed {i}", active=True))
    session.commit()
    result = get_active_feeds(session)
    assert len(result) == 5


def test_get_active_feeds_db_vuoto(session):
    result = get_active_feeds(session)
    assert result == []


# ── get_active_keywords ────────────────────────────────────────


def test_get_active_keywords_solo_attive(session):
    session.add(make_keyword("startup", active=True))
    session.add(make_keyword("innovazione", active=True))
    session.add(make_keyword("obsoleta", active=False))
    session.commit()

    result = get_active_keywords(session)
    words = [k.keyword for k in result]
    assert "startup" in words
    assert "innovazione" in words
    assert "obsoleta" not in words


def test_get_active_keywords_nessuna(session):
    session.add(make_keyword("disattivata", active=False))
    session.commit()
    result = get_active_keywords(session)
    assert result == []


def test_get_active_keywords_db_vuoto(session):
    result = get_active_keywords(session)
    assert result == []


def test_get_active_keywords_cluster_diversi(session):
    session.add(make_keyword("calabria", cluster="A", active=True))
    session.add(make_keyword("startup", cluster="B", active=True))
    session.add(make_keyword("stem", cluster="C", active=True))
    session.commit()

    result = get_active_keywords(session)
    assert len(result) == 3
    clusters = {k.cluster for k in result}
    assert clusters == {"A", "B", "C"}


# ── get_articles_by_date ───────────────────────────────────────


def test_get_articles_by_date_filtra_per_data(session):
    today = date(2026, 3, 13)
    yesterday = date(2026, 3, 12)

    session.add(make_article("Articolo oggi", today))
    session.add(make_article("Articolo ieri", yesterday))
    session.commit()

    result = get_articles_by_date(session, today)
    titles = [a.title for a in result]
    assert "Articolo oggi" in titles
    assert "Articolo ieri" not in titles


def test_get_articles_by_date_nessun_risultato(session):
    result = get_articles_by_date(session, date(2026, 1, 1))
    assert result == []


def test_get_articles_by_date_multipli_stesso_giorno(session):
    today = date(2026, 3, 13)
    for i in range(4):
        session.add(make_article(f"Articolo {i}", today))
    session.commit()

    result = get_articles_by_date(session, today)
    assert len(result) == 4


def test_get_articles_by_date_non_mescola_date(session):
    """Tre date diverse → ogni query ritorna solo i propri articoli."""
    d1 = date(2026, 3, 11)
    d2 = date(2026, 3, 12)
    d3 = date(2026, 3, 13)

    session.add(make_article("Art d1", d1))
    session.add(make_article("Art d2", d2))
    session.add(make_article("Art d3", d3))
    session.commit()

    assert len(get_articles_by_date(session, d1)) == 1
    assert len(get_articles_by_date(session, d2)) == 1
    assert len(get_articles_by_date(session, d3)) == 1
