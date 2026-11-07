import asyncio
from enum import Enum
from functools import reduce
import pathlib
import json
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

from .models import file_model

logger = logging.getLogger(__name__)


class EndpointEventType(Enum):
    EVENT_INPUT = 0x00
    EVENT_OUTPUT = 0x01


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
                    with open(path, "w") as f:
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
            with open(editor_model_file_path, "r") as f:
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
        with open(editor_model_file_path, "w") as f:
            json.dump(editor_model, f, indent=2)


class NodeGraph(BaseNodeGraph[FileNodeGraphPersist]):
    def __init__(self, name: str, properties: dict[str, PropertyDataType]):
        super().__init__(name, properties)

        self._active_web_sockets: tuple[WebSocket, ...] = ()
        self._broadcast_task: asyncio.Task | None = None

        self._outputs_buffer: list[bytes] = []
        self._editor_models: dict[str, file_model.EditorModel] = {}
        self._data_storage: DataStorage | None = None

        self.properties = properties

    def finalize(self):
        if self._persist is not None:
            self._persist.flush()
        super().finalize()

    def _on_output(self, port: StaticTypeOutputPort, values: list[Any]):
        bytes_to_send = bytearray()
        bytes_to_send += EndpointEventType.EVENT_OUTPUT.value.to_bytes(1, "big")
        bytes_to_send += len(port.name).to_bytes(1, "big")
        bytes_to_send += port.name.encode()

        try:
            port_values_to_bytes(values, port.value_type_list, bytes_to_send)
        except Exception as e:
            logger.error(f"Failed to convert values to bytes: {e}")
            return

        # traceback.print_stack()

        self._outputs_buffer.append(bytes_to_send)

    def flush_outputs(self):
        if len(self._outputs_buffer) == 0:
            return

        buffered = self._outputs_buffer
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
                except WebSocketDisconnect:
                    pass

    def handle_endpoint_event(
        self, event_type: EndpointEventType, received_bytes: bytes
    ):
        if event_type == EndpointEventType.EVENT_INPUT:
            try:
                # logger.info(f"< {len(received_bytes)}")
                port_name_length = received_bytes[1]
                offset = 2

                port_name = received_bytes[offset : offset + port_name_length].decode()
                offset += port_name_length

                value_count = received_bytes[offset]
                offset += 1

                input_port = self.inputs.get(port_name)
                if input_port is None:
                    logger.warning(f"Port not found: {port_name}")
                    return

                values: list[PortValue] = []
                value_type_list: list[PortValueType] = []

                for value_index in range(value_count):
                    data_type = DataType(received_bytes[offset])
                    offset += 1

                    ndim = received_bytes[offset]
                    offset += 1

                    # 効率的に形状データを一度に読み取る
                    shape = np.frombuffer(
                        received_bytes, dtype=">u2", count=ndim, offset=offset
                    )
                    offset += ndim * 2

                    data_size = int.from_bytes(
                        received_bytes[offset : offset + 4], "big"
                    )
                    offset += 4

                    match data_type:
                        case DataType.Float32:
                            f32array = np.frombuffer(
                                received_bytes,
                                dtype=">f4",
                                count=data_size // 4,
                                offset=offset,
                            )
                            f32array = f32array.reshape(-1, *shape)
                            values.append(f32array)
                        case DataType.Float64:
                            f64array = np.frombuffer(
                                received_bytes,
                                dtype=">f8",
                                count=data_size // 8,
                                offset=offset,
                            )
                            f64array = f64array.reshape(-1, *shape)
                            values.append(f64array)
                        case DataType.Uint8:
                            u8array = np.frombuffer(
                                received_bytes,
                                dtype=">u1",
                                count=data_size,
                                offset=offset,
                            )
                            u8array = u8array.reshape(-1, *shape)
                            values.append(u8array)
                        case DataType.Int8:
                            i8array = np.frombuffer(
                                received_bytes,
                                dtype=">i1",
                                count=data_size,
                                offset=offset,
                            )
                            values.append(i8array)
                        case DataType.Int16:
                            i16array = np.frombuffer(
                                received_bytes,
                                dtype=">i2",
                                count=data_size // 2,
                                offset=offset,
                            )
                            i16array = i16array.reshape(-1, *shape)
                            values.append(i16array)
                        case DataType.Uint16:
                            u16array = np.frombuffer(
                                received_bytes,
                                dtype=">u2",
                                count=data_size // 2,
                                offset=offset,
                            )
                            u16array = u16array.reshape(-1, *shape)
                            values.append(u16array)
                        case DataType.Bool:
                            bool_array = np.frombuffer(
                                received_bytes,
                                dtype=">u1",
                                count=data_size,
                                offset=offset,
                            ).astype(bool)
                            bool_array = bool_array.reshape(-1, *shape)
                            values.append(bool_array)
                        case DataType.Int32:
                            i32array = np.frombuffer(
                                received_bytes,
                                dtype=">i4",
                                count=data_size // 4,
                                offset=offset,
                            )
                            i32array = i32array.reshape(-1, *shape)
                            values.append(i32array)
                        case DataType.Uint32:
                            u32array = np.frombuffer(
                                received_bytes,
                                dtype=">u4",
                                count=data_size // 4,
                                offset=offset,
                            )
                            u32array = u32array.reshape(-1, *shape)
                            values.append(u32array)
                        case DataType.Int64:
                            i64array = np.frombuffer(
                                received_bytes,
                                dtype=">i8",
                                count=data_size // 8,
                                offset=offset,
                            )
                            i64array = i64array.reshape(-1, *shape)
                            values.append(i64array)
                        case DataType.Uint64:
                            u64array = np.frombuffer(
                                received_bytes,
                                dtype=">u8",
                                count=data_size // 8,
                                offset=offset,
                            )
                            u64array = u64array.reshape(-1, *shape)
                            values.append(u64array)
                        case DataType.String:
                            # Format: each string followed by NULL terminator "A\0B\0"
                            byte_data = received_bytes[offset : offset + data_size]
                            if byte_data:
                                # Split by NULL, remove trailing empty from final terminator
                                parts = byte_data.split(b"\x00")
                                strings = [s.decode("utf-8") for s in parts[:-1]]
                            else:
                                strings = []
                            # print(f"{strings=}")
                            str_array = np.array(strings, dtype=np.dtypes.StringDType())  # type: ignore
                            str_array = str_array.reshape(-1, *shape)
                            values.append(str_array)
                            # print(str_array)
                        case _:
                            logger.warning(
                                f"Unsupported data type: {data_type=}, {value_index=}, {port_name=}"
                            )
                            return

                    value_type_list.append(PortValueType(data_type, tuple(shape)))
                    offset += data_size

            except Exception as e:
                logger.error(f"Failed to parse input event: {e}")
                return

            if len(values) != value_count:
                logger.warning(f"Data count mismatch: {len(values)} != {value_count}")
                return

            if input_port.value_type_list != value_type_list:
                logger.warning(
                    f"Data type mismatch: [{','.join([v.name for v in input_port.value_type_list])}] != [{','.join([ v.name for v in value_type_list])}]"
                )
                return

            input_port.dispatch(values)

            # flush the outputs
            self.flush_outputs()

    async def handle_websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self._active_web_sockets = (*self._active_web_sockets, websocket)

        try:
            while True:
                received_bytes = await websocket.receive_bytes()
                # print(f"!< {time.time_ns()}")
                self.handle_endpoint_event(
                    EndpointEventType(received_bytes[0]), received_bytes
                )
                # await asyncio.sleep(0)
        except WebSocketDisconnect:
            pass

        ws_tuple = self._active_web_sockets
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
