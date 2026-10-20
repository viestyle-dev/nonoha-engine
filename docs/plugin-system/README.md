# Nonoha Engine Plugin System

## Overview

The Nonoha Engine plugin system allows developers to extend the engine's functionality by creating custom nodes. Plugins can be loaded either from directory-based packages or as built-in modules bundled with the application.

## Plugin Structure

### Directory Layout

Each plugin must follow this standard structure:

```
plugins/
├── manifest.json              # Required: Plugin configuration
├── plugin-name/               # Plugin directory (with hyphens)
│   ├── pyproject.toml        # Package configuration
│   ├── README.md             # Plugin documentation
│   └── plugin_name/          # Python package (with underscores)
│       ├── __init__.py       # Must contain register_nodes()
│       └── nodes.py          # Node implementations
```

**Important**: 
- Plugin directory uses hyphens: `plugin-name/`
- Python package uses underscores: `plugin_name/`
- The `__init__.py` must be inside the Python package directory

## Loading Methods

### 1. Directory-Based Plugins (Development)

Plugins are loaded from a directory specified by the `--plugins` argument:

```bash
python main.py --vnf flow.vnf --plugins ./plugins
```

The `manifest.json` file is **required**:

```json
{
  "plugins": [
    {
      "name": "example-nodes",
      "enabled": true
    },
    {
      "name": "osc-nodes",
      "enabled": true
    },
    {
      "name": "audio-nodes",
      "enabled": false
    }
  ]
}
```

### 2. Built-in Plugins (Production)

For production builds, plugins can be imported directly:

```python
# src/main.py
import example_nodes
import osc_nodes
import audio_nodes

nonoha_engine.run(
    RuntimeConfig(
        builtin_plugins=(example_nodes, osc_nodes, audio_nodes)
    )
)
```

## Required Functions

### `register_nodes(registry: NodeRegistry)`

**Required** function in every plugin's `__init__.py`:

```python
from nonoha_core.node_registry import NodeRegistry
from .nodes import MyCustomNode

def register_nodes(registry: NodeRegistry):
    """Register plugin nodes with the engine."""
    registry.register_node("MyCustomNode", MyCustomNode)
```

### `finalize()` (Optional)

Optional async cleanup function:

```python
async def finalize():
    """Clean up plugin resources during shutdown."""
    await cleanup_resources()
    logger.info("Plugin finalized")
```

## Plugin Example

### Complete Plugin Structure

```
plugins/
├── manifest.json
└── example-nodes/
    ├── pyproject.toml
    ├── README.md
    └── example_nodes/
        ├── __init__.py
        └── example_nodes.py
```

### pyproject.toml

```toml
[project]
name = "example-nodes"
version = "0.1.0"
description = "Example nodes for Nonoha Engine"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "numpy>=2.0",
    "nonoha-core"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### __init__.py

```python
import logging
from nonoha_core.node_registry import NodeRegistry
from .example_nodes import HelloFromPluginNode

logger = logging.getLogger(__name__)

def register_nodes(registry: NodeRegistry):
    """Register all nodes from this plugin."""
    logger.info("Registering example-nodes plugin")
    registry.register_node("HelloFromPlugin", HelloFromPluginNode)

async def finalize():
    """Optional cleanup function."""
    logger.info("Finalizing example-nodes plugin")
```

### example_nodes.py

```python
import numpy as np
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType

class HelloFromPluginNode(BaseNode):
    """Example node that adds a prefix to input values."""
    
    def __init__(self, name: str):
        super().__init__(name, "HelloFromPlugin")
        
        # Create input port
        input_port = StaticTypeInputPort("in", [
            PortValueType(DataType.Float32)
        ])
        input_port.subscribe(id(self), self._on_input)
        
        # Create output port
        output_port = StaticTypeOutputPort("out", [
            PortValueType(DataType.String)
        ])
        
        # Store references
        self.inputs[input_port.name] = input_port
        self.outputs[output_port.name] = output_port
        self._output_port = output_port
        
        # Properties
        self._prefix = "Hello"
        self.properties["prefix"] = self._prefix
    
    def _on_input(self, values: list[np.ndarray]):
        """Process input and send to output."""
        result = f"{self._prefix}: {values[0]}"
        self._output_port.dispatch([np.array(result)])
    
    def set_properties(self, properties: dict):
        """Update node properties."""
        if "prefix" in properties:
            self._prefix = str(properties["prefix"])
            self.properties["prefix"] = self._prefix
```

## Plugin Lifecycle

1. **Discovery**: 
   - Directory plugins: Read from manifest.json
   - Built-in plugins: Passed via RuntimeConfig

2. **Loading**:
   - Import plugin module
   - Create isolated namespace (directory plugins)

3. **Registration**:
   - Call `register_nodes(registry)`
   - Nodes become available for use

4. **Runtime**:
   - Nodes are instantiated when added to flows
   - Handle data processing via callbacks

5. **Finalization**:
   - Call `finalize()` if defined
   - Clean up resources during shutdown

## Best Practices

### Do's ✅
- Use consistent naming: `plugin-name/` for directory, `plugin_name/` for package
- Include all dependencies in pyproject.toml
- Implement proper error handling
- Use logging for debugging
- Clean up resources in `finalize()`
- Document node properties and behavior

### Don'ts ❌
- Don't use relative imports between plugins
- Don't modify input arrays directly
- Don't send `None` through ports
- Don't block the main thread
- Don't store references to other nodes

## Troubleshooting

### Plugin Not Loading

1. **Check manifest.json exists** in the plugins directory
2. **Verify plugin is listed** in manifest.json
3. **Ensure enabled: true** for the plugin
4. **Check directory structure**: `plugin-name/plugin_name/__init__.py`
5. **Verify register_nodes()** function exists in `__init__.py`

### Import Errors

1. **Module not found**: Check package structure uses underscores
2. **Dependencies missing**: Add to pyproject.toml and run `uv sync`
3. **Path issues**: Ensure plugin is in correct directory

### Runtime Errors

1. **Enable logging**: Check console output for error messages
2. **Validate data types**: Ensure correct NumPy dtypes
3. **Check port connections**: Verify input/output compatibility

## Migration from Old Structure

If migrating from the old flat structure:

**Old structure:**
```
plugins/
├── example-nodes/
│   ├── __init__.py
│   └── example_nodes.py
```

**New structure:**
```
plugins/
├── manifest.json
└── example-nodes/
    └── example_nodes/
        ├── __init__.py
        └── example_nodes.py
```

Steps:
1. Create subdirectory with underscored name
2. Move Python files into subdirectory
3. Update imports if necessary
4. Add plugin to manifest.json

## Next Steps

- Read the [API Reference](api-reference.md) for detailed API documentation
- See [Development Guide](development-guide.md) for step-by-step tutorials
- Explore [Examples](examples.md) for more complex implementations