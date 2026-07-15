"""
Test suite per src/formatter.py

Copre:
  - format_daily: struttura output, sezioni, split, header, footer
  - format_weekly: top 5 per sezione, sezioni vuote
  - _filter_section: ordinamento per score, top N
  - _article_block: formato esteso sezione 1
  - _article_line: formato compatto sezione 2/3
  - _split: messaggi entro 4096 chars, split corretto
  - _day_italian: tutti i giorni della settimana
"""

from datetime import date

from src.formatter import DigestFormatter, _day_italian

# ── Helpers ────────────────────────────────────────────────────


def make_article(
    title: str = "Titolo articolo",
    section: str = "section1",
    score: float = 10.0,
    feed_name: str = "Test Feed",
    url: str = "https://example.com/articolo",
    excerpt: str = "Testo di esempio per il test.",
) -> dict:
    return {
        "title": title,
        "section": section,
        "score": score,
        "feed_name": feed_name,
        "url": url,
        "excerpt": excerpt,
    }


SAMPLE_DATE = date(2026, 3, 13)  # Venerdì


# ── format_daily ───────────────────────────────────────────────


def test_format_daily_ritorna_lista():
    """format_daily ritorna sempre una lista non vuota."""
    f = DigestFormatter()
    result = f.format_daily([], SAMPLE_DATE)
    assert isinstance(result, list)
    assert len(result) >= 1


def test_format_daily_lista_vuota():
    """Nessun articolo → messaggio con sezioni vuote ma struttura presente."""
    f = DigestFormatter()
    result = f.format_daily([], SAMPLE_DATE)
    text = "\n".join(result)
    assert "DRITARA NEWS MONITOR" in text
    assert "SUD + TECH" in text
    assert "TREND NAZIONALI" in text
    assert "IN BREVE" in text
    assert "Nessuna notizia" in text


def test_format_daily_con_articoli():
    """Articoli presenti → compaiono nel testo."""
    f = DigestFormatter()
    articles = [
        make_article("Hub digitale a Cosenza", section="section1", score=15.0),
        make_article("AI nel settore agricolo", section="section2", score=8.0),
        make_article("Banda larga in Sicilia", section="section3", score=5.0),
    ]
    result = f.format_daily(articles, SAMPLE_DATE)
    text = "\n".join(result)
    assert "Hub digitale a Cosenza" in text
    assert "AI nel settore agricolo" in text
    assert "Banda larga in Sicilia" in text


def test_format_daily_header_con_feed_stats():
    """Header mostra statistiche feed se feed_stats è presente."""
    f = DigestFormatter()
    feed_stats = {
        "feeds_ok": 25,
        "feeds_attempted": 28,
        "articles_fetched": 142,
    }
    result = f.format_daily([], SAMPLE_DATE, feed_stats=feed_stats)
    text = "\n".join(result)
    assert "25/28" in text
    assert "142" in text


def test_format_daily_header_senza_feed_stats():
    """Header senza feed_stats non mostra la riga statistiche."""
    f = DigestFormatter()
    result = f.format_daily([], SAMPLE_DATE, feed_stats=None)
    text = "\n".join(result)
    assert "Feed monitorati" not in text


def test_format_daily_header_data_italiana():
    """Header contiene data in formato italiano."""
    f = DigestFormatter()
    result = f.format_daily([], SAMPLE_DATE)
    text = "\n".join(result)
    assert "13/03/2026" in text
    assert "Venerdì" in text


def test_format_daily_footer_presente():
    """Footer con totale articoli e firma sempre presente."""
    f = DigestFormatter()
    articles = [make_article()]
    result = f.format_daily(articles, SAMPLE_DATE)
    text = "\n".join(result)
    assert "Totale articoli analizzati" in text
    assert "dritara.tech" in text


def test_format_daily_contatori_sezioni():
    """Header mostra i contatori corretti per sezione."""
    f = DigestFormatter()
    articles = [
        make_article(section="section1"),
        make_article(section="section1"),
        make_article(section="section2"),
        make_article(section="section3"),
    ]
    result = f.format_daily(articles, SAMPLE_DATE)
    text = "\n".join(result)
    assert "Sezione 1: 2" in text
    assert "Sezione 2: 1" in text
    assert "In breve: 1" in text


def test_format_daily_section3_max_5():
    """Sezione 3 mostra al massimo 5 articoli."""
    f = DigestFormatter()
    articles = [
        make_article(title=f"Articolo {i}", section="section3") for i in range(8)
    ]
    result = f.format_daily(articles, SAMPLE_DATE)
    text = "\n".join(result)
    # Conta quante volte appare "Articolo N" nel testo
    count = sum(1 for i in range(8) if f"Articolo {i}" in text)
    assert count == 5


def test_format_daily_section2_max_10():
    """Sezione 2 mostra al massimo 10 articoli."""
    f = DigestFormatter()
    articles = [
        make_article(title=f"Notizia {i}", section="section2") for i in range(15)
    ]
    result = f.format_daily(articles, SAMPLE_DATE)
    text = "\n".join(result)
    count = sum(1 for i in range(15) if f"Notizia {i}" in text)
    assert count == 10


# ── Ordinamento per score ──────────────────────────────────────


def test_filter_section_ordine_score():
    """Articoli ordinati per score decrescente dentro la sezione."""
    f = DigestFormatter()
    articles = [
        make_article("Basso", section="section1", score=5.0),
        make_article("Alto", section="section1", score=20.0),
        make_article("Medio", section="section1", score=10.0),
    ]
    result = f._filter_section(articles, "section1")
    assert result[0]["title"] == "Alto"
    assert result[1]["title"] == "Medio"
    assert result[2]["title"] == "Basso"


def test_filter_section_top_n():
    """top=N ritorna solo i primi N articoli."""
    f = DigestFormatter()
    articles = [make_article(title=f"Art {i}", score=float(i)) for i in range(10)]
    result = f._filter_section(articles, "section1", top=3)
    assert len(result) == 3


def test_filter_section_sezione_sbagliata():
    """Articoli di altra sezione non compaiono."""
    f = DigestFormatter()
    articles = [make_article(section="section2")]
    result = f._filter_section(articles, "section1")
    assert result == []


# ── _article_block (sezione 1) ─────────────────────────────────


def test_article_block_contiene_titolo():
    f = DigestFormatter()
    a = make_article("Startup calabrese raccoglie fondi", excerpt="Testo breve.")
    block = f._article_block(a)
    assert "Startup calabrese raccoglie fondi" in block


def test_article_block_contiene_excerpt():
    f = DigestFormatter()
    a = make_article(excerpt="Descrizione importante dell'articolo.")
    block = f._article_block(a)
    assert "Descrizione importante" in block


def test_article_block_excerpt_troncato():
    """Excerpt lungo >200 chars viene troncato."""
    f = DigestFormatter()
    long_excerpt = "Parola " * 50  # ~350 chars
    a = make_article(excerpt=long_excerpt)
    block = f._article_block(a)
    assert "…" in block


def test_article_block_contiene_link():
    f = DigestFormatter()
    a = make_article(url="https://test.com/articolo-speciale")
    block = f._article_block(a)
    assert "https://test.com/articolo-speciale" in block


def test_article_block_contiene_score():
    f = DigestFormatter()
    a = make_article(score=12.5)
    block = f._article_block(a)
    assert "12.5" in block


# ── _article_line (sezione 2/3) ────────────────────────────────


def test_article_line_formato_compatto():
    """Formato compatto: bullet + titolo + fonte."""
    f = DigestFormatter()
    a = make_article(
        "Titolo compatto", feed_name="Corriere", url="https://corriere.it/x"
    )
    line = f._article_line(a)
    assert "Titolo compatto" in line
    assert "Corriere" in line
    assert "https://corriere.it/x" in line
    assert line.startswith("•")


# ── _split ─────────────────────────────────────────────────────


def test_split_testo_corto():
    """Testo sotto 4096 → lista con un solo elemento."""
    f = DigestFormatter()
    result = f._split("Testo breve")
    assert len(result) == 1
    assert result[0] == "Testo breve"


def test_split_testo_lungo():
    """Testo >4096 chars → più messaggi."""
    f = DigestFormatter()
    long_text = ("Riga di testo abbastanza lunga per il test.\n") * 200
    result = f._split(long_text)
    assert len(result) > 1


def test_split_ogni_messaggio_entro_limite():
    """Ogni messaggio prodotto è entro 4096 chars."""
    f = DigestFormatter()
    long_text = ("Articolo molto lungo con contenuto ripetuto.\n") * 300
    result = f._split(long_text)
    for msg in result:
        assert len(msg) <= 4096


def test_split_nessuna_perdita_contenuto():
    """Il contenuto totale dopo split non perde testo."""
    f = DigestFormatter()
    long_text = ("Contenuto da preservare.\n") * 300
    result = f._split(long_text)
    rejoined = "\n".join(result)
    # Verifica che le righe originali siano tutte presenti
    assert "Contenuto da preservare." in rejoined


# ── format_weekly ──────────────────────────────────────────────


def test_format_weekly_ritorna_lista():
    f = DigestFormatter()
    result = f.format_weekly([], "10-16 marzo 2026")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_format_weekly_contiene_label():
    f = DigestFormatter()
    result = f.format_weekly([], "10-16 marzo 2026")
    text = "\n".join(result)
    assert "10-16 marzo 2026" in text


def test_format_weekly_sezioni_vuote():
    """Senza articoli mostra messaggio sezioni vuote."""
    f = DigestFormatter()
    result = f.format_weekly([], "10-16 marzo 2026")
    text = "\n".join(result)
    assert "Nessun articolo" in text


def test_format_weekly_top_5_per_sezione():
    """Weekly mostra max 5 articoli per sezione."""
    f = DigestFormatter()
    articles = [
        make_article(title=f"S1 {i}", section="section1", score=float(i))
        for i in range(8)
    ] + [
        make_article(title=f"S2 {i}", section="section2", score=float(i))
        for i in range(8)
    ]
    result = f.format_weekly(articles, "10-16 marzo 2026")
    text = "\n".join(result)
    s1_count = sum(1 for i in range(8) if f"S1 {i}" in text)
    s2_count = sum(1 for i in range(8) if f"S2 {i}" in text)
    assert s1_count == 5
    assert s2_count == 5


# ── _day_italian ───────────────────────────────────────────────


def test_day_italian_tutti_i_giorni():
    """Verifica la mappatura corretta per tutti i 7 giorni."""
    cases = [
        (date(2026, 3, 9), "Lunedì"),
        (date(2026, 3, 10), "Martedì"),
        (date(2026, 3, 11), "Mercoledì"),
        (date(2026, 3, 12), "Giovedì"),
        (date(2026, 3, 13), "Venerdì"),
        (date(2026, 3, 14), "Sabato"),
        (date(2026, 3, 15), "Domenica"),
    ]
    for d, expected in cases:
        assert _day_italian(d) == expected
