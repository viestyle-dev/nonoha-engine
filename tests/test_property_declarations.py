"""The engine's own nodes and sci-nodes declare their properties, and each property port sets its property."""

import sci_nodes
from nonoha_core._testing import (
    assert_all_properties_declared,
    assert_property_ports_apply,
)
from nonoha_core.node_registry import NodeRegistry

from nonoha_engine.node_flow.nodes import (
    clock_nodes,
    graph_nodes,
    process_nodes,
    record_nodes,
)


def _registry() -> NodeRegistry:
    registry = NodeRegistry()
    registry.register_node("HiResClock", clock_nodes.HiResClockNode)
    sci_nodes.register_nodes(registry)
    registry.register_node("PortValuesSend", graph_nodes.PortValuesSendNode)
    registry.register_node("Record", record_nodes.RecordNode)
    registry.register_node("Replay", record_nodes.ReplayNode)
    registry.register_node("RotatingRecord", record_nodes.RotatingRecordNode)
    registry.register_node("Process", process_nodes.ProcessNode)
    return registry


def test_all_properties_are_declared():
    assert_all_properties_declared(_registry())


def test_property_ports_apply():
    assert_property_ports_apply(_registry())
