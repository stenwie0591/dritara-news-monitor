"""
Test suite per src/bot.py
Copre i nuovi comandi feed e keyword (nessuna rete, DB in-memory):
  - _handle_feedlist: lista feed con statistiche
  - _handle_feedadd: validazione sintassi, feed duplicato
  - _handle_feeddisable / _handle_feedenable: toggle stato
  - _handle_kwlist: lista keyword per cluster
  - _handle_kwadd: aggiunta keyword, duplicato, cluster non valido, peso non valido
  - _handle_kwremove: rimozione definitiva, keyword inesistente
  - _handle_kwset: modifica peso, salva history, peso invariato
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.models import FeedSource, KeywordConfig, KeywordWeightHistory


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


def patch_session(session):
    return patch("src.database.get_session", return_value=iter([session]))


def patch_send():
    return patch("src.bot._send", new_callable=AsyncMock)


# ── Helpers ────────────────────────────────────────────────────
def make_feed(
    session,
    name="Test Feed",
    url="https://example.com/rss",
    level=2,
    active=True,
    category="tech",
):
    feed = FeedSource(name=name, url=url, level=level, active=active, category=category)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def make_keyword(session, keyword="startup", cluster="B", weight=1.5, active=True):
    kw = KeywordConfig(keyword=keyword, cluster=cluster, weight=weight, active=active)
    session.add(kw)
    session.commit()
    session.refresh(kw)
    return kw


# ── Test /feedlist ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_feedlist_feed_presenti(session):
    make_feed(session, name="Corriere", url="https://corriere.com/rss", level=1)
    make_feed(
        session, name="Locale", url="https://locale.com/rss", level=3, active=False
    )

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedlist

        await _handle_feedlist()

    testo = mock_send.call_args[0][1]
    assert "Corriere" in testo
    assert "Locale" in testo
    assert "🟢" in testo
    assert "🔴" in testo


@pytest.mark.asyncio
async def test_feedlist_vuota(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedlist

        await _handle_feedlist()

    testo = mock_send.call_args[0][1]
    assert "Nessun feed" in testo


# ── Test /feedadd ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_feedadd_sintassi_errata(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedadd

        await _handle_feedadd("/feedadd")

    testo = mock_send.call_args[0][1]
    assert "Sintassi" in testo


@pytest.mark.asyncio
async def test_feedadd_livello_non_valido(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedadd

        await _handle_feedadd("/feedadd https://example.com/rss Nome 5")

    testo = mock_send.call_args[0][1]
    assert "livello" in testo.lower()


@pytest.mark.asyncio
async def test_feedadd_feed_duplicato(session):
    make_feed(session, url="https://example.com/rss")

    with patch_session(session), patch_send() as mock_send:
        with patch("src.bot.httpx.AsyncClient") as mock_client:
            mock_resp = AsyncMock()
            mock_resp.raise_for_status = AsyncMock()
            mock_resp.text = (
                "<rss><channel><item><title>Test</title></item></channel></rss>"
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_resp
            )
            with patch("src.bot.feedparser.parse") as mock_parse:
                mock_parse.return_value.bozo = False
                mock_parse.return_value.entries = [{"title": "Test"}]
                from src.bot import _handle_feedadd

                await _handle_feedadd("/feedadd https://example.com/rss Nome 2")

    testo = mock_send.call_args[0][1]
    assert "già presente" in testo


@pytest.mark.asyncio
async def test_feedadd_fetch_fallito(session):
    with patch_session(session), patch_send() as mock_send:
        with patch("src.bot.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("timeout")
            )
            from src.bot import _handle_feedadd

            await _handle_feedadd("/feedadd https://nonexistent.com/rss Nome 2")

    testo = mock_send.call_args[0][1]
    assert "Impossibile" in testo


# ── Test /feeddisable ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_feeddisable_successo(session):
    from sqlmodel import select

    feed = make_feed(session, active=True)
    feed_id = feed.id

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feeddisable

        await _handle_feeddisable(f"/feeddisable {feed_id}")

    testo = mock_send.call_args[0][1]
    assert "🔴" in testo
    risultato = session.exec(select(FeedSource).where(FeedSource.id == feed_id)).first()
    assert risultato.active is False


@pytest.mark.asyncio
async def test_feeddisable_gia_disattivo(session):
    feed = make_feed(session, active=False)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feeddisable

        await _handle_feeddisable(f"/feeddisable {feed.id}")

    testo = mock_send.call_args[0][1]
    assert "già disattivato" in testo


@pytest.mark.asyncio
async def test_feeddisable_id_inesistente(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feeddisable

        await _handle_feeddisable("/feeddisable 9999")

    testo = mock_send.call_args[0][1]
    assert "Nessun feed" in testo


@pytest.mark.asyncio
async def test_feeddisable_sintassi_errata(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feeddisable

        await _handle_feeddisable("/feeddisable")

    testo = mock_send.call_args[0][1]
    assert "Sintassi" in testo


# ── Test /feedenable ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_feedenable_successo(session):
    from sqlmodel import select

    feed = make_feed(session, active=False)
    feed_id = feed.id

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedenable

        await _handle_feedenable(f"/feedenable {feed_id}")

    testo = mock_send.call_args[0][1]
    assert "🟢" in testo
    risultato = session.exec(select(FeedSource).where(FeedSource.id == feed_id)).first()
    assert risultato.active is True


@pytest.mark.asyncio
async def test_feedenable_gia_attivo(session):
    feed = make_feed(session, active=True)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_feedenable

        await _handle_feedenable(f"/feedenable {feed.id}")

    testo = mock_send.call_args[0][1]
    assert "già attivo" in testo


# ── Test /kwlist ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_kwlist_per_cluster(session):
    make_keyword(session, keyword="calabria", cluster="A", weight=2.0)
    make_keyword(session, keyword="startup", cluster="B", weight=1.5)
    make_keyword(session, keyword="stem", cluster="C", weight=1.5)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwlist

        await _handle_kwlist()

    testo = mock_send.call_args[0][1]
    assert "calabria" in testo
    assert "startup" in testo
    assert "stem" in testo
    assert "Cluster A" in testo
    assert "Cluster B" in testo
    assert "Cluster C" in testo


@pytest.mark.asyncio
async def test_kwlist_vuota(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwlist

        await _handle_kwlist()

    testo = mock_send.call_args[0][1]
    assert "Nessuna keyword" in testo


# ── Test /kwadd ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_kwadd_successo(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd B 1.5 robotica")

    testo = mock_send.call_args[0][1]
    assert "aggiunta" in testo.lower()
    assert "robotica" in testo


@pytest.mark.asyncio
async def test_kwadd_cluster_non_valido(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd X 1.5 robotica")

    testo = mock_send.call_args[0][1]
    assert "Cluster non valido" in testo


@pytest.mark.asyncio
async def test_kwadd_peso_non_valido(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd B 5.0 robotica")

    testo = mock_send.call_args[0][1]
    assert "peso" in testo.lower()


@pytest.mark.asyncio
async def test_kwadd_sintassi_errata(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd B")

    testo = mock_send.call_args[0][1]
    assert "Sintassi" in testo


@pytest.mark.asyncio
async def test_kwadd_duplicato_attivo(session):
    make_keyword(session, keyword="robotica", cluster="B", weight=1.5)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd B 1.5 robotica")

    testo = mock_send.call_args[0][1]
    assert "esiste già" in testo


@pytest.mark.asyncio
async def test_kwadd_riattiva_disattiva(session):
    make_keyword(session, keyword="robotica", cluster="B", weight=1.5, active=False)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwadd

        await _handle_kwadd("/kwadd B 2.0 robotica")

    testo = mock_send.call_args[0][1]
    assert "riattivata" in testo.lower()


# ── Test /kwremove ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_kwremove_successo(session):
    make_keyword(session, keyword="robotica")

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwremove

        await _handle_kwremove("/kwremove robotica")

    testo = mock_send.call_args[0][1]
    assert "rimossa" in testo.lower()


@pytest.mark.asyncio
async def test_kwremove_inesistente(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwremove

        await _handle_kwremove("/kwremove inesistente")

    testo = mock_send.call_args[0][1]
    assert "non trovata" in testo


@pytest.mark.asyncio
async def test_kwremove_sintassi_errata(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwremove

        await _handle_kwremove("/kwremove")

    testo = mock_send.call_args[0][1]
    assert "Sintassi" in testo


@pytest.mark.asyncio
async def test_kwremove_eliminazione_definitiva(session):
    from sqlmodel import select

    make_keyword(session, keyword="robotica")

    with patch_session(session), patch_send():
        from src.bot import _handle_kwremove

        await _handle_kwremove("/kwremove robotica")

    risultato = session.exec(
        select(KeywordConfig).where(KeywordConfig.keyword == "robotica")
    ).first()
    assert risultato is None


# ── Test /kwset ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_kwset_successo(session):
    make_keyword(session, keyword="startup", weight=1.5)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset startup 2.0")

    testo = mock_send.call_args[0][1]
    assert "1.5" in testo
    assert "2.0" in testo


@pytest.mark.asyncio
async def test_kwset_salva_history(session):
    from sqlmodel import select

    make_keyword(session, keyword="startup", weight=1.5)

    with patch_session(session), patch_send():
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset startup 2.0")

    history = session.exec(
        select(KeywordWeightHistory).where(KeywordWeightHistory.keyword == "startup")
    ).first()
    assert history is not None
    assert history.peso_precedente == 1.5
    assert history.peso_nuovo == 2.0
    assert history.motivo == "modifica_manuale"


@pytest.mark.asyncio
async def test_kwset_peso_invariato(session):
    make_keyword(session, keyword="startup", weight=1.5)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset startup 1.5")

    testo = mock_send.call_args[0][1]
    assert "già" in testo


@pytest.mark.asyncio
async def test_kwset_keyword_inesistente(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset inesistente 2.0")

    testo = mock_send.call_args[0][1]
    assert "non trovata" in testo


@pytest.mark.asyncio
async def test_kwset_peso_non_valido(session):
    make_keyword(session, keyword="startup", weight=1.5)

    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset startup 9.9")

    testo = mock_send.call_args[0][1]
    assert "peso" in testo.lower()


@pytest.mark.asyncio
async def test_kwset_sintassi_errata(session):
    with patch_session(session), patch_send() as mock_send:
        from src.bot import _handle_kwset

        await _handle_kwset("/kwset")

    testo = mock_send.call_args[0][1]
    assert "Sintassi" in testo
