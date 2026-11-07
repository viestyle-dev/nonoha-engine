import pathlib
from typing import Callable
import logging
import cryptography.fernet

from nonoha_engine.file_binary_converts import file_binary_converts

from nonoha_core.node import BaseNodeFlow
from nonoha_core.node_registry import NodeRegistry
from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.data_type import name_to_port_value_type

from .node import (
    FileNodeGraphPersist,
    GraphFileExtension,
    NodeGraph,
    BaseNode,
    NodeGraphPersist,
)
from .data_storage import DataStorage
from .models.file_model import NodeFlowModel, NodeGraphModel

logger = logging.getLogger(__name__)


class NodeFactory:
    def __init__(self, type_name: str, make_function: Callable[[str], BaseNode]):
        self._make_function = make_function
        self._type_name = type_name

    @property
    def type_name(self):
        return self._type_name

    def make_node(self, name: str) -> BaseNode:
        return self._make_function(name)


class NodeFlow(BaseNodeFlow[NodeGraph]):
    def __init__(self, node_registry: NodeRegistry):
        super().__init__()
        self._node_registry = node_registry
        self.readonly: bool = False

    def finalize(self):
        logger.info("NodeFlow finalizing")
        super().finalize()

    @property
    def node_registry(self):
        return self._node_registry

    def _load_graph(
        self,
        preferred_name: str,
        graph_model: NodeGraphModel,
        persist: FileNodeGraphPersist | None = None,
    ):
        if preferred_name in self.graph_names:
            preferred_name = preferred_name + "_"

        graph = NodeGraph(preferred_name, graph_model.properties)
        # Attach the flow before applying node properties so graph-referencing
        # nodes (GraphProxy) can resolve previously loaded siblings.
        graph.set_parent_flow(self)
        if persist is not None:
            graph.set_persist(persist)
            # Set the persist to readonly for loading
            persist.readonly = True

        for node_name, node_model in graph_model.nodes.items():
            try:
                node = self._node_registry.create_node(node_model.type, node_name)
            except Exception as e:
                raise ValueError(
                    f"Failed to create node '{node_name}' (type: {node_model.type}) in graph '{preferred_name}'"
                ) from e
            graph.add_node(node)

            node.set_properties(node_model.properties)

            # Apply property groups from graph config
            if node_model.property_groups:
                node.set_property_groups(
                    [
                        {"keys": pg.keys, "dispatch_flags": pg.dispatch_flags}
                        for pg in node_model.property_groups
                    ]
                )

            for port_name, port in node.inputs.items():
                port_model = node_model.inputs.get(port_name)
                if port_model is None:
                    continue
                if len(port.dispatch_flags) != len(port_model.dispatch_flags):
                    logger.warning(
                        f"Node {node_name} port {port_name} dispatch flags length mismatch"
                    )
                    continue
                port.dispatch_flags = list(port_model.dispatch_flags)

        for input_name, input_model in graph_model.inputs.items():
            input_port = StaticTypeInputPort(
                input_name,
                [name_to_port_value_type(t) for t in input_model.types],
            )
            graph.add_input_port(input_port)

        for output_name, output_model in graph_model.outputs.items():
            output_port = StaticTypeOutputPort(
                output_name,
                [name_to_port_value_type(t) for t in output_model.types],
            )
            graph.add_output_port(output_port)

        for edge in graph_model.edges:
            source_node_name, source_port_name = edge.source.split(".", 1)
            target_node_name, target_port_name = edge.target.split(".", 1)

            try:
                if source_node_name == "" and target_node_name != "":
                    graph.connect_input_to_node(
                        source_port_name, target_node_name, target_port_name
                    )
                elif source_node_name != "" and target_node_name == "":
                    graph.connect_node_to_output(
                        source_node_name, source_port_name, target_port_name
                    )
                elif source_node_name != "" and target_node_name != "":
                    graph.connect_nodes(
                        source_node_name,
                        source_port_name,
                        target_node_name,
                        target_port_name,
                    )
            except (ValueError, KeyError) as e:
                # Store as invalid edge (no callback, edge record preserved)
                graph.add_invalid_edge(edge.source, edge.target)
                logger.warning(
                    f"Edge {edge.source} -> {edge.target} stored as invalid: {e}"
                )

        # Dispatch properties to nodes
        graph.set_properties(graph_model.properties)

        self.add_graph(graph)

        if persist is not None:
            persist.readonly = self.readonly

            graph.set_data_storage(DataStorage(
                persist.data_dir_path,
                readonly=persist.readonly,
            ))

        # Activate all nodes after loading is complete
        for node in graph.nodes.values():
            node._do_activate()

        graph.notify_graph_loaded()

        # Configuration contract: the loader commits the whole load batch
        # (set_properties/activate/graph_loaded emissions) with one flush.
        graph.flush_outputs()

        return graph

    async def load_graph_from_path(self, dir_path: pathlib.Path):
        if dir_path.suffix != ".vng":
            raise ValueError(f"Invalid file extension for graph: {dir_path}")

        graph_name = dir_path.stem

        if (dir_path / "graph.json").exists():
            extension = GraphFileExtension.JSON
            graph_file = dir_path / "graph.json"
            try:
                with open(graph_file) as f:
                    graph_model = NodeGraphModel.model_validate_json(f.read())
            except Exception as e:
                raise ValueError(f"Failed to parse graph file: {graph_file}") from e
        elif (dir_path / "graph.vjb").exists():
            extension = GraphFileExtension.VJB
            graph_file = dir_path / "graph.vjb"
            with open(graph_file, "rb") as f:
                data = f.read()
            try:
                text = file_binary_converts.decode(data)
            except cryptography.fernet.InvalidToken:
                raise ValueError(f"Failed to decrypt graph file: {graph_file}")
            try:
                graph_model = NodeGraphModel.model_validate_json(text)
            except Exception as e:
                raise ValueError(f"Failed to parse graph file: {graph_file}") from e
        else:
            raise ValueError(f"Graph file not found in: {dir_path}")

        persist = FileNodeGraphPersist(graph_model, dir_path, extension)
        graph = self._load_graph(graph_name, graph_model, persist)

        return graph

    async def load_node_flow_from_path(self, dir_path: pathlib.Path):
        if dir_path.suffix != ".vnf":
            raise ValueError(f"Invalid file extension for VNF: {dir_path}")

        flow_file_path = dir_path / "flow.json"
        try:
            with open(flow_file_path) as f:
                flow_model = NodeFlowModel.model_validate_json(f.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"VNF flow file not found: {flow_file_path}")
        except Exception as e:
            raise ValueError(f"Failed to parse VNF flow file: {flow_file_path}") from e

        for graph_name in flow_model.graphs:
            graph_dir = dir_path / "graphs" / f"{graph_name}.vng"
            try:
                await self.load_graph_from_path(graph_dir)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load graph '{graph_name}' in VNF: {dir_path}"
                ) from e
