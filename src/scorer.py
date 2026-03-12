import re
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger
from sqlmodel import Session

from src.database import get_active_keywords
from src.models import KeywordConfig

# ── Keyword che richiedono contesto rafforzato ─────────────────
# Vengono accettate solo se appaiono con almeno una keyword
# STANDALONE dello stesso cluster nello stesso testo.
CONTEXT_REQUIRED = {
    # Cluster B — generiche, richiedono contesto tech
    "startup",
    "pnrr",
    "automazione",
    "brevetto",
    "spin-off",
    "smart city",
    "fondi europei",
    # Cluster C — generiche, richiedono contesto lavoro digitale
    "fuga dei cervelli",
    "talenti digitali",
    "stem",
    "brain drain",
    # Originali
    "ai",
    "ricerca",
    "università",
}

# ── Blacklist — termini che segnalano cronaca non pertinente ───
# Se una keyword tech appare in un articolo con questi termini,
# lo score viene azzerato e l'articolo scartato.
BLACKLIST = {
    "arresto",
    "arrestato",
    "arrestati",
    "sequestro",
    "sequestrato",
    "incidente",
    "incidenti",
    "sciopero",
    "scioperi",
    "delibera comunale",
    "consiglio regionale",
    "inaugurazione",
    "sagra",
    "traffico",
    "meteo",
    "omicidio",
    "omicidi",
    "rapina",
    "rapine",
    "camorra",
    "mafia",
    "ndrangheta",
}

# ── Boilerplate da rimuovere dagli excerpt ─────────────────────
# Pattern ricorrenti nei feed che inquinano il testo con nomi di testate.
BOILERPLATE_PATTERNS = [
    re.compile(r"^Il Quotidiano del Sud\s+", re.IGNORECASE),
    re.compile(r"\s+Il Quotidiano del Sud\s*\.\s*$", re.IGNORECASE),
    re.compile(r"^Corriere della Calabria\s+", re.IGNORECASE),
    re.compile(r"\[&#8230;\].*$"),  # tronca il suffisso RSS tipico
    re.compile(r"\[…\].*$"),
]

# ── Moltiplicatore territoriale ────────────────────────────────
# Applicato quando Cluster A e Cluster B co-occorrono nello stesso articolo.
TERRITORIAL_BOOST = 1.5

# ── Finestra proximity per CONTEXT_REQUIRED ────────────────────
PROXIMITY_WINDOW = 20  # parole


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

    Formula base:
        score = (score_titolo × 2.0) + (score_excerpt × 1.0) + bonus_fonte

    Regole avanzate:
        - Territorial boost × 1.5 se Cluster A e Cluster B co-occorrono
        - CONTEXT_REQUIRED: accettate solo se una keyword STANDALONE
          dello stesso cluster appare entro PROXIMITY_WINDOW parole
        - Blacklist: articolo scartato se contiene termini di cronaca non pertinente

    Sezioni:
        section1 — Cluster A AND (Cluster B OR Cluster C)
        section2 — Cluster B OR Cluster C (senza A)
        section3 — solo Cluster A
        discarded — nessun cluster o blacklist attivata
    """

    SOURCE_BONUS = {1: 0.5, 2: 0.0, 3: 1.0}
    TITLE_MULTIPLIER = 2.0
    EXCERPT_MULTIPLIER = 1.0

    def __init__(self, keywords: list[KeywordConfig]):
        self._patterns: dict[str, list[tuple]] = {"A": [], "B": [], "C": []}
        self._blacklist_patterns: list[re.Pattern] = []
        self._compile(keywords)
        self._compile_blacklist()
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

    def _compile_blacklist(self) -> None:
        """Pre-compila i pattern della blacklist."""
        for term in BLACKLIST:
            self._blacklist_patterns.append(
                re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
            )

    def _clean_excerpt(self, excerpt: str) -> str:
        """Rimuove boilerplate ricorrenti dall'excerpt."""
        for pattern in BOILERPLATE_PATTERNS:
            excerpt = pattern.sub("", excerpt)
        return excerpt.strip()

    def _has_blacklist(self, text: str) -> Optional[str]:
        """
        Controlla se il testo contiene termini blacklist.
        Ritorna il termine trovato, o None se pulito.
        """
        for pattern in self._blacklist_patterns:
            m = pattern.search(text)
            if m:
                return m.group(0)
        return None

    def _check_proximity(self, text: str, context_kw: str, cluster: str) -> bool:
        """
        Verifica se una keyword CONTEXT_REQUIRED appare entro PROXIMITY_WINDOW
        parole da una keyword STANDALONE dello stesso cluster.
        """
        words = text.lower().split()
        # Trova le posizioni della keyword ambigua
        context_positions = []
        ctx_pattern = re.compile(r"\b" + re.escape(context_kw) + r"\b", re.IGNORECASE)
        for i, w in enumerate(words):
            if ctx_pattern.search(w):
                context_positions.append(i)

        if not context_positions:
            return False

        # Trova le posizioni delle keyword STANDALONE dello stesso cluster
        standalone_positions = []
        for pattern, _, word in self._patterns[cluster]:
            if word not in CONTEXT_REQUIRED:
                for i, w in enumerate(words):
                    if pattern.search(w):
                        standalone_positions.append(i)

        if not standalone_positions:
            return False

        # Controlla se almeno una coppia è entro la finestra
        for cp in context_positions:
            for sp in standalone_positions:
                if abs(cp - sp) <= PROXIMITY_WINDOW:
                    return True

        return False

    def _match_text(self, text: str, cluster: str) -> tuple[float, list[str]]:
        """
        Trova le keyword di un cluster nel testo.
        Le keyword CONTEXT_REQUIRED vengono accettate solo se:
        - almeno una keyword STANDALONE dello stesso cluster è presente nel testo
        - E appare entro PROXIMITY_WINDOW parole (proximity check)
        Ritorna (score_parziale, lista_keyword_trovate).
        """
        raw_found = []
        for pattern, weight, word in self._patterns[cluster]:
            if pattern.search(text):
                raw_found.append((word, weight))

        definite = [(w, wt) for w, wt in raw_found if w not in CONTEXT_REQUIRED]
        ambiguous = [(w, wt) for w, wt in raw_found if w in CONTEXT_REQUIRED]

        # Le keyword ambigue richiedono:
        # 1. almeno una keyword definite presente
        # 2. proximity check entro PROXIMITY_WINDOW parole
        accepted_ambiguous = []
        if definite:
            for w, wt in ambiguous:
                if self._check_proximity(text, w, cluster):
                    accepted_ambiguous.append((w, wt))
                else:
                    logger.debug(
                        f"CONTEXT_REQUIRED '{w}' scartata: nessuna keyword entro {PROXIMITY_WINDOW} parole"
                    )

        accepted = definite + accepted_ambiguous
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
        excerpt = self._clean_excerpt(excerpt or "")
        result = ScoreResult()
        all_matches = []

        detail = {}
        has_cluster = {"A": False, "B": False, "C": False}

        # ── Blacklist check ────────────────────────────────────
        full_text = f"{title} {excerpt}"
        blacklisted = self._has_blacklist(full_text)
        if blacklisted:
            logger.debug(f"Blacklist '{blacklisted}': {title[:60]}")
            detail["blacklisted"] = blacklisted
            detail["total"] = 0.0
            result.score = 0.0
            result.section = "discarded"
            result.score_detail = detail
            return result

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

        # ── Score base ─────────────────────────────────────────
        base_score = sum(detail[f"cluster_{c}_score"] for c in ("A", "B", "C"))

        # ── Territorial boost ──────────────────────────────────
        # Applicato se Cluster A e Cluster B co-occorrono
        territorial_boost_applied = False
        if has_cluster["A"] and has_cluster["B"]:
            base_score = round(base_score * TERRITORIAL_BOOST, 3)
            territorial_boost_applied = True
            logger.debug(
                f"Territorial boost ×{TERRITORIAL_BOOST} applicato: {title[:60]}"
            )

        detail["territorial_boost"] = territorial_boost_applied
        total = round(base_score + bonus, 3)
        detail["total"] = total

        # ── Assegnazione sezione ───────────────────────────────
        has_A = has_cluster["A"]
        has_B = has_cluster["B"]
        has_C = has_cluster["C"]

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
