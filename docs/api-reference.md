# Nonoha Engine API Reference

## Overview

The Nonoha Engine provides REST and WebSocket APIs for managing node flows, graphs, and real-time data processing. The API is available at `http://localhost:8000` by default.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. CORS is enabled for all origins.

## REST API

### Root Endpoint

#### GET /
Get API information and available endpoints.

**Response:**
```json
{
  "node_flow_url": "/node_flow"
}
```

---

### Graph Management

#### GET /node-flow/graphs
Get list of available graphs.

**Response:**
```json
["graph1", "graph2", "main_graph"]
```

#### GET /node-flow/graphs/{graph_name}/properties
Get graph properties.

**Parameters:**
- `graph_name` (path): Name of the graph

**Response:**
```json
{
  "property1": "value1",
  "property2": 123
}
```

#### PATCH /node-flow/graphs/{graph_name}/properties
Update graph properties.

**Parameters:**
- `graph_name` (path): Name of the graph

**Request Body:**
```json
{
  "property1": "new_value",
  "property2": 456
}
```

---

### Node Management

#### GET /node-flow/graphs/{graph_name}/nodes
Get list of nodes in a graph.

**Parameters:**
- `graph_name` (path): Name of the graph

**Response:**
```json
["node1", "node2", "AddNumber_1"]
```

#### POST /node-flow/graphs/{graph_name}/nodes
Create a new node in the graph.

**Parameters:**
- `graph_name` (path): Name of the graph

**Request Body:**
```json
{
  "type": "AddNumber",
  "preferred_name": "my_adder",
  "properties": {
    "value": 10.0
  }
}
```

**Response:**
```json
{
  "name": "my_adder",
  "type": "AddNumber",
  "properties": {
    "value": 10.0
  },
  "inputs": [
    {
      "name": "input",
      "values": [
        {
          "type": "Float32[-1]",
          "name": "default",
          "dispatch_flag": true
        }
      ]
    }
  ],
  "outputs": [
    {
      "name": "output",
      "values": [
        {
          "type": "Float32[-1]",
          "name": "default"
        }
      ]
    }
  ]
}
```

#### GET /node-flow/graphs/{graph_name}/nodes/{node_name}
Get node details.

**Parameters:**
- `graph_name` (path): Name of the graph
- `node_name` (path): Name of the node

**Response:** Same as POST response

#### DELETE /node-flow/graphs/{graph_name}/nodes/{node_name}
Delete a node from the graph.

**Parameters:**
- `graph_name` (path): Name of the graph
- `node_name` (path): Name of the node

---

### Node Properties

#### GET /node-flow/graphs/{graph_name}/nodes/{node_name}/properties
Get node properties.

**Parameters:**
- `graph_name` (path): Name of the graph
- `node_name` (path): Name of the node

**Response:**
```json
{
  "gain": 1.5,
  "offset": 0.0
}
```

#### PATCH /node-flow/graphs/{graph_name}/nodes/{node_name}/properties
Update node properties.

**Parameters:**
- `graph_name` (path): Name of the graph
- `node_name` (path): Name of the node

**Request Body:**
```json
{
  "gain": 2.0,
  "offset": 1.0
}
```

---

### Port Management

#### GET /node-flow/graphs/{graph_name}/inputs
Get graph input ports.

**Parameters:**
- `graph_name` (path): Name of the graph

**Response:**
```json
[
  {
    "name": "input1",
    "values": [
      {
        "type": "Float32[-1]",
        "name": "default",
        "dispatch_flag": true
      }
    ]
  }
]
```

#### POST /node-flow/graphs/{graph_name}/inputs
Add input port to graph.

**Parameters:**
- `graph_name` (path): Name of the graph

**Request Body:**
```json
{
  "name": "new_input",
  "values": [
    {
      "type": "Float32[-1]",
      "name": "default",
      "dispatch_flag": true
    }
  ]
}
```

#### DELETE /node-flow/graphs/{graph_name}/inputs/{input_name}
Remove input port from graph.

**Parameters:**
- `graph_name` (path): Name of the graph
- `input_name` (path): Name of the input port

#### GET /node-flow/graphs/{graph_name}/outputs
Get graph output ports.

**Parameters:**
- `graph_name` (path): Name of the graph

**Response:**
```json
[
  {
    "name": "output1",
    "values": [
      {
        "type": "Float32[-1]",
        "name": "default"
      }
    ]
  }
]
```

#### POST /node-flow/graphs/{graph_name}/outputs
Add output port to graph.

**Parameters:**
- `graph_name` (path): Name of the graph

**Request Body:**
```json
{
  "name": "new_output",
  "values": [
    {
      "type": "Float32[-1]",
      "name": "default"
    }
  ]
}
```

#### DELETE /node-flow/graphs/{graph_name}/outputs/{output_name}
Remove output port from graph.

**Parameters:**
- `graph_name` (path): Name of the graph
- `output_name` (path): Name of the output port

#### GET /node-flow/graphs/{graph_name}/outputs/{output_name}/values
Get current values from output port (binary format).

**Parameters:**
- `graph_name` (path): Name of the graph
- `output_name` (path): Name of the output port

**Response:** Binary data (application/octet-stream)

---

### Edge Management

#### GET /node-flow/graphs/{graph_name}/edges
Get all edges (connections) in the graph.

**Parameters:**
- `graph_name` (path): Name of the graph

**Response:**
```json
[
  {
    "source": "node1.output",
    "target": "node2.input"
  },
  {
    "source": ".input1",
    "target": "node1.input"
  },
  {
    "source": "node2.output",
    "target": ".output1"
  }
]
```

**Note:** Empty node name (`.portname`) indicates graph input/output ports.

#### POST /node-flow/graphs/{graph_name}/edges
Create a new edge (connection).

**Parameters:**
- `graph_name` (path): Name of the graph

**Request Body:**
```json
{
  "source": "node1.output",
  "target": "node2.input"
}
```

**Edge Types:**
- Node to Node: `"nodeA.output" -> "nodeB.input"`
- Graph Input to Node: `".input1" -> "nodeA.input"`
- Node to Graph Output: `"nodeA.output" -> ".output1"`

#### DELETE /node-flow/graphs/{graph_name}/edges/{edge_key}
Delete an edge.

**Parameters:**
- `graph_name` (path): Name of the graph
- `edge_key` (path): Edge identifier in format `source-target` (e.g., `node1.output-node2.input`)

---

### Node Catalog

#### GET /node-flow/catalog/nodes
Get list of available node types.

**Response:**
```json
[
  "AddNumber",
  "Multiply",
  "BandPassFilter",
  "FFT",
  "PureScript",
  "Recorder",
  "WebRTCSource"
]
```

---

### Editor Models

#### GET /node-flow/graphs/{graph_name}/editors/{editor_name}/models/{model_name}
Get editor model value.

**Parameters:**
- `graph_name` (path): Name of the graph
- `editor_name` (path): Name of the editor
- `model_name` (path): Name of the model
- `query` (query): Query string

#### PUT /node-flow/graphs/{graph_name}/editors/{editor_name}/models/{model_name}
Set editor model value.

**Parameters:**
- `graph_name` (path): Name of the graph
- `editor_name` (path): Name of the editor
- `model_name` (path): Name of the model
- `query` (query): Query string

**Request Body:** Any JSON value

#### PATCH /node-flow/graphs/{graph_name}/editors/{editor_name}/models/{model_name}
Update editor model value.

**Parameters:**
- `graph_name` (path): Name of the graph
- `editor_name` (path): Name of the editor
- `model_name` (path): Name of the model
- `query` (query): Query string

**Request Body:** Any JSON value

#### DELETE /node-flow/graphs/{graph_name}/editors/{editor_name}/models/{model_name}
Delete editor model value.

**Parameters:**
- `graph_name` (path): Name of the graph
- `editor_name` (path): Name of the editor
- `model_name` (path): Name of the model
- `query` (query): Query string

---

## WebSocket API

### Graph Endpoint WebSocket

#### WS /node-flow/graphs/{graph_name}/endpoint/ws
Connect to graph for real-time data streaming.

**Parameters:**
- `graph_name` (path): Name of the graph

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/node-flow/graphs/main_graph/endpoint/ws');
```

### Binary Protocol Specification

The WebSocket uses a binary protocol for efficient data transfer. All multi-byte integers are in **big-endian** format.

#### Message Structure

Every message starts with a 1-byte event type:

| Byte | Description |
|------|-------------|
| 0 | Event Type (0x00 = INPUT, 0x01 = OUTPUT) |

#### Input Message Format (Client → Server)

Sends values to graph input ports.

```
+--------+-------------+----------+-------------+
| Offset | Size (bytes)| Type     | Description |
+--------+-------------+----------+-------------+
| 0      | 1           | uint8    | Event Type (0x00) |
| 1      | 1           | uint8    | Port name length |
| 2      | N           | string   | Port name (UTF-8) |
| 2+N    | 1           | uint8    | Value count |
| 3+N    | ...         | Values[] | Array of values |
+--------+-------------+----------+-------------+
```

##### Value Format

Each value in the array has the following structure:

```
+--------+-------------+----------+--------------------------------+
| Offset | Size (bytes)| Type     | Description                    |
+--------+-------------+----------+--------------------------------+
| 0      | 1           | uint8    | Data type (see Data Type enum)|
| 1      | 1           | uint8    | Number of dimensions (ndim)   |
| 2      | ndim*2      | uint16[] | Shape array (big-endian)      |
| 2+ndim*2| 4          | uint32   | Data size in bytes           |
| 6+ndim*2| data_size  | bytes    | Raw data (type-specific)     |
+--------+-------------+----------+--------------------------------+
```

#### Output Message Format (Server → Client)

Receives values from graph output ports.

```
+--------+-------------+----------+-------------+
| Offset | Size (bytes)| Type     | Description |
+--------+-------------+----------+-------------+
| 0      | 1           | uint8    | Event Type (0x01) |
| 1      | 1           | uint8    | Port name length |
| 2      | N           | string   | Port name (UTF-8) |
| 2+N    | 1           | uint8    | Value count |
| 3+N    | ...         | Values[] | Array of values |
+--------+-------------+----------+-------------+
```

The value format is identical to the input message format.

#### Data Type Enumeration

| Value | Type | NumPy dtype | Bytes per element |
|-------|------|-------------|-------------------|
| 0x00 | Float32 | `>f4` | 4 |
| 0x01 | Float64 | `>f8` | 8 |
| 0x02 | Int8 | `>i1` | 1 |
| 0x03 | Int16 | `>i2` | 2 |
| 0x04 | Int32 | `>i4` | 4 |
| 0x05 | Int64 | `>i8` | 8 |
| 0x06 | Uint8 | `>u1` | 1 |
| 0x07 | Uint16 | `>u2` | 2 |
| 0x08 | Uint32 | `>u4` | 4 |
| 0x09 | Uint64 | `>u8` | 8 |
| 0x0A | Bool | `>?` | 1 |
| 0x0B | Complex64 | `>c8` | 8 |
| 0x0C | Complex128 | `>c16` | 16 |
| 0x0D | String | object | variable |

**Note:** The `>` prefix indicates big-endian byte order.

### Binary Protocol Examples

#### Example 1: Sending Float32 Array

Sending `[1.0, 2.0, 3.0]` to input port "data":

```
00                  # Event type: INPUT
04                  # Port name length: 4
64 61 74 61         # Port name: "data"
01                  # Value count: 1
00                  # Data type: Float32
01                  # Dimensions: 1
00 03               # Shape: [3]
00 00 00 0C         # Data size: 12 bytes
3F 80 00 00         # 1.0 (big-endian float32)
40 00 00 00         # 2.0 (big-endian float32)
40 40 00 00         # 3.0 (big-endian float32)
```

#### Example 2: Receiving 2D Matrix

Receiving a 2x3 Float32 matrix from output port "result":

```
01                  # Event type: OUTPUT
06                  # Port name length: 6
72 65 73 75 6C 74   # Port name: "result"
01                  # Value count: 1
00                  # Data type: Float32
02                  # Dimensions: 2
00 02 00 03         # Shape: [2, 3]
00 00 00 18         # Data size: 24 bytes
[24 bytes of float32 data]
```

### JavaScript Implementation Example

```javascript
class NonohaWebSocket {
  constructor(graphName) {
    this.ws = new WebSocket(`ws://localhost:8000/node-flow/graphs/${graphName}/endpoint/ws`);
    this.ws.binaryType = 'arraybuffer';
  }

  // Send float array to input port
  sendInput(portName, floatArray) {
    const encoder = new TextEncoder();
    const portNameBytes = encoder.encode(portName);
    
    // Calculate buffer size
    const bufferSize = 1 + 1 + portNameBytes.length + 1 + 1 + 1 + 2 + 4 + floatArray.length * 4;
    const buffer = new ArrayBuffer(bufferSize);
    const view = new DataView(buffer);
    let offset = 0;
    
    // Event type
    view.setUint8(offset++, 0x00); // INPUT
    
    // Port name
    view.setUint8(offset++, portNameBytes.length);
    new Uint8Array(buffer, offset, portNameBytes.length).set(portNameBytes);
    offset += portNameBytes.length;
    
    // Value count
    view.setUint8(offset++, 1);
    
    // Data type (Float32)
    view.setUint8(offset++, 0x00);
    
    // Dimensions
    view.setUint8(offset++, 1);
    
    // Shape
    view.setUint16(offset, floatArray.length, false); // false = big-endian
    offset += 2;
    
    // Data size
    view.setUint32(offset, floatArray.length * 4, false);
    offset += 4;
    
    // Data
    for (let i = 0; i < floatArray.length; i++) {
      view.setFloat32(offset, floatArray[i], false);
      offset += 4;
    }
    
    this.ws.send(buffer);
  }
  
  // Parse output message
  parseOutput(arrayBuffer) {
    const view = new DataView(arrayBuffer);
    let offset = 0;
    
    const eventType = view.getUint8(offset++);
    if (eventType !== 0x01) return null; // Not OUTPUT
    
    const portNameLength = view.getUint8(offset++);
    const decoder = new TextDecoder();
    const portName = decoder.decode(new Uint8Array(arrayBuffer, offset, portNameLength));
    offset += portNameLength;
    
    const valueCount = view.getUint8(offset++);
    const values = [];
    
    for (let i = 0; i < valueCount; i++) {
      const dataType = view.getUint8(offset++);
      const ndim = view.getUint8(offset++);
      
      const shape = [];
      for (let j = 0; j < ndim; j++) {
        shape.push(view.getUint16(offset, false));
        offset += 2;
      }
      
      const dataSize = view.getUint32(offset, false);
      offset += 4;
      
      // Parse Float32 data
      if (dataType === 0x00) {
        const count = dataSize / 4;
        const data = [];
        for (let k = 0; k < count; k++) {
          data.push(view.getFloat32(offset, false));
          offset += 4;
        }
        values.push({ type: 'Float32', shape, data });
      }
    }
    
    return { portName, values };
  }
}

// Usage
const client = new NonohaWebSocket('main_graph');

client.ws.onmessage = (event) => {
  const output = client.parseOutput(event.data);
  if (output) {
    console.log(`Received from ${output.portName}:`, output.values);
  }
};

client.ws.onopen = () => {
  // Send data to input
  client.sendInput('data', [1.0, 2.0, 3.0, 4.0, 5.0]);
};
```

### Python Implementation Example

```python
import struct
import numpy as np
import websocket

class NonohaWebSocket:
    def __init__(self, graph_name):
        self.ws = websocket.WebSocket()
        self.ws.connect(f"ws://localhost:8000/node-flow/graphs/{graph_name}/endpoint/ws")
    
    def send_input(self, port_name: str, data: np.ndarray):
        """Send numpy array to input port."""
        buffer = bytearray()
        
        # Event type
        buffer.append(0x00)  # INPUT
        
        # Port name
        port_bytes = port_name.encode('utf-8')
        buffer.append(len(port_bytes))
        buffer.extend(port_bytes)
        
        # Value count
        buffer.append(1)
        
        # Data type (Float32)
        buffer.append(0x00)
        
        # Dimensions
        buffer.append(len(data.shape))
        
        # Shape
        for dim in data.shape:
            buffer.extend(struct.pack('>H', dim))
        
        # Data size
        data_bytes = data.astype('>f4').tobytes()
        buffer.extend(struct.pack('>I', len(data_bytes)))
        
        # Data
        buffer.extend(data_bytes)
        
        self.ws.send(buffer, opcode=websocket.ABNF.OPCODE_BINARY)
    
    def receive_output(self):
        """Receive and parse output message."""
        data = self.ws.recv()
        if not isinstance(data, bytes):
            return None
        
        offset = 0
        event_type = data[offset]
        offset += 1
        
        if event_type != 0x01:  # Not OUTPUT
            return None
        
        # Port name
        port_name_length = data[offset]
        offset += 1
        port_name = data[offset:offset+port_name_length].decode('utf-8')
        offset += port_name_length
        
        # Value count
        value_count = data[offset]
        offset += 1
        
        values = []
        for _ in range(value_count):
            # Data type
            data_type = data[offset]
            offset += 1
            
            # Dimensions
            ndim = data[offset]
            offset += 1
            
            # Shape
            shape = struct.unpack(f'>{ndim}H', data[offset:offset+ndim*2])
            offset += ndim * 2
            
            # Data size
            data_size = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            
            # Parse data based on type
            if data_type == 0x00:  # Float32
                count = data_size // 4
                array_data = np.frombuffer(data[offset:offset+data_size], dtype='>f4')
                array_data = array_data.reshape(shape)
                values.append(array_data)
            
            offset += data_size
        
        return {'port_name': port_name, 'values': values}

# Usage
client = NonohaWebSocket('main_graph')

# Send data
data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
client.send_input('data', data)

# Receive data
output = client.receive_output()
if output:
    print(f"Received from {output['port_name']}: {output['values']}")
```

---

## Data Types

### Port Value Types

Port values are specified using type strings:

| Type String | Description | NumPy Type |
|------------|-------------|------------|
| `Float32` | 32-bit float scalar | np.float32 |
| `Float32[3]` | Fixed-size float array | np.float32 |
| `Float32[-1]` | Variable-size float array | np.float32 |
| `Float64` | 64-bit float scalar | np.float64 |
| `Int32` | 32-bit integer | np.int32 |
| `Bool` | Boolean | np.bool_ |
| `String` | String | object |
| `Complex64` | Complex number | np.complex64 |

### Property Data Types

Properties can be:
- Numbers (float, int)
- Strings
- Booleans
- Arrays
- Objects (nested dictionaries)

---

## Error Handling

All endpoints return standard HTTP status codes:

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found (graph/node/port not found) |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Examples

### Create a Simple Processing Pipeline

```bash
# 1. Get available graphs
curl http://localhost:8000/node-flow/graphs

# 2. Create an AddNumber node
curl -X POST http://localhost:8000/node-flow/graphs/main_graph/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "type": "AddNumber",
    "preferred_name": "adder1",
    "properties": {"value": 5.0}
  }'

# 3. Create a Multiply node
curl -X POST http://localhost:8000/node-flow/graphs/main_graph/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Multiply",
    "preferred_name": "mult1",
    "properties": {"factor": 2.0}
  }'

# 4. Connect the nodes
curl -X POST http://localhost:8000/node-flow/graphs/main_graph/edges \
  -H "Content-Type: application/json" \
  -d '{
    "source": "adder1.output",
    "target": "mult1.input"
  }'

# 5. Connect graph input to first node
curl -X POST http://localhost:8000/node-flow/graphs/main_graph/edges \
  -H "Content-Type: application/json" \
  -d '{
    "source": ".input1",
    "target": "adder1.input"
  }'

# 6. Connect last node to graph output
curl -X POST http://localhost:8000/node-flow/graphs/main_graph/edges \
  -H "Content-Type: application/json" \
  -d '{
    "source": "mult1.output",
    "target": ".output1"
  }'
```

### Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"
GRAPH_NAME = "main_graph"

# Get available node types
response = requests.get(f"{BASE_URL}/node-flow/catalog/nodes")
node_types = response.json()
print(f"Available node types: {node_types}")

# Create a node
node_data = {
    "type": "PureScript",
    "preferred_name": "script1",
    "properties": {
        "script": "output = input * 2"
    }
}
response = requests.post(
    f"{BASE_URL}/node-flow/graphs/{GRAPH_NAME}/nodes",
    json=node_data
)
node = response.json()
print(f"Created node: {node['name']}")

# Update node properties
properties = {"script": "output = input * 3 + 1"}
requests.patch(
    f"{BASE_URL}/node-flow/graphs/{GRAPH_NAME}/nodes/script1/properties",
    json=properties
)

# Get all edges
response = requests.get(f"{BASE_URL}/node-flow/graphs/{GRAPH_NAME}/edges")
edges = response.json()
print(f"Current edges: {edges}")
```

---

## WebRTC Gateway

The engine also includes WebRTC support through a separate router. See WebRTC documentation for details on peer-to-peer streaming capabilities.