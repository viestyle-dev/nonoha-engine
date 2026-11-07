# Plugin Development Guide

This guide walks you through creating a plugin for nonoha-engine from scratch. By the end, you'll have a working plugin with custom nodes that integrate seamlessly with the engine.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setting Up Your Plugin](#setting-up-your-plugin)
3. [Creating Your First Node](#creating-your-first-node)
4. [Working with Ports](#working-with-ports)
5. [Implementing Properties](#implementing-properties)
6. [Advanced Topics](#advanced-topics)
7. [Testing Your Plugin](#testing-your-plugin)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting plugin development, ensure you have:
- Python 3.11+ installed
- nonoha-engine repository cloned and set up
- Basic understanding of NumPy arrays
- Familiarity with Python classes and inheritance

## Setting Up Your Plugin

### 1. Create Plugin Directory Structure

```bash
# Navigate to the plugins directory
cd nonoha-workspace/plugins/

# Create your plugin directory
mkdir my_awesome_plugin
cd my_awesome_plugin

# Create required files
touch __init__.py
touch nodes.py
```

### 2. Configure manifest.json (Required)

You must add your plugin to the `plugins/manifest.json` file for it to be loaded:

```json
{
  "plugins": [
    {
      "name": "my_awesome_plugin",
      "enabled": true
    }
  ]
}
```

**Important:** 
- **manifest.json is required** - your plugin will not load without being listed
- The plugin name must match your directory name exactly
- Set `enabled: false` to temporarily disable a plugin without removing it

### 3. Basic Plugin Structure

Every plugin must have an `__init__.py` file with a `register_nodes` function:

```python
# __init__.py
from nonoha_core.node_registry import NodeRegistry
from .nodes import MyFirstNode, MySecondNode

def register_nodes(registry: NodeRegistry):
    """Register all plugin nodes with the engine.
    
    This function is called by the plugin loader when the engine starts.
    """
    registry.register_node("MyFirstNode", MyFirstNode)
    registry.register_node("MySecondNode", MySecondNode)

# Optional: Add async finalize for cleanup
async def finalize():
    """Clean up plugin resources on shutdown.
    
    This async function is called when the engine shuts down.
    """
    # Clean up any resources, close connections, etc.
    pass
```

## Creating Your First Node

### Step 1: Import Required Modules

```python
# nodes.py
from typing import ClassVar, Optional
import numpy as np
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType
```

### Step 2: Define Your Node Class

```python
class MultiplyNode(BaseNode):
    """Multiplies input by a configurable factor."""
    
    # Class-level metadata (optional but recommended)
    DESCRIPTION: ClassVar[str] = "Multiplies input values by a factor"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "factor": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=2.0,
            min_value=0.0,
            max_value=100.0,
            description="Multiplication factor"
        )
    }
    
    def __init__(self, name: str):
        # Initialize base class with node name and type
        super().__init__(name, "Multiply")
        
        # Initialize properties
        self._factor = 2.0
        self.properties["factor"] = self._factor
        
        # Create and configure input port
        self._setup_ports()
    
    def _setup_ports(self):
        """Set up input and output ports."""
        # Create input port for float arrays
        input_port = StaticTypeInputPort("input", [
            PortValueType(DataType.Float32, (-1,))  # Variable-length array
        ])
        # Subscribe to input changes
        input_port.subscribe(id(self), self._on_input_received)
        
        # Create output port
        output_port = StaticTypeOutputPort("output", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Register ports
        self.inputs[input_port.name] = input_port
        self.outputs[output_port.name] = output_port
        
        # Store output reference for dispatching
        self._output_port = output_port
    
    def _on_input_received(self, values: list[np.ndarray]):
        """Handle input data."""
        # values is a list with one array (we have one input port)
        input_array = values[0]
        
        # Process the data
        result = input_array * self._factor
        
        # Send to output
        self._output_port.dispatch([result])
    
    def set_properties(self, properties: dict[str, PropertyDataType]):
        """Update node properties."""
        if "factor" in properties:
            self._factor = float(properties["factor"])
            self.properties["factor"] = self._factor
            
            # Notify graph if properties affect structure
            if self.parent_graph is not None:
                self.parent_graph.notify_node_updated(self)
    
    def finalize(self):
        """Clean up resources when node is destroyed."""
        # Unsubscribe from all ports
        for input_port in self.inputs.values():
            input_port.unsubscribe(id(self))
```

## Working with Ports

### Port Types and Data Types

#### Available Data Types
```python
from nonoha_core.data_type import DataType

# Numeric types
DataType.Bool      # Boolean values
DataType.Int8      # 8-bit signed integer
DataType.Int16     # 16-bit signed integer
DataType.Int32     # 32-bit signed integer
DataType.Int64     # 64-bit signed integer
DataType.Uint8     # 8-bit unsigned integer
DataType.Uint16    # 16-bit unsigned integer
DataType.Uint32    # 32-bit unsigned integer
DataType.Uint64    # 64-bit unsigned integer
DataType.Float32   # 32-bit float
DataType.Float64   # 64-bit float
DataType.Complex64 # 64-bit complex
DataType.Complex128 # 128-bit complex
DataType.String    # String values
DataType.Any       # Any type (use sparingly)
```

#### Shape Specifications
```python
# Scalar value
PortValueType(DataType.Float32, ())

# 1D array of fixed length 100
PortValueType(DataType.Float32, (100,))

# 1D array of variable length
PortValueType(DataType.Float32, (-1,))

# 2D array 10x20
PortValueType(DataType.Float32, (10, 20))

# 2D array with variable rows, 3 columns
PortValueType(DataType.Float32, (-1, 3))
```

### Multiple Input Ports

```python
class AddNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "Add")
        
        # Create two input ports
        input_a = StaticTypeInputPort("a", [
            PortValueType(DataType.Float32, (-1,))
        ])
        input_b = StaticTypeInputPort("b", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Subscribe both to the same handler
        input_a.subscribe(id(self), self._on_input)
        input_b.subscribe(id(self), self._on_input)
        
        # Create output
        output = StaticTypeOutputPort("sum", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Register all ports
        self.inputs["a"] = input_a
        self.inputs["b"] = input_b
        self.outputs["sum"] = output
        
        self._output = output
        self._last_a = None
        self._last_b = None
    
    def _on_input(self, values: list[np.ndarray]):
        """Handle input from either port."""
        # Check which port triggered the callback
        if len(values) > 0:
            # Store latest values
            if self.inputs["a"].has_data():
                self._last_a = self.inputs["a"].get_data()[0]
            if self.inputs["b"].has_data():
                self._last_b = self.inputs["b"].get_data()[0]
            
            # Process if both inputs are available
            if self._last_a is not None and self._last_b is not None:
                result = self._last_a + self._last_b
                self._output.dispatch([result])
```

### Source Nodes (No Inputs)

```python
class RandomGeneratorNode(BaseNode):
    """Generates random numbers periodically."""
    
    def __init__(self, name: str):
        super().__init__(name, "RandomGenerator")
        
        # Only output port, no inputs
        output = StaticTypeOutputPort("random", [
            PortValueType(DataType.Float32, (1,))
        ])
        self.outputs["random"] = output
        self._output = output
        
        # Timer for periodic generation
        self._timer = None
        self._start_generation()
    
    def _start_generation(self):
        """Start generating random numbers."""
        import asyncio
        
        async def generate():
            while True:
                await asyncio.sleep(1.0)  # Generate every second
                value = np.random.random(1).astype(np.float32)
                self._output.dispatch([value])
        
        # Start async task
        self._task = asyncio.create_task(generate())
    
    def finalize(self):
        """Stop generation when node is destroyed."""
        if self._task:
            self._task.cancel()
```

## Implementing Properties

### Simple Properties

```python
class ConfigurableNode(BaseNode):
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "mode": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="linear",
            options=["linear", "exponential", "logarithmic"],
            description="Processing mode"
        ),
        "threshold": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            description="Detection threshold"
        ),
        "enabled": PropertyDescription(
            data_type=PropertyDataType.Bool,
            default_value=True,
            description="Enable processing"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "Configurable")
        
        # Initialize with defaults
        self._mode = "linear"
        self._threshold = 0.5
        self._enabled = True
        
        # Set initial properties
        self.properties["mode"] = self._mode
        self.properties["threshold"] = self._threshold
        self.properties["enabled"] = self._enabled
    
    def set_properties(self, properties: dict):
        """Handle property updates from UI."""
        changed = False
        
        if "mode" in properties and properties["mode"] != self._mode:
            self._mode = properties["mode"]
            self.properties["mode"] = self._mode
            changed = True
        
        if "threshold" in properties:
            self._threshold = float(properties["threshold"])
            self.properties["threshold"] = self._threshold
        
        if "enabled" in properties:
            self._enabled = bool(properties["enabled"])
            self.properties["enabled"] = self._enabled
        
        # Rebuild node if structural changes
        if changed and self.parent_graph:
            self.parent_graph.notify_node_updated(self)
```

### Dynamic Properties Based on Other Properties

```python
def set_properties(self, properties: dict):
    """Update properties and potentially create/remove ports."""
    if "num_inputs" in properties:
        new_count = int(properties["num_inputs"])
        if new_count != self._num_inputs:
            self._num_inputs = new_count
            self._rebuild_ports()  # Recreate ports based on new count
            
            if self.parent_graph:
                self.parent_graph.notify_node_updated(self)
```

## Advanced Topics

### Using External Libraries

```python
class ImageProcessingNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "ImageProcessor")
        
        # Import heavy libraries only when needed
        try:
            import cv2
            self._cv2 = cv2
        except ImportError:
            raise RuntimeError("OpenCV is required for ImageProcessingNode")
        
        self._setup_ports()
    
    def _on_image_input(self, values: list[np.ndarray]):
        """Process image with OpenCV."""
        image = values[0]
        
        # Apply Gaussian blur
        blurred = self._cv2.GaussianBlur(image, (5, 5), 0)
        
        self._output.dispatch([blurred])
```

### Sharing Resources Between Nodes

```python
# __init__.py
from nonoha_core.node_registry import NodeRegistry
from .shared_resource import SharedDatabase
from .nodes import DatabaseReaderNode, DatabaseWriterNode

def create_reader_factory(database: SharedDatabase):
    def factory(name: str) -> BaseNode:
        return DatabaseReaderNode(name, database)
    return factory

def create_writer_factory(database: SharedDatabase):
    def factory(name: str) -> BaseNode:
        return DatabaseWriterNode(name, database)
    return factory

def register_nodes(registry: NodeRegistry):
    # Create shared resource
    database = SharedDatabase("connection_string")
    
    # Register nodes with shared resource
    registry.register_node("DatabaseReader", create_reader_factory(database))
    registry.register_node("DatabaseWriter", create_writer_factory(database))
```

### Stateful Processing

```python
class MovingAverageNode(BaseNode):
    """Calculates moving average over a window."""
    
    def __init__(self, name: str):
        super().__init__(name, "MovingAverage")
        
        self._window_size = 10
        self._buffer = []
        
        # Setup ports...
    
    def _on_input(self, values: list[np.ndarray]):
        """Update buffer and calculate average."""
        new_value = values[0]
        
        # Add to buffer
        self._buffer.append(new_value)
        
        # Maintain window size
        if len(self._buffer) > self._window_size:
            self._buffer.pop(0)
        
        # Calculate average
        if self._buffer:
            average = np.mean(self._buffer, axis=0)
            self._output.dispatch([average])
    
    def set_properties(self, properties: dict):
        """Update window size."""
        if "window_size" in properties:
            self._window_size = int(properties["window_size"])
            # Clear buffer on window size change
            self._buffer.clear()
```

## Testing Your Plugin

### 1. Unit Testing

Create a test file for your nodes:

```python
# test_my_plugin.py
import numpy as np
from my_awesome_plugin.nodes import MultiplyNode

def test_multiply_node():
    # Create node instance
    node = MultiplyNode("test_multiply")
    
    # Set properties
    node.set_properties({"factor": 3.0})
    
    # Create test input
    test_input = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    
    # Simulate input
    received_output = None
    def capture_output(values):
        nonlocal received_output
        received_output = values[0]
    
    # Connect output capture
    node._output_port.subscribe("test", capture_output)
    
    # Send input
    node._on_input_received([test_input])
    
    # Verify output
    expected = np.array([3.0, 6.0, 9.0], dtype=np.float32)
    assert np.allclose(received_output, expected)
    
    # Cleanup
    node.finalize()
```

### 2. Integration Testing

Test your plugin with the engine:

```bash
# Start the engine with your plugin
cd nonoha-workspace
python nonoha-engine/main.py --plugins ./plugins --vnf workspace/test.vnf

# In the editor, add your nodes and test connections
```

### 3. Debugging Tips

Add logging to your nodes:

```python
import logging

class DebugNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "Debug")
        self.logger = logging.getLogger(f"DebugNode.{name}")
        self.logger.setLevel(logging.DEBUG)
    
    def _on_input(self, values: list[np.ndarray]):
        self.logger.debug(f"Received input shape: {values[0].shape}")
        self.logger.debug(f"Input dtype: {values[0].dtype}")
        self.logger.debug(f"Input values: {values[0][:5]}")  # First 5 values
        
        # Process...
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Node not appearing in editor
**Solution**: Check that:
- `__init__.py` exists and has `register_nodes` function
- Node type name in registration matches exactly
- No import errors in your plugin
- Plugin directory is in `plugins/nodes/`

#### Issue: "None" sent through port error
**Solution**: Never send `None` through ports. Use empty arrays instead:
```python
# Wrong
self._output.dispatch([None])

# Correct
self._output.dispatch([np.array([], dtype=np.float32)])
```

#### Issue: Properties not updating
**Solution**: Ensure you:
- Update both internal state and `self.properties` dict
- Call `self.parent_graph.notify_node_updated(self)` for structural changes
- Convert property values to correct types

#### Issue: Memory leak with subscriptions
**Solution**: Always unsubscribe in `finalize()`:
```python
def finalize(self):
    for input_port in self.inputs.values():
        input_port.unsubscribe(id(self))
```

#### Issue: Async operations not stopping
**Solution**: Cancel async tasks in `finalize()`:
```python
def finalize(self):
    if hasattr(self, '_task') and self._task:
        self._task.cancel()
```

### Performance Optimization

1. **Use NumPy operations** instead of Python loops
2. **Avoid copying arrays** unless necessary
3. **Cache computed values** when appropriate
4. **Use appropriate data types** (Float32 vs Float64)
5. **Batch operations** when possible

### Security Considerations

1. **Validate all inputs** before processing
2. **Sanitize file paths** if handling files
3. **Limit resource usage** (memory, CPU)
4. **Handle errors gracefully** without exposing internals
5. **Use isolated module names** (handled by plugin loader)

## Next Steps

- Explore the [API Reference](./api-reference.md) for detailed method documentation
- Check [Examples](./examples.md) for more complex node implementations
- Review existing plugins in the repository for inspiration
- Test your plugin thoroughly before deployment