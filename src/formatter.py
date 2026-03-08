from datetime import date
from typing import Optional

from loguru import logger


# ── Costanti Telegram ──────────────────────────────────────────
TELEGRAM_MAX_CHARS = 4096
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

        full_text = "\n".join(blocks)
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

        lines = []
        lines.append(f"📅 *DRITARA WEEKLY — {week_label}*")
        lines.append("Il meglio della settimana su tech e digitale nel Mezzogiorno\n")

        lines.append("🔴 *SUD + TECH — I migliori della settimana*")
        if s1:
            for a in s1:
                lines.append(self._article_line(a))
        else:
            lines.append("_Nessun articolo questa settimana_")

        lines.append("")
        lines.append("🟡 *TREND NAZIONALI — I migliori della settimana*")
        if s2:
            for a in s2:
                lines.append(self._article_line(a))
        else:
            lines.append("_Nessun articolo questa settimana_")

        lines.append("")
        lines.append("─────────────────────")
        lines.append("_Dritara · info@dritara.tech_")

        return self._split("\n".join(lines))

    # ── Blocchi interni ────────────────────────────────────────
    def _header(
        self,
        digest_date: date,
        feed_stats: Optional[dict],
        n1: int,
        n2: int,
        n3: int,
    ) -> str:
        day_it = _day_italian(digest_date)
        date_str = digest_date.strftime("%d/%m/%Y")

        lines = []
        lines.append(f"📰 *DRITARA NEWS MONITOR*")
        lines.append(f"_{day_it}, {date_str}_\n")

        if feed_stats:
            ok  = feed_stats.get("feeds_ok", 0)
            tot = feed_stats.get("feeds_attempted", 0)
            fetched = feed_stats.get("articles_fetched", 0)
            lines.append(f"Feed monitorati: {ok}/{tot} ✓ — Articoli raccolti: {fetched}")

        lines.append(f"Sezione 1: {n1} | Sezione 2: {n2} | In breve: {n3}\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def _section1(self, articles: list[dict]) -> str:
        lines = []
        lines.append("\n🔴 *SUD + TECH*")
        lines.append("_Notizie con impatto diretto sul Mezzogiorno digitale_\n")

        if not articles:
            lines.append("_Nessuna notizia rilevante oggi in questa sezione_")
        else:
            for a in articles:
                lines.append(self._article_block(a))

        return "\n".join(lines)

    def _section2(self, articles: list[dict]) -> str:
        lines = []
        lines.append("\n🟡 *TREND NAZIONALI*")
        lines.append("_Sviluppi tech e innovazione da tenere d'occhio_\n")

        if not articles:
            lines.append("_Nessuna notizia rilevante oggi in questa sezione_")
        else:
            for a in articles[:10]:  # max 10 in sezione 2
                lines.append(self._article_line(a))

        return "\n".join(lines)

    def _section3(self, articles: list[dict]) -> str:
        lines = []
        lines.append("\n📋 *IN BREVE — SUD*")
        lines.append("_Notizie dal territorio_\n")

        if not articles:
            lines.append("_Nessuna notizia oggi_")
        else:
            for a in articles:
                lines.append(self._article_line(a))

        return "\n".join(lines)

    def _footer(self, articles: list[dict]) -> str:
        lines = []
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"_Totale articoli analizzati: {len(articles)}_")
        lines.append("_Dritara · info@dritara.tech_")
        lines.append("_Usa /pubblica per condividere con la community_")
        return "\n".join(lines)

    # ── Formato articolo ───────────────────────────────────────
    def _article_block(self, article: dict) -> str:
        """Formato esteso per Sezione 1: titolo + excerpt + fonte + link."""
        title   = article.get("title", "")
        excerpt = article.get("excerpt", "")
        source  = article.get("feed_name", "")
        url     = article.get("url", "")
        score   = article.get("score", 0)

        lines = []
        lines.append(f"*{title}*")
        if excerpt:
            # Tronca a 200 chars per non appesantire
            short = excerpt[:200].rsplit(" ", 1)[0] + "…" if len(excerpt) > 200 else excerpt
            lines.append(f"_{short}_")
        lines.append(f"[{source} · score {score:.1f}]({url})\n")
        return "\n".join(lines)

    def _article_line(self, article: dict) -> str:
        """Formato compatto per Sezione 2 e 3: titolo + fonte + link."""
        title  = article.get("title", "")
        source = article.get("feed_name", "")
        url    = article.get("url", "")
        return f"• [{title}]({url}) — _{source}_"

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
        """Splitta il testo in messaggi da max 4096 chars."""
        if len(text) <= TELEGRAM_MAX_CHARS:
            return [text]

        messages = []
        while text:
            if len(text) <= TELEGRAM_MAX_CHARS:
                messages.append(text)
                break
            # Taglia sull'ultimo \n prima del limite
            cut = text.rfind("\n", 0, TELEGRAM_MAX_CHARS)
            if cut == -1:
                cut = TELEGRAM_MAX_CHARS
            messages.append(text[:cut])
            text = text[cut:].lstrip("\n")

        return messages


# ── Helper data italiana ───────────────────────────────────────
def _day_italian(d: date) -> str:
    days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì",
            "Venerdì", "Sabato", "Domenica"]
    return days[d.weekday()]
