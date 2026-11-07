"""Memory benchmarks for engine-level operations."""

import asyncio
import pathlib

from nonoha_core.node_registry import NodeRegistry
import nonoha_core.nodes

from nonoha_engine.node_flow.node_flow import NodeFlow
from nonoha_engine.runtime_config import RuntimeConfig
from nonoha_engine.plugin_management.plugin_host import PluginHost

BENCHMARK_VNF = pathlib.Path(__file__).resolve().parent / "fixtures" / "bench.vnf"


def test_memory_load_vnf(memory_tracker):
    """Peak memory when loading the benchmark VNF."""
    from nonoha_engine import _register_all_nodes

    node_registry = NodeRegistry()
    node_flow = NodeFlow(node_registry)
    plugin_host = PluginHost()
    runtime_config = RuntimeConfig(auto_set_process_priority=False)
    _register_all_nodes(node_registry, plugin_host, runtime_config)

    memory_tracker.start()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(node_flow.load_node_flow_from_path(BENCHMARK_VNF))
    loop.close()

    memory_tracker.stop()
    memory_tracker.assert_below(50 * 1024 * 1024, "VNF load")


def test_memory_create_100_nodes(memory_tracker):
    """Peak memory when creating 100 nodes via registry."""
    node_registry = NodeRegistry()
    nonoha_core.nodes.register_nodes(node_registry)

    memory_tracker.start()

    for i in range(100):
        node_registry.create_node("Add", f"bench_node_{i}")

    memory_tracker.stop()
    memory_tracker.assert_below(20 * 1024 * 1024, "100 nodes creation")
