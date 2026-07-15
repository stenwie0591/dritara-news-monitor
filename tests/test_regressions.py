"""Regression tests for production-impacting serialization and feed creation bugs."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import Article, FeedSource, PublishQueue


def test_article_scoring_metadata_uses_valid_json() -> None:
    article = Article(
        id="article-id",
        feed_source_id=1,
        feed_name="Test feed",
        feed_level=1,
        title="Test article",
        url="https://example.com/article",
    )

    detail = {"territorial_boost": True, "total": 12.5}
    matches = ["calabria", "startup"]
    article.set_score_detail(detail)
    article.set_keyword_matches(matches)

    assert json.loads(article.score_detail) == detail
    assert json.loads(article.keyword_matches) == matches
    assert article.get_score_detail() == detail
    assert article.get_keyword_matches() == matches


def test_article_reads_legacy_python_serialization() -> None:
    article = Article(
        id="legacy-id",
        feed_source_id=1,
        feed_name="Legacy feed",
        feed_level=1,
        title="Legacy article",
        url="https://example.com/legacy",
        score_detail="{'territorial_boost': True, 'total': 9.5}",
        keyword_matches="['calabria', 'startup']",
    )

    assert article.get_score_detail()["territorial_boost"] is True
    assert article.get_keyword_matches() == ["calabria", "startup"]


def test_publish_queue_rejects_duplicate_article_in_same_digest() -> None:
    from datetime import date

    from sqlalchemy.exc import IntegrityError

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            PublishQueue(
                article_id="same-article",
                digest_date=date(2026, 7, 14),
                position=1,
            )
        )
        session.commit()
        session.add(
            PublishQueue(
                article_id="same-article",
                digest_date=date(2026, 7, 14),
                position=2,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_csv_cells_cannot_become_spreadsheet_formulas(prefix: str) -> None:
    from src.drive import _safe_csv_cell

    assert _safe_csv_cell(f"{prefix}SUM(1,1)").startswith("'")


@pytest.mark.asyncio
async def test_feedadd_accepts_multiword_name_and_sets_category() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        response = AsyncMock()
        response.raise_for_status = lambda: None
        response.text = "<rss/>"

        client = AsyncMock()
        client.get.return_value = response
        client_context = AsyncMock()
        client_context.__aenter__.return_value = client

        with (
            patch("src.bot.get_session", create=True, return_value=iter([session])),
            patch("src.database.get_session", return_value=iter([session])),
            patch("src.bot._send", new_callable=AsyncMock),
            patch("src.bot.httpx.AsyncClient", return_value=client_context),
            patch(
                "src.bot.get_public_feed",
                new_callable=AsyncMock,
                return_value=response,
            ),
            patch("src.bot.feedparser.parse") as parse,
        ):
            parse.return_value.bozo = False
            parse.return_value.entries = [{"title": "Example"}]

            from src.bot import _handle_feedadd

            await _handle_feedadd(
                "/feedadd https://example.com/rss Example News Feed 3"
            )

        feed = session.exec(select(FeedSource)).one()
        assert feed.name == "Example News Feed"
        assert feed.level == 3
        assert feed.category == "locale"
