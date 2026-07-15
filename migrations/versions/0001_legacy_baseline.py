"""Create the current schema on a fresh database.

Existing legacy databases must never execute this upgrade directly. They are
verified against the synthetic semantic fingerprint and then stamped by the
M02.02 runner. M02.01 tests that sequence without touching runtime data.
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_legacy_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "digestlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("run_at", sa.DateTime(), nullable=False),
        sa.Column("feeds_attempted", sa.Integer(), nullable=False),
        sa.Column("feeds_ok", sa.Integer(), nullable=False),
        sa.Column("feeds_failed", sa.Integer(), nullable=False),
        sa.Column("articles_fetched", sa.Integer(), nullable=False),
        sa.Column("articles_filtered", sa.Integer(), nullable=False),
        sa.Column("section1_count", sa.Integer(), nullable=False),
        sa.Column("section2_count", sa.Integer(), nullable=False),
        sa.Column("section3_count", sa.Integer(), nullable=False),
        sa.Column("sent_telegram", sa.Boolean(), nullable=False),
        sa.Column("sent_drive", sa.Boolean(), nullable=False),
        sa.Column("drive_file_path", sa.String(), nullable=True),
        sa.Column("error_log", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digestlog_digest_date", "digestlog", ["digest_date"], unique=False
    )

    op.create_table(
        "feedsource",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("consecutive_errors", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_feedsource_name", "feedsource", ["name"], unique=False)

    op.create_table(
        "keywordconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cluster", sa.String(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_keywordconfig_cluster", "keywordconfig", ["cluster"], unique=False
    )

    op.create_table(
        "article",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("feed_source_id", sa.Integer(), nullable=False),
        sa.Column("feed_name", sa.String(), nullable=False),
        sa.Column("feed_level", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("excerpt", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_detail", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("keyword_matches", sa.String(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("digest_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["feed_source_id"], ["feedsource.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_article_digest_date", "article", ["digest_date"])
    op.create_index("ix_article_score", "article", ["score"])
    op.create_index("ix_article_section", "article", ["section"])

    op.create_table(
        "feedstats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feed_source_id", sa.Integer(), nullable=False),
        sa.Column("feed_name", sa.String(), nullable=False),
        sa.Column("fetch_date", sa.Date(), nullable=False),
        sa.Column("articles_fetched", sa.Integer(), nullable=False),
        sa.Column("articles_relevant", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["feed_source_id"], ["feedsource.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feedstats_feed_date",
        "feedstats",
        ["feed_source_id", "fetch_date"],
    )
    op.create_index("ix_feedstats_fetch_date", "feedstats", ["fetch_date"])

    op.create_table(
        "keywordweighthistory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("cluster", sa.String(), nullable=False),
        sa.Column("peso_precedente", sa.Float(), nullable=False),
        sa.Column("peso_nuovo", sa.Float(), nullable=False),
        sa.Column("modificato_at", sa.DateTime(), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("applicato", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywordconfig.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "publishqueue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.String(), nullable=False),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("deferred_count", sa.Integer(), nullable=False),
        sa.Column("scheduled_hour", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "article_id",
            "digest_date",
            name="uq_publishqueue_article_digest",
        ),
    )
    op.create_index(
        "ix_publishqueue_digest_date", "publishqueue", ["digest_date"]
    )
    op.create_index(
        "ix_publishqueue_published_at", "publishqueue", ["published_at"]
    )
    op.create_index("ix_publishqueue_status", "publishqueue", ["status"])
    op.create_index(
        "ix_publishqueue_status_date",
        "publishqueue",
        ["status", "digest_date"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade 0001 disabilitato: per la baseline legacy usare il restore "
        "dello snapshot verificato."
    )
