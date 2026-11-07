# Plugin API Reference

Complete API documentation for Nonoha Engine plugin development.

## Table of Contents
- [Core Classes](#core-classes)
  - [BaseNode](#basenode)
  - [NodeRegistry](#noderegistry)
- [Port System](#port-system)
  - [StaticTypeInputPort](#statictypeinputport)
  - [StaticTypeOutputPort](#statictypeoutputport)
- [Data Types](#data-types)
  - [DataType](#datatype)
  - [PortValueType](#portvaluetype)
- [Plugin Functions](#plugin-functions)

## Core Classes

### BaseNode

Base class for all custom nodes.

```python
from nonoha_core.node import BaseNode
```

#### Constructor

```python
def __init__(self, name: str, type_name: str)
```

**Parameters:**
- `name`: Unique instance identifier
- `type_name`: Node type name

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Node instance name |
| `type_name` | str | Node type identifier |
| `inputs` | dict[str, InputPort] | Input ports |
| `outputs` | dict[str, OutputPort] | Output ports |
| `properties` | dict[str, Any] | Node properties |
| `parent_graph` | Optional[Graph] | Parent graph reference |

#### Methods

##### set_properties
```python
def set_properties(self, properties: dict) -> None
```
Handle property updates from the UI.

**Example:**
```python
def set_properties(self, properties: dict):
    if "threshold" in properties:
        self._threshold = float(properties["threshold"])
        self.properties["threshold"] = self._threshold
```

##### finalize
```python
def finalize(self) -> None
```
Cleanup when node is destroyed.

**Example:**
```python
def finalize(self):
    for input_port in self.inputs.values():
        input_port.unsubscribe(id(self))
```

### NodeRegistry

Registry for node types.

```python
from nonoha_core.node_registry import NodeRegistry
```

#### Methods

##### register_node
```python
def register_node(self, type_name: str, factory: Callable[[str], BaseNode]) -> None
```

Register a node type with the engine.

**Parameters:**
- `type_name`: Node type identifier
- `factory`: Function that creates node instances

**Example:**
```python
def register_nodes(registry: NodeRegistry):
    registry.register_node("MyNode", MyNode)
    # Or with factory
    registry.register_node("MyNode", lambda name: MyNode(name, config))
```

## Port System

### StaticTypeInputPort

Input port with fixed data type.

```python
from nonoha_core.port import StaticTypeInputPort
```

#### Constructor

```python
def __init__(self, name: str, accepted_types: list[PortValueType])
```

**Parameters:**
- `name`: Port name
- `accepted_types`: List of accepted data types

#### Methods

##### subscribe
```python
def subscribe(self, subscriber_id: int, callback: Callable[[list[np.ndarray]], None]) -> None
```

Subscribe to port value changes.

**Example:**
```python
input_port = StaticTypeInputPort("input", [
    PortValueType(DataType.Float32, (-1,))
])
input_port.subscribe(id(self), self._on_input)
```

##### unsubscribe
```python
def unsubscribe(self, subscriber_id: int) -> None
```

Unsubscribe from port updates.

### StaticTypeOutputPort

Output port with fixed data type.

```python
from nonoha_core.port import StaticTypeOutputPort
```

#### Constructor

```python
def __init__(self, name: str, output_types: list[PortValueType])
```

**Parameters:**
- `name`: Port name
- `output_types`: List of output data types

#### Methods

##### dispatch
```python
def dispatch(self, values: list[np.ndarray]) -> None
```

Send values to connected nodes.

**Example:**
```python
output_port = StaticTypeOutputPort("output", [
    PortValueType(DataType.Float32, (-1,))
])
output_port.dispatch([np.array([1.0, 2.0, 3.0])])
```

## Data Types

### DataType

Enumeration of supported data types.

```python
from nonoha_core.data_type import DataType
```

| Value | NumPy dtype | Description |
|-------|-------------|-------------|
| `Float32` | np.float32 | 32-bit float |
| `Float64` | np.float64 | 64-bit float |
| `Int32` | np.int32 | 32-bit integer |
| `Int64` | np.int64 | 64-bit integer |
| `Bool` | np.bool_ | Boolean |
| `String` | object | String (as object array) |
| `Complex64` | np.complex64 | 64-bit complex |
| `Complex128` | np.complex128 | 128-bit complex |

### PortValueType

Defines port data type and shape.

```python
from nonoha_core.data_type import PortValueType
```

#### Constructor

```python
def __init__(self, dtype: DataType, shape: tuple[int, ...] = ())
```

**Parameters:**
- `dtype`: Data type
- `shape`: Expected array shape (use -1 for variable length)

**Examples:**
```python
# Scalar float
PortValueType(DataType.Float32)

# Fixed-size array
PortValueType(DataType.Float32, (3,))

# Variable-length array
PortValueType(DataType.Float32, (-1,))

# 2D matrix
PortValueType(DataType.Float64, (4, 4))

# Variable rows, fixed columns
PortValueType(DataType.Int32, (-1, 3))
```

## Plugin Functions

### register_nodes

**Required** function for all plugins.

```python
def register_nodes(registry: NodeRegistry) -> None:
    """Register plugin nodes with the engine."""
    pass
```

**Parameters:**
- `registry`: Node registry instance

**Example:**
```python
def register_nodes(registry: NodeRegistry):
    registry.register_node("AddNode", AddNode)
    registry.register_node("MultiplyNode", MultiplyNode)
```

### finalize

Optional async cleanup function.

```python
async def finalize() -> None:
    """Clean up plugin resources."""
    pass
```

**Example:**
```python
async def finalize():
    await close_connections()
    logger.info("Plugin cleaned up")
```

## Complete Example

```python
# my_plugin/__init__.py
import numpy as np
from nonoha_core.node_registry import NodeRegistry
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType

class ProcessorNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "Processor")
        
        # Input port - variable length float array
        self._input = StaticTypeInputPort("input", [
            PortValueType(DataType.Float32, (-1,))
        ])
        self._input.subscribe(id(self), self._process)
        
        # Output port - same as input
        self._output = StaticTypeOutputPort("output", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Register ports
        self.inputs[self._input.name] = self._input
        self.outputs[self._output.name] = self._output
        
        # Properties
        self._gain = 1.0
        self.properties["gain"] = self._gain
    
    def _process(self, values: list[np.ndarray]):
        """Process input data."""
        if len(values) > 0:
            result = values[0] * self._gain
            self._output.dispatch([result])
    
    def set_properties(self, properties: dict):
        """Update properties."""
        if "gain" in properties:
            self._gain = float(properties["gain"])
            self.properties["gain"] = self._gain
    
    def finalize(self):
        """Cleanup."""
        self._input.unsubscribe(id(self))

def register_nodes(registry: NodeRegistry):
    """Register nodes."""
    registry.register_node("Processor", ProcessorNode)

async def finalize():
    """Plugin cleanup."""
    print("Plugin finalized")
```

## Type Hints

For better IDE support, use these type hints:

```python
from typing import Optional, Callable, Any
import numpy as np
import numpy.typing as npt

# Port callback type
PortCallback = Callable[[list[npt.NDArray[Any]]], None]

# Node factory type
NodeFactory = Callable[[str], BaseNode]

# Property value types
PropertyValue = Union[float, int, str, bool, list, dict]
```

## Error Handling

Always validate inputs:

```python
def _on_input(self, values: list[np.ndarray]):
    if not values:
        return
    
    try:
        data = values[0]
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        
        result = self._process_data(data)
        self._output.dispatch([result])
    except Exception as e:
        logger.error(f"Processing failed: {e}")
```

## Thread Safety

Nodes run in the main thread. For async operations:

```python
import asyncio

class AsyncNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "AsyncNode")
        self._task = None
    
    async def _async_process(self, data):
        # Async processing
        await asyncio.sleep(0.1)
        return data * 2
    
    def _on_input(self, values: list[np.ndarray]):
        if self._task:
            self._task.cancel()
        
        self._task = asyncio.create_task(
            self._process_async(values[0])
        )
    
    async def _process_async(self, data):
        result = await self._async_process(data)
        self._output.dispatch([result])
```