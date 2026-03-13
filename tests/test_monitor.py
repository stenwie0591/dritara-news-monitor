"""
Test suite per src/monitor.py

Copre la funzione pura _get_low_yield_feeds (nessuna rete):
  - Feed con 0 rilevanti per LOW_YIELD_DAYS+ giorni → compare
  - Feed con almeno 1 rilevante → non compare
  - Feed con dati insufficienti (<LOW_YIELD_DAYS record) → non compare
  - Lista stats vuota → lista vuota
  - Ordinamento per n_days decrescente
"""

from datetime import date, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.models import FeedSource, FeedStats
from src.monitor import LOW_YIELD_DAYS, _get_low_yield_feeds

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


def make_feed(session: Session, name: str) -> FeedSource:
    feed = FeedSource(
        name=name,
        url=f"https://example.com/{name}.xml",
        level=2,
        category="tech",
        active=True,
    )
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def add_stats(
    session: Session,
    feed: FeedSource,
    today: date,
    days: int,
    relevant_per_day: int = 0,
    fetched_per_day: int = 5,
) -> None:
    """Aggiunge `days` record di FeedStats consecutivi fino a `today`."""
    for i in range(days):
        day = today - timedelta(days=days - 1 - i)
        session.add(
            FeedStats(
                feed_source_id=feed.id,
                feed_name=feed.name,
                fetch_date=day,
                articles_fetched=fetched_per_day,
                articles_relevant=relevant_per_day,
            )
        )
    session.commit()


TODAY = date(2026, 3, 13)


# ── Test principali ────────────────────────────────────────────


def test_feed_zero_rilevanti_compare(session):
    """Feed con 0 rilevanti per LOW_YIELD_DAYS giorni → presente nella lista."""
    feed = make_feed(session, "Feed silenzioso")
    add_stats(session, feed, TODAY, days=LOW_YIELD_DAYS, relevant_per_day=0)

    result = _get_low_yield_feeds(session, TODAY)
    names = [r[0] for r in result]
    assert "Feed silenzioso" in names


def test_feed_con_rilevanti_non_compare(session):
    """Feed con almeno 1 articolo rilevante in un giorno → non compare."""
    feed = make_feed(session, "Feed attivo")
    add_stats(session, feed, TODAY, days=LOW_YIELD_DAYS - 1, relevant_per_day=0)
    # Aggiunge un giorno con 1 rilevante
    session.add(
        FeedStats(
            feed_source_id=feed.id,
            feed_name=feed.name,
            fetch_date=TODAY,
            articles_fetched=5,
            articles_relevant=1,
        )
    )
    session.commit()

    result = _get_low_yield_feeds(session, TODAY)
    names = [r[0] for r in result]
    assert "Feed attivo" not in names


def test_feed_dati_insufficienti_non_compare(session):
    """Feed con meno di LOW_YIELD_DAYS record → non compare (dati insufficienti)."""
    feed = make_feed(session, "Feed recente")
    add_stats(session, feed, TODAY, days=LOW_YIELD_DAYS - 1, relevant_per_day=0)

    result = _get_low_yield_feeds(session, TODAY)
    names = [r[0] for r in result]
    assert "Feed recente" not in names


def test_nessuna_stats_ritorna_lista_vuota(session):
    """Nessun record FeedStats → lista vuota."""
    result = _get_low_yield_feeds(session, TODAY)
    assert result == []


def test_struttura_tupla_corretta(session):
    """Ogni elemento ritornato è (feed_name, n_days, avg_fetched)."""
    feed = make_feed(session, "Feed struttura")
    add_stats(
        session, feed, TODAY, days=LOW_YIELD_DAYS, relevant_per_day=0, fetched_per_day=8
    )

    result = _get_low_yield_feeds(session, TODAY)
    assert len(result) == 1
    fname, n_days, avg_fetched = result[0]
    assert fname == "Feed struttura"
    assert n_days == LOW_YIELD_DAYS
    assert avg_fetched == 8.0


def test_avg_fetched_calcolato_correttamente(session):
    """avg_fetched è la media degli articoli fetchati nei giorni di osservazione."""
    feed = make_feed(session, "Feed media")
    # 3 giorni con 10, 20, 30 articoli fetchati
    for i, fetched in enumerate([10, 20, 30]):
        day = TODAY - timedelta(days=LOW_YIELD_DAYS - 1 - i)
        session.add(
            FeedStats(
                feed_source_id=feed.id,
                feed_name=feed.name,
                fetch_date=day,
                articles_fetched=fetched,
                articles_relevant=0,
            )
        )
    session.commit()

    result = _get_low_yield_feeds(session, TODAY)
    assert len(result) == 1
    _, _, avg = result[0]
    assert avg == 20.0


def test_ordinamento_per_n_days_decrescente(session):
    """Feed con più giorni di silenzio appare prima."""
    feed_lungo = make_feed(session, "Feed lungo silenzio")
    feed_corto = make_feed(session, "Feed corto silenzio")

    add_stats(session, feed_lungo, TODAY, days=LOW_YIELD_DAYS + 2, relevant_per_day=0)
    add_stats(session, feed_corto, TODAY, days=LOW_YIELD_DAYS, relevant_per_day=0)

    result = _get_low_yield_feeds(session, TODAY)
    assert result[0][0] == "Feed lungo silenzio"
    assert result[1][0] == "Feed corto silenzio"


def test_feed_multipli_misti(session):
    """Solo i feed con 0 rilevanti per tutti i giorni compaiono."""
    feed_ok = make_feed(session, "Feed ok")
    feed_ko = make_feed(session, "Feed ko")

    add_stats(session, feed_ok, TODAY, days=LOW_YIELD_DAYS, relevant_per_day=2)
    add_stats(session, feed_ko, TODAY, days=LOW_YIELD_DAYS, relevant_per_day=0)

    result = _get_low_yield_feeds(session, TODAY)
    names = [r[0] for r in result]
    assert "Feed ko" in names
    assert "Feed ok" not in names
