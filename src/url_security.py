"""Policy di rete per feed RSS non attendibili.

La validazione applicativa riduce il rischio SSRF. In produzione va affiancata a
regole egress del sistema operativo che blocchino reti private e link-local.
"""

import asyncio
import ipaddress
import socket
from dataclasses import dataclass, field
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpcore
import httpx

MAX_REDIRECTS = 3
MAX_FEED_BYTES = 2 * 1024 * 1024
MAX_FETCH_RUN_BYTES = 32 * 1024 * 1024
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class UnsafeFeedUrl(ValueError):
    """URL non ammesso dalla policy di fetch pubblico."""


@dataclass
class FetchBudget:
    """Quota condivisa e concurrency-safe per un intero ciclo RSS."""

    limit: int = MAX_FETCH_RUN_BYTES
    consumed: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def consume(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("La quota RSS non accetta byte negativi")
        async with self._lock:
            if self.consumed + amount > self.limit:
                raise UnsafeFeedUrl("Quota byte del ciclo RSS superata")
            self.consumed += amount


def validate_feed_url_syntax(url: str) -> str:
    """Valida e normalizza gli aspetti sintattici che non richiedono DNS."""
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeFeedUrl("Sono ammessi solo URL http o https")
    if not parsed.hostname:
        raise UnsafeFeedUrl("Hostname mancante")
    if parsed.username or parsed.password:
        raise UnsafeFeedUrl("Credenziali nell'URL non ammesse")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeFeedUrl("Porta URL non valida") from exc
    if port is not None and not 1 <= port <= 65535:
        raise UnsafeFeedUrl("Porta URL non valida")
    return parsed.geturl()


def validate_public_addresses(addresses: list[str]) -> None:
    """Rifiuta la destinazione se anche un solo indirizzo non è pubblico."""
    if not addresses:
        raise UnsafeFeedUrl("Hostname senza indirizzi risolvibili")
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise UnsafeFeedUrl("Indirizzo IP non valido") from exc
        if not address.is_global:
            raise UnsafeFeedUrl("Destinazione di rete privata o riservata")


async def _resolve(hostname: str, port: int) -> list[str]:
    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(
        hostname,
        port,
        family=socket.AF_UNSPEC,
        type=socket.SOCK_STREAM,
    )
    return sorted({record[4][0] for record in records})


def _canonical_addresses(addresses: list[str]) -> list[str]:
    validate_public_addresses(addresses)
    return sorted({str(ipaddress.ip_address(address)) for address in addresses})


def _peer_address(stream: Any) -> str:
    if stream is None or not hasattr(stream, "get_extra_info"):
        raise UnsafeFeedUrl("Peer IP non verificabile")
    server = stream.get_extra_info("server_addr")
    if isinstance(server, (tuple, list)) and server:
        server = server[0]
    if not isinstance(server, str):
        raise UnsafeFeedUrl("Peer IP non verificabile")
    return str(ipaddress.ip_address(server))


class PublicNetworkBackend(httpcore.AsyncNetworkBackend):
    """Backend che risolve e connette direttamente solo a IP pubblici."""

    def __init__(
        self,
        resolver: Callable[[str, int], Awaitable[list[str]]] = _resolve,
        backend: httpcore.AsyncNetworkBackend | None = None,
    ) -> None:
        self._resolver = resolver
        self._backend = backend or httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ):
        addresses = _canonical_addresses(await self._resolver(host, port))
        # Un solo tentativo deterministico: nessun retry implicito su altri IP.
        stream = await self._backend.connect_tcp(
            addresses[0],
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )
        try:
            peer = _peer_address(stream)
            validate_public_addresses([peer])
            if peer not in addresses:
                raise UnsafeFeedUrl("Peer IP diverso dagli indirizzi DNS validati")
        except Exception:
            await stream.aclose()
            raise
        return stream

    async def connect_unix_socket(self, *args, **kwargs):
        raise UnsafeFeedUrl("Unix socket non ammesso per feed RSS")

    async def sleep(self, seconds: float) -> None:
        await self._backend.sleep(seconds)


class SafeAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    """HTTPX transport senza proxy/retry e con connect DNS-pinned."""

    def __init__(
        self,
        *,
        resolver: Callable[[str, int], Awaitable[list[str]]] = _resolve,
    ) -> None:
        super().__init__(trust_env=False, retries=0, limits=httpx.Limits(max_keepalive_connections=0))
        self._pool._network_backend = PublicNetworkBackend(resolver=resolver)


class SafeAsyncClient(httpx.AsyncClient):
    """Marker di tipo per impedire fetch RSS con client/proxy non governati."""

    dritara_safe_egress = True


def build_safe_http_client(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15,
    resolver: Callable[[str, int], Awaitable[list[str]]] = _resolve,
) -> SafeAsyncClient:
    return SafeAsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        transport=SafeAsyncHTTPTransport(resolver=resolver),
    )


async def ensure_public_feed_url(
    url: str,
    resolver: Callable[[str, int], Awaitable[list[str]]] = _resolve,
) -> str:
    """Valida sintassi e risoluzione DNS immediatamente prima del fetch."""
    normalized = validate_feed_url_syntax(url)
    parsed = urlsplit(normalized)
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    validate_public_addresses(await resolver(parsed.hostname or "", port))
    return normalized


async def get_public_feed(
    client: httpx.AsyncClient,
    url: str,
    *,
    timeout: float,
    max_redirects: int = MAX_REDIRECTS,
    budget: FetchBudget | None = None,
) -> httpx.Response:
    """Fetch bounded con redirect, DNS, connect e peer IP fail-closed."""
    if getattr(client, "dritara_safe_egress", False) is not True:
        raise UnsafeFeedUrl("Client RSS privo di egress policy")

    current = url
    async with asyncio.timeout(timeout):
        for redirect_count in range(max_redirects + 1):
            current = await ensure_public_feed_url(current)
            request = client.build_request("GET", current)
            response = await client.send(request, stream=True, follow_redirects=False)
            try:
                peer = _peer_address(response.extensions.get("network_stream"))
                validate_public_addresses([peer])

                if response.status_code in REDIRECT_STATUSES:
                    if redirect_count == max_redirects:
                        raise UnsafeFeedUrl("Troppi redirect")
                    location = response.headers.get("location")
                    if not location:
                        raise UnsafeFeedUrl("Redirect senza destinazione")
                    current = urljoin(current, location)
                    continue

                declared_length = response.headers.get("content-length")
                if declared_length is not None:
                    try:
                        declared_bytes = int(declared_length)
                    except ValueError as exc:
                        raise UnsafeFeedUrl("Content-Length RSS non valido") from exc
                    if declared_bytes < 0 or declared_bytes > MAX_FEED_BYTES:
                        raise UnsafeFeedUrl("Feed oltre il limite di 2 MiB")

                content = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(content) + len(chunk) > MAX_FEED_BYTES:
                        raise UnsafeFeedUrl("Feed oltre il limite di 2 MiB")
                    if budget is not None:
                        await budget.consume(len(chunk))
                    content.extend(chunk)

                return httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=bytes(content),
                    request=request,
                )
            finally:
                await response.aclose()

    raise UnsafeFeedUrl("Redirect non valido")
