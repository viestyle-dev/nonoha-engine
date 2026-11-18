"""Environment values: the .env grammar, where it is, and the write rules."""

import json
import os
import pathlib
import stat
import sys

import pytest

from nonoha_core import environment
from nonoha_core.node import BaseNode, EnvDoc, NodeDoc

from nonoha_engine import env_file
from nonoha_engine.env_settings import EnvSettingError, EnvSettings, declared_env


# --- grammar ---------------------------------------------------------------


def test_parse_common_forms():
    text = "\ufeff# comment\n\nA=plain\nexport B = spaced  # tail comment\nC=\"q \\\"x\\\" \\\\ \\n\"\nD='lit $X \\n'\nE=\nbad line\nA=last\n"
    assert env_file.parse(text) == {"A": "last", "B": "spaced", "C": 'q "x" \\ \n', "D": "lit $X \\n", "E": ""}


def test_no_interpolation():
    assert env_file.parse("A=${HOME}/x\n") == {"A": "${HOME}/x"}


def test_rewrite_keeps_other_lines_and_drops_duplicates():
    text = "# keep\nA=1\nB=2\nA=3\n"
    assert env_file.rewrite(text, "A", "new") == '# keep\nA="new"\nB=2\n'
    assert env_file.rewrite(text, "A", None) == "# keep\nB=2\n"
    assert env_file.rewrite("", "X", 'a"b\\c') == 'X="a\\"b\\\\c"\n'
    # Round trip through the parser
    assert env_file.parse(env_file.rewrite("", "X", 'a"b\\c $Y')) == {"X": 'a"b\\c $Y'}


def test_write_is_atomic_private_and_creates_folders(tmp_path):
    path = tmp_path / "apps" / "demo" / ".env"
    env_file.write_value(path, "KEY", "v1")
    env_file.write_value(path, "OTHER", "v2")
    env_file.write_value(path, "KEY", None)
    assert env_file.read(path) == {"OTHER": "v2"}
    assert not list(path.parent.glob(".*.tmp"))
    if sys.platform != "win32":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


# --- where the file is -------------------------------------------------------


def test_resolve(tmp_path, monkeypatch):
    explicit = tmp_path / "kiosk.env"
    assert env_file.resolve(str(explicit), "app-1") == explicit.resolve()
    # An app: the per-user folder by app id, never next to the executable
    assert env_file.resolve(None, "cv_demo-7f3a9c21") == env_file.per_user_dir() / "cv_demo-7f3a9c21" / ".env"
    # Otherwise none: the engine does not guess (a launcher passes --env-file)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("A=1\n", encoding="utf-8")
    assert env_file.resolve(None, None) is None
    for bad in ("../x", "a/b", "..", "with space"):
        with pytest.raises(ValueError):
            env_file.resolve(None, bad)


@pytest.mark.parametrize(
    "platform, environ, expected",
    [
        ("win32", {"LOCALAPPDATA": "C:/Users/u/AppData/Local"}, "C:/Users/u/AppData/Local/nonoha/apps"),
        ("win32", {}, "HOME/AppData/Local/nonoha/apps"),
        ("darwin", {}, "HOME/Library/Application Support/nonoha/apps"),
        ("linux", {}, "HOME/.config/nonoha/apps"),
        # Not $XDG_CONFIG_HOME: the place must not depend on how the app was started
        ("linux", {"XDG_CONFIG_HOME": "/elsewhere"}, "HOME/.config/nonoha/apps"),
        ("freebsd14", {}, "HOME/.config/nonoha/apps"),
    ],
)
def test_per_user_dir_on_each_os(monkeypatch, tmp_path, platform, environ, expected):
    monkeypatch.setattr(env_file.sys, "platform", platform)
    monkeypatch.setattr(env_file.Path, "home", classmethod(lambda cls: pathlib.Path("HOME")))
    for name in ("LOCALAPPDATA", "XDG_CONFIG_HOME"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environ.items():
        monkeypatch.setenv(name, value)
    assert env_file.per_user_dir() == pathlib.Path(expected)


def test_a_write_that_changes_nothing_creates_nothing(tmp_path):
    path = tmp_path / "apps" / "demo" / ".env"
    assert env_file.write_value(path, "KEY", None) is False
    assert not path.parent.exists()
    assert env_file.write_value(path, "KEY", "v") is True
    mtime = path.stat().st_mtime_ns
    assert env_file.write_value(path, "KEY", "v") is False
    assert path.stat().st_mtime_ns == mtime


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links need a privilege on Windows")
def test_a_linked_env_file_updates_its_target(tmp_path):
    target = tmp_path / "secrets" / "project.env"
    target.parent.mkdir()
    target.write_text("A=1\n", encoding="utf-8")
    link = tmp_path / ".env"
    link.symlink_to(target)
    env_file.write_value(link, "B", "2")
    assert link.is_symlink()
    assert env_file.read(target) == {"A": "1", "B": "2"}


@pytest.mark.parametrize("kind", ["utf16", "folder"])
def test_an_unreadable_env_file_does_not_stop_the_engine(tmp_path, clean_env, kind):
    path = tmp_path / ".env"
    if kind == "utf16":
        path.write_bytes("TEST_KEY=x\n".encode("utf-16"))  # PowerShell 5.1 `echo ... > .env`
    else:
        path.mkdir()  # python -m venv .env
    settings = EnvSettings(path)
    settings.load_into_process()  # warns, does not raise
    flow = _flow("TEST_KEY")
    status = settings.status(declared_env(flow))
    assert not status["writable"] and "Cannot read" in status["items"][0]["reason"]
    with pytest.raises(EnvSettingError) as e:
        settings.set_value("TEST_KEY", "v", declared_env(flow))
    assert e.value.status_code == 409
    if kind == "utf16":
        assert path.read_bytes().decode("utf-16") == "TEST_KEY=x\n"  # never overwritten


def test_read_only_mode_never_changes_the_file(tmp_path, clean_env):
    path = tmp_path / ".env"
    path.write_text("TEST_KEY=old\n", encoding="utf-8")
    settings = EnvSettings(path, readonly=True)
    settings.load_into_process()
    flow = _flow("TEST_KEY")
    item = settings.status(declared_env(flow))["items"][0]
    assert not item["writable"] and "--readonly" in item["reason"]
    with pytest.raises(EnvSettingError) as e:
        settings.set_value("TEST_KEY", "new", declared_env(flow))
    assert e.value.status_code == 403
    assert env_file.read(path) == {"TEST_KEY": "old"}


# --- the engine's settings ---------------------------------------------------


class _AiNode(BaseNode):
    PROPERTIES = {"api_key_env": {"description": "", "default_value": ""}}

    def __init__(self, name):
        super().__init__(name, "AiNode")

    @classmethod
    def describe(cls, properties=None):
        name = str((properties or {}).get("api_key_env") or "TEST_KEY_DEFAULT")
        return NodeDoc(env=(EnvDoc(name, "Test key", "https://example.com/keys"),))


class _BrokenDocNode(BaseNode):
    def __init__(self, name):
        super().__init__(name, "Broken")

    @classmethod
    def describe(cls, properties=None):
        raise RuntimeError("boom")


class _Graph:
    def __init__(self, nodes):
        self.nodes = {n.name: n for n in nodes}


class _Flow:
    def __init__(self, graphs):
        self._graphs = graphs

    @property
    def graph_names(self):
        return list(self._graphs)

    def get_graph(self, name):
        return self._graphs.get(name)


def _flow(*key_names):
    nodes = []
    for i, key in enumerate(key_names):
        node = _AiNode(f"Ai_{i}")
        node.properties["api_key_env"] = key
        nodes.append(node)
    nodes.append(_BrokenDocNode("Broken_1"))
    return _Flow({"app": _Graph(nodes)})


@pytest.fixture
def clean_env(monkeypatch):
    for name in list(os.environ):
        if name.startswith("TEST_"):
            monkeypatch.delenv(name)
    with environment.using({}):
        yield monkeypatch


def test_declared_names_follow_properties():
    declared = declared_env(_flow("TEST_A", "TEST_A", "TEST_B"))
    assert set(declared) == {"TEST_A", "TEST_B"}
    assert declared["TEST_A"].declared_by == ["app/Ai_0", "app/Ai_1"]
    assert declared["TEST_A"].url == "https://example.com/keys"


def test_load_puts_file_values_into_os_environ_but_os_wins(tmp_path, clean_env):
    path = tmp_path / ".env"
    path.write_text("TEST_FILE=from-file\nTEST_BOTH=from-file\n", encoding="utf-8")
    clean_env.setenv("TEST_BOTH", "from-os")
    settings = EnvSettings(path)
    settings.load_into_process()
    assert os.environ["TEST_FILE"] == "from-file"
    assert os.environ["TEST_BOTH"] == "from-os"
    status = {i["name"]: i for i in settings.status(declared_env(_flow("TEST_FILE", "TEST_BOTH")))["items"]}
    assert status["TEST_FILE"]["source"] == "file" and status["TEST_FILE"]["writable"]
    assert status["TEST_BOTH"]["source"] == "os" and not status["TEST_BOTH"]["writable"]


def test_status_never_contains_values_and_hides_os_only_names(tmp_path, clean_env):
    path = tmp_path / ".env"
    path.write_text("TEST_UNDECLARED=secret-in-file\n", encoding="utf-8")
    clean_env.setenv("TEST_OS_ONLY", "secret-in-os")
    settings = EnvSettings(path)
    settings.load_into_process()
    flow = _flow("TEST_KEY")
    settings.set_value("TEST_KEY", "secret-set-now", declared_env(flow))
    dumped = json.dumps(settings.status(declared_env(flow)))
    assert "secret" not in dumped
    names = [i["name"] for i in settings.status(declared_env(flow))["items"]]
    assert names == ["TEST_KEY", "TEST_UNDECLARED"]


def test_change_writes_the_file_then_nodes_see_it(tmp_path, clean_env):
    path = tmp_path / ".env"
    settings = EnvSettings(path)
    settings.load_into_process()
    flow = _flow("TEST_KEY")
    settings.set_value("TEST_KEY", "k1", declared_env(flow))
    assert env_file.read(path) == {"TEST_KEY": "k1"}
    assert environment.get("TEST_KEY") == "k1"
    assert "TEST_KEY" not in os.environ  # running libraries see it after a restart
    settings.remove_value("TEST_KEY", declared_env(flow))
    assert env_file.read(path) == {}
    assert environment.get("TEST_KEY") is None


@pytest.mark.parametrize(
    "name, value, code",
    [
        ("TEST_UNDECLARED", "v", 403),  # no node uses it
        ("HTTPS_PROXY", "http://evil", 400),  # reserved even if declared
        ("PATH", "x", 400),
        ("bad-name", "x", 400),
        ("TEST_KEY", "a\nPATH=/evil", 400),  # line injection
        ("TEST_KEY", "x" * 5000, 400),
    ],
)
def test_change_refusals(tmp_path, clean_env, name, value, code):
    settings = EnvSettings(tmp_path / ".env")
    flow = _flow("TEST_KEY", "HTTPS_PROXY", "PATH")
    with pytest.raises(EnvSettingError) as e:
        settings.set_value(name, value, declared_env(flow))
    assert e.value.status_code == code
    assert value not in e.value.message
    assert not (tmp_path / ".env").exists()


def test_os_set_names_cannot_be_written(tmp_path, clean_env):
    clean_env.setenv("TEST_KEY", "from-os")
    settings = EnvSettings(tmp_path / ".env")
    settings.load_into_process()
    with pytest.raises(EnvSettingError) as e:
        settings.set_value("TEST_KEY", "other", declared_env(_flow("TEST_KEY")))
    assert e.value.status_code == 403
    assert environment.get("TEST_KEY") == "from-os"


def test_no_file_or_read_only_file(tmp_path, clean_env, monkeypatch):
    flow = _flow("TEST_KEY")
    none = EnvSettings(None)
    assert not none.status(declared_env(flow))["writable"]
    with pytest.raises(EnvSettingError) as e:
        none.set_value("TEST_KEY", "v", declared_env(flow))
    assert e.value.status_code == 409

    settings = EnvSettings(tmp_path / ".env")
    monkeypatch.setattr(env_file, "is_writable", lambda _p: False)
    item = settings.status(declared_env(flow))["items"][0]
    assert not item["writable"] and "read-only" in item["reason"]
    with pytest.raises(EnvSettingError):
        settings.set_value("TEST_KEY", "v", declared_env(flow))
    assert environment.get("TEST_KEY") is None


def test_failed_write_leaves_values_unchanged(tmp_path, clean_env, monkeypatch):
    settings = EnvSettings(tmp_path / ".env")

    def fail(*_a):
        raise env_file.EnvFileError("disk full")

    monkeypatch.setattr(env_file, "write_value", fail)
    with pytest.raises(EnvSettingError) as e:
        settings.set_value("TEST_KEY", "v", declared_env(_flow("TEST_KEY")))
    assert e.value.status_code == 409
    assert environment.get("TEST_KEY") is None


def test_catalog_lists_env_declarations():
    from nonoha_core.node_registry import NodeRegistry
    from nonoha_engine.node_flow.catalog import catalog

    registry = NodeRegistry()
    registry.register_node("AiNode", _AiNode)
    entry = catalog(registry)[0]
    assert entry["env"] == [{"name": "TEST_KEY_DEFAULT", "description": "Test key", "url": "https://example.com/keys"}]
    assert "env" not in catalog_entry_without_env()


def catalog_entry_without_env():
    from nonoha_core.node_registry import NodeRegistry
    from nonoha_engine.node_flow.catalog import catalog

    class Plain(BaseNode):
        def __init__(self, name):
            super().__init__(name, "Plain")

    registry = NodeRegistry()
    registry.register_node("Plain", Plain)
    return catalog(registry)[0]


def test_engine_env_endpoint_reports_status_without_values(tmp_path):
    """A real server: GET works, PUT of an undeclared name is refused, nothing echoes."""
    import urllib.error
    import urllib.request

    from test_inspector_ws import start_server

    port, stop = start_server(tmp_path)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/node-flow/capabilities", timeout=5) as r:
            assert json.loads(r.read())["env_settings"] is False  # the test server has no EnvSettings
    finally:
        stop()


def test_engine_env_endpoints(tmp_path, clean_env):
    import asyncio
    import shutil
    import threading
    import urllib.error
    import urllib.request

    import uvicorn

    import nonoha_engine
    from nonoha_core.node_registry import NodeRegistry
    from nonoha_engine.node_flow.node_flow import NodeFlow
    from nonoha_engine.plugin_management.plugin_host import PluginHost
    from nonoha_engine.runtime_config import RuntimeConfig

    engine_root = pathlib.Path(__file__).resolve().parents[1]
    vnf = tmp_path / "flows" / "default.vnf"
    shutil.copytree(engine_root / "templates" / "default" / "flows" / "default.vnf", vnf)
    shutil.copytree(engine_root / "templates" / "default" / "plugins", tmp_path / "plugins")
    env_path = tmp_path / ".env"
    env_path.write_text("TEST_PRESET=already\n", encoding="utf-8")
    settings = EnvSettings(env_path)
    settings.load_into_process()

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
                registry, flow, engine_root, vnf, PluginHost(), RuntimeConfig(),
                tmp_path / "plugins", editor_html_path=None, env_settings=settings,
            )
            registry.register_node("AiNode", _AiNode)
            graph = flow.get_graph("app")
            node = _AiNode("Ai_1")
            node.properties["api_key_env"] = "TEST_KEY"
            graph.nodes["Ai_1"] = node  # declared by a node of a loaded graph
            server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
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
    assert ready.wait(30)
    base = f"http://127.0.0.1:{holder['port']}/node-flow"

    def call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    try:
        code, text = call("GET", "/capabilities")
        assert json.loads(text)["env_settings"] is True
        code, text = call("PUT", "/env/TEST_KEY", {"value": "secret-123"})
        assert code == 200 and "secret-123" not in text
        assert environment.get("TEST_KEY") == "secret-123"
        assert env_file.read(env_path)["TEST_KEY"] == "secret-123"
        code, text = call("GET", "/env")
        items = {i["name"]: i for i in json.loads(text)["items"]}
        assert items["TEST_KEY"]["set"] and items["TEST_KEY"]["source"] == "file"
        assert "secret-123" not in text and "already" not in text
        code, text = call("PUT", "/env/TEST_OTHER", {"value": "secret-456"})
        assert code == 403 and "secret-456" not in text
        code, text = call("PUT", "/env/TEST_KEY", {"wrong": "secret-789"})
        assert code == 400 and "secret-789" not in text
        code, text = call("DELETE", "/env/TEST_KEY")
        assert code == 200 and environment.get("TEST_KEY") is None
    finally:
        holder["server"].should_exit = True
        thread.join(10)
