"""RequestGuard: foreign Origins and rebound Hosts get 403; normal use passes."""

import asyncio

import pytest

from nonoha_engine.request_guard import RequestGuard, is_loopback_bind, is_public_name, split_host


async def _ok_app(scope, receive, send):
    if scope["type"] == "websocket":
        await send({"type": "websocket.accept"})
        return
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def _call(guard, host=None, origin=None, kind="http"):
    headers = []
    if host is not None:
        headers.append((b"host", host.encode()))
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    scope = {"type": kind, "path": "/node-flow/graphs", "headers": headers}
    sent = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        sent.append(message)

    asyncio.run(guard(scope, receive, send))
    return sent


def _status(sent):
    first = sent[0]
    if first["type"] == "websocket.accept":
        return 101
    if first["type"] == "websocket.close":
        return 403
    return first["status"]


def make(**kw):
    kw.setdefault("own_names", ("kiosk01",))
    return RequestGuard(_ok_app, **kw)


@pytest.mark.parametrize(
    "host, origin",
    [
        # Same machine (Hub, kiosk screen), dev editor on :3000, SSH port forwarding
        ("127.0.0.1:8000", "http://127.0.0.1:8000"),
        ("localhost:8000", "http://localhost:8000"),
        ("127.0.0.1:8765", "http://localhost:3000"),
        ("[::1]:8000", "http://[::1]:8000"),
        # Another PC on the LAN (bind 0.0.0.0), by IP and by mDNS name
        ("192.168.1.10:8000", "http://192.168.1.10:8000"),
        ("kiosk.local:8000", "http://kiosk.local:8000"),
        ("raspberrypi:8000", "http://raspberrypi:8000"),
        # Editor of engine A talking to engine B; VPN (Tailscale CGNAT range)
        ("192.168.1.11:8000", "http://192.168.1.10:8000"),
        ("100.101.102.103:8000", "http://100.101.102.103:8000"),
        ("100.101.102.104:8000", "http://100.101.102.103:8000"),
        # A page from a *.localhost name (a webview's virtual host) and this
        # machine's own host name
        ("127.0.0.1:8000", "http://tauri.localhost"),
        ("kiosk01:8000", "http://kiosk01:8000"),
    ],
)
def test_normal_use_passes(host, origin):
    assert _status(_call(make(), host, origin)) == 200


def test_non_browser_clients_pass():
    # CLI, Python, Flutter send no Origin
    assert _status(_call(make(), "127.0.0.1:8000")) == 200
    assert _status(_call(make(), "192.168.1.10:8000")) == 200
    assert _status(_call(make())) == 200


@pytest.mark.parametrize(
    "host, origin",
    [
        # A web page the user opened, calling the local engine
        ("127.0.0.1:8000", "https://evil.example"),
        ("localhost:8000", "http://attacker.test:8000"),
        # Sandboxed frame / file:// page
        ("127.0.0.1:8000", "null"),
        # Public IP origin
        ("127.0.0.1:8000", "http://203.0.113.5"),
    ],
)
def test_foreign_origin_rejected(host, origin):
    sent = _call(make(), host, origin)
    assert _status(sent) == 403
    assert b"--allow-origin" in sent[1]["body"]


def test_dns_rebinding_rejected_even_when_same_origin():
    # The attacker's name resolves to 127.0.0.1: Origin == Host, still refused
    sent = _call(make(), "rebind.attacker.test:8000", "http://rebind.attacker.test:8000")
    assert _status(sent) == 403
    assert b"--allow-host rebind.attacker.test" in sent[1]["body"]


def test_websocket_handshake_rejected():
    assert _status(_call(make(), "127.0.0.1:8000", "https://evil.example", kind="websocket")) == 403
    assert _status(_call(make(), "rebind.attacker.test", None, kind="websocket")) == 403
    assert _status(_call(make(), "127.0.0.1:8000", "http://127.0.0.1:8000", kind="websocket")) == 101


def test_vpn_fqdn_and_tunnels_need_allow_host():
    tailnet = "kiosk.tail1234.ts.net"
    assert _status(_call(make(), tailnet, f"http://{tailnet}")) == 403
    assert _status(_call(make(allow_hosts=[tailnet]), tailnet, f"http://{tailnet}")) == 200

    # A tunnel terminating TLS: Origin https://x, Host x (no port)
    tunnel = "abc123.ngrok-free.app"
    guard = make(allow_hosts=[".ngrok-free.app"])
    assert _status(_call(guard, tunnel, f"https://{tunnel}")) == 200
    assert _status(_call(guard, "ngrok-free.app", "https://ngrok-free.app")) == 200
    # The suffix does not open other domains, nor pages from another tunnel
    assert _status(_call(guard, "evil-ngrok-free.app", "https://evil-ngrok-free.app")) == 403
    assert _status(_call(guard, tunnel, "https://other.ngrok-free.app")) == 403


def test_company_dns_and_dashboards_need_allowances():
    name = "kiosk01.corp.example.com"
    assert _status(_call(make(), name)) == 403
    assert _status(_call(make(allow_hosts=[name]), name)) == 200

    dash = "https://dash.example.com"
    assert _status(_call(make(), "127.0.0.1:8000", dash)) == 403
    assert _status(_call(make(allow_origins=[dash]), "127.0.0.1:8000", dash)) == 200
    assert _status(_call(make(allow_origins=[dash + "/"]), "127.0.0.1:8000", dash)) == 200


def test_same_origin_port_must_match():
    # A page on another port of a public-looking name is not the same origin
    guard = make(allow_hosts=["box.example.com"])
    assert _status(_call(guard, "box.example.com:8000", "http://box.example.com:8000")) == 200
    assert _status(_call(guard, "box.example.com:8000", "http://box.example.com:9999")) == 403


def test_lifespan_passes_through():
    calls = []

    async def app(scope, receive, send):
        calls.append(scope["type"])

    async def nothing():
        return {}

    async def ignore(_):
        return None

    asyncio.run(RequestGuard(app)({"type": "lifespan"}, nothing, ignore))
    assert calls == ["lifespan"]


def test_split_host_and_public_names():
    assert split_host("Example.COM:8000") == ("example.com", 8000)
    assert split_host("[::1]:8000") == ("::1", 8000)
    assert split_host("example.com.") == ("example.com", None)
    assert is_public_name(".ngrok-free.app")
    assert is_public_name("kiosk.tail1234.ts.net")
    assert not is_public_name("kiosk.local")
    assert not is_public_name("raspberrypi")
    assert not is_public_name("192.168.1.10")


def test_decisions_are_cached_and_bounded():
    guard = make()
    for i in range(600):
        _call(guard, f"h{i}.example.com")
    assert len(guard._host_cache) <= 256


@pytest.mark.parametrize(
    "origin",
    [
        # Browser extensions and webviews: the "host" is an opaque id with no dot,
        # which must not pass as a LAN name
        "chrome-extension://abcdefghijklmnopabcdefghijklmnop",
        "moz-extension://1b2c3d4e-0000-4000-8000-000000000000",
        "safari-web-extension://abcdef",
        "vscode-webview://0abc",
        "tauri://localhost",
    ],
)
def test_non_web_origins_need_an_allowance(origin):
    assert _status(_call(make(), "127.0.0.1:8000", origin)) == 403
    assert _status(_call(make(allow_origins=[origin]), "127.0.0.1:8000", origin)) == 200


@pytest.mark.parametrize(
    "origin",
    [
        "http://10.0.0.1",  # a captive portal
        "http://192.168.1.1",  # a router's admin page
        "http://192.168.1.20:3000",  # another machine's page
        "http://printer.local",
        "http://raspberrypi:8000",
        "http://100.101.102.103:8000",
    ],
)
def test_an_engine_on_loopback_refuses_pages_from_the_lan(origin):
    on_loopback = make(lan_origins=False)
    assert _status(_call(on_loopback, "127.0.0.1:8000", origin)) == 403
    assert _status(_call(make(), "127.0.0.1:8000", origin)) == 200  # bound to the network: allowed
    assert _status(_call(make(lan_origins=False, allow_origins=[origin]), "127.0.0.1:8000", origin)) == 200


def test_an_engine_on_loopback_still_serves_this_machine():
    on_loopback = make(lan_origins=False)
    assert _status(_call(on_loopback, "127.0.0.1:8000", "http://127.0.0.1:8000")) == 200
    assert _status(_call(on_loopback, "127.0.0.1:8765", "http://localhost:3000")) == 200
    assert _status(_call(on_loopback, "[::1]:8000", "http://[::1]:8000")) == 200
    assert _status(_call(on_loopback, "127.0.0.1:8000", "http://tauri.localhost")) == 200
    assert _status(_call(on_loopback, "127.0.0.1:8000")) == 200  # no Origin: not a browser


@pytest.mark.parametrize(
    "host, loopback",
    [
        ("127.0.0.1", True), ("127.0.0.2", True), ("localhost", True), ("::1", True), ("[::1]", True),
        ("0.0.0.0", False), ("::", False), ("192.168.1.5", False), ("kiosk.local", False),
    ],
)
def test_is_loopback_bind(host, loopback):
    assert is_loopback_bind(host) is loopback
