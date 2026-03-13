"""
Test suite per src/scorer.py

Copre:
  - Articoli blacklistati
  - Territorial boost (Cluster A + B co-occorrenti)
  - Proximity check per CONTEXT_REQUIRED
  - Feed level 3 (Cluster B deve essere nel titolo)
  - Sezioni corrette (section1, section2, section3, discarded)
"""

from src.scorer import Scorer

# ── Fixture ────────────────────────────────────────────────────


def make_scorer() -> Scorer:
    """Scorer costruito dal DB reale — usa le keyword attive."""
    from src.database import get_session
    from src.scorer import build_scorer

    session = next(get_session())
    scorer = build_scorer(session)
    session.close()
    return scorer


# ── Test blacklist ─────────────────────────────────────────────


def test_blacklist_ndrangheta():
    scorer = make_scorer()
    result = scorer.score(
        title="'Ndrangheta, arrestati 5 boss in Calabria",
        excerpt="Operazione antimafia in Calabria con 5 arresti.",
        feed_level=2,
    )
    assert result.section == "discarded"
    assert result.score == 0.0


def test_blacklist_incidente():
    scorer = make_scorer()
    result = scorer.score(
        title="Grave incidente stradale a Reggio Calabria",
        excerpt="Scontro tra due auto sulla statale.",
        feed_level=2,
    )
    assert result.section == "discarded"


def test_blacklist_meteo():
    scorer = make_scorer()
    result = scorer.score(
        title="Allerta meteo in Calabria per domani",
        excerpt="Previste forti piogge nel weekend.",
        feed_level=2,
    )
    assert result.section == "discarded"


# ── Test territorial boost ─────────────────────────────────────


def test_territorial_boost_applicato():
    """Cluster A + B co-occorrenti → boost x1.5"""
    scorer = make_scorer()
    result = scorer.score(
        title="Startup calabrese raccoglie fondi per hub digitale",
        excerpt="Una startup di Cosenza ha avviato un hub digitale per l'innovazione.",
        feed_level=2,
    )
    assert result.score_detail.get("territorial_boost") is True
    assert result.score > 8.0  # deve essere section1


def test_territorial_boost_non_applicato_solo_a():
    """Solo Cluster A → nessun boost"""
    scorer = make_scorer()
    result = scorer.score(
        title="Notizie dalla Calabria oggi",
        excerpt="Aggiornamenti dalla regione Calabria.",
        feed_level=2,
    )
    assert result.score_detail.get("territorial_boost") is False


def test_territorial_boost_non_applicato_solo_b():
    """Solo Cluster B → nessun boost"""
    scorer = make_scorer()
    result = scorer.score(
        title="Nuova startup lancia hub digitale in Italia",
        excerpt="La startup ha aperto un hub digitale a Milano.",
        feed_level=2,
    )
    assert result.score_detail.get("territorial_boost") is False


# ── Test sezioni ───────────────────────────────────────────────


def test_section1_score_alto():
    scorer = make_scorer()
    result = scorer.score(
        title="Hub digitale in Calabria finanziato dal PNRR",
        excerpt="La Calabria riceve fondi PNRR per un hub digitale sull'innovazione.",
        feed_level=2,
    )
    assert result.section == "section1"
    assert result.score >= 8.0


def test_section2_score_medio():
    scorer = make_scorer()
    result = scorer.score(
        title="Intelligenza artificiale rivoluziona il lavoro in Italia",
        excerpt="L'intelligenza artificiale sta cambiando il mercato del lavoro italiano.",
        feed_level=2,
    )
    assert result.section in ("section1", "section2")


def test_discarded_score_zero():
    scorer = make_scorer()
    result = scorer.score(
        title="Oggi piove a Milano",
        excerpt="Previsioni meteo per il nord Italia.",
        feed_level=2,
    )
    assert result.section == "discarded"
    assert result.score == 0.0


# ── Test proximity check (CONTEXT_REQUIRED) ───────────────────


def test_context_required_con_contesto():
    """'startup' accettata se keyword standalone entro 20 parole"""
    scorer = make_scorer()
    result = scorer.score(
        title="La startup calabrese vince il premio innovazione",
        excerpt="Una startup di Reggio Calabria ha vinto il premio.",
        feed_level=2,
    )
    assert "startup" in result.keyword_matches or result.score > 0


def test_context_required_senza_contesto():
    """'startup' scartata se nessuna keyword standalone entro 20 parole"""
    scorer = make_scorer()
    result = scorer.score(
        title="Startup",
        excerpt="Una startup ha aperto un nuovo ufficio.",
        feed_level=2,
    )
    # Senza keyword A o altre B nelle vicinanze, startup CONTEXT_REQUIRED viene scartata
    assert "startup" not in result.keyword_matches


# ── Test feed level 3 ──────────────────────────────────────────


def test_feed_level3_keyword_b_nel_titolo():
    """Feed locale (level 3): Cluster B deve essere nel titolo"""
    scorer = make_scorer()
    result = scorer.score(
        title="Hub digitale apre a Cosenza grazie al PNRR",
        excerpt="La Calabria investe nell'innovazione digitale.",
        feed_level=3,
    )
    assert result.section != "discarded"


def test_feed_level3_keyword_b_solo_excerpt():
    """Feed locale (level 3): B solo nell'excerpt con score alto → section2 (mai section1)"""
    scorer = make_scorer()
    result = scorer.score(
        title="Notizie dalla Calabria",
        excerpt="Un nuovo hub digitale aprirà grazie al PNRR.",
        feed_level=3,
    )
    assert result.section == "section2"


def test_feed_level3_keyword_b_solo_excerpt_score_basso():
    """Feed locale (level 3): B solo nell'excerpt con score basso → discarded"""
    scorer = make_scorer()
    result = scorer.score(
        title="Notizie dalla Calabria",
        excerpt="Una piccola iniziativa tech.",
        feed_level=3,
    )
    assert result.section == "discarded"


# ── Test keyword_matches ───────────────────────────────────────
def test_keyword_matches_popolato():
    scorer = make_scorer()
    result = scorer.score(
        title="Innovazione digitale in Calabria con intelligenza artificiale",
        excerpt="La Calabria punta sull'intelligenza artificiale per crescere.",
        feed_level=2,
    )
    assert len(result.keyword_matches) > 0
    assert isinstance(result.keyword_matches, list)
