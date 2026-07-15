import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from src.url_security import (
    MAX_FEED_BYTES,
    FetchBudget,
    PublicNetworkBackend,
    SafeAsyncHTTPTransport,
    UnsafeFeedUrl,
    build_safe_http_client,
    ensure_public_feed_url,
    get_public_feed,
    validate_feed_url_syntax,
    validate_public_addresses,
)


class FakeStream:
    def __init__(self, peer: str | None) -> None:
        self.peer = peer
        self.closed = False

    def get_extra_info(self, name: str):
        if name == "server_addr" and self.peer is not None:
            return (self.peer, 443)
        return None

    async def aclose(self) -> None:
        self.closed = True


class FakeClient:
    dritara_safe_egress = True

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses

    def build_request(self, method: str, url: str) -> httpx.Request:
        return httpx.Request(method, url)

    async def send(self, request, *, stream: bool, follow_redirects: bool):
        assert stream is True
        assert follow_redirects is False
        response = self.responses.pop(0)
        response.request = request
        return response


def make_response(
    status: int = 200,
    *,
    content: bytes = b"<rss />",
    headers: dict[str, str] | None = None,
    peer: str | None = "93.184.216.34",
) -> httpx.Response:
    extensions = {"network_stream": FakeStream(peer)} if peer is not None else {}
    return httpx.Response(status, headers=headers, content=content, extensions=extensions)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/feed",
        "https://user:pass@example.com/feed",
        "https:///feed",
    ],
)
def test_rejects_unsafe_url_syntax(url: str) -> None:
    with pytest.raises(UnsafeFeedUrl):
        validate_feed_url_syntax(url)


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1"],
)
def test_rejects_non_public_addresses(address: str) -> None:
    with pytest.raises(UnsafeFeedUrl):
        validate_public_addresses([address])


def test_accepts_public_addresses() -> None:
    validate_public_addresses(["1.1.1.1", "2606:4700:4700::1111"])


@pytest.mark.asyncio
async def test_dns_resolution_is_validated() -> None:
    resolver = AsyncMock(return_value=["127.0.0.1"])
    with pytest.raises(UnsafeFeedUrl):
        await ensure_public_feed_url("https://example.com/rss", resolver=resolver)


@pytest.mark.asyncio
async def test_redirect_target_is_revalidated(monkeypatch) -> None:
    validated: list[str] = []

    async def fake_validate(url: str) -> str:
        validated.append(url)
        if "localhost" in url:
            raise UnsafeFeedUrl("private")
        return url

    redirect = make_response(302, headers={"location": "http://localhost/admin"})
    client = FakeClient([redirect])
    monkeypatch.setattr("src.url_security.ensure_public_feed_url", fake_validate)

    with pytest.raises(UnsafeFeedUrl):
        await get_public_feed(client, "https://example.com/rss", timeout=10)

    assert validated == ["https://example.com/rss", "http://localhost/admin"]


@pytest.mark.asyncio
async def test_rejects_client_without_safe_egress_policy() -> None:
    with pytest.raises(UnsafeFeedUrl, match="egress policy"):
        await get_public_feed(AsyncMock(), "https://example.com/rss", timeout=10)


@pytest.mark.asyncio
async def test_rejects_private_or_missing_connected_peer(monkeypatch) -> None:
    async def public_url(url: str) -> str:
        return url

    monkeypatch.setattr("src.url_security.ensure_public_feed_url", public_url)
    for response in [make_response(peer="127.0.0.1"), make_response(peer=None)]:
        with pytest.raises(UnsafeFeedUrl):
            await get_public_feed(
                FakeClient([response]), "https://example.com/rss", timeout=10
            )


@pytest.mark.asyncio
async def test_streaming_cap_rejects_declared_and_actual_oversize(monkeypatch) -> None:
    async def public_url(url: str) -> str:
        return url

    monkeypatch.setattr("src.url_security.ensure_public_feed_url", public_url)
    responses = [
        make_response(headers={"content-length": str(MAX_FEED_BYTES + 1)}),
        make_response(content=b"x" * (MAX_FEED_BYTES + 1)),
    ]
    for response in responses:
        with pytest.raises(UnsafeFeedUrl, match="2 MiB"):
            await get_public_feed(
                FakeClient([response]), "https://example.com/rss", timeout=10
            )


@pytest.mark.asyncio
async def test_run_budget_is_shared_and_fail_closed(monkeypatch) -> None:
    async def public_url(url: str) -> str:
        return url

    monkeypatch.setattr("src.url_security.ensure_public_feed_url", public_url)
    budget = FetchBudget(limit=5)
    first = await get_public_feed(
        FakeClient([make_response(content=b"123")]),
        "https://example.com/one",
        timeout=10,
        budget=budget,
    )
    assert first.content == b"123"
    with pytest.raises(UnsafeFeedUrl, match="Quota"):
        await get_public_feed(
            FakeClient([make_response(content=b"456")]),
            "https://example.com/two",
            timeout=10,
            budget=budget,
        )
    assert budget.consumed == 3


@pytest.mark.asyncio
async def test_total_redirect_chain_timeout(monkeypatch) -> None:
    async def public_url(url: str) -> str:
        return url

    class SlowClient(FakeClient):
        async def send(self, request, *, stream: bool, follow_redirects: bool):
            await asyncio.sleep(0.02)
            return await super().send(
                request, stream=stream, follow_redirects=follow_redirects
            )

    monkeypatch.setattr("src.url_security.ensure_public_feed_url", public_url)
    with pytest.raises(TimeoutError):
        await get_public_feed(
            SlowClient([make_response()]),
            "https://example.com/rss",
            timeout=0.001,
        )


@pytest.mark.asyncio
async def test_network_backend_connects_to_validated_ip_not_hostname() -> None:
    resolver = AsyncMock(return_value=["93.184.216.34"])
    stream = FakeStream("93.184.216.34")
    backend = AsyncMock()
    backend.connect_tcp.return_value = stream
    policy = PublicNetworkBackend(resolver=resolver, backend=backend)

    result = await policy.connect_tcp("example.com", 443)

    assert result is stream
    resolver.assert_awaited_once_with("example.com", 443)
    assert backend.connect_tcp.await_args.args[:2] == ("93.184.216.34", 443)


@pytest.mark.asyncio
async def test_network_backend_rejects_dns_private_and_peer_mismatch() -> None:
    backend = AsyncMock()
    private = PublicNetworkBackend(
        resolver=AsyncMock(return_value=["169.254.169.254"]), backend=backend
    )
    with pytest.raises(UnsafeFeedUrl):
        await private.connect_tcp("metadata.invalid", 80)
    backend.connect_tcp.assert_not_awaited()

    stream = FakeStream("1.1.1.1")
    backend.connect_tcp.return_value = stream
    mismatch = PublicNetworkBackend(
        resolver=AsyncMock(return_value=["93.184.216.34"]), backend=backend
    )
    with pytest.raises(UnsafeFeedUrl, match="diverso"):
        await mismatch.connect_tcp("example.com", 443)
    assert stream.closed is True


@pytest.mark.asyncio
async def test_safe_client_disables_automatic_redirects_and_environment_proxy() -> None:
    client = build_safe_http_client()
    try:
        assert client.follow_redirects is False
        assert client.trust_env is False
        assert isinstance(client._transport, SafeAsyncHTTPTransport)
    finally:
        await client.aclose()
