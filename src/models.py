from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
import json


class FeedSource(SQLModel, table=True):
    """Anagrafica dei 30 feed RSS monitorati."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    url: str = Field(unique=True)
    level: int = Field(ge=1, le=3)           # 1, 2 o 3
    category: str                             # tech | generalista | locale
    region: Optional[str] = None             # calabria | campania | puglia | sicilia | None
    active: bool = Field(default=True)
    last_fetched_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    consecutive_errors: int = Field(default=0)
    notes: Optional[str] = None


class Article(SQLModel, table=True):
    """Articolo raccolto da un feed, con score e sezione assegnata."""

    id: str = Field(primary_key=True)        # SHA-256 dell'URL
    feed_source_id: int = Field(foreign_key="feedsource.id")
    feed_name: str
    feed_level: int
    title: str
    url: str
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    # Scoring
    score: float = Field(default=0.0)
    score_detail: str = Field(default="{}")  # JSON: breakdown per cluster
    section: str = Field(default="discarded")  # section1|section2|section3|discarded
    keyword_matches: str = Field(default="[]")  # JSON: lista keyword trovate

    # Delivery
    sent_at: Optional[datetime] = None
    digest_date: Optional[date] = None

    def get_score_detail(self) -> dict:
        return json.loads(self.score_detail)

    def get_keyword_matches(self) -> list:
        return json.loads(self.keyword_matches)

    def set_score_detail(self, data: dict):
        self.score_detail = json.dumps(data, ensure_ascii=False)

    def set_keyword_matches(self, data: list):
        self.keyword_matches = json.dumps(data, ensure_ascii=False)


class DigestLog(SQLModel, table=True):
    """Log di ogni esecuzione del digest giornaliero."""

    id: Optional[int] = Field(default=None, primary_key=True)
    digest_date: date = Field(index=True)
    run_at: datetime = Field(default_factory=datetime.utcnow)

    # Statistiche fetch
    feeds_attempted: int = Field(default=0)
    feeds_ok: int = Field(default=0)
    feeds_failed: int = Field(default=0)
    articles_fetched: int = Field(default=0)
    articles_filtered: int = Field(default=0)

    # Statistiche sezioni
    section1_count: int = Field(default=0)
    section2_count: int = Field(default=0)
    section3_count: int = Field(default=0)

    # Delivery
    sent_telegram: bool = Field(default=False)
    sent_drive: bool = Field(default=False)
    drive_file_path: Optional[str] = None
    error_log: str = Field(default="[]")  # JSON: lista errori per fonte

    def get_error_log(self) -> list:
        return json.loads(self.error_log)

    def set_error_log(self, data: list):
        self.error_log = json.dumps(data, ensure_ascii=False)


class KeywordConfig(SQLModel, table=True):
    """Catalogo keyword attive con cluster e peso."""

    id: Optional[int] = Field(default=None, primary_key=True)
    cluster: str = Field(index=True)         # A | B | C
    keyword: str
    weight: float
    active: bool = Field(default=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class PublishQueue(SQLModel, table=True):
    """Coda di pubblicazione articoli approvati dall'admin."""
    id:           Optional[int]      = Field(default=None, primary_key=True)
    article_id:   str                = Field(foreign_key="article.id")
    digest_date:  date               = Field(index=True)
    position:     int                = Field()          # numero mostrato all'admin
    status:        str                = Field(default="pending")  # pending/approved/published/deferred
    deferred_count:  int               = Field(default=0)
    scheduled_hour:  Optional[int]     = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
