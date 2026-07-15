"""Contract e abuse test per il rendering Telegram centralizzato."""

from html import unescape

import pytest
from pydantic import SecretStr

from src.config import RuntimeSettings
from src.formatter import DigestFormatter
from src.telegram_renderer import (
    TELEGRAM_MAX_CHARS,
    TelegramMessage,
    telegram_renderer,
)


def test_untrusted_text_cannot_open_html_entities() -> None:
    rendered = telegram_renderer.message(
        telegram_renderer.bold('Titolo </b><a href="https://evil.test">clicca')
    )

    assert rendered.parse_mode == "HTML"
    assert rendered.text.count("<b>") == 1
    assert rendered.text.count("</b>") == 1
    assert '<a href="https://evil.test">' not in rendered.text
    assert "&lt;a href=" in rendered.text


@pytest.mark.parametrize(
    "control",
    ["\x00", "\x1f", "\x7f", "\u200b", "\u202e", "\u2066", "\u2069"],
)
def test_control_and_bidi_characters_are_removed(control: str) -> None:
    rendered = telegram_renderer.message(f"prima{control}dopo")

    assert control not in rendered.text
    assert unescape(rendered.text) == "primadopo"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "https://user:secret@example.com/news",
        "//example.com/news",
        "https:///news",
    ],
)
def test_unsafe_links_fall_back_to_plain_label(url: str) -> None:
    rendered = telegram_renderer.link("Leggi", url)

    assert rendered == "Leggi"
    assert "href=" not in rendered


def test_valid_link_escapes_label_and_attribute() -> None:
    rendered = telegram_renderer.link(
        'Titolo </a><a href="https://evil.test">male',
        'https://example.com/news?q="x"&page=1',
    )

    assert rendered.count("<a ") == 1
    assert rendered.count("</a>") == 1
    assert "evil.test" not in rendered.split(">", 1)[0]
    assert "&quot;" in rendered
    assert "&amp;" in rendered


def test_plain_legacy_message_is_escaped_and_split_without_broken_entities() -> None:
    raw = "<&>" * 2000

    messages = telegram_renderer.plain_messages(raw)

    assert len(messages) > 1
    assert all(len(message.text) <= TELEGRAM_MAX_CHARS for message in messages)
    assert all(message.parse_mode == "HTML" for message in messages)
    assert "".join(unescape(message.text) for message in messages) == raw


def test_split_lines_never_breaks_balanced_markup() -> None:
    lines = [telegram_renderer.bold(f"Riga {index} " + "x" * 300) for index in range(30)]

    messages = telegram_renderer.split_lines(lines)

    assert len(messages) > 1
    assert all(len(message.text) <= TELEGRAM_MAX_CHARS for message in messages)
    assert all(message.text.count("<b>") == message.text.count("</b>") for message in messages)


@pytest.mark.asyncio
async def test_sender_contract_uses_renderer_for_legacy_text(monkeypatch) -> None:
    from src import sender_telegram

    payloads: list[dict] = []

    class Response:
        def json(self):
            return {"ok": True, "result": {"message_id": 42}}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, _url, **kwargs):
            payloads.append(kwargs["json"])
            return Response()

    monkeypatch.setattr(sender_telegram.httpx, "AsyncClient", Client)
    settings = RuntimeSettings(
        _env_file=None,
        telegram_bot_token=SecretStr("test-token"),
        telegram_admin_chat_id=1,
        telegram_admin_user_id=1,
        telegram_community_chat_id=-100,
        telegram_news_thread_id=2,
    )

    result = await sender_telegram._send(
        1,
        '*fidato* <a href="https://evil.test">male</a>\u202e',
        settings=settings,
    )

    assert result == 42
    assert payloads == [
        {
            "chat_id": 1,
            "text": '*fidato* &lt;a href="https://evil.test"&gt;male&lt;/a&gt;',
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
    ]


def test_message_rejects_oversize_html() -> None:
    with pytest.raises(ValueError, match="supera il limite"):
        TelegramMessage("x" * (TELEGRAM_MAX_CHARS + 1))


def test_digest_contract_does_not_allow_article_to_replace_link() -> None:
    article = {
        "title": 'Titolo</a><a href="https://evil.test">phishing\u202e',
        "excerpt": "Testo <b>falso</b>\x00",
        "feed_name": "Fonte & partner",
        "url": "https://example.com/news?q=1&lang=it",
        "score": 12.5,
    }

    block = DigestFormatter()._article_block(article)

    assert block.count("<a ") == 1
    assert block.count("</a>") == 1
    assert '<a href="https://evil.test"' not in block
    assert '&lt;a href="https://evil.test"&gt;' in block
    assert 'href="https://example.com/news?q=1&amp;lang=it"' in block
    assert "&lt;b&gt;falso&lt;/b&gt;" in block
    assert "\u202e" not in block
    assert "\x00" not in block
