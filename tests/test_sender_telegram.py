"""
Test suite per src/sender_telegram.py

Copre le funzioni sync della coda pubblicazione (nessuna rete):
  - approve_articles: approvazione, assegnazione orari, deferral, discard dopo MAX_DEFERRALS
  - discard_articles: scarto manuale per posizione
  - get_next_to_publish: articolo corretto per ora e data
  - mark_published / mark_publishing: transizioni di stato
"""

import hashlib
from datetime import date
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import Article, FeedSource, PublishQueue
from src.sender_telegram import (
    MAX_DAILY,
    MAX_DEFERRALS,
    PUBLISH_HOURS,
    approve_articles,
    discard_articles,
    get_next_to_publish,
    mark_published,
    mark_publishing,
)

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


# ── Helper: patch get_session per usare il DB in-memory ────────


def patch_session(session):
    """Sostituisce get_session con la sessione in-memory del test."""
    return patch("src.sender_telegram.get_session", return_value=iter([session]))


# ── Helpers ────────────────────────────────────────────────────


def make_article(session: Session, title: str, feed_name: str = "Test Feed") -> Article:
    aid = hashlib.sha256(title.encode()).hexdigest()
    # Feed source richiesto da FK
    feed = session.get(FeedSource, 1)
    if not feed:
        feed = FeedSource(
            id=1,
            name="Test Feed",
            url="https://example.com/feed.xml",
            level=2,
            category="tech",
            active=True,
        )
        session.add(feed)
        session.commit()

    a = Article(
        id=aid,
        feed_source_id=1,
        feed_name=feed_name,
        feed_level=2,
        title=title,
        url=f"https://example.com/{aid[:8]}",
        digest_date=date(2026, 3, 13),
        score=10.0,
        section="section1",
    )
    session.add(a)
    session.commit()
    return a


def make_queue(
    session: Session,
    article: Article,
    position: int,
    digest_date: date = date(2026, 3, 13),
    status: str = "pending",
    deferred_count: int = 0,
) -> PublishQueue:
    q = PublishQueue(
        article_id=article.id,
        digest_date=digest_date,
        position=position,
        status=status,
        deferred_count=deferred_count,
    )
    session.add(q)
    session.commit()
    return q


# ── approve_articles ───────────────────────────────────────────


def test_approve_articles_stato_approvato(session):
    """Le posizioni indicate diventano 'approved'."""
    a1 = make_article(session, "Articolo 1")
    a2 = make_article(session, "Articolo 2")
    make_queue(session, a1, position=1)
    make_queue(session, a2, position=2)

    with patch_session(session):
        approved = approve_articles([1], date(2026, 3, 13))

    assert approved == 1
    q = session.exec(select(PublishQueue).where(PublishQueue.position == 1)).first()
    assert q.status == "approved"


def test_approve_articles_assegna_orario(session):
    """Articolo approvato riceve l'orario corretto da PUBLISH_HOURS."""
    a1 = make_article(session, "Articolo orario")
    make_queue(session, a1, position=1)

    with patch_session(session):
        approve_articles([1], date(2026, 3, 13))

    q = session.exec(select(PublishQueue).where(PublishQueue.position == 1)).first()
    assert q.scheduled_hour == PUBLISH_HOURS[0]


def test_approve_articles_resto_diventa_deferred(session):
    """Articoli non approvati diventano 'deferred'."""
    a1 = make_article(session, "Approvato")
    a2 = make_article(session, "Non approvato")
    make_queue(session, a1, position=1)
    make_queue(session, a2, position=2)

    with patch_session(session):
        approve_articles([1], date(2026, 3, 13))

    q2 = session.exec(select(PublishQueue).where(PublishQueue.position == 2)).first()
    assert q2.status == "deferred"
    assert q2.deferred_count == 1


def test_approve_articles_max_daily(session):
    """Non approva più di MAX_DAILY articoli anche se richiesti di più."""
    articles = [make_article(session, f"Art {i}") for i in range(6)]
    for i, a in enumerate(articles, 1):
        make_queue(session, a, position=i)

    with patch_session(session):
        approved = approve_articles([1, 2, 3, 4, 5, 6], date(2026, 3, 13))

    assert approved <= MAX_DAILY


def test_approve_articles_discard_dopo_max_deferrals(session):
    """Articolo che raggiunge MAX_DEFERRALS viene scartato definitivamente."""
    a = make_article(session, "Articolo quasi scartato")
    article_id = a.id  # salva l'ID prima che la sessione venga chiusa
    make_queue(session, a, position=1, deferred_count=MAX_DEFERRALS - 1)

    with patch_session(session):
        a2 = make_article(session, "Articolo approvato")
        make_queue(session, a2, position=2)
        approve_articles([2], date(2026, 3, 13))

    session.expire_all()
    q = session.exec(
        select(PublishQueue).where(PublishQueue.article_id == article_id)
    ).first()
    assert q.status == "discarded"


def test_approve_articles_posizione_inesistente(session):
    """Posizione che non esiste → approved=0, nessun errore."""
    with patch_session(session):
        approved = approve_articles([99], date(2026, 3, 13))
    assert approved == 0


def test_approve_articles_multipli_orari_corretti(session):
    """Più approvazioni → orari assegnati nell'ordine di PUBLISH_HOURS."""
    articles = [make_article(session, f"Multi {i}") for i in range(3)]
    for i, a in enumerate(articles, 1):
        make_queue(session, a, position=i)

    with patch_session(session):
        approve_articles([1, 2, 3], date(2026, 3, 13))

    for idx in range(3):
        q = session.exec(
            select(PublishQueue).where(PublishQueue.position == idx + 1)
        ).first()
        assert q.scheduled_hour == PUBLISH_HOURS[idx]


# ── discard_articles ───────────────────────────────────────────


def test_discard_articles_stato_discarded(session):
    """Articoli nelle posizioni indicate diventano 'discarded'."""
    a = make_article(session, "Da scartare")
    make_queue(session, a, position=1)

    with patch_session(session):
        discarded = discard_articles([1], date(2026, 3, 13))

    assert discarded == 1
    q = session.exec(select(PublishQueue).where(PublishQueue.position == 1)).first()
    assert q.status == "discarded"


def test_discard_articles_posizione_inesistente(session):
    """Posizione inesistente → return 0, nessun errore."""
    with patch_session(session):
        result = discard_articles([99], date(2026, 3, 13))
    assert result == 0


def test_discard_articles_multipli(session):
    """Scarta più posizioni in una sola chiamata."""
    articles = [make_article(session, f"Scarto {i}") for i in range(3)]
    for i, a in enumerate(articles, 1):
        make_queue(session, a, position=i)

    with patch_session(session):
        discarded = discard_articles([1, 2, 3], date(2026, 3, 13))

    assert discarded == 3


def test_discard_articles_solo_pending(session):
    """Scarta solo articoli in stato 'pending', non 'approved'."""
    a1 = make_article(session, "Pending")
    a2 = make_article(session, "Approved")
    make_queue(session, a1, position=1, status="pending")
    make_queue(session, a2, position=2, status="approved")

    with patch_session(session):
        discarded = discard_articles([1, 2], date(2026, 3, 13))

    assert discarded == 1


# ── get_next_to_publish ────────────────────────────────────────


def test_get_next_to_publish_articolo_corretto(session):
    """Ritorna l'articolo approvato per l'ora indicata."""
    a = make_article(session, "Da pubblicare alle 9")
    q = make_queue(session, a, position=1, status="approved")
    q.scheduled_hour = 9
    session.add(q)
    session.commit()

    with patch_session(session):
        result = get_next_to_publish(date(2026, 3, 13), hour=9)

    assert result is not None
    assert result["title"] == "Da pubblicare alle 9"
    assert result["queue_id"] == q.id


def test_get_next_to_publish_ora_sbagliata(session):
    """Nessun articolo per quell'ora → None."""
    a = make_article(session, "Articolo ore 18")
    q = make_queue(session, a, position=1, status="approved")
    q.scheduled_hour = 18
    session.add(q)
    session.commit()

    with patch_session(session):
        result = get_next_to_publish(date(2026, 3, 13), hour=9)

    assert result is None


def test_get_next_to_publish_coda_vuota(session):
    """Nessun articolo in coda → None."""
    with patch_session(session):
        result = get_next_to_publish(date(2026, 3, 13), hour=9)
    assert result is None


def test_get_next_to_publish_solo_approved(session):
    """Non ritorna articoli in stato diverso da 'approved'."""
    a = make_article(session, "Articolo pending")
    q = make_queue(session, a, position=1, status="pending")
    q.scheduled_hour = 9
    session.add(q)
    session.commit()

    with patch_session(session):
        result = get_next_to_publish(date(2026, 3, 13), hour=9)

    assert result is None


# ── mark_published / mark_publishing ──────────────────────────


def test_mark_publishing_cambia_stato(session):
    """mark_publishing → stato 'publishing'."""
    a = make_article(session, "In pubblicazione")
    q = make_queue(session, a, position=1, status="approved")
    queue_id = q.id

    with patch_session(session):
        mark_publishing(queue_id)

    # Rilegge dal DB — la funzione ha usato e chiuso la propria sessione
    session.expire_all()
    q_reloaded = session.exec(
        select(PublishQueue).where(PublishQueue.id == queue_id)
    ).first()
    assert q_reloaded.status == "publishing"


def test_mark_published_cambia_stato(session):
    """mark_published → stato 'published' con timestamp."""
    a = make_article(session, "Pubblicato")
    q = make_queue(session, a, position=1, status="publishing")
    queue_id = q.id

    with patch_session(session):
        mark_published(queue_id)

    session.expire_all()
    q_reloaded = session.exec(
        select(PublishQueue).where(PublishQueue.id == queue_id)
    ).first()
    assert q_reloaded.status == "published"
    assert q_reloaded.published_at is not None


def test_mark_published_id_inesistente(session):
    """ID inesistente → nessun errore."""
    with patch_session(session):
        mark_published(9999)  # non deve sollevare eccezioni
