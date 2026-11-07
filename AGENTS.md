# AGENTS.md — nonoha-engine

AI agent guide for developing custom nodes, plugins, and apps with nonoha-engine.

## Overview

nonoha-engine is a visual node-based data processing engine. Data flows through directed graphs of nodes as **numpy arrays with batch dimensions**. The engine exposes REST and WebSocket APIs.

## Quick Start Commands

```bash
# Run engine (built-in nodes only)
uv run main.py --vnf flows/default.vnf

# Run engine with template (plugins + sample app)
uv run main.py --vnf templates/default/flows/default.vnf --plugins ./templates/default/plugins

# Install dependencies
uv sync

# Run tests
uv run pytest tests -s

# Generate node catalog (JSON)
uv run main.py catalog
```

Editor: `http://localhost:8000/editor?engine-uri=localhost:8000`
(requires an `editor_html/` build next to `main.py`; not included in this repository)
Custom App: `http://localhost:8000/app`

## Critical Rules

1. **All data flows as numpy arrays with batch dimension** — scalar `5.0` → `np.array([5.0])` shape `(1,)`
2. **`dispatch()` values must include batch dimension** — if port type is `f32[N]` (ndim=1), dispatched array must be shape `(batch, N)` i.e. ndim=2. Add `[np.newaxis]` to prepend batch dim. This is auto-validated during `pytest` via the `nonoha_core._testing` plugin.
3. **`__init__()` must be side-effect-free** — no asyncio, no I/O, no network. Use `activate()` for runtime
4. **Port names cannot contain**: `.` (dot), `-` (hyphen), `$` (dollar) — reserved delimiters
5. **Always call `notify_node_updated()`** after modifying ports in `set_properties()`
6. **Python 3.11 only** — 3.12+ is not supported
7. **Use `catalog` subcommand to discover nodes** — do NOT scan source files manually

## Node Catalog

To see all available nodes (built-in + plugins), use the catalog subcommand:

```bash
# Output full catalog as JSON (no server needed)
uv run main.py --plugins ./templates/default/plugins catalog

# Or via REST API when engine is running
# GET http://localhost:8000/node-flow/catalog/nodes
```

The catalog includes node type, description, category, input/output ports with types, and properties with defaults. Always use this instead of reading node source files.

Important: the `-o` flag is required (output to file, not stdout):
```bash
uv run main.py --plugins ./templates/default/plugins catalog -o catalog.json
```

## Common Pitfalls

- **Clock node requires `enabled=true`** to start emitting time values. It does NOT auto-start. You must send `true` to its `enabled` input port (e.g., via a graph input connected from the app, or a RealNumberValue node).
- **Stopping the engine**: Send `quit` to the engine's stdin for graceful shutdown. When running in background, use a named pipe:

```bash
# Start with named pipe (allows graceful shutdown)
mkfifo /tmp/engine_stdin
cat /tmp/engine_stdin | uv run main.py --vnf flows/default.vnf &

# Graceful stop
echo "quit" > /tmp/engine_stdin

# Fallback (Windows): pkill does not work for native python.exe.
# Find PID then force kill:
netstat -ano | findstr ":8000" | findstr "LISTEN"
taskkill //PID <PID> //F
```
- **nonoha-client-js method names**: `addOutputCallback()` (not `onOutput`), `addClosedCallback()` (not `onClosed`), `dispatchInput()` (not `sendInput`). Check the nonoha-client-js source (`graph-endpoint.ts`) for the exact API.

## Plugin Structure

```
plugins/
├── manifest.json                 # Plugin registry
└── my_plugin/                    # Plugin directory (underscores)
    ├── pyproject.toml            # Package metadata
    └── my_plugin/                # Python package (same name)
        ├── __init__.py           # register_nodes(registry) — REQUIRED
        └── nodes.py              # Node implementations
```

### manifest.json

```json
{
  "plugins": [
    {"name": "my_plugin", "enabled": true}
  ]
}
```

### pyproject.toml

```toml
[project]
name = "my-plugin"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["my_plugin"]

[tool.hatch.metadata]
allow-direct-references = true
```

### __init__.py

```python
from nonoha_core.node_registry import NodeRegistry
from .nodes import MyNode

def register_nodes(registry: NodeRegistry):
    registry.register_node("MyNode", MyNode)

# Optional: cleanup on shutdown
async def finalize():
    pass
```

## Node Implementation

### Minimal Node (data-in → data-out)

```python
import numpy as np
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType

class MyNode(BaseNode):
    # 1. describe() — catalog documentation (not used at runtime)
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Multiplies input by a configurable factor",
            category="Custom",
            inputs={"in": "Input values"},
            outputs={"out": "Result"},
        )

    # 2. PROPERTIES — runtime configuration
    PROPERTIES = {
        "factor": {"description": "Multiplication factor", "default_value": 2.0, "data_type": "f64"},
    }

    def __init__(self, name: str):
        super().__init__(name, "MyNode")

        # 3. Define port value types
        value_type = PortValueType(DataType.Float32)

        # 4. Create input port and subscribe to data
        self._input = StaticTypeInputPort("in", [value_type])
        self._input.subscribe(id(self), self._on_input)
        self.inputs[self._input.name] = self._input

        # 5. Create output port
        self._output = StaticTypeOutputPort("out", [value_type])
        self.outputs[self._output.name] = self._output

    def _on_input(self, values: list[np.ndarray]):
        # values[0] is a numpy array with batch dimension
        factor = self.properties["factor"]
        result = values[0] * factor
        self._output.dispatch([result])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if "factor" in properties:
            self.properties["factor"] = float(properties["factor"])
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)
```

### Source Node (activate/finalize pattern)

For nodes that produce data on their own (timers, sensors, etc.):

```python
import asyncio
import numpy as np
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.port import StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType

class CounterNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Emits an incrementing counter at regular intervals",
            category="Custom",
            outputs={"count": "Current counter value"},
        )

    PROPERTIES = {
        "interval": {"description": "Seconds between ticks", "default_value": 1.0, "data_type": "f64"},
    }

    def __init__(self, name: str):
        super().__init__(name, "Counter")
        value_type = PortValueType(DataType.Float32)
        self._output = StaticTypeOutputPort("count", [value_type])
        self.outputs[self._output.name] = self._output
        self._count = 0
        self._task: asyncio.Task | None = None

    def activate(self):
        # Called when node enters a running graph — safe to use asyncio
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._tick_loop())

    async def _tick_loop(self):
        while True:
            await asyncio.sleep(self.properties["interval"])
            self._count += 1
            self._output.dispatch([np.array([float(self._count)], dtype=np.float32)])

    def finalize(self):
        # Called on removal — clean up. No super().finalize() needed
        if self._task:
            self._task.cancel()
            self._task = None
```

### set_properties with Port Replacement

When properties change port types, replace ports atomically:

```python
def set_properties(self, properties: dict[str, PropertyDataType]):
    # 1. Extract new values (start from current)
    new_type_name = properties.get("value_type", self.properties["value_type"])

    # 2. Check if ports need replacement
    if new_type_name != self.properties["value_type"]:
        new_pvt = PortValueType(name_to_data_type(new_type_name))

        # 3. Unsubscribe old port
        self._input.unsubscribe(id(self))
        if self.parent_graph:
            self.parent_graph.disconnect_all_from_node_input(self.name, self._input.name)

        # 4. Create and subscribe new port
        self._input = StaticTypeInputPort("in", [new_pvt])
        self._input.subscribe(id(self), self._on_input)
        self.inputs[self._input.name] = self._input

    # 5. Update properties dict
    self.properties["value_type"] = new_type_name

    # 6. ALWAYS notify graph
    if self.parent_graph:
        self.parent_graph.notify_node_updated(self)
```

## Data Types

| DataType | Short Name | numpy dtype | Example |
| --- | --- | --- | --- |
| Bool | bool | np.bool_ | `np.array([True])` |
| Int8 | i8 | np.int8 | `np.array([1], dtype=np.int8)` |
| Uint8 | u8 | np.uint8 | |
| Int16 | i16 | np.int16 | |
| Uint16 | u16 | np.uint16 | |
| Int32 | i32 | np.int32 | |
| Uint32 | u32 | np.uint32 | |
| Int64 | i64 | np.int64 | |
| Uint64 | u64 | np.uint64 | |
| Float32 | f32 | np.float32 | `np.array([3.14], dtype=np.float32)` |
| Float64 | f64 | np.float64 | |
| Complex64 | c64 | np.complex64 | |
| Complex128 | c128 | np.complex128 | |
| String | str | np.dtypes.StringDType | `np.array(["hello"])` |
| Any | any | (varies) | Accepts all types |

## Custom App Development

Custom apps are HTML/JS served from `flows/default.vnf/app/` at `http://host:port/app`.

### WebSocket Endpoint

```
ws://{host}:{port}/node-flow/graphs/{graph_name}/endpoint/ws
```

The app communicates with a graph's input/output ports via binary WebSocket protocol.

### Using nonoha-client.iife.js

```html
<script src="nonoha-client.iife.js"></script>
<script>
  const host = window.location.hostname;
  const port = window.location.port;
  const endpoint = NonohaClient.makeGraphEndpoint(`${host}:${port}`, 'app');

  // Listen for output data from graph
  endpoint.addOutputCallback((data) => {
    console.log('Port:', data.portName, 'Values:', data.values);
  });

  // Listen for disconnection
  endpoint.addClosedCallback((wasClean) => {
    console.log('Disconnected', wasClean);
  });

  // Connect
  endpoint.connect();

  // Send data to graph input port
  endpoint.dispatchInput({
    portName: 'my_input',
    values: [{
      dataType: NonohaClient.PortDataType.Float32,
      shape: [1],
      array: new Float32Array([42.0])
    }]
  });
</script>
```

### Graph Requirements for App

The graph (`app.vng`) must define input/output ports in `graph.json`:

```json
{
  "inputs": {
    "my_input": {
      "values": [{"type": "f32"}]
    }
  },
  "outputs": {
    "my_output": {
      "values": [{"type": "f32"}]
    }
  },
  "nodes": {},
  "edges": []
}
```

If the app needs data from another graph, use GraphProxy nodes. A GraphProxy
resolves its target by name within the same flow (the loaded `.vnf`), via the
graph's `parent_flow` — so the target graph must be listed **before** the
referencing graph in `flow.json`. GraphProxy, GraphLoaded and
GraphPropertiesChanged are implemented in `nonoha-core`
(`nonoha_core/nodes/graph_nodes.py`) and registered by core's
`register_nodes()`; only the WebSocket-based PortValuesSend node remains
engine-side.

## Graph Editor Settings (Node Layout)

Each `.vng` graph can have an editor layout file at:
`{graph}.vng/editors/nonoha-editor/models/settings.json`

Without this file, all nodes appear at default positions when opened in the editor.

```json
{
  "nodes": {
    "NodeName_1": { "type": "BasicEngineNode", "x": 400, "y": 300 },
    "$input:portName": { "type": "BasicPortNode", "x": 100, "y": 200 },
    "$output:portName": { "type": "BasicPortNode", "x": 800, "y": 200 },
    "$graph": { "width": 1400, "height": 800 }
  },
  "editor_edges": {}
}
```

Node type mapping:
- Engine nodes → `"BasicEngineNode"`
- Graph input/output ports → `"BasicPortNode"` (prefix `$input:` or `$output:`)
- `$graph` → canvas dimensions (no `type` field)

## Node Lifecycle

```
__init__()  →  [added to graph]  →  activate()  →  [running]  →  finalize()
  │                                      │                            │
  │ Define ports, properties             │ Get event loop,            │ Cancel tasks,
  │ Subscribe callbacks                  │ start tasks,               │ close connections
  │ NO side effects                      │ open connections           │ No super() needed
```

## REST API Quick Reference

```
GET  /node-flow/graphs                              # List graphs
GET  /node-flow/catalog/nodes                       # Node catalog

POST   /node-flow/graphs/{graph}/nodes              # Create node
DELETE /node-flow/graphs/{graph}/nodes/{node}        # Delete node
PATCH  /node-flow/graphs/{graph}/nodes/{node}/properties  # Set properties
GET    /node-flow/graphs/{graph}/nodes/{node}        # Get node info

POST   /node-flow/graphs/{graph}/edges              # Connect nodes
DELETE /node-flow/graphs/{graph}/edges/{edge}        # Disconnect
```

## Source Code Map

| Path | Description |
| --- | --- |
| `packages/nonoha-core/src/nonoha_core/node.py` | BaseNode class |
| `packages/nonoha-core/src/nonoha_core/port.py` | Port classes (StaticTypeInputPort, StaticTypeOutputPort) |
| `packages/nonoha-core/src/nonoha_core/data_type.py` | DataType enum, PortValueType |
| `packages/nonoha-core/src/nonoha_core/node_registry.py` | NodeRegistry |
| `packages/nonoha-core/src/nonoha_core/nodes/` | Built-in node implementations |
| `nonoha_engine/node_flow/router.py` | REST/WebSocket API |
| `nonoha_engine/node_flow/node.py` | WebSocket endpoint binary protocol |
| `templates/default/` | Template workspace (plugins, app, graphs) |

## Detailed Documentation

| Document | Content |
| --- | --- |
| `docs/plugin-system/development-guide.md` | Step-by-step plugin tutorial |
| `docs/plugin-system/api-reference.md` | Plugin API reference |
| `docs/api-reference.md` | Engine REST API |
| `packages/nonoha-core/docs/port-system-specification.md` | Port system, batch dimensions, dispatch |
| `packages/nonoha-core/docs/nodegraph-architecture.md` | Core architecture |
| `packages/nonoha-core/docs/adding-node-properties.md` | Property system patterns |
