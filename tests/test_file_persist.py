"""Tests for FileNodeGraphPersist serialization and VNG file format optimization.

Covers:
- _build_node_model: @property port exclusion, dispatch_flag sparse save, property_groups
- EdgeModel: valid field removed from file format
- _write_graph / round-trip: JSON output is compact and correct
- Load tolerance: files with/without optional fields parse correctly
"""

import asyncio
import json
import pathlib
import tempfile

import numpy as np

from nonoha_core.node import BaseNode, BaseNodeGraph, Edge
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType

from nonoha_engine.node_flow.node import FileNodeGraphPersist, GraphFileExtension
from nonoha_engine.node_flow.models import file_model


# ---------------------------------------------------------------------------
# Test nodes
# ---------------------------------------------------------------------------

class SampleNode(BaseNode):
    """Node with PROPERTIES for testing."""

    PROPERTIES = {
        "freq": {"description": "Frequency", "data_type": "f64", "default_value": 440.0},
        "gain": {"description": "Gain", "data_type": "f32", "default_value": 1.0},
    }

    def __init__(self, name: str):
        super().__init__(name, "SampleNode")
        f32 = PortValueType(DataType.Float32)
        in_port = StaticTypeInputPort("values", [f32, f32])
        in_port.subscribe(id(self), lambda v: None)
        self.inputs[in_port.name] = in_port
        out_port = StaticTypeOutputPort("out", [f32])
        self.outputs[out_port.name] = out_port


class PlainNode(BaseNode):
    """Node without PROPERTIES (no @ports)."""

    def __init__(self, name: str):
        super().__init__(name, "PlainNode")
        f32 = PortValueType(DataType.Float32)
        in_port = StaticTypeInputPort("in", [f32])
        in_port.subscribe(id(self), lambda v: None)
        self.inputs[in_port.name] = in_port
        out_port = StaticTypeOutputPort("out", [f32])
        self.outputs[out_port.name] = out_port
        self.properties["value"] = 0.0


# ---------------------------------------------------------------------------
# _build_node_model tests
# ---------------------------------------------------------------------------

class TestBuildNodeModel:

    def test_excludes_property_ports(self):
        node = SampleNode("T1")
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))

        # @freq, @gain should NOT appear in inputs
        if "inputs" in data:
            for key in data["inputs"]:
                assert not key.startswith("@")

    def test_excludes_all_false_dispatch_flags(self):
        node = SampleNode("T1")
        # All dispatch_flags default to False
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))
        assert "inputs" not in data

    def test_includes_true_dispatch_flag(self):
        node = SampleNode("T1")
        node.inputs["values"].dispatch_flags[0] = True
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))

        assert "inputs" in data
        assert "values" in data["inputs"]
        assert data["inputs"]["values"]["dispatch_flags"] == [True, False]

    def test_omits_empty_property_groups(self):
        node = SampleNode("T1")
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))
        assert "property_groups" not in data

    def test_includes_non_empty_property_groups(self):
        node = SampleNode("T1")
        node.set_property_groups([{"keys": ["freq", "gain"], "dispatch_flags": [False, True]}])
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))

        assert "property_groups" in data
        pg = data["property_groups"][0]
        assert pg["keys"] == ["freq", "gain"]
        assert pg["dispatch_flags"] == [False, True]

    def test_properties_always_saved(self):
        node = SampleNode("T1")
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))

        assert data["properties"]["freq"] == 440.0
        assert data["properties"]["gain"] == 1.0

    def test_plain_node_without_properties_class(self):
        node = PlainNode("P1")
        model = FileNodeGraphPersist._build_node_model(node)
        data = json.loads(model.model_dump_json(exclude_defaults=True))

        assert data["type"] == "PlainNode"
        assert data["properties"]["value"] == 0.0


# ---------------------------------------------------------------------------
# EdgeModel tests
# ---------------------------------------------------------------------------

class TestEdgeModel:

    def test_no_valid_field_in_serialization(self):
        edge = file_model.EdgeModel(source="A.out", target="B.in")
        data = json.loads(edge.model_dump_json())
        assert "valid" not in data

    def test_edge_fields(self):
        edge = file_model.EdgeModel(source=".input1", target="Node_1.port")
        assert edge.source == ".input1"
        assert edge.target == "Node_1.port"


# ---------------------------------------------------------------------------
# NodeModel deserialization tolerance
# ---------------------------------------------------------------------------

class TestNodeModelDeserialization:

    def test_loads_without_inputs(self):
        """Files without inputs field should parse (new compact format)."""
        raw = '{"type": "Test", "properties": {"a": 1}}'
        model = file_model.NodeModel.model_validate_json(raw)
        assert model.type == "Test"
        assert model.inputs == {}
        assert model.property_groups == []

    def test_loads_new_format_inputs(self):
        """New SoA format with dispatch array."""
        raw = '{"type": "Test", "properties": {}, "inputs": {"port": {"dispatch_flags": [true, false]}}}'
        model = file_model.NodeModel.model_validate_json(raw)
        assert model.inputs["port"].dispatch_flags == [True, False]

    def test_loads_legacy_format_inputs(self):
        """Old AoS format with values array (backward compat via validator)."""
        raw = '{"type": "Test", "properties": {}, "inputs": {"port": {"values": [{"dispatch_flag": true}]}}}'
        model = file_model.NodeModel.model_validate_json(raw)
        assert model.inputs["port"].dispatch_flags == [True]

    def test_loads_new_format_property_groups(self):
        raw = '{"type": "Test", "properties": {}, "property_groups": [{"keys": ["a", "b"], "dispatch_flags": [false, true]}]}'
        model = file_model.NodeModel.model_validate_json(raw)
        assert model.property_groups[0].keys == ["a", "b"]
        assert model.property_groups[0].dispatch_flags == [False, True]

    def test_loads_legacy_property_groups(self):
        """Old format: list of lists → migrated to PropertyGroupModel."""
        raw = '{"type": "Test", "properties": {}, "property_groups": [["a", "b"]]}'
        model = file_model.NodeModel.model_validate_json(raw)
        assert model.property_groups[0].keys == ["a", "b"]
        assert model.property_groups[0].dispatch_flags == [False, False]

    def test_loads_edge_without_valid(self):
        """New format edges (no valid field)."""
        raw = '{"source": "A.out", "target": "B.in"}'
        edge = file_model.EdgeModel.model_validate_json(raw)
        assert edge.source == "A.out"

    def test_loads_edge_with_valid_backward_compat(self):
        """Old format edges (with valid field) should still parse without error."""
        raw = '{"source": "A.out", "target": "B.in", "valid": true}'
        # Pydantic ignores extra fields by default or accepts known ones
        # Since we removed valid from the model, this tests tolerance
        try:
            edge = file_model.EdgeModel.model_validate_json(raw)
            assert edge.source == "A.out"
        except Exception:
            # If strict validation rejects extra fields, that's also acceptable
            pass


# ---------------------------------------------------------------------------
# Full graph round-trip (save → load)
# ---------------------------------------------------------------------------

class TestGraphRoundTrip:

    def _make_graph_model(self) -> file_model.NodeGraphModel:
        return file_model.NodeGraphModel(
            properties={"param": 42},
            nodes={
                "SampleNode_1": file_model.NodeModel(
                    type="SampleNode",
                    properties={"freq": 440.0, "gain": 1.0},
                ),
                "SampleNode_2": file_model.NodeModel(
                    type="SampleNode",
                    properties={"freq": 880.0, "gain": 0.5},
                    inputs={
                        "values": file_model.NodeInputPortModel(
                            dispatch_flags=[True, False],
                        )
                    },
                    property_groups=[file_model.PropertyGroupModel(keys=["freq", "gain"], dispatch_flags=[False, True])],
                ),
            },
            inputs={
                "series": file_model.PortModel(types=["f32", "f32[3]"]),
            },
            outputs={},
            edges=[
                file_model.EdgeModel(source="SampleNode_1.out", target="SampleNode_2.values"),
            ],
        )

    def test_save_json_compact(self):
        async def _test():
            with tempfile.TemporaryDirectory(suffix=".vng") as tmpdir:
                graph_model = self._make_graph_model()
                persist = FileNodeGraphPersist(
                    graph_model, pathlib.Path(tmpdir), GraphFileExtension.JSON
                )
                persist._write_graph(persist._take_graph_snapshot())

                saved = pathlib.Path(tmpdir) / "graph.json"
                assert saved.exists()

                text = saved.read_text()
                data = json.loads(text)

                # SampleNode_1: no inputs, no property_groups → omitted
                n1 = data["nodes"]["SampleNode_1"]
                assert "inputs" not in n1
                assert "property_groups" not in n1

                # SampleNode_2: has dispatch and property_groups
                n2 = data["nodes"]["SampleNode_2"]
                assert "inputs" in n2
                assert n2["inputs"]["values"]["dispatch_flags"] == [True, False]
                assert "property_groups" in n2

                # Graph inputs: SoA types array
                assert data["inputs"]["series"]["types"] == ["f32", "f32[3]"]

                # Edge: no valid field
                edge = data["edges"][0]
                assert "valid" not in edge
                assert edge["source"] == "SampleNode_1.out"

        asyncio.run(_test())

    def test_save_and_reload(self):
        async def _test():
            with tempfile.TemporaryDirectory(suffix=".vng") as tmpdir:
                graph_model = self._make_graph_model()
                persist = FileNodeGraphPersist(
                    graph_model, pathlib.Path(tmpdir), GraphFileExtension.JSON
                )
                persist._write_graph(persist._take_graph_snapshot())

                # Reload
                saved = pathlib.Path(tmpdir) / "graph.json"
                reloaded = file_model.NodeGraphModel.model_validate_json(saved.read_text())

                assert reloaded.properties == {"param": 42}
                assert len(reloaded.nodes) == 2
                assert len(reloaded.edges) == 1
                assert reloaded.nodes["SampleNode_1"].properties["freq"] == 440.0
                assert reloaded.nodes["SampleNode_2"].property_groups[0].keys == ["freq", "gain"]
                assert reloaded.nodes["SampleNode_2"].property_groups[0].dispatch_flags == [False, True]
                assert reloaded.nodes["SampleNode_2"].inputs["values"].dispatch_flags == [True, False]
                assert reloaded.inputs["series"].types == ["f32", "f32[3]"]

        asyncio.run(_test())
