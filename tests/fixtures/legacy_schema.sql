PRAGMA foreign_keys = OFF;

CREATE TABLE digestlog (
    id INTEGER NOT NULL PRIMARY KEY,
    digest_date DATE NOT NULL,
    run_at DATETIME NOT NULL,
    feeds_attempted INTEGER NOT NULL,
    feeds_ok INTEGER NOT NULL,
    feeds_failed INTEGER NOT NULL,
    articles_fetched INTEGER NOT NULL,
    articles_filtered INTEGER NOT NULL,
    section1_count INTEGER NOT NULL,
    section2_count INTEGER NOT NULL,
    section3_count INTEGER NOT NULL,
    sent_telegram BOOLEAN NOT NULL,
    sent_drive BOOLEAN NOT NULL,
    drive_file_path VARCHAR,
    error_log VARCHAR NOT NULL
);
CREATE INDEX ix_digestlog_digest_date ON digestlog (digest_date);

CREATE TABLE feedsource (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL,
    url VARCHAR NOT NULL UNIQUE,
    level INTEGER NOT NULL,
    category VARCHAR NOT NULL,
    region VARCHAR,
    active BOOLEAN NOT NULL,
    last_fetched_at DATETIME,
    last_success_at DATETIME,
    consecutive_errors INTEGER NOT NULL,
    notes VARCHAR
);
CREATE INDEX ix_feedsource_name ON feedsource (name);

CREATE TABLE keywordconfig (
    id INTEGER NOT NULL PRIMARY KEY,
    cluster VARCHAR NOT NULL,
    keyword VARCHAR NOT NULL,
    weight FLOAT NOT NULL,
    active BOOLEAN NOT NULL,
    added_at DATETIME NOT NULL
);
CREATE INDEX ix_keywordconfig_cluster ON keywordconfig (cluster);

CREATE TABLE article (
    id VARCHAR NOT NULL PRIMARY KEY,
    feed_source_id INTEGER NOT NULL REFERENCES feedsource (id),
    feed_name VARCHAR NOT NULL,
    feed_level INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    excerpt VARCHAR,
    published_at DATETIME,
    fetched_at DATETIME NOT NULL,
    score FLOAT NOT NULL,
    score_detail VARCHAR NOT NULL,
    section VARCHAR NOT NULL,
    keyword_matches VARCHAR NOT NULL,
    sent_at DATETIME,
    digest_date DATE
);

CREATE TABLE feedstats (
    id INTEGER NOT NULL PRIMARY KEY,
    feed_source_id INTEGER NOT NULL REFERENCES feedsource (id),
    feed_name VARCHAR NOT NULL,
    fetch_date DATE NOT NULL,
    articles_fetched INTEGER NOT NULL,
    articles_relevant INTEGER NOT NULL
);
CREATE INDEX ix_feedstats_fetch_date ON feedstats (fetch_date);

CREATE TABLE keywordweighthistory (
    id INTEGER NOT NULL PRIMARY KEY,
    keyword_id INTEGER NOT NULL REFERENCES keywordconfig (id),
    keyword VARCHAR NOT NULL,
    cluster VARCHAR NOT NULL,
    peso_precedente FLOAT NOT NULL,
    peso_nuovo FLOAT NOT NULL,
    modificato_at DATETIME NOT NULL,
    motivo VARCHAR NOT NULL,
    applicato BOOLEAN NOT NULL
);

CREATE TABLE publishqueue (
    id INTEGER NOT NULL PRIMARY KEY,
    article_id VARCHAR NOT NULL REFERENCES article (id),
    digest_date DATE NOT NULL,
    position INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    deferred_count INTEGER NOT NULL,
    scheduled_hour INTEGER,
    published_at DATETIME
);
CREATE INDEX ix_publishqueue_digest_date ON publishqueue (digest_date);

INSERT INTO feedsource (
    id, name, url, level, category, region, active,
    last_fetched_at, last_success_at, consecutive_errors, notes
) VALUES (
    1, 'Fixture Feed', 'https://example.invalid/feed.xml', 2,
    'tech', NULL, 1, NULL, NULL, 0, 'synthetic fixture'
);
