# Plugin Examples

This document provides practical examples of plugin implementations for various use cases. Each example is complete and can be used as a starting point for your own plugins.

## Table of Contents
1. [Basic Examples](#basic-examples)
   - [Simple Math Operations](#simple-math-operations)
   - [String Processing](#string-processing)
2. [Data Processing Examples](#data-processing-examples)
   - [Signal Processing](#signal-processing)
   - [Data Filtering](#data-filtering)
3. [Device Integration Examples](#device-integration-examples)
   - [Sensor Data Reader](#sensor-data-reader)
   - [Hardware Monitor](#hardware-monitor)
4. [Advanced Examples](#advanced-examples)
   - [Machine Learning Integration](#machine-learning-integration)
   - [Real-time Stream Processing](#real-time-stream-processing)
   - [State Machine Node](#state-machine-node)

## Basic Examples

### Simple Math Operations

Complete plugin with basic mathematical operations:

```python
# plugins/nodes/math_operations/__init__.py
from nonoha_core.node_registry import NodeRegistry
from .nodes import AddNode, SubtractNode, MultiplyNode, DivideNode, PowerNode

def register_nodes(registry: NodeRegistry):
    registry.register_node("Add", AddNode)
    registry.register_node("Subtract", SubtractNode)
    registry.register_node("Multiply", MultiplyNode)
    registry.register_node("Divide", DivideNode)
    registry.register_node("Power", PowerNode)
```

```python
# plugins/nodes/math_operations/nodes.py
from typing import ClassVar
import numpy as np
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class MathOperationBase(BaseNode):
    """Base class for binary math operations."""
    
    def __init__(self, name: str, operation: str):
        super().__init__(name, operation)
        
        # Create input ports
        input_a = StaticTypeInputPort("a", [
            PortValueType(DataType.Float32, (-1,))
        ])
        input_b = StaticTypeInputPort("b", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Subscribe to inputs
        input_a.subscribe(id(self), self._on_input)
        input_b.subscribe(id(self), self._on_input)
        
        # Create output port
        output = StaticTypeOutputPort("result", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Register ports
        self.inputs["a"] = input_a
        self.inputs["b"] = input_b
        self.outputs["result"] = output
        
        self._output = output
        self._last_a = None
        self._last_b = None
    
    def _on_input(self, values: list[np.ndarray]):
        """Handle input from either port."""
        # Update cached values
        if "a" in self.inputs and len(values) > 0:
            self._last_a = values[0]
        
        # Try to get both inputs
        try:
            a_data = self.inputs["a"].get_data()
            b_data = self.inputs["b"].get_data()
            
            if a_data and b_data:
                result = self._compute(a_data[0], b_data[0])
                self._output.dispatch([result])
        except Exception as e:
            print(f"Error in {self.type_name}: {e}")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Override in subclasses."""
        raise NotImplementedError
    
    def finalize(self):
        for port in self.inputs.values():
            port.unsubscribe(id(self))

class AddNode(MathOperationBase):
    DESCRIPTION: ClassVar[str] = "Adds two arrays element-wise"
    
    def __init__(self, name: str):
        super().__init__(name, "Add")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a + b

class SubtractNode(MathOperationBase):
    DESCRIPTION: ClassVar[str] = "Subtracts second array from first"
    
    def __init__(self, name: str):
        super().__init__(name, "Subtract")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a - b

class MultiplyNode(MathOperationBase):
    DESCRIPTION: ClassVar[str] = "Multiplies two arrays element-wise"
    
    def __init__(self, name: str):
        super().__init__(name, "Multiply")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a * b

class DivideNode(MathOperationBase):
    DESCRIPTION: ClassVar[str] = "Divides first array by second"
    
    def __init__(self, name: str):
        super().__init__(name, "Divide")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        # Avoid division by zero
        return np.divide(a, b, out=np.zeros_like(a), where=b!=0)

class PowerNode(MathOperationBase):
    DESCRIPTION: ClassVar[str] = "Raises first array to power of second"
    
    def __init__(self, name: str):
        super().__init__(name, "Power")
    
    def _compute(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.power(a, b)
```

### String Processing

String manipulation plugin example:

```python
# plugins/nodes/string_processor/nodes.py
import numpy as np
from typing import ClassVar
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class StringFormatterNode(BaseNode):
    """Formats strings with a template."""
    
    DESCRIPTION: ClassVar[str] = "Format strings using a template"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "template": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="Value: {}",
            description="Format template (use {} for placeholder)"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "StringFormatter")
        
        # Properties
        self._template = "Value: {}"
        self.properties["template"] = self._template
        
        # Input port
        input_port = StaticTypeInputPort("input", [
            PortValueType(DataType.String, (-1,))
        ])
        input_port.subscribe(id(self), self._on_input)
        
        # Output port
        output_port = StaticTypeOutputPort("formatted", [
            PortValueType(DataType.String, (-1,))
        ])
        
        self.inputs["input"] = input_port
        self.outputs["formatted"] = output_port
        self._output = output_port
    
    def _on_input(self, values: list[np.ndarray]):
        """Format input strings."""
        input_array = values[0]
        
        # Apply template to each string
        result = np.array([
            self._template.format(str(val)) for val in input_array
        ], dtype=np.str_)
        
        self._output.dispatch([result])
    
    def set_properties(self, properties: dict):
        if "template" in properties:
            self._template = str(properties["template"])
            self.properties["template"] = self._template
    
    def finalize(self):
        self.inputs["input"].unsubscribe(id(self))

class StringSplitterNode(BaseNode):
    """Splits strings by delimiter."""
    
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "delimiter": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value=",",
            description="Split delimiter"
        ),
        "index": PropertyDescription(
            data_type=PropertyDataType.Int,
            default_value=0,
            min_value=0,
            description="Index of split part to return"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "StringSplitter")
        
        self._delimiter = ","
        self._index = 0
        self.properties["delimiter"] = self._delimiter
        self.properties["index"] = self._index
        
        # Ports setup...
        # Similar to StringFormatterNode
```

## Data Processing Examples

### Signal Processing

Digital signal processing nodes:

```python
# plugins/nodes/signal_processing/filters.py
import numpy as np
from typing import ClassVar
from scipy import signal
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class LowPassFilterNode(BaseNode):
    """Butterworth low-pass filter."""
    
    DESCRIPTION: ClassVar[str] = "Apply low-pass filter to signal"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "cutoff_freq": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=100.0,
            min_value=1.0,
            max_value=10000.0,
            description="Cutoff frequency (Hz)"
        ),
        "sample_rate": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=1000.0,
            min_value=1.0,
            description="Sample rate (Hz)"
        ),
        "order": PropertyDescription(
            data_type=PropertyDataType.Int,
            default_value=4,
            min_value=1,
            max_value=10,
            description="Filter order"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "LowPassFilter")
        
        # Filter parameters
        self._cutoff = 100.0
        self._sample_rate = 1000.0
        self._order = 4
        
        # Initialize properties
        self.properties["cutoff_freq"] = self._cutoff
        self.properties["sample_rate"] = self._sample_rate
        self.properties["order"] = self._order
        
        # Design filter
        self._design_filter()
        
        # Setup ports
        input_port = StaticTypeInputPort("signal", [
            PortValueType(DataType.Float32, (-1,))
        ])
        input_port.subscribe(id(self), self._on_signal)
        
        output_port = StaticTypeOutputPort("filtered", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        self.inputs["signal"] = input_port
        self.outputs["filtered"] = output_port
        self._output = output_port
        
        # Filter state
        self._zi = None
    
    def _design_filter(self):
        """Design Butterworth filter coefficients."""
        nyquist = self._sample_rate / 2
        normal_cutoff = self._cutoff / nyquist
        
        # Ensure cutoff is valid
        if normal_cutoff >= 1.0:
            normal_cutoff = 0.99
        
        self._b, self._a = signal.butter(
            self._order, 
            normal_cutoff, 
            btype='low', 
            analog=False
        )
        
        # Reset filter state
        self._zi = signal.lfilter_zi(self._b, self._a)
    
    def _on_signal(self, values: list[np.ndarray]):
        """Apply filter to input signal."""
        input_signal = values[0]
        
        # Apply filter with state
        if self._zi is not None:
            filtered, self._zi = signal.lfilter(
                self._b, self._a, input_signal, zi=self._zi
            )
        else:
            filtered = signal.lfilter(self._b, self._a, input_signal)
        
        self._output.dispatch([filtered.astype(np.float32)])
    
    def set_properties(self, properties: dict):
        rebuild = False
        
        if "cutoff_freq" in properties:
            self._cutoff = float(properties["cutoff_freq"])
            self.properties["cutoff_freq"] = self._cutoff
            rebuild = True
        
        if "sample_rate" in properties:
            self._sample_rate = float(properties["sample_rate"])
            self.properties["sample_rate"] = self._sample_rate
            rebuild = True
        
        if "order" in properties:
            self._order = int(properties["order"])
            self.properties["order"] = self._order
            rebuild = True
        
        if rebuild:
            self._design_filter()
            if self.parent_graph:
                self.parent_graph.notify_node_updated(self)
    
    def finalize(self):
        self.inputs["signal"].unsubscribe(id(self))
```

### Data Filtering

Statistical data filtering example:

```python
# plugins/nodes/data_filters/statistical.py
import numpy as np
from collections import deque
from typing import ClassVar
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class MovingAverageNode(BaseNode):
    """Calculates moving average over a window."""
    
    DESCRIPTION: ClassVar[str] = "Compute moving average of input data"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "window_size": PropertyDescription(
            data_type=PropertyDataType.Int,
            default_value=10,
            min_value=1,
            max_value=1000,
            description="Window size for averaging"
        ),
        "mode": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="simple",
            options=["simple", "exponential", "weighted"],
            description="Averaging mode"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "MovingAverage")
        
        # Parameters
        self._window_size = 10
        self._mode = "simple"
        self._buffer = deque(maxlen=self._window_size)
        
        # Set properties
        self.properties["window_size"] = self._window_size
        self.properties["mode"] = self._mode
        
        # Setup ports
        input_port = StaticTypeInputPort("data", [
            PortValueType(DataType.Float32, (-1,))
        ])
        input_port.subscribe(id(self), self._on_data)
        
        output_port = StaticTypeOutputPort("average", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        self.inputs["data"] = input_port
        self.outputs["average"] = output_port
        self._output = output_port
    
    def _on_data(self, values: list[np.ndarray]):
        """Process new data."""
        new_data = values[0]
        
        # Add to buffer
        self._buffer.append(new_data)
        
        if len(self._buffer) > 0:
            if self._mode == "simple":
                # Simple moving average
                result = np.mean(self._buffer, axis=0)
            
            elif self._mode == "exponential":
                # Exponential moving average
                alpha = 2.0 / (len(self._buffer) + 1)
                result = new_data
                for i, data in enumerate(list(self._buffer)[:-1]):
                    weight = (1 - alpha) ** (len(self._buffer) - i - 1)
                    result = alpha * data * weight + (1 - alpha) * result
            
            elif self._mode == "weighted":
                # Weighted moving average
                weights = np.arange(1, len(self._buffer) + 1)
                weighted_sum = sum(
                    data * weight 
                    for data, weight in zip(self._buffer, weights)
                )
                result = weighted_sum / weights.sum()
            
            else:
                result = new_data
            
            self._output.dispatch([result.astype(np.float32)])
    
    def set_properties(self, properties: dict):
        if "window_size" in properties:
            new_size = int(properties["window_size"])
            if new_size != self._window_size:
                self._window_size = new_size
                self._buffer = deque(maxlen=self._window_size)
                self.properties["window_size"] = self._window_size
        
        if "mode" in properties:
            self._mode = str(properties["mode"])
            self.properties["mode"] = self._mode
    
    def finalize(self):
        self.inputs["data"].unsubscribe(id(self))
```

## Device Integration Examples

### Sensor Data Reader

Mock sensor data reader with realistic patterns:

```python
# plugins/nodes/sensors/temperature_sensor.py
import asyncio
import numpy as np
from typing import ClassVar, Optional
from datetime import datetime
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class TemperatureSensorNode(BaseNode):
    """Simulates temperature sensor readings."""
    
    DESCRIPTION: ClassVar[str] = "Generate temperature sensor data"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "base_temp": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=20.0,
            min_value=-50.0,
            max_value=100.0,
            description="Base temperature (°C)"
        ),
        "noise_level": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=0.5,
            min_value=0.0,
            max_value=5.0,
            description="Noise amplitude"
        ),
        "sample_rate": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=1.0,
            min_value=0.1,
            max_value=100.0,
            description="Samples per second"
        ),
        "enabled": PropertyDescription(
            data_type=PropertyDataType.Bool,
            default_value=True,
            description="Enable sensor"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "TemperatureSensor")
        
        # Sensor parameters
        self._base_temp = 20.0
        self._noise_level = 0.5
        self._sample_rate = 1.0
        self._enabled = True
        
        # Set properties
        self.properties["base_temp"] = self._base_temp
        self.properties["noise_level"] = self._noise_level
        self.properties["sample_rate"] = self._sample_rate
        self.properties["enabled"] = self._enabled
        
        # Output ports
        temp_output = StaticTypeOutputPort("temperature", [
            PortValueType(DataType.Float32, (1,))
        ])
        
        timestamp_output = StaticTypeOutputPort("timestamp", [
            PortValueType(DataType.Float64, (1,))
        ])
        
        self.outputs["temperature"] = temp_output
        self.outputs["timestamp"] = timestamp_output
        
        self._temp_output = temp_output
        self._timestamp_output = timestamp_output
        
        # Async task
        self._task: Optional[asyncio.Task] = None
        self._start_sensor()
    
    def _start_sensor(self):
        """Start async sensor reading."""
        if self._task:
            self._task.cancel()
        
        if self._enabled:
            self._task = asyncio.create_task(self._read_sensor())
    
    async def _read_sensor(self):
        """Async sensor reading loop."""
        while self._enabled:
            try:
                # Simulate temperature reading
                noise = np.random.normal(0, self._noise_level)
                
                # Add daily variation
                hour = datetime.now().hour
                daily_variation = 5 * np.sin(2 * np.pi * hour / 24)
                
                temperature = self._base_temp + daily_variation + noise
                
                # Send data
                self._temp_output.dispatch([
                    np.array([temperature], dtype=np.float32)
                ])
                
                self._timestamp_output.dispatch([
                    np.array([datetime.now().timestamp()], dtype=np.float64)
                ])
                
                # Wait for next sample
                await asyncio.sleep(1.0 / self._sample_rate)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Sensor error: {e}")
                await asyncio.sleep(1.0)
    
    def set_properties(self, properties: dict):
        restart_needed = False
        
        if "base_temp" in properties:
            self._base_temp = float(properties["base_temp"])
            self.properties["base_temp"] = self._base_temp
        
        if "noise_level" in properties:
            self._noise_level = float(properties["noise_level"])
            self.properties["noise_level"] = self._noise_level
        
        if "sample_rate" in properties:
            self._sample_rate = float(properties["sample_rate"])
            self.properties["sample_rate"] = self._sample_rate
            restart_needed = True
        
        if "enabled" in properties:
            self._enabled = bool(properties["enabled"])
            self.properties["enabled"] = self._enabled
            restart_needed = True
        
        if restart_needed:
            self._start_sensor()
    
    def finalize(self):
        if self._task:
            self._task.cancel()
```

### Hardware Monitor

Real hardware monitoring example (Windows):

```python
# plugins/nodes/hardware_monitor/__init__.py
import sys
import platform
from nonoha_core.node_registry import NodeRegistry

def register_nodes(registry: NodeRegistry):
    if platform.system() == "Windows":
        from .windows_monitor import WindowsHardwareMonitor, create_cpu_monitor, create_gpu_monitor
        
        # Create shared monitor instance
        monitor = WindowsHardwareMonitor()
        
        # Register nodes with shared monitor
        registry.register_node("CPUMonitor", create_cpu_monitor(monitor))
        registry.register_node("GPUMonitor", create_gpu_monitor(monitor))
    else:
        # Register dummy nodes for other platforms
        from .dummy_monitor import DummyCPUMonitor, DummyGPUMonitor
        registry.register_node("CPUMonitor", DummyCPUMonitor)
        registry.register_node("GPUMonitor", DummyGPUMonitor)
```

## Advanced Examples

### Machine Learning Integration

Integration with scikit-learn for real-time predictions:

```python
# plugins/nodes/ml_nodes/classifier.py
import numpy as np
import pickle
from typing import ClassVar, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class MLClassifierNode(BaseNode):
    """Real-time ML classification node."""
    
    DESCRIPTION: ClassVar[str] = "Apply trained ML model for classification"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "model_path": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="",
            description="Path to saved model file"
        ),
        "confidence_threshold": PropertyDescription(
            data_type=PropertyDataType.Float,
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            description="Minimum confidence for prediction"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "MLClassifier")
        
        # Model components
        self._model: Optional[RandomForestClassifier] = None
        self._scaler: Optional[StandardScaler] = None
        self._model_path = ""
        self._confidence_threshold = 0.5
        
        # Properties
        self.properties["model_path"] = self._model_path
        self.properties["confidence_threshold"] = self._confidence_threshold
        
        # Input port for features
        features_input = StaticTypeInputPort("features", [
            PortValueType(DataType.Float32, (-1,))  # Variable feature vector
        ])
        features_input.subscribe(id(self), self._on_features)
        
        # Output ports
        class_output = StaticTypeOutputPort("class", [
            PortValueType(DataType.Int32, (1,))
        ])
        
        confidence_output = StaticTypeOutputPort("confidence", [
            PortValueType(DataType.Float32, (1,))
        ])
        
        probabilities_output = StaticTypeOutputPort("probabilities", [
            PortValueType(DataType.Float32, (-1,))
        ])
        
        # Register ports
        self.inputs["features"] = features_input
        self.outputs["class"] = class_output
        self.outputs["confidence"] = confidence_output
        self.outputs["probabilities"] = probabilities_output
        
        self._class_output = class_output
        self._confidence_output = confidence_output
        self._prob_output = probabilities_output
    
    def _load_model(self, path: str):
        """Load trained model from file."""
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                self._model = model_data['model']
                self._scaler = model_data.get('scaler', None)
                print(f"Model loaded from {path}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            self._model = None
            self._scaler = None
    
    def _on_features(self, values: list[np.ndarray]):
        """Process features and make prediction."""
        if not self._model:
            return
        
        features = values[0].reshape(1, -1)  # Ensure 2D
        
        try:
            # Scale features if scaler available
            if self._scaler:
                features = self._scaler.transform(features)
            
            # Make prediction
            prediction = self._model.predict(features)[0]
            probabilities = self._model.predict_proba(features)[0]
            confidence = np.max(probabilities)
            
            # Check confidence threshold
            if confidence >= self._confidence_threshold:
                self._class_output.dispatch([
                    np.array([prediction], dtype=np.int32)
                ])
                self._confidence_output.dispatch([
                    np.array([confidence], dtype=np.float32)
                ])
                self._prob_output.dispatch([
                    probabilities.astype(np.float32)
                ])
            
        except Exception as e:
            print(f"Prediction error: {e}")
    
    def set_properties(self, properties: dict):
        if "model_path" in properties:
            new_path = str(properties["model_path"])
            if new_path != self._model_path:
                self._model_path = new_path
                self.properties["model_path"] = self._model_path
                if self._model_path:
                    self._load_model(self._model_path)
        
        if "confidence_threshold" in properties:
            self._confidence_threshold = float(properties["confidence_threshold"])
            self.properties["confidence_threshold"] = self._confidence_threshold
    
    def finalize(self):
        self.inputs["features"].unsubscribe(id(self))
```

### Real-time Stream Processing

WebSocket stream processor:

```python
# plugins/nodes/stream_processor/websocket_stream.py
import asyncio
import json
import numpy as np
from typing import ClassVar, Optional
import websockets
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class WebSocketStreamNode(BaseNode):
    """Bidirectional WebSocket stream processor."""
    
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "url": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="ws://localhost:8765",
            description="WebSocket URL"
        ),
        "auto_reconnect": PropertyDescription(
            data_type=PropertyDataType.Bool,
            default_value=True,
            description="Automatically reconnect on disconnect"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "WebSocketStream")
        
        # Connection settings
        self._url = "ws://localhost:8765"
        self._auto_reconnect = True
        self._websocket = None
        self._task = None
        
        # Properties
        self.properties["url"] = self._url
        self.properties["auto_reconnect"] = self._auto_reconnect
        
        # Input port for sending data
        send_input = StaticTypeInputPort("send", [
            PortValueType(DataType.String, (-1,))
        ])
        send_input.subscribe(id(self), self._on_send_data)
        
        # Output ports
        receive_output = StaticTypeOutputPort("received", [
            PortValueType(DataType.String, (-1,))
        ])
        
        status_output = StaticTypeOutputPort("status", [
            PortValueType(DataType.String, (1,))
        ])
        
        # Register ports
        self.inputs["send"] = send_input
        self.outputs["received"] = receive_output
        self.outputs["status"] = status_output
        
        self._receive_output = receive_output
        self._status_output = status_output
        
        # Start connection
        self._start_connection()
    
    def _start_connection(self):
        """Start WebSocket connection."""
        if self._task:
            self._task.cancel()
        
        self._task = asyncio.create_task(self._maintain_connection())
    
    async def _maintain_connection(self):
        """Maintain WebSocket connection with reconnection."""
        while True:
            try:
                self._emit_status("connecting")
                
                async with websockets.connect(self._url) as websocket:
                    self._websocket = websocket
                    self._emit_status("connected")
                    
                    # Receive messages
                    async for message in websocket:
                        try:
                            # Parse and emit received data
                            data = json.loads(message)
                            
                            # Convert to numpy array
                            if isinstance(data, list):
                                array_data = np.array(data, dtype=np.str_)
                            else:
                                array_data = np.array([str(data)], dtype=np.str_)
                            
                            self._receive_output.dispatch([array_data])
                            
                        except json.JSONDecodeError:
                            # Emit raw message if not JSON
                            self._receive_output.dispatch([
                                np.array([message], dtype=np.str_)
                            ])
                        except Exception as e:
                            print(f"Message processing error: {e}")
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                self._emit_status(f"error: {e}")
                self._websocket = None
                
                if not self._auto_reconnect:
                    break
                
                # Wait before reconnecting
                await asyncio.sleep(5)
    
    def _on_send_data(self, values: list[np.ndarray]):
        """Send data through WebSocket."""
        if not self._websocket:
            return
        
        data = values[0]
        
        # Convert to JSON and send
        asyncio.create_task(self._send_async(data))
    
    async def _send_async(self, data: np.ndarray):
        """Async send operation."""
        if self._websocket:
            try:
                # Convert numpy array to list for JSON serialization
                message = json.dumps(data.tolist())
                await self._websocket.send(message)
            except Exception as e:
                print(f"Send error: {e}")
    
    def _emit_status(self, status: str):
        """Emit connection status."""
        self._status_output.dispatch([
            np.array([status], dtype=np.str_)
        ])
    
    def set_properties(self, properties: dict):
        restart_needed = False
        
        if "url" in properties:
            new_url = str(properties["url"])
            if new_url != self._url:
                self._url = new_url
                self.properties["url"] = self._url
                restart_needed = True
        
        if "auto_reconnect" in properties:
            self._auto_reconnect = bool(properties["auto_reconnect"])
            self.properties["auto_reconnect"] = self._auto_reconnect
        
        if restart_needed:
            self._start_connection()
    
    def finalize(self):
        if self._task:
            self._task.cancel()
        
        if self._websocket:
            asyncio.create_task(self._websocket.close())
        
        self.inputs["send"].unsubscribe(id(self))
```

### State Machine Node

Complex state machine implementation:

```python
# plugins/nodes/state_machine/fsm_node.py
import numpy as np
from typing import ClassVar, Dict, Optional
from enum import Enum
from nonoha_core.node import BaseNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.port_value_type import PortValueType
from nonoha_core.data_type import DataType
from nonoha_core.property_description import PropertyDescription, PropertyDataType

class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class StateMachineNode(BaseNode):
    """Finite state machine controller."""
    
    DESCRIPTION: ClassVar[str] = "State machine with configurable transitions"
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {
        "initial_state": PropertyDescription(
            data_type=PropertyDataType.String,
            default_value="idle",
            options=["idle", "running", "paused", "error"],
            description="Initial state"
        )
    }
    
    def __init__(self, name: str):
        super().__init__(name, "StateMachine")
        
        # State machine setup
        self._current_state = State.IDLE
        self._state_data = {}
        self._transition_count = 0
        
        # Properties
        self.properties["initial_state"] = self._current_state.value
        
        # Define transitions
        self._transitions = {
            State.IDLE: {
                "start": State.RUNNING,
                "error": State.ERROR
            },
            State.RUNNING: {
                "pause": State.PAUSED,
                "stop": State.IDLE,
                "error": State.ERROR
            },
            State.PAUSED: {
                "resume": State.RUNNING,
                "stop": State.IDLE,
                "error": State.ERROR
            },
            State.ERROR: {
                "reset": State.IDLE
            }
        }
        
        # Input port for commands
        command_input = StaticTypeInputPort("command", [
            PortValueType(DataType.String, (1,))
        ])
        command_input.subscribe(id(self), self._on_command)
        
        # Output ports
        state_output = StaticTypeOutputPort("state", [
            PortValueType(DataType.String, (1,))
        ])
        
        transition_output = StaticTypeOutputPort("transition_count", [
            PortValueType(DataType.Int32, (1,))
        ])
        
        valid_output = StaticTypeOutputPort("is_valid", [
            PortValueType(DataType.Bool, (1,))
        ])
        
        # Register ports
        self.inputs["command"] = command_input
        self.outputs["state"] = state_output
        self.outputs["transition_count"] = transition_output
        self.outputs["is_valid"] = valid_output
        
        self._state_output = state_output
        self._transition_output = transition_output
        self._valid_output = valid_output
        
        # Emit initial state
        self._emit_state()
    
    def _on_command(self, values: list[np.ndarray]):
        """Process state machine command."""
        command = str(values[0][0])
        
        # Check if transition is valid
        valid_transitions = self._transitions.get(self._current_state, {})
        
        if command in valid_transitions:
            # Valid transition
            new_state = valid_transitions[command]
            self._transition_to(new_state)
            self._valid_output.dispatch([np.array([True], dtype=np.bool_)])
        else:
            # Invalid transition
            print(f"Invalid transition: {command} from {self._current_state.value}")
            self._valid_output.dispatch([np.array([False], dtype=np.bool_)])
    
    def _transition_to(self, new_state: State):
        """Execute state transition."""
        old_state = self._current_state
        self._current_state = new_state
        self._transition_count += 1
        
        # State entry actions
        if new_state == State.RUNNING:
            self._on_enter_running()
        elif new_state == State.ERROR:
            self._on_enter_error()
        
        # State exit actions
        if old_state == State.RUNNING:
            self._on_exit_running()
        
        # Emit new state
        self._emit_state()
    
    def _emit_state(self):
        """Emit current state information."""
        self._state_output.dispatch([
            np.array([self._current_state.value], dtype=np.str_)
        ])
        
        self._transition_output.dispatch([
            np.array([self._transition_count], dtype=np.int32)
        ])
    
    def _on_enter_running(self):
        """Actions when entering RUNNING state."""
        self._state_data["start_time"] = np.datetime64('now')
    
    def _on_exit_running(self):
        """Actions when exiting RUNNING state."""
        if "start_time" in self._state_data:
            duration = np.datetime64('now') - self._state_data["start_time"]
            print(f"Running duration: {duration}")
    
    def _on_enter_error(self):
        """Actions when entering ERROR state."""
        print("Error state entered - intervention required")
    
    def set_properties(self, properties: dict):
        if "initial_state" in properties:
            state_str = str(properties["initial_state"])
            try:
                self._current_state = State(state_str)
                self.properties["initial_state"] = state_str
                self._transition_count = 0
                self._emit_state()
            except ValueError:
                print(f"Invalid state: {state_str}")
    
    def finalize(self):
        self.inputs["command"].unsubscribe(id(self))
```

## Plugin Testing Template

Template for testing your plugins:

```python
# test_plugin.py
import sys
import numpy as np
from pathlib import Path

# Add plugin path
plugin_path = Path(__file__).parent
sys.path.insert(0, str(plugin_path))

from nonoha_core.node_registry import NodeRegistry
from your_plugin import register_nodes

def test_plugin():
    """Test plugin registration and basic functionality."""
    
    # Create registry
    registry = NodeRegistry()
    
    # Register plugin nodes
    register_nodes(registry)
    
    # Create node instance
    node = registry.create_node("YourNodeType", "test_instance")
    
    # Test properties
    node.set_properties({"property_name": "value"})
    assert node.properties["property_name"] == "value"
    
    # Test data flow
    test_data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    
    # Capture output
    output_data = None
    def capture(values):
        nonlocal output_data
        output_data = values[0]
    
    # Subscribe to output
    if "output" in node.outputs:
        node.outputs["output"].subscribe("test", capture)
    
    # Send test input
    if hasattr(node, "_on_input"):
        node._on_input([test_data])
    
    # Verify output
    print(f"Output: {output_data}")
    
    # Cleanup
    node.finalize()
    
    print("Plugin test passed!")

if __name__ == "__main__":
    test_plugin()
```

## Best Practices Summary

1. **Always inherit from BaseNode** for consistency
2. **Use NumPy arrays** for all data operations
3. **Handle errors gracefully** without crashing
4. **Clean up in finalize()** method
5. **Document properties** with descriptions
6. **Validate inputs** before processing
7. **Use async/await** for I/O operations
8. **Cache expensive computations** when appropriate
9. **Provide meaningful error messages**
10. **Test thoroughly** before deployment

These examples demonstrate various plugin patterns from simple data processing to complex device integration and state management. Use them as templates for your own plugin development.