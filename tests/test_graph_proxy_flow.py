"""GraphProxy resolution through NodeFlow (.vnf loading)."""

import asyncio
import json
import pathlib
import tempfile

import numpy as np

import nonoha_core.nodes
from nonoha_core.node_registry import NodeRegistry

from nonoha_engine.node_flow.node_flow import NodeFlow


# source: graph input "in" -> Abs -> graph output "out"
SOURCE_GRAPH = {
    "properties": {},
    "nodes": {"Abs_1": {"type": "Abs", "properties": {}}},
    "inputs": {"in": {"types": ["f32"]}},
    "outputs": {"out": {"types": ["f32"]}},
    "edges": [
        {"source": ".in", "target": "Abs_1.value"},
        {"source": "Abs_1.value", "target": ".out"},
    ],
}

# main: graph input "x" -> GraphProxy(source) -> graph output "y"
MAIN_GRAPH = {
    "properties": {},
    "nodes": {
        "GraphProxy_1": {
            "type": "GraphProxy",
            "properties": {"graph_name": "source"},
        }
    },
    "inputs": {"x": {"types": ["f32"]}},
    "outputs": {"y": {"types": ["f32"]}},
    "edges": [
        {"source": ".x", "target": "GraphProxy_1.in"},
        {"source": "GraphProxy_1.out", "target": ".y"},
    ],
}


def _write_vnf(root: pathlib.Path, graph_order: list[str]) -> pathlib.Path:
    vnf = root / "test.vnf"
    (vnf / "graphs").mkdir(parents=True)
    (vnf / "flow.json").write_text(json.dumps({"graphs": graph_order}))
    for name, model in [("source", SOURCE_GRAPH), ("main", MAIN_GRAPH)]:
        graph_dir = vnf / "graphs" / f"{name}.vng"
        graph_dir.mkdir()
        (graph_dir / "graph.json").write_text(json.dumps(model))
    return vnf


def _make_flow() -> NodeFlow:
    registry = NodeRegistry()
    nonoha_core.nodes.register_nodes(registry)
    return NodeFlow(registry)


def test_proxy_binds_and_forwards_through_vnf():
    async def _test():
        with tempfile.TemporaryDirectory() as tmp:
            vnf = _write_vnf(pathlib.Path(tmp), ["source", "main"])
            flow = _make_flow()
            await flow.load_node_flow_from_path(vnf)

            main = flow.get_graph("main")
            assert main is not None
            assert main.parent_flow is flow

            proxy = main.get_node("GraphProxy_1")
            assert set(proxy.inputs.keys()) == {"in"}
            assert set(proxy.outputs.keys()) == {"out"}

            received: list[list] = []
            main.outputs["y"].subscribe(1, lambda values: received.append(values))
            main.inputs["x"].dispatch([np.array([-1.5], dtype=np.float32)])

            assert received, "value did not flow through the proxy"
            np.testing.assert_array_equal(
                received[-1][0], np.array([1.5], dtype=np.float32)
            )

            flow.finalize()

    asyncio.run(_test())


def test_proxy_stays_unbound_when_target_loads_later():
    async def _test():
        with tempfile.TemporaryDirectory() as tmp:
            # main is listed first, so "source" is unknown when the proxy binds
            vnf = _write_vnf(pathlib.Path(tmp), ["main", "source"])
            flow = _make_flow()
            await flow.load_node_flow_from_path(vnf)

            main = flow.get_graph("main")
            assert main is not None
            proxy = main.get_node("GraphProxy_1")
            assert proxy.inputs == {}
            assert proxy.outputs == {}

            flow.finalize()

    asyncio.run(_test())
