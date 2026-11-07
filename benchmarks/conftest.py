"""Shared fixtures for nonoha-engine benchmarks."""

import asyncio
import pathlib
import tracemalloc
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from nonoha_core.node_registry import NodeRegistry

from nonoha_engine.node_flow.node_flow import NodeFlow
from nonoha_engine.node_flow.router import generate_router
from nonoha_engine.runtime_config import RuntimeConfig
from nonoha_engine.plugin_management.plugin_host import PluginHost


BENCHMARK_VNF = pathlib.Path(__file__).resolve().parent / "fixtures" / "bench.vnf"


def _build_app_sync() -> tuple[FastAPI, NodeFlow]:
    """Build app synchronously for session-scoped fixture."""
    from nonoha_engine import _register_all_nodes

    node_registry = NodeRegistry()
    node_flow = NodeFlow(node_registry)
    plugin_host = PluginHost()
    runtime_config = RuntimeConfig(auto_set_process_priority=False)

    # Register core + engine nodes only (no plugins)
    _register_all_nodes(node_registry, plugin_host, runtime_config)

    # Load benchmark VNF
    loop = asyncio.new_event_loop()
    loop.run_until_complete(node_flow.load_node_flow_from_path(BENCHMARK_VNF))
    loop.close()

    app = FastAPI()
    app.include_router(generate_router(node_flow))

    return app, node_flow


@pytest.fixture(scope="session")
def app_and_flow():
    """Session-scoped FastAPI app + NodeFlow with benchmark VNF loaded."""
    return _build_app_sync()


@pytest.fixture(scope="session")
def client(app_and_flow):
    """Starlette TestClient for synchronous API benchmarks."""
    app, _ = app_and_flow
    return TestClient(app)


@pytest.fixture(scope="session")
def node_flow(app_and_flow) -> NodeFlow:
    _, nf = app_and_flow
    return nf


@dataclass
class MemoryTracker:
    peak: int = 0

    def start(self):
        tracemalloc.start()

    def stop(self) -> int:
        _, self.peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return self.peak

    def assert_below(self, limit_bytes: int, label: str = ""):
        msg = f"Peak memory {self.peak:,} bytes exceeds {limit_bytes:,} bytes"
        if label:
            msg = f"[{label}] {msg}"
        assert self.peak < limit_bytes, msg


@pytest.fixture
def memory_tracker():
    return MemoryTracker()
