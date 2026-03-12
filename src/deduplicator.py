import hashlib

from loguru import logger
from rapidfuzz import fuzz


# ── ID articolo ────────────────────────────────────────────────
def make_article_id(url: str) -> str:
    """SHA-256 dell'URL — usato come primary key."""
    return hashlib.sha256(url.strip().encode()).hexdigest()


def _title_hash(title: str) -> str:
    """Hash MD5 del titolo normalizzato — per dedup esatto O(1)."""
    return hashlib.md5(_normalize_title(title).encode()).hexdigest()


# ── Deduplicatore ──────────────────────────────────────────────
class Deduplicator:
    """
    Elimina articoli duplicati usando tre strategie in cascata:
    1. URL esatto (SHA-256 — O(1))
    2. Title hash esatto (MD5 normalizzato — O(1))
    3. Title fingerprint fuzzy (rapidfuzz ≥ soglia — solo se 1 e 2 falliscono)

    Gestisce duplicati cross-source: stesso articolo
    ripreso da ANSA, AGI e Adnkronos viene contato una volta sola.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self._seen_ids: set[str] = set()
        self._seen_title_hashes: set[str] = set()
        self._seen_titles: list[str] = []

    def reset(self) -> None:
        """Resetta lo stato per un nuovo ciclo di fetch."""
        self._seen_ids.clear()
        self._seen_title_hashes.clear()
        self._seen_titles.clear()

    def is_duplicate(self, article_id: str, title: str) -> tuple[bool, str]:
        """
        Controlla se un articolo è duplicato.
        Ritorna (is_dup, motivo).
        """
        # 1. Controllo URL esatto — O(1)
        if article_id in self._seen_ids:
            return True, "url_exact"

        # 2. Controllo title hash esatto — O(1)
        th = _title_hash(title)
        if th in self._seen_title_hashes:
            return True, "title_exact"

        # 3. Controllo title fingerprint fuzzy — O(n), solo se necessario
        title_clean = _normalize_title(title)
        for seen_title in self._seen_titles:
            similarity = fuzz.ratio(title_clean, seen_title)
            if similarity >= self.threshold * 100:
                return True, f"title_similarity:{similarity:.0f}%"

        return False, ""

    def register(self, article_id: str, title: str) -> None:
        """Registra un articolo come visto."""
        self._seen_ids.add(article_id)
        self._seen_title_hashes.add(_title_hash(title))
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
            logger.info(
                f"Deduplicazione: {len(articles)} articoli → {len(unique)} unici "
                f"({duplicates} duplicati rimossi)"
            )

        return unique


# ── Helper ─────────────────────────────────────────────────────
def _normalize_title(title: str) -> str:
    """Normalizza il titolo per il confronto: lowercase, spazi ridotti."""
    return " ".join(title.lower().split())
