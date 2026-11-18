import asyncio
from enum import Enum
from functools import reduce
import pathlib
import json
import struct
import threading
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
import numpy as np
import logging

from nonoha_engine.file_binary_converts import file_binary_converts
from .data_storage import DataStorage

from nonoha_core.node import BaseNode, BaseNodeGraph, Edge, NodeGraphPersist
from nonoha_core.port import (
    DataType,
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
    port_values_to_bytes,
)
from nonoha_core.data_type import PortValueType, PropertyDataType
from nonoha_core.error_log import ErrorLog

from .models import file_model

logger = logging.getLogger(__name__)


class EndpointEventType(Enum):
    EVENT_INPUT = 0x00
    EVENT_OUTPUT = 0x01


# The endpoint protocol's hot path reads these, built once (no Enum call,
# dtype string or format string per message)
_EVENT_INPUT = EndpointEventType.EVENT_INPUT.value
_EVENT_OUTPUT_HEADER = bytes((EndpointEventType.EVENT_OUTPUT.value,))
# Data type byte -> (big-endian dtype, DataType) for the numeric types
_DECODE: dict[int, tuple[np.dtype, DataType]] = {
    DataType.Int8.value: (np.dtype(">i1"), DataType.Int8),
    DataType.Uint8.value: (np.dtype(">u1"), DataType.Uint8),
    DataType.Int16.value: (np.dtype(">i2"), DataType.Int16),
    DataType.Uint16.value: (np.dtype(">u2"), DataType.Uint16),
    DataType.Int32.value: (np.dtype(">i4"), DataType.Int32),
    DataType.Uint32.value: (np.dtype(">u4"), DataType.Uint32),
    DataType.Int64.value: (np.dtype(">i8"), DataType.Int64),
    DataType.Uint64.value: (np.dtype(">u8"), DataType.Uint64),
    DataType.Float32.value: (np.dtype(">f4"), DataType.Float32),
    DataType.Float64.value: (np.dtype(">f8"), DataType.Float64),
}
_BOOL = DataType.Bool.value
_STRING = DataType.String.value
_VALID_TYPES = frozenset(t.value for t in DataType)
_U8 = np.dtype(">u1")
_U32 = struct.Struct(">I")
_SHAPES = tuple(struct.Struct(f">{n}H") for n in range(8))


class GraphFileExtension(Enum):
    JSON = 0
    VJB = 1


class FileNodeGraphPersist(NodeGraphPersist):
    def __init__(
        self,
        graph_file_model: file_model.NodeGraphModel,
        graph_dir_path: pathlib.Path,
        graph_file_extension: GraphFileExtension,
    ):
        self._graph_file_model = graph_file_model
        self._graph_dir_path = graph_dir_path
        self._graph_file_extension = graph_file_extension
        self.readonly = False
        self._save_handle: asyncio.TimerHandle | None = None
        self._save_lock = threading.Lock()
        self._loop = asyncio.get_running_loop()
        self._editor_save_locks: dict[str, asyncio.Lock] = {}

    @property
    def data_dir_path(self):
        return self._graph_dir_path / "data"

    def update_properties(self, node: BaseNode):
        if self.readonly:
            return
        self._graph_file_model.nodes[node.name].properties = node.properties
        self._schedule_save()

    def update_graph_properties(self, properties: dict[str, PropertyDataType]):
        if self.readonly:
            return
        self._graph_file_model.properties = properties
        self._schedule_save()

    @staticmethod
    def _build_node_model(node: BaseNode) -> file_model.NodeModel:
        # Only save non-@property ports that have at least one dispatch_flag=True
        inputs = {}
        for port in node.inputs.values():
            if port.name.startswith("@"):
                continue
            if any(port.dispatch_flags):
                inputs[port.name] = file_model.NodeInputPortModel(
                    dispatch_flags=list(port.dispatch_flags)
                )

        # Only include property_groups if non-empty
        groups_list: list[file_model.PropertyGroupModel] = []
        seen: set[int] = set()
        for pg in node._property_group_by_key.values():
            pg_id = id(pg)
            if pg_id not in seen:
                seen.add(pg_id)
                groups_list.append(
                    file_model.PropertyGroupModel(
                        keys=pg.keys, dispatch_flags=pg.dispatch_flags
                    )
                )

        kwargs: dict = dict(type=node.type, properties=node.properties)
        if inputs:
            kwargs["inputs"] = inputs
        if groups_list:
            kwargs["property_groups"] = groups_list
        return file_model.NodeModel(**kwargs)

    def update_node(self, node: BaseNode):
        if self.readonly:
            return
        self._graph_file_model.nodes[node.name] = self._build_node_model(node)
        self._schedule_save()

    def update_edges(self, edges: dict[tuple[str, str], Edge]):
        if self.readonly:
            return
        self._graph_file_model.edges = [
            file_model.EdgeModel(source=source, target=target)
            for (source, target) in edges.keys()
        ]
        self._schedule_save()

    def add_node(self, node: BaseNode):
        if self.readonly:
            return
        self._graph_file_model.nodes[node.name] = self._build_node_model(node)
        self._schedule_save()

    def remove_node(self, node_name: str):
        if self.readonly:
            return
        self._graph_file_model.nodes.pop(node_name)
        self._schedule_save()

    def add_input_port(self, port: StaticTypeInputPort):
        if self.readonly:
            return
        port_model = file_model.PortModel(
            types=[pt.name for pt in port.value_type_list]
        )
        self._graph_file_model.inputs[port.name] = port_model
        self._schedule_save()

    def remove_input_port(self, port_name: str):
        if self.readonly:
            return
        self._graph_file_model.inputs.pop(port_name)
        self._schedule_save()

    def add_output_port(self, port: StaticTypeOutputPort):
        if self.readonly:
            return
        port_model = file_model.PortModel(
            types=[pt.name for pt in port.value_type_list]
        )
        self._graph_file_model.outputs[port.name] = port_model
        self._schedule_save()

    def remove_output_port(self, port_name: str):
        if self.readonly:
            return
        self._graph_file_model.outputs.pop(port_name)
        self._schedule_save()

    _SAVE_DEBOUNCE_SECONDS = 0.1

    def _schedule_save(self):
        """Reschedule the debounce timer. Called on the asyncio thread."""
        if self._save_handle is not None:
            self._save_handle.cancel()
        self._save_handle = self._loop.call_later(
            self._SAVE_DEBOUNCE_SECONDS, self._snapshot_and_save
        )

    def _snapshot_and_save(self):
        """Timer callback. Takes a snapshot on the asyncio thread, then dispatches file I/O to the thread pool."""
        self._save_handle = None
        snapshot = self._take_graph_snapshot()
        asyncio.create_task(asyncio.to_thread(self._write_graph, snapshot))

    def _take_graph_snapshot(self) -> str:
        """Serialize the graph model to a JSON string. Must be called on the asyncio thread."""
        match self._graph_file_extension:
            case GraphFileExtension.VJB:
                return self._graph_file_model.model_dump_json(exclude_defaults=True)
            case GraphFileExtension.JSON:
                return self._graph_file_model.model_dump_json(
                    indent=2, exclude_defaults=True
                )

    def _write_graph(self, snapshot: str):
        """Write the snapshot string to disk. Runs on the thread pool."""
        with self._save_lock:
            match self._graph_file_extension:
                case GraphFileExtension.VJB:
                    path = self._graph_dir_path / "graph.vjb"
                    with open(path, "wb") as f:
                        f.write(file_binary_converts.encode(snapshot))
                case GraphFileExtension.JSON:
                    path = self._graph_dir_path / "graph.json"
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(snapshot)

    def flush(self):
        """Flush any pending graph save immediately. Called during shutdown."""
        if self._save_handle is not None:
            self._save_handle.cancel()
            self._save_handle = None
            self._write_graph(self._take_graph_snapshot())

    async def load_editor_model(
        self, editor_name: str, model_name: str
    ) -> file_model.EditorModel | None:
        return await asyncio.to_thread(self._load_editor_model, editor_name, model_name)

    def _load_editor_model(
        self, editor_name: str, model_name: str
    ) -> file_model.EditorModel | None:
        editor_model_file_path = (
            self._graph_dir_path / f"editors/{editor_name}/models/{model_name}.json"
        )
        if not editor_model_file_path.exists():
            return {}
        try:
            with open(editor_model_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load editor model: {editor_model_file_path}")
            return None

    async def save_editor_model(
        self, editor_name: str, model_name: str, editor_model: file_model.EditorModel
    ):
        if self.readonly:
            return
        model_key = f"{editor_name}/{model_name}"
        lock = self._editor_save_locks.setdefault(model_key, asyncio.Lock())
        async with lock:
            await asyncio.to_thread(
                self._save_editor_model, editor_name, model_name, editor_model
            )

    def _save_editor_model(
        self, editor_name: str, model_name: str, editor_model: file_model.EditorModel
    ):
        editor_model_file_path = (
            self._graph_dir_path / f"editors/{editor_name}/models/{model_name}.json"
        )
        editor_model_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(editor_model_file_path, "w", encoding="utf-8") as f:
            json.dump(editor_model, f, indent=2)


class NodeGraph(BaseNodeGraph[FileNodeGraphPersist]):
    def __init__(self, name: str, properties: dict[str, PropertyDataType]):
        super().__init__(name, properties)

        self._active_web_sockets: tuple[WebSocket, ...] = ()
        self._broadcast_task: asyncio.Task | None = None

        self._outputs_buffer: list[bytes] = []
        # True when outputs were dispatched since the last flush (the flush
        # callbacks run even when no WebSocket needs the bytes).
        self._outputs_dispatched = False
        # Apps can send at audio rate: problems are logged rate-limited
        self._endpoint_warnings = ErrorLog(logger)
        self._endpoint_errors = ErrorLog(logger)
        self._output_errors = ErrorLog(logger)
        self._editor_models: dict[str, file_model.EditorModel] = {}
        self._data_storage: DataStorage | None = None

        self.properties = properties

    def finalize(self):
        if self._persist is not None:
            self._persist.flush()
        super().finalize()

    def _on_output(self, port: StaticTypeOutputPort, values: list[Any]):
        self._outputs_dispatched = True
        if not self._active_web_sockets:
            return  # nobody to send to: skip the serialization

        name = port.name.encode()
        bytes_to_send = bytearray(_EVENT_OUTPUT_HEADER)
        bytes_to_send.append(len(name))  # in bytes, as the receiver reads it
        bytes_to_send += name

        try:
            port_values_to_bytes(values, port.value_type_list, bytes_to_send)
        except Exception as e:
            self._output_errors.warning(f"Failed to convert values of {port.name!r} to bytes: {e}")
            return

        # traceback.print_stack()

        self._outputs_buffer.append(bytes_to_send)

    def flush_outputs(self):
        if not self._outputs_dispatched:
            return
        self._outputs_dispatched = False

        buffered = self._outputs_buffer
        if buffered:
            self._outputs_buffer = []
            prev = self._broadcast_task
            self._broadcast_task = asyncio.create_task(
                self._broadcast_outputs(buffered, prev)
            )

        for callback in self._flush_outputs_callbacks.values():
            callback()

    async def _broadcast_outputs(
        self, messages: list[bytes], prev: asyncio.Task | None
    ):
        if prev is not None:
            try:
                await prev
            except BaseException as e:
                logger.warning(
                    f"Previous broadcast task failed: {type(e).__name__}: {e}"
                )
        for bytes_to_send in messages:
            for websocket in self._active_web_sockets:
                try:
                    await websocket.send(
                        {"type": "websocket.send", "bytes": bytes_to_send}
                    )
                except Exception:
                    # A closing socket (WebSocketDisconnect, uvicorn's
                    # ClientDisconnected, RuntimeError after close) must not
                    # stop delivery to the other sockets.
                    pass

    def handle_endpoint_event(self, received_bytes: bytes) -> None:
        """Dispatch one input event (an app's values for a graph input).

        Never raises: a malformed message is logged (rate-limited), and so is
        a node that fails on the values; the connection stays open.
        """
        try:
            port_name_length = received_bytes[1]
            offset = 2
            port_name = received_bytes[offset : offset + port_name_length].decode()
            offset += port_name_length

            value_count = received_bytes[offset]
            offset += 1

            input_port = self.inputs.get(port_name)
            if input_port is None:
                self._endpoint_warnings.warning(f"Port not found: {port_name}")
                return

            expected = input_port.value_type_list
            # Compared value by value with the port's types (what
            # PortValueType.__eq__ compares), without building PortValueTypes;
            # the received types are only collected for a mismatch message
            received: list[tuple[DataType, tuple[int, ...]]] | None = (
                None if len(expected) == value_count else []
            )
            values: list[PortValue] = []
            for value_index in range(value_count):
                type_byte = received_bytes[offset]
                ndim = received_bytes[offset + 1]
                offset += 2
                shape_struct = _SHAPES[ndim] if ndim < 8 else struct.Struct(f">{ndim}H")
                shape = shape_struct.unpack_from(received_bytes, offset)
                offset += ndim * 2
                data_size = _U32.unpack_from(received_bytes, offset)[0]
                offset += 4

                decode = _DECODE.get(type_byte)
                if decode is not None:
                    dtype, data_type = decode
                    array = np.frombuffer(
                        received_bytes, dtype=dtype, count=data_size // dtype.itemsize, offset=offset
                    ).reshape(-1, *shape)
                elif type_byte == _BOOL:
                    data_type = DataType.Bool
                    array = (
                        np.frombuffer(received_bytes, dtype=_U8, count=data_size, offset=offset)
                        .astype(bool)
                        .reshape(-1, *shape)
                    )
                elif type_byte == _STRING:
                    data_type = DataType.String
                    # Format: each string followed by NULL terminator "A\0B\0"
                    byte_data = received_bytes[offset : offset + data_size]
                    if byte_data:
                        # Split by NULL, remove trailing empty from final terminator
                        strings = [s.decode("utf-8") for s in byte_data.split(b"\x00")[:-1]]
                    else:
                        strings = []
                    array = np.array(strings, dtype=np.dtypes.StringDType()).reshape(-1, *shape)  # type: ignore
                elif type_byte in _VALID_TYPES:
                    self._endpoint_warnings.warning(
                        f"Unsupported data type: data_type={DataType(type_byte)}, {value_index=}, {port_name=}"
                    )
                    return
                else:
                    self._endpoint_warnings.warning(
                        f"Failed to parse input event: {type_byte} is not a valid DataType"
                    )
                    return

                if received is None:
                    port_type = expected[value_index]
                    if port_type.data_type != data_type or port_type.shape != shape:
                        received = [(t.data_type, t.shape) for t in expected[:value_index]]
                if received is not None:
                    received.append((data_type, shape))
                values.append(array)
                offset += data_size

        except Exception as e:
            self._endpoint_warnings.warning(f"Failed to parse input event: {e}")
            return

        if received is not None:
            got = ",".join(PortValueType(t, s).name for t, s in received)
            want = ",".join(v.name for v in expected)
            self._endpoint_warnings.warning(f"Data type mismatch: [{want}] != [{got}]")
            return

        try:
            input_port.dispatch(values)
        except Exception:
            # A node's failure must not close the app's connection
            self._endpoint_errors.exception(f"{self.name}: a node failed on input {port_name!r} from an app")
        # Flush what was dispatched, also before a failure
        try:
            self.flush_outputs()
        except Exception:
            self._endpoint_errors.exception(f"{self.name}: flushing the graph's outputs failed")

    async def handle_websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self._active_web_sockets = (*self._active_web_sockets, websocket)

        try:
            while True:
                try:
                    message = await websocket.receive()
                except (WebSocketDisconnect, RuntimeError):
                    break  # the connection is gone
                if message["type"] == "websocket.disconnect":
                    break
                received_bytes = message.get("bytes")
                if not received_bytes:
                    continue  # text frames are not part of this protocol
                if received_bytes[0] == _EVENT_INPUT:
                    self.handle_endpoint_event(received_bytes)
                else:
                    self._endpoint_warnings.warning(f"Unknown endpoint event type {received_bytes[0]!r}")
        finally:
            ws_tuple = self._active_web_sockets
            if websocket in ws_tuple:
                i = ws_tuple.index(websocket)
                self._active_web_sockets = ws_tuple[:i] + ws_tuple[i + 1 :]

    def notify_node_updated(self, node: BaseNode):
        if self._persist is None:
            return

        self._persist.update_node(node)

    def notify_properties_changed(self, node: BaseNode):
        if self._persist is None:
            return

        self._persist.update_properties(node)

    def set_data_storage(self, data_storage: DataStorage):
        self._data_storage = data_storage

    @property
    def data_storage(self) -> DataStorage | None:
        return self._data_storage

    @property
    def editor_models(self):
        return self._editor_models

    async def get_editor_model_value(
        self, editor_name: str, model_name: str, query: str
    ):
        model_id = f"{editor_name}.{model_name}"
        editor_model = self._editor_models.get(model_id)

        if editor_model is None and self._persist is not None:
            editor_model = await self._persist.load_editor_model(
                editor_name, model_name
            )

        if editor_model is None:
            return None

        self._editor_models[model_id] = editor_model

        query_key = query.split(".")
        try:
            return reduce(lambda d, k: d[k], query_key, editor_model)
        except Exception:
            return None

    async def put_editor_model_value(
        self, editor_name: str, model_name: str, query: str, value: Any
    ):
        model_id = f"{editor_name}.{model_name}"
        editor_model = self._editor_models.get(model_id)

        if editor_model is None and self._persist is not None:
            editor_model = await self._persist.load_editor_model(
                editor_name, model_name
            )

        if editor_model is None:
            editor_model = {}

        self._editor_models[model_id] = editor_model

        query_key = query.split(".")
        try:
            if len(query_key) == 1:
                editor_model[query_key[0]] = value
            else:
                reduce(lambda d, k: d.setdefault(k, {}), query_key[:-1], editor_model)[
                    query_key[-1]
                ] = value
        except Exception:
            return

        if self._persist is not None:
            await self._persist.save_editor_model(editor_name, model_name, editor_model)

    async def patch_editor_model_value(
        self, editor_name: str, model_name: str, query: str, value: Any
    ):
        model_id = f"{editor_name}.{model_name}"
        editor_model = self._editor_models.get(model_id)

        if editor_model is None and self._persist is not None:
            editor_model = await self._persist.load_editor_model(
                editor_name, model_name
            )

        if editor_model is None:
            editor_model = {}

        self._editor_models[model_id] = editor_model

        query_key = query.split(".")

        def deep_update(dict_base, other):
            stack = [(dict_base, other)]
            while stack:
                current_base, current_other = stack.pop()
                for k, v in current_other.items():
                    if (
                        isinstance(v, dict)
                        and k in current_base
                        and isinstance(current_base[k], dict)
                    ):
                        stack.append((current_base[k], v))
                    else:
                        current_base[k] = v

        try:
            target_dict = reduce(
                lambda d, k: d.setdefault(k, {}), query_key[:-1], editor_model
            )
            if isinstance(target_dict.get(query_key[-1]), dict) and isinstance(
                value, dict
            ):
                deep_update(target_dict[query_key[-1]], value)
            else:
                target_dict[query_key[-1]] = value
        except Exception:
            return
        if self._persist is not None:
            await self._persist.save_editor_model(editor_name, model_name, editor_model)

    async def delete_editor_model_value(
        self, editor_name: str, model_name: str, query: str
    ):
        model_id = f"{editor_name}.{model_name}"
        editor_model = self._editor_models.get(model_id)

        if editor_model is None and self._persist is not None:
            editor_model = await self._persist.load_editor_model(
                editor_name, model_name
            )

        if editor_model is None:
            editor_model = {}

        self._editor_models[model_id] = editor_model

        query_key = query.split(".")

        reduce(lambda d, k: d.setdefault(k, {}), query_key[:-1], editor_model).pop(
            query_key[-1], None
        )

        if self._persist is not None:
            await self._persist.save_editor_model(editor_name, model_name, editor_model)
