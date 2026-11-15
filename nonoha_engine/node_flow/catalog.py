"""The node catalog as JSON: one shape for GET /node-flow/catalog/nodes and the CLI."""

from __future__ import annotations

from nonoha_core.node_registry import NodeDefinition, NodeRegistry, PortMetadata


def _port(p: PortMetadata) -> dict:
    entry: dict = {"name": p.name, "description": p.description, "types": p.value_types}
    if any(n is not None for n in p.value_names):
        entry["value_names"] = p.value_names
    return entry


def catalog_entry(defn: NodeDefinition) -> dict:
    m = defn.metadata
    entry: dict = {
        "type": defn.type_name,
        "description": m.description,
        "category": m.category,
        "inputs": [_port(p) for p in m.inputs],
        "outputs": [_port(p) for p in m.outputs],
        "properties": {
            name: {"default": prop.default, "description": prop.description}
            for name, prop in m.properties.items()
        },
    }
    if m.env:
        # Environment values the node reads (names only, never values)
        entry["env"] = [{"name": e.name, "description": e.description, "url": e.url} for e in m.env]
    return entry


def catalog(registry: NodeRegistry) -> list[dict]:
    return [catalog_entry(defn) for defn in registry.node_definitions.values()]
