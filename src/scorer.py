import re
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger
from sqlmodel import Session

from src.database import get_active_keywords
from src.models import KeywordConfig

# ── Keyword che richiedono contesto rafforzato ─────────────────
# Vengono accettate solo se appaiono con almeno una keyword
# dello stesso cluster nello stesso campo (titolo o excerpt).
CONTEXT_REQUIRED = {"stem", "ai", "lavoro", "ricerca", "università"}


# ── Struttura risultato scoring ────────────────────────────────
@dataclass
class ScoreResult:
    score: float = 0.0
    section: str = "discarded"
    score_detail: dict = field(default_factory=dict)
    keyword_matches: list = field(default_factory=list)


# ── Scorer principale ──────────────────────────────────────────
class Scorer:
    """
    Calcola lo score di un articolo basandosi su keyword e livello fonte.

    Formula:
        score = (score_titolo × 2.0) + (score_excerpt × 1.0) + bonus_fonte

    Sezioni:
        section1 — Cluster A AND (Cluster B OR Cluster C)
        section2 — Cluster B OR Cluster C  (senza A)
        section3 — solo Cluster A
        discarded — nessun cluster
    """

    SOURCE_BONUS = {1: 0.5, 2: 0.0, 3: 1.0}
    TITLE_MULTIPLIER = 2.0
    EXCERPT_MULTIPLIER = 1.0

    def __init__(self, keywords: list[KeywordConfig]):
        self._patterns: dict[str, list[tuple]] = {"A": [], "B": [], "C": []}
        self._compile(keywords)
        logger.info(
            f"Scorer inizializzato — "
            f"A:{len(self._patterns['A'])} "
            f"B:{len(self._patterns['B'])} "
            f"C:{len(self._patterns['C'])} keyword"
        )

    def _compile(self, keywords: list[KeywordConfig]) -> None:
        """Pre-compila i pattern regex con word-boundary."""
        for kw in keywords:
            pattern = re.compile(r"\b" + re.escape(kw.keyword) + r"\b", re.IGNORECASE)
            self._patterns[kw.cluster].append((pattern, kw.weight, kw.keyword))

    def _match_text(self, text: str, cluster: str) -> tuple[float, list[str]]:
        """
        Trova le keyword di un cluster nel testo.
        Le keyword in CONTEXT_REQUIRED vengono accettate solo
        se almeno un'altra keyword dello stesso cluster è presente.
        Ritorna (score_parziale, lista_keyword_trovate).
        """
        # Prima passata: trova tutte le keyword senza filtri
        raw_found = []
        for pattern, weight, word in self._patterns[cluster]:
            if pattern.search(text):
                raw_found.append((word, weight))

        # Keyword non ambigue trovate
        definite = [(w, wt) for w, wt in raw_found if w not in CONTEXT_REQUIRED]
        ambiguous = [(w, wt) for w, wt in raw_found if w in CONTEXT_REQUIRED]

        # Le keyword ambigue sono accettate solo se ci sono anche keyword definite
        if definite:
            accepted = definite + ambiguous
        else:
            accepted = definite  # scarta le ambigue se sono sole

        score = sum(wt for _, wt in accepted)
        found = [w for w, _ in accepted]
        return score, found

    def score(
        self,
        title: str,
        excerpt: Optional[str],
        feed_level: int,
    ) -> ScoreResult:
        """Calcola lo score completo di un articolo."""

        title = title or ""
        excerpt = excerpt or ""
        result = ScoreResult()
        all_matches = []

        detail = {}
        has_cluster = {"A": False, "B": False, "C": False}

        for cluster in ("A", "B", "C"):
            t_score, t_found = self._match_text(title, cluster)
            e_score, e_found = self._match_text(excerpt, cluster)

            cluster_score = (
                t_score * self.TITLE_MULTIPLIER + e_score * self.EXCERPT_MULTIPLIER
            )
            found = list(set(t_found + e_found))

            if cluster_score > 0:
                has_cluster[cluster] = True
                all_matches.extend(found)

            detail[f"cluster_{cluster}_score"] = round(cluster_score, 3)
            detail[f"cluster_{cluster}_keywords"] = found

        # ── Bonus fonte ────────────────────────────────────────
        bonus = self.SOURCE_BONUS.get(feed_level, 0.0)
        detail["source_bonus"] = bonus
        detail["feed_level"] = feed_level

        # ── Score totale ───────────────────────────────────────
        base_score = sum(detail[f"cluster_{c}_score"] for c in ("A", "B", "C"))
        total = round(base_score + bonus, 3)
        detail["total"] = total

        # ── Assegnazione sezione ───────────────────────────────
        has_A = has_cluster["A"]
        has_B = has_cluster["B"]
        has_C = has_cluster["C"]

        # Soglia minima per section1
        SECTION1_MIN_SCORE = 8.0

        # Feed locali (livello 3): il cluster B deve essere nel titolo
        level3_b_in_title = True
        if feed_level == 3:
            _, b_title_found = self._match_text(title, "B")
            level3_b_in_title = len(b_title_found) > 0

        if (
            has_A
            and (has_B or has_C)
            and total >= SECTION1_MIN_SCORE
            and level3_b_in_title
        ):
            section = "section1"
        elif has_B or has_C:
            section = "section2"
        elif has_A:
            section = "section3"
        else:
            section = "discarded"

        result.score = total
        result.section = section
        result.score_detail = detail
        result.keyword_matches = list(set(all_matches))

        return result


# ── Factory ────────────────────────────────────────────────────
def build_scorer(session: Session) -> Scorer:
    """Crea uno Scorer caricando le keyword attive dal DB."""
    keywords = get_active_keywords(session)
    return Scorer(keywords)
