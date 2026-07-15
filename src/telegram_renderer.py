"""Rendering HTML sicuro per tutti i messaggi Telegram di Dritara."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable
from unicodedata import category, normalize
from urllib.parse import urlsplit


TELEGRAM_MAX_CHARS = 4096
DEFAULT_FIELD_CHARS = 1024
ALLOWED_SCHEMES = frozenset({"http", "https"})


class HtmlFragment(str):
    """Frammento già escapato, creato esclusivamente da TelegramRenderer."""


@dataclass(frozen=True)
class TelegramMessage:
    """Messaggio pronto per Telegram con markup HTML bilanciato."""

    text: str
    parse_mode: str = "HTML"

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("Il messaggio Telegram non può essere vuoto")
        if len(self.text) > TELEGRAM_MAX_CHARS:
            raise ValueError("Il messaggio Telegram supera il limite sicuro")


def _clean(value: object, *, limit: int | None = None) -> str:
    """Normalizza testo e rimuove controlli, inclusi override bidi invisibili."""
    raw = normalize("NFC", str(value or "")).replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(
        char
        for char in raw
        if char == "\n" or (category(char) not in {"Cc", "Cf", "Cs"})
    )
    if limit is not None:
        cleaned = cleaned[:limit]
    return cleaned


class TelegramRenderer:
    """Costruisce soltanto HTML Telegram da dati escapati e link validati."""

    def text(self, value: object, *, limit: int | None = DEFAULT_FIELD_CHARS) -> HtmlFragment:
        return HtmlFragment(escape(_clean(value, limit=limit), quote=False))

    def join(self, *parts: object) -> HtmlFragment:
        return HtmlFragment(
            "".join(
                str(part) if isinstance(part, HtmlFragment) else str(self.text(part))
                for part in parts
            )
        )

    def bold(self, value: object, *, limit: int | None = DEFAULT_FIELD_CHARS) -> HtmlFragment:
        return HtmlFragment(f"<b>{self.text(value, limit=limit)}</b>")

    def italic(self, value: object, *, limit: int | None = DEFAULT_FIELD_CHARS) -> HtmlFragment:
        return HtmlFragment(f"<i>{self.text(value, limit=limit)}</i>")

    def code(self, value: object, *, limit: int | None = DEFAULT_FIELD_CHARS) -> HtmlFragment:
        return HtmlFragment(f"<code>{self.text(value, limit=limit)}</code>")

    def link(
        self,
        label: object,
        url: object,
        *,
        label_limit: int | None = DEFAULT_FIELD_CHARS,
    ) -> HtmlFragment:
        safe_label = self.text(label, limit=label_limit)
        safe_url = self.safe_url(url)
        if safe_url is None:
            return safe_label
        return HtmlFragment(f'<a href="{escape(safe_url, quote=True)}">{safe_label}</a>')

    def safe_url(self, value: object) -> str | None:
        candidate = _clean(value, limit=2048).strip()
        try:
            parsed = urlsplit(candidate)
            port = parsed.port
        except (TypeError, ValueError):
            return None
        if (
            parsed.scheme.lower() not in ALLOWED_SCHEMES
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or port is not None and not 1 <= port <= 65535
        ):
            return None
        return candidate

    def message(self, *parts: object) -> TelegramMessage:
        return TelegramMessage(str(self.join(*parts)))

    def split_lines(self, lines: Iterable[HtmlFragment]) -> list[TelegramMessage]:
        """Divide solo tra righe, così non spezza tag o HTML entity."""
        messages: list[TelegramMessage] = []
        current = ""
        for line in lines:
            rendered = str(line)
            if len(rendered) > TELEGRAM_MAX_CHARS:
                raise ValueError("Una singola riga Telegram supera il limite sicuro")
            candidate = rendered if not current else f"{current}\n{rendered}"
            if len(candidate) <= TELEGRAM_MAX_CHARS:
                current = candidate
            else:
                messages.append(TelegramMessage(current))
                current = rendered
        if current:
            messages.append(TelegramMessage(current))
        return messages

    def plain_messages(self, value: object) -> list[TelegramMessage]:
        """Default fail-safe per chiamanti legacy: nessun markup viene interpretato."""
        cleaned = _clean(value)
        if not cleaned:
            cleaned = " "

        chunks: list[str] = []
        current = ""
        for char in cleaned:
            rendered = escape(char, quote=False)
            if current and len(current) + len(rendered) > TELEGRAM_MAX_CHARS:
                chunks.append(current)
                current = ""
            current += rendered
        if current:
            chunks.append(current)
        return [TelegramMessage(chunk) for chunk in chunks]


telegram_renderer = TelegramRenderer()
