import hashlib
from typing import Optional

from rapidfuzz import fuzz
from loguru import logger

from src.models import Article


# ── ID articolo ────────────────────────────────────────────────
def make_article_id(url: str) -> str:
    """SHA-256 dell'URL — usato come primary key."""
    return hashlib.sha256(url.strip().encode()).hexdigest()


# ── Deduplicatore ──────────────────────────────────────────────
class Deduplicator:
    """
    Elimina articoli duplicati usando due strategie:
    1. URL esatto (SHA-256 — istantaneo)
    2. Title fingerprint (rapidfuzz similarità ≥ soglia)

    Gestisce duplicati cross-source: stesso articolo
    ripreso da ANSA, AGI e Adnkronos viene contato una volta sola.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self._seen_ids: set[str] = set()
        self._seen_titles: list[str] = []

    def reset(self) -> None:
        """Resetta lo stato per un nuovo ciclo di fetch."""
        self._seen_ids.clear()
        self._seen_titles.clear()

    def is_duplicate(self, article_id: str, title: str) -> tuple[bool, str]:
        """
        Controlla se un articolo è duplicato.
        Ritorna (is_dup, motivo).
        """
        # 1. Controllo URL esatto
        if article_id in self._seen_ids:
            return True, "url_exact"

        # 2. Controllo title fingerprint
        title_clean = _normalize_title(title)
        for seen_title in self._seen_titles:
            similarity = fuzz.ratio(title_clean, seen_title)
            if similarity >= self.threshold * 100:
                return True, f"title_similarity:{similarity:.0f}%"

        return False, ""

    def register(self, article_id: str, title: str) -> None:
        """Registra un articolo come visto."""
        self._seen_ids.add(article_id)
        self._seen_titles.append(_normalize_title(title))

    def filter(self, articles: list[dict]) -> list[dict]:
        """
        Filtra una lista di articoli grezzi rimuovendo i duplicati.
        Ritorna solo gli articoli unici.
        """
        unique = []
        duplicates = 0

        for art in articles:
            article_id = make_article_id(art["url"])
            title = art.get("title", "")

            is_dup, reason = self.is_duplicate(article_id, title)
            if is_dup:
                duplicates += 1
                logger.debug(f"Duplicato ({reason}): {title[:60]}")
            else:
                self.register(article_id, title)
                art["id"] = article_id
                unique.append(art)

        if duplicates:
            logger.info(f"Deduplicazione: {len(articles)} articoli → {len(unique)} unici ({duplicates} duplicati rimossi)")

        return unique


# ── Helper ─────────────────────────────────────────────────────
def _normalize_title(title: str) -> str:
    """Normalizza il titolo per il confronto: lowercase, spazi ridotti."""
    return " ".join(title.lower().split())
