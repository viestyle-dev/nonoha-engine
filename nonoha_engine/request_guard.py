"""Reject browser requests that come from foreign web sites.

A page the user opens in a browser can send requests to the engine
(``http://127.0.0.1:<port>``) and, with DNS rebinding, even make them look
same-origin. This pure ASGI middleware reads two headers before any route
runs, for HTTP requests and WebSocket handshakes alike:

- ``Host`` must be a name a public DNS cannot point at the engine (IP
  literals, ``localhost``, ``*.localhost``, single-label names, ``*.local``,
  this machine's host name) or one the operator allowed.
- ``Origin``, when present (browsers send it; other clients do not), must be
  the same origin, a loopback or private-network origin, or one the operator
  allowed.

It does not authenticate anyone: same-machine use and LAN use (``--host
0.0.0.0``) keep working without credentials. Established WebSocket frames
are never inspected, so streaming costs nothing extra.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from collections.abc import Iterable
from typing import Any, Awaitable, Callable, MutableMapping

logger = logging.getLogger(__name__)

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Origins of pages served from machines on the same (private) network:
# RFC 1918, RFC 6598 shared address space (Tailscale and other VPNs),
# IPv6 unique local and link local. Loopback is handled separately.
_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(n)
    for n in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "169.254.0.0/16",
        "fc00::/7",
        "fe80::/10",
    )
)

_DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443}

# Decisions are cached per distinct header value; a few clients send the
# same values over and over. The cap bounds memory against junk headers.
_CACHE_LIMIT = 256


def split_host(value: str) -> tuple[str, int | None]:
    """``"Example.com:8000"`` -> ``("example.com", 8000)``; brackets kept off IPv6."""
    value = value.strip().lower()
    port: int | None = None
    if value.startswith("["):
        end = value.find("]")
        if end < 0:
            return value, None
        host = value[1:end]
        rest = value[end + 1 :]
        if rest.startswith(":") and rest[1:].isdigit():
            port = int(rest[1:])
        return host, port
    if value.count(":") == 1:
        host, _, port_text = value.partition(":")
        if port_text.isdigit():
            port = int(port_text)
        value = host
    return value.rstrip("."), port


def _ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _is_loopback_name(host: str) -> bool:
    return host == "localhost" or host.endswith(".localhost")


def _is_lan_name(host: str) -> bool:
    """Names only the local network resolves: single labels and mDNS ``.local``."""
    return "." not in host or host.endswith(".local")


def _matches(host: str, patterns: frozenset[str], suffixes: tuple[str, ...]) -> bool:
    if host in patterns:
        return True
    for suffix in suffixes:  # ".example.com" allows example.com and its subdomains
        if host.endswith(suffix) or host == suffix[1:]:
            return True
    return False


def _split_patterns(values: Iterable[str]) -> tuple[frozenset[str], tuple[str, ...]]:
    exact: set[str] = set()
    suffixes: list[str] = []
    for raw in values:
        value = raw.strip().lower().rstrip(".")
        if not value:
            continue
        if value.startswith("."):
            suffixes.append(value)
        else:
            exact.add(value)
    return frozenset(exact), tuple(suffixes)


def is_public_name(host: str) -> bool:
    """Whether a Host allowance names something the internet can resolve."""
    host = host.strip().lower().lstrip(".").rstrip(".")
    return not (_ip(host) is not None or _is_loopback_name(host) or _is_lan_name(host))


class RequestGuard:
    """ASGI middleware: 403 for foreign ``Origin`` and rebound ``Host`` values."""

    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Iterable[str] = (),
        allow_hosts: Iterable[str] = (),
        own_names: Iterable[str] | None = None,
    ):
        self.app = app
        self._allow_origins = frozenset(o.strip().lower().rstrip("/") for o in allow_origins if o.strip())
        self._allow_hosts, self._allow_host_suffixes = _split_patterns(allow_hosts)
        if own_names is None:
            # gethostname() never touches DNS; getfqdn() can stall startup
            # on a broken resolver, so other FQDNs go through --allow-host.
            own_names = (socket.gethostname(),)
        self._own_names = frozenset(n.strip().lower().rstrip(".") for n in own_names if n)
        self._host_cache: dict[bytes, bool] = {}
        self._origin_cache: dict[tuple[bytes, bytes], bool] = {}
        self._logged: set[bytes] = set()  # one warning per rejected value

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        kind = scope["type"]
        if kind != "http" and kind != "websocket":
            await self.app(scope, receive, send)
            return

        host: bytes = b""
        origin: bytes = b""
        for key, value in scope["headers"]:
            if key == b"host":
                host = value
            elif key == b"origin":
                origin = value

        if host and not self._host_allowed(host):
            await self._reject(scope, send, "Host", host)
            return
        if origin and not self._origin_allowed(origin, host):
            await self._reject(scope, send, "Origin", origin)
            return
        await self.app(scope, receive, send)

    # --- decisions (cached) ---

    def _host_allowed(self, raw: bytes) -> bool:
        cached = self._host_cache.get(raw)
        if cached is not None:
            return cached
        name, _ = split_host(raw.decode("latin-1"))
        allowed = (
            _ip(name) is not None
            or _is_loopback_name(name)
            or _is_lan_name(name)
            or name in self._own_names
            or _matches(name, self._allow_hosts, self._allow_host_suffixes)
        )
        self._remember(self._host_cache, raw, allowed)
        return allowed

    def _origin_allowed(self, raw: bytes, host: bytes) -> bool:
        key = (raw, host)
        cached = self._origin_cache.get(key)
        if cached is not None:
            return cached
        allowed = self._decide_origin(raw.decode("latin-1").strip().lower(), host.decode("latin-1"))
        self._remember(self._origin_cache, key, allowed)
        return allowed

    def _decide_origin(self, origin: str, host_header: str) -> bool:
        if origin == "null":  # sandboxed frames and file:// pages
            return False
        if origin.rstrip("/") in self._allow_origins:
            return True
        scheme, sep, rest = origin.partition("://")
        if not sep:
            return False
        if scheme == "tauri":  # the Hub's own window
            return True
        name, port = split_host(rest.split("/", 1)[0])
        if port is None:
            port = _DEFAULT_PORTS.get(scheme)

        # Same origin: compared by name and port, not scheme, because a
        # tunnel or reverse proxy that terminates TLS turns https://x into
        # Host: x. A Host without a port accepts the origin's default port.
        if host_header:
            host_name, host_port = split_host(host_header)
            if name == host_name and (host_port is None or host_port == port):
                return True

        if _is_loopback_name(name) or _is_lan_name(name):
            return True
        address = _ip(name)
        if address is not None:
            if address.is_loopback:
                return True
            return any(address in net for net in _PRIVATE_NETWORKS)
        return False

    @staticmethod
    def _remember(cache: dict, key: Any, value: bool) -> None:
        if len(cache) >= _CACHE_LIMIT:
            cache.clear()
        cache[key] = value

    # --- rejection ---

    async def _reject(self, scope: Scope, send: Send, header: str, raw: bytes) -> None:
        value = raw.decode("latin-1")
        if raw not in self._logged:
            if len(self._logged) >= _CACHE_LIMIT:
                self._logged.clear()
            self._logged.add(raw)
            logger.warning(f"Rejected a request with {header}: {value!r} ({scope.get('path', '')})")
        if scope["type"] == "websocket":
            # Closing before accept makes the server answer the handshake with 403
            await send({"type": "websocket.close", "code": 1008})
            return
        if header == "Host":
            name, _ = split_host(value)
            hint = (
                f"This engine does not accept the host name '{name}'.\n"
                f"To allow it, start the engine with --allow-host {name} "
                f"(or a leading dot for all subdomains, e.g. --allow-host .{name.partition('.')[2] or name}),\n"
                f"or add it under 'Allowed host names' in the nonoha Hub start options.\n"
            )
        else:
            hint = (
                f"This engine does not accept requests from pages at '{value}'.\n"
                f"To allow that site, start the engine with --allow-origin {value}.\n"
            )
        body = hint.encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"text/plain; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
