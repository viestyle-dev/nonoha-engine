from typing import Optional
import numpy as np
import logging
import asyncio
import websockets
from enum import Enum

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    replace_node_input_port,
)
from nonoha_core.port import (
    StaticTypeOutputPort,
    StaticTypeInputPort,
    port_values_to_bytes,
    PortValue,
)
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)

# Moved to nonoha-core in 0.11.0-alpha.5 (GraphProxy resolves its target via
# parent_graph.parent_flow). Re-exported here for one release as a shim.
from nonoha_core.nodes.graph_nodes import (  # noqa: F401
    GraphLoadedNode,
    GraphPropertiesChangedNode,
    GraphProxyNode,
)

from ..node import EndpointEventType

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class PortValuesSendNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Send port values to a remote graph via WebSocket",
            category="Graph",
            inputs={"values": ""},
            outputs={"status": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "PortValuesSend")

        # Connection settings
        # ex) ws://localhost:8080/node-flow/graphs/default/endpoint/ws
        self._url = ""
        self._target_port = ""
        self._auto_reconnect = True
        self._reconnect_interval = 5.0

        # WebSocket connection
        self._websocket: Optional[websockets.ClientConnection] = None
        self._is_connected = False
        self._connection_task: Optional[asyncio.Task] = None
        self._connection_lock = asyncio.Lock()
        self._current_target_port = ""  # Store for send operations
        self._reconnect_event = asyncio.Event()  # Event for interruptible sleep

        # Initialize properties
        self.properties["url"] = self._url
        self.properties["target_port"] = self._target_port
        self.properties["auto_reconnect"] = self._auto_reconnect
        self.properties["reconnect_interval"] = self._reconnect_interval

        # Default input port with Float32 type
        value_type_list = [PortValueType(DataType.Float32)]
        input_values = StaticTypeInputPort("values", value_type_list)
        input_values.subscribe(id(self), self._on_input_values)

        self._input_values = input_values
        self._value_type_list = value_type_list
        self.inputs[input_values.name] = input_values

        # Status output port
        output_status = StaticTypeOutputPort("status", [PortValueType(DataType.Int32)])
        self.outputs["status"] = output_status
        self._output_status = output_status

        # Add value_types property
        self.properties["value_types"] = ",".join(
            [value_type.name for value_type in value_type_list]
        )

        # Initialize status
        self._update_status(ConnectionStatus.DISCONNECTED)

    async def _ensure_disconnected(self):
        """Ensure any existing connection is closed."""
        async with self._connection_lock:
            # Cancel existing connection task
            if self._connection_task and not self._connection_task.done():
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass
                self._connection_task = None

            # Close websocket if exists
            if self._websocket:
                try:
                    await self._websocket.close()
                except Exception:
                    pass
                self._websocket = None

            self._is_connected = False

    def _request_connect(self):
        """Request new connection."""
        if not self._url or not self._target_port:
            logger.info(f"{self.name}: Cannot connect with empty URL or target_port")
            asyncio.create_task(self._ensure_disconnected())
            self._update_status(ConnectionStatus.DISCONNECTED)
            return

        async def start_connection():
            await self._ensure_disconnected()

            # Capture current parameters
            url = self._url
            target_port = self._target_port
            auto_reconnect = self._auto_reconnect

            self._current_target_port = target_port

            self._connection_task = asyncio.create_task(
                self._run_connection(url, auto_reconnect)
            )

        asyncio.create_task(start_connection())

    async def _run_connection(
        self,
        url: str,
        auto_reconnect: bool,
    ):
        """Run connection with auto-reconnect."""
        try:
            while True:
                try:
                    # Connect
                    self._update_status(ConnectionStatus.CONNECTING)
                    self._websocket = await websockets.connect(url)
                    self._is_connected = True
                    self._update_status(ConnectionStatus.CONNECTED)
                    logger.info(f"{self.name}: Connected to {url}")

                    # Keep connection alive and detect disconnection
                    while self._is_connected:
                        try:
                            # WebSocketから何か受信を待つ（接続チェック兼用）
                            await asyncio.wait_for(self._websocket.recv(), timeout=1.0)
                        except asyncio.TimeoutError:
                            # タイムアウトは正常（何も受信しない）
                            logger.info(f"{self.name}: Timeout, sending ping")
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logger.info(f"{self.name}: Connection closed")
                            break

                    logger.info(f"{self.name}: Connection loop exited")

                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"{self.name}: Connection closed")
                except Exception as e:
                    logger.error(f"{self.name}: Connection error: {e}")

                # Clean up
                self._is_connected = False
                if self._websocket:
                    try:
                        await self._websocket.close()
                    except Exception:
                        pass
                    self._websocket = None
                self._update_status(ConnectionStatus.DISCONNECTED)

                # Check if should reconnect
                if not auto_reconnect:
                    break

                # Wait before reconnecting with interruptable sleep
                self._reconnect_event.clear()
                try:
                    await asyncio.wait_for(
                        self._reconnect_event.wait(), timeout=self._reconnect_interval
                    )
                    # Event was set, meaning reconnect_interval was changed
                    logger.info(
                        f"{self.name}: Reconnect interval changed, reconnecting immediately"
                    )
                except asyncio.TimeoutError:
                    # Normal timeout, proceed with reconnection
                    pass

                logger.info(f"{self.name}: Reconnecting...")

        except asyncio.CancelledError:
            # Clean up on cancellation
            self._is_connected = False
            if self._websocket:
                try:
                    await self._websocket.close()
                except Exception:
                    pass
                self._websocket = None
            self._update_status(ConnectionStatus.DISCONNECTED)
            raise

    def _update_status(self, status: ConnectionStatus):
        self._output_status.dispatch([np.array([status.value], dtype=np.int32)])
        if self.parent_graph:
            self.parent_graph.flush_outputs()

    def _on_input_values(self, values: list[PortValue]):
        """Handle input values and send to remote graph."""
        if not self._is_connected or not self._websocket:
            return

        # Use current target port from connection params
        target_port = self._current_target_port
        if not target_port:
            logger.warning(f"{self.name}: No target port set")
            return

        # Create byte array with protocol format
        bytes_to_send = bytearray()
        bytes_to_send += EndpointEventType.EVENT_INPUT.value.to_bytes(1, "big")
        bytes_to_send += len(target_port).to_bytes(1, "big")
        bytes_to_send += target_port.encode()

        try:
            # Serialize port values
            port_values_to_bytes(
                values, self._input_values.value_type_list, bytes_to_send
            )

            # Send asynchronously
            async def send():
                try:
                    if self._websocket and self._is_connected:
                        await self._websocket.send(bytes_to_send)
                        logger.debug(f"{self.name}: Sent {len(bytes_to_send)} bytes")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to send data: {e}")

            asyncio.create_task(send())
        except Exception as e:
            logger.error(f"{self.name}: Failed to serialize values: {e}")

    def set_properties(self, properties: dict[str, PropertyDataType]):
        """Update node properties."""
        # Prepare all new values first (validation phase)
        new_url = self._url
        new_target_port = self._target_port
        new_auto_reconnect = self._auto_reconnect
        new_reconnect_interval = self._reconnect_interval
        reconnect_needed = False
        trigger_reconnect_event = False

        if "url" in properties:
            temp_url = str(properties["url"])
            if temp_url != self._url:
                new_url = temp_url
                reconnect_needed = True

        if "target_port" in properties:
            new_target_port = str(properties["target_port"])

        if "auto_reconnect" in properties:
            new_auto_reconnect = bool(properties["auto_reconnect"])

        if "reconnect_interval" in properties:
            temp_interval = float(properties["reconnect_interval"])
            if temp_interval != self._reconnect_interval:
                # Check if we should trigger immediate reconnect
                if (
                    self._reconnect_interval > temp_interval
                    and self._connection_task
                    and not self._is_connected
                ):
                    trigger_reconnect_event = True
                new_reconnect_interval = temp_interval

        # Configure input port based on value types if provided
        value_type_list = self._value_type_list
        if "value_types" in properties:
            value_types_str = properties["value_types"]
            if not isinstance(value_types_str, str):
                raise ValueError("value_types must be a comma-separated string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_types_str.split(",")
            ]

        # Prepare new input port if value types changed
        new_input_values = self._input_values
        if value_type_list != self._input_values.value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)

        # Update input port if changed
        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values
            self._value_type_list = value_type_list

        self.properties["value_types"] = ",".join(
            [value_type.name for value_type in value_type_list]
        )

        # All validation passed, now apply the changes atomically
        self._url = new_url
        self.properties["url"] = self._url

        self._target_port = new_target_port
        self.properties["target_port"] = self._target_port

        self._auto_reconnect = new_auto_reconnect
        self.properties["auto_reconnect"] = self._auto_reconnect

        self._reconnect_interval = new_reconnect_interval
        self.properties["reconnect_interval"] = self._reconnect_interval

        # Trigger reconnect event if needed (after all values are updated)
        if trigger_reconnect_event:
            self._reconnect_event.set()

        # Handle reconnection if needed
        if reconnect_needed:
            self._request_connect()
        elif "target_port" in properties:
            # Only target_port changed, update without reconnecting
            self._current_target_port = self._target_port

        if self.parent_graph:
            self.parent_graph.notify_node_updated(self)

    def finalize(self):
        """Clean up when node is removed."""
        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
            self._connection_task = None
