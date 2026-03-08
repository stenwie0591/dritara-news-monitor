from datetime import datetime
from pathlib import Path
from typing import Generator

import yaml
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import Article, DigestLog, FeedSource, KeywordConfig

# ── Percorsi ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DB_PATH  = BASE_DIR / "data" / "dritara.db"
CFG_DIR  = BASE_DIR / "config"

# ── Engine singleton ───────────────────────────────────────────
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Crea tabelle e popola i dati iniziali se il DB è vuoto."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    logger.info(f"Database inizializzato: {DB_PATH}")

    with Session(engine) as session:
        _seed_feed_sources(session)
        _seed_keywords(session)


def get_session() -> Generator[Session, None, None]:
    """Dependency per ottenere una sessione DB."""
    with Session(engine) as session:
        yield session


# ── Seed feed sources ──────────────────────────────────────────
def _seed_feed_sources(session: Session) -> None:
    existing = session.exec(select(FeedSource)).all()
    if existing:
        return

    cfg_path = CFG_DIR / "feeds.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    feeds = config.get("feeds", [])
    for feed in feeds:
        source = FeedSource(
            name=feed["name"],
            url=feed["url"],
            level=feed["level"],
            category=feed["category"],
            region=feed.get("region"),
        )
        session.add(source)

    session.commit()
    logger.info(f"Feed sources inseriti: {len(feeds)}")


# ── Seed keywords ──────────────────────────────────────────────
def _seed_keywords(session: Session) -> None:
    existing = session.exec(select(KeywordConfig)).all()
    if existing:
        return

    cfg_path = CFG_DIR / "keywords.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    count = 0
    for cluster_id, cluster_data in config.get("clusters", {}).items():
        for kw in cluster_data.get("keywords", []):
            session.add(KeywordConfig(
                cluster=cluster_id,
                keyword=kw["word"],
                weight=kw["weight"],
            ))
            count += 1

    session.commit()
    logger.info(f"Keyword inserite: {count}")


# ── Query helpers ──────────────────────────────────────────────
def get_active_feeds(session: Session) -> list[FeedSource]:
    return session.exec(
        select(FeedSource).where(FeedSource.active == True)
    ).all()


def get_active_keywords(session: Session) -> list[KeywordConfig]:
    return session.exec(
        select(KeywordConfig).where(KeywordConfig.active == True)
    ).all()


def article_exists(session: Session, article_id: str) -> bool:
    return session.get(Article, article_id) is not None


def get_articles_by_date(session: Session, digest_date) -> list[Article]:
    return session.exec(
        select(Article).where(Article.digest_date == digest_date)
    ).all()


def get_digest_log(session: Session, digest_date) -> DigestLog | None:
    return session.exec(
        select(DigestLog).where(DigestLog.digest_date == digest_date)
    ).first()
