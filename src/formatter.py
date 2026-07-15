from datetime import date
from typing import Optional

from loguru import logger

from src.telegram_renderer import (
    TELEGRAM_MAX_CHARS,
    HtmlFragment,
    telegram_renderer,
)


# ── Costanti Telegram ──────────────────────────────────────────
SECTION3_MAX = 5


# ── Formatter principale ───────────────────────────────────────
class DigestFormatter:
    """
    Formatta gli articoli scorati in messaggi Telegram.

    Struttura digest:
        Intestazione con data e statistiche
        Sezione 1 — Sud + Tech (priorità massima)
        Sezione 2 — Trend nazionali
        Sezione 3 — In breve (max 5, solo geo)
        Footer con totali
    """

    def format_daily(
        self,
        articles: list[dict],
        digest_date: date,
        feed_stats: Optional[dict] = None,
    ) -> list[str]:
        """
        Formatta il digest giornaliero.
        Ritorna una lista di messaggi (split se > 4096 chars).
        """
        s1 = self._filter_section(articles, "section1")
        s2 = self._filter_section(articles, "section2")
        s3 = self._filter_section(articles, "section3")[:SECTION3_MAX]

        blocks = []

        # ── Intestazione ───────────────────────────────────────
        blocks.append(self._header(digest_date, feed_stats, len(s1), len(s2), len(s3)))

        # ── Sezione 1 ──────────────────────────────────────────
        blocks.append(self._section1(s1))

        # ── Sezione 2 ──────────────────────────────────────────
        blocks.append(self._section2(s2))

        # ── Sezione 3 ──────────────────────────────────────────
        blocks.append(self._section3(s3))

        # ── Footer ─────────────────────────────────────────────
        blocks.append(self._footer(articles))

        full_text = HtmlFragment("\n".join(str(block) for block in blocks))
        messages = self._split(full_text)

        logger.info(
            f"Digest formattato — {len(s1)}+{len(s2)}+{len(s3)} articoli "
            f"— {len(messages)} messaggio/i Telegram"
        )
        return messages

    def format_weekly(
        self,
        articles: list[dict],
        week_label: str,
    ) -> list[str]:
        """
        Formatta il weekly digest con i migliori articoli della settimana.
        Prende i top 5 per sezione ordinati per score.
        """
        s1 = self._filter_section(articles, "section1", top=5)
        s2 = self._filter_section(articles, "section2", top=5)

        lines: list[HtmlFragment] = []
        lines.append(
            telegram_renderer.join(
                "📅 ", telegram_renderer.bold(f"DRITARA WEEKLY — {week_label}")
            )
        )
        lines.append(telegram_renderer.text("Il meglio della settimana su tech e digitale nel Mezzogiorno\n"))

        lines.append(telegram_renderer.join("🔴 ", telegram_renderer.bold("SUD + TECH — I migliori della settimana")))
        if s1:
            for a in s1:
                lines.append(self._article_line(a))
        else:
            lines.append(telegram_renderer.italic("Nessun articolo questa settimana"))

        lines.append(HtmlFragment(""))
        lines.append(telegram_renderer.join("🟡 ", telegram_renderer.bold("TREND NAZIONALI — I migliori della settimana")))
        if s2:
            for a in s2:
                lines.append(self._article_line(a))
        else:
            lines.append(telegram_renderer.italic("Nessun articolo questa settimana"))

        lines.append(HtmlFragment(""))
        lines.append(telegram_renderer.text("─────────────────────"))
        lines.append(telegram_renderer.italic("Dritara · info@dritara.tech"))

        return self._split(HtmlFragment("\n".join(str(line) for line in lines)))

    # ── Blocchi interni ────────────────────────────────────────
    def _header(
        self,
        digest_date: date,
        feed_stats: Optional[dict],
        n1: int,
        n2: int,
        n3: int,
    ) -> HtmlFragment:
        day_it = _day_italian(digest_date)
        date_str = digest_date.strftime("%d/%m/%Y")

        lines: list[HtmlFragment] = []
        lines.append(telegram_renderer.join("📰 ", telegram_renderer.bold("DRITARA NEWS MONITOR")))
        lines.append(telegram_renderer.join(telegram_renderer.italic(f"{day_it}, {date_str}"), "\n"))

        if feed_stats:
            ok  = feed_stats.get("feeds_ok", 0)
            tot = feed_stats.get("feeds_attempted", 0)
            fetched = feed_stats.get("articles_fetched", 0)
            lines.append(telegram_renderer.text(f"Feed monitorati: {ok}/{tot} ✓ — Articoli raccolti: {fetched}"))

        lines.append(telegram_renderer.text(f"Sezione 1: {n1} | Sezione 2: {n2} | In breve: {n3}\n"))
        lines.append(telegram_renderer.text("━━━━━━━━━━━━━━━━━━━━━━━━━"))
        return HtmlFragment("\n".join(str(line) for line in lines))

    def _section1(self, articles: list[dict]) -> HtmlFragment:
        lines: list[HtmlFragment] = []
        lines.append(telegram_renderer.join("\n🔴 ", telegram_renderer.bold("SUD + TECH")))
        lines.append(telegram_renderer.join(telegram_renderer.italic("Notizie con impatto diretto sul Mezzogiorno digitale"), "\n"))

        if not articles:
            lines.append(telegram_renderer.italic("Nessuna notizia rilevante oggi in questa sezione"))
        else:
            for a in articles:
                lines.append(self._article_block(a))

        return HtmlFragment("\n".join(str(line) for line in lines))

    def _section2(self, articles: list[dict]) -> HtmlFragment:
        lines: list[HtmlFragment] = []
        lines.append(telegram_renderer.join("\n🟡 ", telegram_renderer.bold("TREND NAZIONALI")))
        lines.append(telegram_renderer.join(telegram_renderer.italic("Sviluppi tech e innovazione da tenere d'occhio"), "\n"))

        if not articles:
            lines.append(telegram_renderer.italic("Nessuna notizia rilevante oggi in questa sezione"))
        else:
            for a in articles[:10]:  # max 10 in sezione 2
                lines.append(self._article_line(a))

        return HtmlFragment("\n".join(str(line) for line in lines))

    def _section3(self, articles: list[dict]) -> HtmlFragment:
        lines: list[HtmlFragment] = []
        lines.append(telegram_renderer.join("\n📋 ", telegram_renderer.bold("IN BREVE — SUD")))
        lines.append(telegram_renderer.join(telegram_renderer.italic("Notizie dal territorio"), "\n"))

        if not articles:
            lines.append(telegram_renderer.italic("Nessuna notizia oggi"))
        else:
            for a in articles:
                lines.append(self._article_line(a))

        return HtmlFragment("\n".join(str(line) for line in lines))

    def _footer(self, articles: list[dict]) -> HtmlFragment:
        lines = [telegram_renderer.text("\n━━━━━━━━━━━━━━━━━━━━━━━━━")]
        lines.append(telegram_renderer.italic(f"Totale articoli analizzati: {len(articles)}"))
        lines.append(telegram_renderer.italic("Dritara · info@dritara.tech"))
        lines.append(telegram_renderer.italic("Usa /pubblica per condividere con la community"))
        return HtmlFragment("\n".join(str(line) for line in lines))

    # ── Formato articolo ───────────────────────────────────────
    def _article_block(self, article: dict) -> HtmlFragment:
        """Formato esteso per Sezione 1: titolo + excerpt + fonte + link."""
        title   = article.get("title", "")
        excerpt = article.get("excerpt", "")
        source  = article.get("feed_name", "")
        url     = article.get("url", "")
        score   = article.get("score", 0)

        lines: list[HtmlFragment] = []
        lines.append(telegram_renderer.bold(title, limit=300))
        if excerpt:
            # Tronca a 200 chars per non appesantire
            short = excerpt[:200].rsplit(" ", 1)[0] + "…" if len(excerpt) > 200 else excerpt
            lines.append(telegram_renderer.italic(short, limit=220))
        lines.append(telegram_renderer.join(telegram_renderer.link(f"{source} · score {score:.1f}", url, label_limit=400), "\n"))
        return HtmlFragment("\n".join(str(line) for line in lines))

    def _article_line(self, article: dict) -> HtmlFragment:
        """Formato compatto per Sezione 2 e 3: titolo + fonte + link."""
        title  = article.get("title", "")
        source = article.get("feed_name", "")
        url    = article.get("url", "")
        return telegram_renderer.join(
            "• ",
            telegram_renderer.link(title, url, label_limit=300),
            " — ",
            telegram_renderer.italic(source, limit=200),
        )

    # ── Helpers ────────────────────────────────────────────────
    def _filter_section(
        self,
        articles: list[dict],
        section: str,
        top: Optional[int] = None,
    ) -> list[dict]:
        filtered = [a for a in articles if a.get("section") == section]
        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
        return filtered[:top] if top else filtered

    def _split(self, text: str) -> list[str]:
        """Splitta tramite il renderer, senza spezzare tag o entity HTML."""
        if not isinstance(text, HtmlFragment):
            return [message.text for message in telegram_renderer.plain_messages(text)]
        lines = [HtmlFragment(line) for line in str(text).split("\n")]
        return [message.text for message in telegram_renderer.split_lines(lines)]


# ── Helper data italiana ───────────────────────────────────────
def _day_italian(d: date) -> str:
    days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì",
            "Venerdì", "Sabato", "Domenica"]
    return days[d.weekday()]
