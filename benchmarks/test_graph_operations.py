"""Benchmarks for graph operations (node creation, edge connection, loading)."""

import asyncio
import pathlib

from nonoha_core.node_registry import NodeRegistry

from nonoha_engine.node_flow.node_flow import NodeFlow
from nonoha_engine.runtime_config import RuntimeConfig
from nonoha_engine.plugin_management.plugin_host import PluginHost


BENCHMARK_VNF = pathlib.Path(__file__).resolve().parent / "fixtures" / "bench.vnf"


def test_load_benchmark_vnf(benchmark):
    """Load the benchmark VNF from disk."""
    from nonoha_engine import _register_all_nodes

    def do_load():
        node_registry = NodeRegistry()
        node_flow = NodeFlow(node_registry)
        plugin_host = PluginHost()
        runtime_config = RuntimeConfig(auto_set_process_priority=False)
        _register_all_nodes(node_registry, plugin_host, runtime_config)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(node_flow.load_node_flow_from_path(BENCHMARK_VNF))
        loop.close()

    benchmark.pedantic(do_load, rounds=10, warmup_rounds=1)


def test_create_100_nodes(benchmark, node_flow):
    """Create 100 Add nodes in a graph via the node registry."""
    registry = node_flow.node_registry

    def do_create():
        nodes = []
        for i in range(100):
            node = registry.create_node("Add", f"bench_node_{i}")
            nodes.append(node)
        return nodes

    benchmark(do_create)
