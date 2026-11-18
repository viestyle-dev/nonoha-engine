"""PluginHost: where plugins and their static files are found."""

import json
import logging
import sys
import textwrap

import pytest

from nonoha_core.node_registry import NodeRegistry

from nonoha_engine import _engine_root, _plugins_path
from nonoha_engine.plugin_management.plugin_host import PluginHost, _package_static_dir
from nonoha_engine.runtime_config import RuntimeConfig


def write_plugin(root, name, node_type, static=True):
    """plugins/<name>/<module>/__init__.py (+ static/views/x.js inside the package)."""
    module = name.replace("-", "_")
    package = root / name / module
    package.mkdir(parents=True)
    (root / name / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (package / "__init__.py").write_text(textwrap.dedent(f"""
        from nonoha_core.node import BaseNode

        class N(BaseNode):
            def __init__(self, name):
                super().__init__(name, "{node_type}")

        def register_nodes(registry):
            registry.register_node("{node_type}", N)
    """), encoding="utf-8")
    if static:
        (package / "static" / "views").mkdir(parents=True)
        (package / "static" / "views" / "x.js").write_text("export {}\n", encoding="utf-8")
    return module


def manifest(root, *names):
    (root / "manifest.json").write_text(
        json.dumps({"plugins": [{"name": n, "enabled": True} for n in names]}), encoding="utf-8"
    )


def test_a_folder_plugin_serves_the_static_folder_inside_its_package(tmp_path):
    plugins = tmp_path / "plugins"
    write_plugin(plugins, "demo-nodes", "Demo")
    manifest(plugins, "demo-nodes")
    host = PluginHost()
    host.load_plugins(plugins, NodeRegistry())
    (info,) = host.plugin_infos()
    assert info["id"] == "demo_nodes" and info["static_dir"] == plugins / "demo-nodes" / "demo_nodes" / "static"


def test_a_built_in_plugin_serves_the_static_folder_next_to_its_module(tmp_path, monkeypatch):
    """Installed (site-packages) or bundled: the package carries static/ along."""
    site = tmp_path / "site-packages"
    write_plugin(site, "boxed-nodes", "Boxed")
    monkeypatch.syspath_prepend(str(site / "boxed-nodes"))
    import boxed_nodes

    host = PluginHost()
    host.load_builtin_plugins((boxed_nodes,), NodeRegistry())
    (info,) = host.plugin_infos()
    assert info["builtin"] and info["static_dir"] == site / "boxed-nodes" / "boxed_nodes" / "static"
    assert _package_static_dir(json) is None  # a package without static/
    sys.modules.pop("boxed_nodes", None)


def test_a_folder_copy_of_a_built_in_plugin_is_skipped(tmp_path, monkeypatch, caplog):
    site = tmp_path / "site"
    write_plugin(site, "twin-nodes", "Twin", static=False)
    monkeypatch.syspath_prepend(str(site / "twin-nodes"))
    import twin_nodes

    plugins = tmp_path / "plugins"
    write_plugin(plugins, "twin-nodes", "Twin", static=False)
    manifest(plugins, "twin-nodes")
    registry = NodeRegistry()
    host = PluginHost()
    host.load_builtin_plugins((twin_nodes,), registry)
    with caplog.at_level(logging.WARNING):
        host.load_plugins(plugins, registry)
    assert "built into this app" in caplog.text
    assert "Failed to load plugin" not in caplog.text
    sys.modules.pop("twin_nodes", None)


def test_plugins_default_to_the_engine_root(tmp_path):
    class Args:
        plugins_path = None

    assert _plugins_path(Args, tmp_path) == tmp_path / "plugins"
    Args.plugins_path = str(tmp_path / "elsewhere")
    assert _plugins_path(Args, tmp_path) == tmp_path / "elsewhere"
    # No plugins/ (or no manifest.json): nothing is loaded, nothing fails
    PluginHost().load_plugins(tmp_path / "plugins", NodeRegistry())


def test_the_engine_root_is_the_app_dir_when_stated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp"])  # started by name from PATH
    assert _engine_root(RuntimeConfig()) == tmp_path  # the current directory: what app_dir prevents
    app = tmp_path / "dist" / "myapp"
    assert _engine_root(RuntimeConfig(app_dir=str(app))) == app.resolve()
