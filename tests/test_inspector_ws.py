"""Integration tests: inspector endpoint, capabilities, plugin static files and
graph WebSocket robustness, against a real server on a background thread."""

import asyncio
import json
import pathlib
import shutil
import struct
import threading
import time
import urllib.request

import pytest
import uvicorn
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from nonoha_core.inspection import decode_header
from nonoha_core.node_registry import NodeRegistry

import nonoha_engine
from nonoha_engine.node_flow.node_flow import NodeFlow
from nonoha_engine.plugin_management.plugin_host import PluginHost
from nonoha_engine.runtime_config import RuntimeConfig

ENGINE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ENGINE_ROOT / "templates" / "default"


def start_server(tmp_path, inspector_enabled=True):
    vnf = tmp_path / "default.vnf"
    shutil.copytree(TEMPLATE / "flows" / "default.vnf", vnf)
    plugins = tmp_path / "plugins"
    shutil.copytree(TEMPLATE / "plugins", plugins)
    static = plugins / "user-nodes" / "user_nodes" / "static" / "views"
    static.mkdir(parents=True, exist_ok=True)
    (static / "manifest.json").write_text('{"sdk": 1, "views": []}', encoding="utf-8")
    (static / "hello.js").write_text("export const hello = 1;\n", encoding="utf-8")

    holder = {}
    ready = threading.Event()

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def main():
            registry = NodeRegistry()
            flow = NodeFlow(registry)
            flow.readonly = True
            app, _, _ = await nonoha_engine._generate_app(
                registry, flow, ENGINE_ROOT, vnf, PluginHost(), RuntimeConfig(),
                plugins, editor_html_path=None, inspector_enabled=inspector_enabled,
            )
            config = uvicorn.Config(app, host="127.0.0.1", port=0, loop="asyncio",
                                    ws="websockets-sansio", ws_per_message_deflate=False, log_level="warning")
            server = uvicorn.Server(config)
            holder["server"] = server
            task = asyncio.create_task(server.serve())
            while not server.started:
                await asyncio.sleep(0.05)
            holder["port"] = server.servers[0].sockets[0].getsockname()[1]
            ready.set()
            await task

        loop.run_until_complete(main())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    assert ready.wait(30), "server did not start"

    def stop():
        holder["server"].should_exit = True
        thread.join(10)

    return holder["port"], stop


@pytest.fixture
def server(tmp_path):
    port, stop = start_server(tmp_path)
    yield port
    stop()


def get_json(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
        return json.loads(r.read())


def bool_input_event(name: str, value: bool) -> bytes:
    """Graph endpoint input event: one bool value (dtype 0, scalar)."""
    encoded = name.encode()
    return bytes([0x00, len(encoded)]) + encoded + bytes([1, 0, 0]) + struct.pack(">I", 1) + bytes([1 if value else 0])


def test_capabilities_and_plugins(server):
    caps = get_json(server, "/node-flow/capabilities")
    assert caps["inspector"] == {"enabled": True, "protocol": 1} and caps["plugin_static"] is True
    plugins = {p["id"]: p for p in get_json(server, "/node-flow/plugins")}
    assert plugins["user_nodes"]["static"] == "/plugins/user_nodes/static/"


def test_plugin_static_is_served_as_javascript(server):
    with urllib.request.urlopen(f"http://127.0.0.1:{server}/plugins/user_nodes/static/views/hello.js", timeout=5) as r:
        assert r.headers["Content-Type"].startswith("text/javascript")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert b"export const hello" in r.read()
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(f"http://127.0.0.1:{server}/plugins/user_nodes/static/..%2F..%2Fpyproject.toml", timeout=5)


def test_inspector_samples_an_internal_port(server):
    with connect(f"ws://127.0.0.1:{server}/node-flow/graphs/app/inspector/ws") as inspector, \
            connect(f"ws://127.0.0.1:{server}/node-flow/graphs/app/endpoint/ws") as graph_ws:
        hello = json.loads(inspector.recv(timeout=5))
        assert hello["t"] == "hello" and hello["protocol"] == 1
        inspector.send(json.dumps({"op": "watch", "id": 1, "node": "Clock_1", "port": "times", "interval_ms": 100}))
        inspector.send(json.dumps({"op": "activity", "interval_ms": 200,
                                   "ports": [{"id": 9, "node": "Synthesizer_1", "port": "waveform"}]}))
        graph_ws.send(bool_input_event("enabled", True))  # start the template's clock

        samples, activity, deadline = [], [], time.monotonic() + 5
        while time.monotonic() < deadline and (len(samples) < 3 or not activity):
            message = inspector.recv(timeout=5)
            if isinstance(message, bytes):
                header = decode_header(message)
                samples.append(header)
                inspector.send(json.dumps({"op": "ack", "seq": header["frame_seq"]}))
            else:
                data = json.loads(message)
                if data["t"] == "activity" and data["p"]:
                    activity.append(data["p"][0])
        graph_ws.send(bool_input_event("enabled", False))

    assert len(samples) >= 3 and all(s["watch_id"] == 1 for s in samples)
    assert samples[-1]["dispatch_count"] > samples[0]["dispatch_count"]
    assert activity[-1][0] == 9 and activity[-1][2] > 0  # Hz


def test_inspector_can_be_disabled(tmp_path):
    port, stop = start_server(tmp_path, inspector_enabled=False)
    try:
        assert get_json(port, "/node-flow/capabilities")["inspector"]["enabled"] is False
        with connect(f"ws://127.0.0.1:{port}/node-flow/graphs/app/inspector/ws") as ws:
            with pytest.raises(ConnectionClosed) as err:
                ws.recv(timeout=5)
            assert err.value.rcvd.code == 4403
    finally:
        stop()


def test_graph_endpoint_survives_text_frames(server):
    with connect(f"ws://127.0.0.1:{server}/node-flow/graphs/app/endpoint/ws") as ws:
        ws.send("not a binary frame")
        ws.send(bool_input_event("enabled", True))
        got = ws.recv(timeout=5)  # still served after the text frame
        assert isinstance(got, bytes) and got[0] == 0x01
        ws.send(bool_input_event("enabled", False))


def test_request_guard_is_wired_for_http_and_websocket(server):
    """A real server answers foreign Origins and rebound Hosts with 403."""
    def status(path, headers):
        req = urllib.request.Request(f"http://127.0.0.1:{server}{path}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.headers
        except urllib.error.HTTPError as e:
            return e.code, e.headers

    assert status("/node-flow/graphs", {"Origin": f"http://127.0.0.1:{server}"})[0] == 200
    assert status("/node-flow/graphs", {"Origin": "http://localhost:3000"})[0] == 200
    code, _ = status("/node-flow/graphs", {"Origin": "https://evil.example"})
    assert code == 403
    assert status("/node-flow/graphs", {"Host": "rebind.attacker.test"})[0] == 403
    # Allowed cross-origin callers still get CORS headers (no credentials)
    _, headers = status("/node-flow/graphs", {"Origin": "http://localhost:3000"})
    assert headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in headers

    with pytest.raises(Exception):
        connect(f"ws://127.0.0.1:{server}/node-flow/graphs/app/endpoint/ws",
                additional_headers={"Origin": "https://evil.example"}, open_timeout=5)
    with connect(f"ws://127.0.0.1:{server}/node-flow/graphs/app/endpoint/ws",
                 additional_headers={"Origin": f"http://127.0.0.1:{server}"}, open_timeout=5):
        pass


def test_an_unknown_output_is_404(server):
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(f"http://127.0.0.1:{server}/node-flow/graphs/app/outputs/nope/values", timeout=5)
    assert err.value.code == 404


# --- the host without a server ----------------------------------------------------------

class _Socket:
    """A WebSocket that delivers ``texts`` and records what is sent."""

    def __init__(self, texts):
        self._texts = list(texts)
        self.sent = []
        self.closed = False

    async def accept(self):
        pass

    async def receive(self):
        await asyncio.sleep(0)
        if self._texts:
            return {"type": "websocket.receive", "text": self._texts.pop(0)}
        await asyncio.sleep(0.05)
        return {"type": "websocket.disconnect"}

    async def send_text(self, text):
        self.sent.append(json.loads(text))

    async def send_bytes(self, data):
        self.sent.append(bytes(data))

    async def close(self, code=1000):
        self.closed = True


def _graph_flow():
    import numpy as np

    from nonoha_core.data_type import DataType, PortValueType
    from nonoha_core.node import BaseNode, BaseNodeGraph
    from nonoha_core.port import StaticTypeOutputPort

    class Source(BaseNode):
        def __init__(self, name):
            super().__init__(name, "Source")
            self.outputs["out"] = StaticTypeOutputPort("out", [PortValueType(DataType.Float32)])

    graph = BaseNodeGraph("g", {})
    graph.add_node(Source("Source_1"))

    class Flow:
        def get_graph(self, name):
            return graph if name == "g" else None

    return Flow()


def test_operations_after_close_leave_nothing_subscribed():
    from nonoha_engine.node_flow.inspector_ws import InspectorHost

    host = InspectorHost(_graph_flow(), enabled=True)
    socket = _Socket([
        json.dumps({"op": "close"}),
        json.dumps({"op": "watch", "id": 1, "node": "Source_1", "port": "out", "batch": "since"}),
        json.dumps({"op": "activity", "ports": [{"id": 1, "node": "Source_1", "port": "out"}]}),
    ])
    asyncio.run(host.handle(socket, "g"))
    assert socket.closed and not host.inspector._probes and not host.inspector.sessions


def test_huge_numbers_get_an_error_reply_not_a_crash():
    from nonoha_engine.node_flow.inspector_ws import InspectorHost

    host = InspectorHost(_graph_flow(), enabled=True)
    socket = _Socket(['{"op": "unwatch", "id": 1e999}'])

    async def run():
        await host.handle(socket, "g")
        await asyncio.sleep(0.05)  # let the sender drain

    asyncio.run(run())
    assert any(m.get("t") == "error" and m.get("code") == "bad_request" for m in socket.sent if isinstance(m, dict))


def test_the_outbox_keeps_the_newest_activity_and_cuts_off_a_client_that_does_not_read():
    from nonoha_engine.node_flow.inspector_ws import Outbox, OutboxFull

    async def run():
        socket = _Socket([])
        outbox = Outbox(socket, limit=4)
        outbox.put({"t": "hello"})
        outbox.put({"t": "activity", "n": 1})
        outbox.put(bytearray(b"frame"))
        outbox.put({"t": "activity", "n": 2})  # replaces n=1 in its place
        outbox.put({"t": "status", "s": "ok"})
        drain = asyncio.create_task(outbox.drain())
        await asyncio.sleep(0.01)
        drain.cancel()
        assert socket.sent == [{"t": "hello"}, {"t": "activity", "n": 2}, b"frame", {"t": "status", "s": "ok"}]

        stuck = Outbox(_Socket([]), limit=3)
        for i in range(3):
            stuck.put({"t": "error", "i": i})
        with pytest.raises(OutboxFull):
            stuck.put({"t": "error", "i": 3})

    asyncio.run(run())
