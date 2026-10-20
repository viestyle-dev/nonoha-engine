import asyncio
import csv
from enum import Enum
import io
import pathlib
import queue
import threading
from typing import Any
import numpy as np
import logging
import pandas as pd

from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
    PortValue,
)
from nonoha_core.node import BaseNode, NodeDoc, replace_node_input_port
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)


def _broadcast_len(values: list[Any]) -> int:
    """Get the minimum length of non-broadcast (len != 1) arrays."""
    non_broadcast = [len(arr) for arr in values if len(arr) != 1]
    if not non_broadcast:
        return 1
    len_min = min(non_broadcast)
    if any(n != len_min for n in non_broadcast):
        logger.warning("length mismatch. truncated min length")
    return len_min


class RecordingStatus(Enum):
    STOPPED = 0
    RECORDING = 1
    STOPPING = 2


class RecordNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Record input values to a CSV file",
            category="Record",
            inputs={
                "values": "",
                "start": "",
                "stop": "",
                "preamble": (
                    "Optional metadata text written as '# '-prefixed comment "
                    "lines at the top of the file, before the header row. "
                    "Held until the next start; one comment line per input "
                    "line. Empty string disables."
                ),
            },
            outputs={
                "recording_status": "",
            },
        )

    PROPERTIES = {
        "headers": {"description": "Comma-separated column headers", "data_type": "str", "default_value": "header1,header2"},
        "value_type_list": {"description": "Comma-separated value types", "data_type": "str", "default_value": "f32,f32"},
        "format": {"description": "Output format: csv (RFC 4180) or text (plain, single column only)", "data_type": "str", "default_value": "csv"},
        "allow_overwrite": {"description": "Allow overwriting existing files", "data_type": "bool", "default_value": False},
    }

    def __init__(self, name: str):
        super().__init__(name, "Record")

        headers: list[str] = ["header1", "header2"]

        value_type_list: list[PortValueType] = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]

        input_values = StaticTypeInputPort("values", value_type_list)
        input_values.subscribe(id(self), self._on_input_values)

        input_start = StaticTypeInputPort(
            "start",
            [PortValueType(DataType.String)],
            ["file_name"],
        )
        input_start.subscribe(id(self), self._on_input_start)

        input_stop = StaticTypeInputPort("stop", [PortValueType(DataType.Any)])
        input_stop.subscribe(id(self), self._on_input_stop)

        input_preamble = StaticTypeInputPort(
            "preamble",
            [PortValueType(DataType.String)],
            ["text"],
        )
        input_preamble.subscribe(id(self), self._on_input_preamble)

        output_recording_status = StaticTypeOutputPort(
            "recording_status", [PortValueType(DataType.Uint8)]
        )

        output_recording_status.dispatch([np.array([RecordingStatus.STOPPED.value])])

        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._activated = threading.Event()
        self._quit_save = threading.Event()
        self._save_worker_thread: threading.Thread | None = None
        self._input_values = input_values

        self._output_recording_status = output_recording_status
        self._headers = headers
        self._value_type_list = value_type_list
        self._format = "csv"
        self._preamble = ""
        self._recording_status = RecordingStatus.STOPPED
        self._values_queue: queue.Queue[list[Any]] = queue.Queue(maxsize=1000)

        self.inputs[input_values.name] = input_values
        self.inputs[input_start.name] = input_start
        self.inputs[input_stop.name] = input_stop
        self.inputs[input_preamble.name] = input_preamble
        self.outputs[output_recording_status.name] = output_recording_status

        self._allow_overwrite = False

    def activate(self):
        self._main_loop = asyncio.get_running_loop()
        self._activated.set()

    def finalize(self):
        self._quit_save.set()
        self._activated.set()

        if self._save_worker_thread is not None:
            self._save_worker_thread.join()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # ── Phase 1: Parse (local variables only, no self mutation) ──
        headers = self._headers
        if "headers" in properties:
            headers_str = properties["headers"]
            if not isinstance(headers_str, str):
                raise ValueError("headers must be a string")
            if headers_str.strip() == "":
                headers = []
            else:
                headers = [header.strip() for header in headers_str.split(",")]

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]
            for value_type in value_type_list:
                if value_type.shape != ():
                    raise ValueError(
                        f"value_type {value_type.name} must be scalar (no shape)"
                    )

        fmt = self._format
        if "format" in properties:
            fmt = str(properties["format"]).strip().lower()

        allow_overwrite = self._allow_overwrite
        if "allow_overwrite" in properties:
            allow_overwrite = bool(properties["allow_overwrite"])

        # ── Phase 2: Validate (cross-field checks) ──
        if fmt not in ("csv", "text"):
            raise ValueError("format must be 'csv' or 'text'")
        if fmt == "text" and len(value_type_list) > 1:
            raise ValueError("text format supports only 1 column")
        if len(headers) > 0 and len(headers) != len(value_type_list):
            raise ValueError("headers and value_type_list must have the same length")

        # ── Phase 3: Prepare (pure, no side effects) ──
        new_input_values = self._input_values
        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)

        # ── Phase 4: Apply (all validation passed) ──
        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

        self._headers = headers
        self._value_type_list = value_type_list
        self._format = fmt
        self._allow_overwrite = allow_overwrite
        self.properties["headers"] = ",".join(headers)
        self.properties["value_type_list"] = ",".join(
            [data_type.name for data_type in value_type_list]
        )
        self.properties["format"] = fmt
        self.properties["allow_overwrite"] = allow_overwrite

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_save_worker_stopped(self):
        self._recording_status = RecordingStatus.STOPPED
        self._output_recording_status.dispatch(
            [np.array([RecordingStatus.STOPPED.value])]
        )
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _save_worker(
        self, headers: list[str], preamble: str, file_path: pathlib.Path, fmt: str
    ):
        self._activated.wait()
        if self._quit_save.is_set():
            return
        loop = self._main_loop
        assert loop is not None
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            match fmt:
                case "csv":
                    file = file_path.open("w", newline="")
                case "text":
                    file = file_path.open("w")
                case _:
                    raise ValueError(f"Unknown format: {fmt}")
        except Exception as e:
            logger.error(f"Failed to open file {file_path}: {e}")
            loop.call_soon_threadsafe(self._on_save_worker_stopped)
            return

        try:
            if preamble:
                # Metadata comment block before the header row. Consumers
                # tolerate it: ReplayNode reads with comment="#", and external
                # recorder tools emit the same "# key: value" convention.
                for line in preamble.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith("#"):
                        line = f"# {line}"
                    file.write(line + "\n")
                file.flush()

            match fmt:
                case "csv":
                    writer = csv.writer(file, lineterminator="\n")
                    if headers:
                        writer.writerow(headers)
                        file.flush()

                    while not self._quit_save.is_set():
                        try:
                            values = self._values_queue.get(timeout=1)
                        except queue.Empty:
                            continue

                        len_min = _broadcast_len(values)
                        writer.writerows(
                            [arr[0 if len(arr) == 1 else i] for arr in values]
                            for i in range(len_min)
                        )
                        try:
                            file.flush()
                        except PermissionError as e:
                            logger.warning(f"PermissionError on flush: {e}")

                case "text":
                    if headers:
                        file.write(headers[0] + "\n")
                        file.flush()

                    while not self._quit_save.is_set():
                        try:
                            values = self._values_queue.get(timeout=1)
                        except queue.Empty:
                            continue

                        arr = values[0]
                        for i in range(len(arr)):
                            file.write(str(arr[i]) + "\n")
                        try:
                            file.flush()
                        except PermissionError as e:
                            logger.warning(f"PermissionError on flush: {e}")
        except Exception as e:
            logger.error(f"Save worker error: {e}")
        finally:
            file.close()

        logger.info("Save worker stopped")
        loop.call_soon_threadsafe(self._on_save_worker_stopped)

    def _on_input_start(self, values: list[PortValue]):
        record_name = str(values[0][-1])

        if self._recording_status != RecordingStatus.STOPPED:
            logger.warning("Not stopped")
            return

        record_path = pathlib.Path(record_name)
        if record_path.is_absolute():
            file_path = record_path
        else:
            parent_graph = self.parent_graph
            if parent_graph is None:
                logger.error("parent_graph is None")
                return

            persist = parent_graph.persist
            if persist is None:
                logger.error("persist is None")
                return

            file_path = persist.data_dir_path / record_name

        if not self._allow_overwrite and file_path.exists():
            logger.warning(
                f"File already exists and allow_overwrite is False: {file_path}"
            )
            return

        save_worker_thread = threading.Thread(
            target=self._save_worker,
            args=(self._headers, self._preamble, file_path, self._format),
        )
        self._quit_save.clear()
        self._save_worker_thread = save_worker_thread
        save_worker_thread.start()
        self._recording_status = RecordingStatus.RECORDING
        self._output_recording_status.dispatch(
            [np.array([RecordingStatus.RECORDING.value])]
        )

    def _on_input_preamble(self, values: list[PortValue]):
        # Held until the next start; snapshotted into the worker thread args
        # there. Dispatch preamble before start when both fire in one cascade.
        self._preamble = str(values[0][-1])

    def _on_input_stop(self, _values: list[PortValue]):
        if self._recording_status != RecordingStatus.RECORDING:
            logger.warning("Not recording")
            return

        if self._save_worker_thread is None:
            logger.error("save_worker_thread is None")
            return

        self._quit_save.set()
        self._recording_status = RecordingStatus.STOPPING
        self._output_recording_status.dispatch(
            [np.array([RecordingStatus.STOPPING.value])]
        )

    def _on_input_values(self, values: list[PortValue]):
        # print(f"{values=}")
        if self._recording_status == RecordingStatus.RECORDING:
            self._values_queue.put([v.copy() for v in values])

        # self._output_values.dispatch(values)


class ReplayFileLoadingStatus(Enum):
    NOT_LOADED = 0
    LOADING = 1
    LOADED = 2


class ReplayNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Replay recorded data from a CSV or Excel file. Lines starting with '#' are treated as comments.",
            category="Record",
            inputs={
                "load": "",
                "clock": "",
                "seek": "",
                "flush": "",
            },
            outputs={
                "values": "",
                "loading_status": "",
            },
        )

    INPUTS = {"load": {"description": "Receives trigger to load file."}}
    PROPERTIES = {
        "value_type_list": {"description": "Comma-separated value types", "data_type": "str", "default_value": "f32,f32"},
        "file_name": {"description": "File name to replay", "data_type": "str", "default_value": ""},
    }

    def __init__(self, name: str):
        super().__init__(name, "Replay")

        value_type_list = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]

        input_load = StaticTypeInputPort("load", [PortValueType(DataType.Any)])
        input_load.subscribe(id(self), self._on_input_load)

        input_clock = StaticTypeInputPort("clock", [PortValueType(DataType.Any)])
        input_clock.subscribe(id(self), self._on_input_clock)

        input_seek = StaticTypeInputPort("seek", [PortValueType(DataType.Int32)])
        input_seek.subscribe(id(self), self._on_input_seek)

        input_flush = StaticTypeInputPort(
            "flush",
            [PortValueType(DataType.Int32), PortValueType(DataType.Int32)],
        )
        input_flush.subscribe(id(self), self._on_input_flush)

        output_values = StaticTypeOutputPort("values", value_type_list)
        output_loading_status = StaticTypeOutputPort(
            "loading_status", [PortValueType(DataType.Uint8)]
        )

        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._file_name = ""
        self._value_type_list = value_type_list
        self._df: pd.DataFrame | None = None
        self._file_loading_status = ReplayFileLoadingStatus.NOT_LOADED
        self._stream_position = 0
        self._output_values = output_values
        self._output_loading_status = output_loading_status

        self.inputs[input_load.name] = input_load
        self.inputs[input_clock.name] = input_clock
        self.inputs[input_seek.name] = input_seek
        self.inputs[input_flush.name] = input_flush
        self.outputs[output_values.name] = output_values
        self.outputs[output_loading_status.name] = output_loading_status

        output_loading_status.dispatch(
            [np.array([ReplayFileLoadingStatus.NOT_LOADED.value])]
        )

    def activate(self):
        self._main_loop = asyncio.get_running_loop()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type_list = self._value_type_list

        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]

            if any(value_type.shape != () for value_type in value_type_list):
                raise ValueError("value_type must be scalar (no shape)")

        file_name = self._file_name

        if "file_name" in properties:
            file_name = properties["file_name"]
            if not isinstance(file_name, str):
                raise ValueError("file_name must be a string")

        if value_type_list != self._value_type_list:
            output_values = StaticTypeOutputPort("values", value_type_list)

            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, self._output_values.name
                )

            self._output_values = output_values

            self.outputs[output_values.name] = output_values

        if file_name != self._file_name or value_type_list != self._value_type_list:
            self._df = None
            self._file_loading_status = ReplayFileLoadingStatus.NOT_LOADED
            self._stream_position = 0

        self._value_type_list = value_type_list
        self._file_name = file_name

        self.properties["value_type_list"] = ",".join(
            [data_type.name for data_type in value_type_list]
        )
        self.properties["file_name"] = file_name

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_load_end(self, df: pd.DataFrame | None):
        # calling in main thread
        self._df = df
        self._stream_position = 0

        self._file_loading_status = ReplayFileLoadingStatus.LOADED
        self._output_loading_status.dispatch(
            [np.array([ReplayFileLoadingStatus.LOADED.value])]
        )
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _load_file_worker(self, file_path: pathlib.Path):
        loop = self._main_loop
        assert loop is not None
        # process in separate thread
        try:
            suffix = file_path.suffix.lower()
            if suffix == ".csv":
                df = pd.read_csv(file_path, comment="#")
            elif suffix in [".xls", ".xlsx"]:
                df = pd.read_excel(file_path, comment="#")
            else:
                logger.warning(f"{self.name}: Unsupported file format: {suffix}")
                loop.call_soon_threadsafe(self._on_load_end, None)
                return

            loop.call_soon_threadsafe(self._on_load_end, df)
        except BaseException as e:
            logger.warning(e)
            loop.call_soon_threadsafe(self._on_load_end, None)
            return

    def _on_input_seek(self, values: list[PortValue]):
        seek_array: np.ndarray = values[0]
        seek = seek_array[-1]

        self._stream_position = seek

    def _on_input_load(self, values: list[PortValue]):
        if self._file_loading_status == ReplayFileLoadingStatus.LOADING:
            logger.warning(f"{self.name}: Already loading")
            return

        self._file_loading_status = ReplayFileLoadingStatus.LOADING
        self._df = None

        parent_graph = self.parent_graph
        if parent_graph is None:
            logger.warning(f"{self.name}: parent_graph is None")
            self._file_loading_status = ReplayFileLoadingStatus.NOT_LOADED
            self._output_loading_status.dispatch(
                [np.array([ReplayFileLoadingStatus.NOT_LOADED.value])]
            )
            return

        persist = parent_graph.persist
        if persist is None:
            logger.warning(f"{self.name}: persist is None")
            self._file_loading_status = ReplayFileLoadingStatus.NOT_LOADED
            self._output_loading_status.dispatch(
                [np.array([ReplayFileLoadingStatus.NOT_LOADED.value])]
            )
            return

        data_dir_path = persist.data_dir_path
        file_path = data_dir_path / self._file_name

        self._output_loading_status.dispatch(
            [np.array([ReplayFileLoadingStatus.LOADING.value])]
        )
        asyncio.create_task(asyncio.to_thread(self._load_file_worker, file_path))

    def _get_values_from_df(self, start_index: int, end_index: int) -> list[PortValue]:
        df = self._df
        if df is None:
            return []

        value_type_list = self._value_type_list
        rows, cols = df.shape

        # print(f"{df.shape=}, {start_index=}, {end_index=}")

        if end_index > rows:
            end_index = rows

        if start_index == end_index:
            return []

        out_values: list[PortValue] = []
        try:
            for col_idx, value_type in enumerate(value_type_list):
                column_data = df.iloc[start_index:end_index, col_idx]
                # print(f"{column_data=}")
                match value_type.data_type:
                    case DataType.Bool:
                        value_array = np.array(column_data, dtype=bool)
                    case DataType.Int8:
                        value_array = np.array(column_data, dtype=np.int8)
                    case DataType.Uint8:
                        value_array = np.array(column_data, dtype=np.uint8)
                    case DataType.Int16:
                        value_array = np.array(column_data, dtype=np.int16)
                    case DataType.Uint16:
                        value_array = np.array(column_data, dtype=np.uint16)
                    case DataType.Int32:
                        value_array = np.array(column_data, dtype=np.int32)
                    case DataType.Uint32:
                        value_array = np.array(column_data, dtype=np.uint32)
                    case DataType.Int64:
                        value_array = np.array(column_data, dtype=np.int64)
                    case DataType.Uint64:
                        value_array = np.array(column_data, dtype=np.uint64)
                    case DataType.Float32:
                        value_array = np.array(column_data, dtype=np.float32)
                    case DataType.Float64:
                        value_array = np.array(column_data, dtype=np.float64)
                    case DataType.String:
                        value_array = np.array(column_data, dtype=np.dtypes.StringDType)  # type: ignore
                    case _:
                        logger.warning(f"Unsupported data type: {value_type.data_type}")
                        return []

                out_values.append(value_array)
            # print(df)
            # print(f"{df=}, {values=}")

        except BaseException as e:
            logger.warning(f"{self.name}: {e}")
            return []

        return out_values

    def _on_input_clock(self, values: list[PortValue]):
        if self._df is None:
            return

        count = len(values[0])
        start_index = self._stream_position
        end_index = start_index + count

        out_values = self._get_values_from_df(start_index, end_index)
        if not out_values:
            return

        # print(f"{len(out_values)=}, {len(out_values[0])=}")

        self._stream_position = start_index + len(out_values[0])

        self._output_values.dispatch(out_values)

    def _on_input_flush(self, values: list[Any]):
        if self._df is None:
            logger.warning(f"{self.name}: df is None")
            return

        start_index_array: np.ndarray = values[0]
        start_index = start_index_array[-1]

        end_index_array: np.ndarray = values[1]
        end_index = end_index_array[-1]

        out_values = self._get_values_from_df(start_index, end_index)
        if not out_values:
            return

        self._output_values.dispatch(out_values)


class RotatingRecordNode(BaseNode):
    """Record values to rotating CSV files with counter-based naming."""

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Record values to rotating CSV files",
            category="Record",
            inputs={
                "values": "Values to record",
                "start": "Start recording trigger",
                "stop": "Stop recording trigger",
            },
            outputs={
                "recording_status": "Recording state (0=Stopped, 1=Recording, 2=Stopping)",
                "current_file": "Currently active file name",
            },
        )

    PROPERTIES = {
        "headers": {
            "description": "Comma-separated column headers",
            "data_type": "str",
            "default_value": "",
        },
        "value_type_list": {
            "description": "Comma-separated value types",
            "data_type": "str",
            "default_value": "str",
        },
        "format": {
            "description": "Output format: csv (RFC 4180) or text (plain, single column only)",
            "data_type": "str",
            "default_value": "text",
        },
        "max_file_size_kb": {
            "description": "Maximum file size in KB before rotation",
            "data_type": "i32",
            "default_value": 1024,
        },
        "max_file_count": {
            "description": "Maximum number of retained files",
            "data_type": "i32",
            "default_value": 10,
        },
        "file_name": {
            "description": "Base file name (e.g. data.csv, output.log)",
            "data_type": "str",
            "default_value": "output.log",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "RotatingRecord")

        headers: list[str] = []
        value_type_list: list[PortValueType] = [PortValueType(DataType.String)]

        input_values = StaticTypeInputPort("values", value_type_list)
        input_values.subscribe(id(self), self._on_input_values)

        input_start = StaticTypeInputPort("start", [PortValueType(DataType.Any)])
        input_start.subscribe(id(self), self._on_input_start)

        input_stop = StaticTypeInputPort("stop", [PortValueType(DataType.Any)])
        input_stop.subscribe(id(self), self._on_input_stop)

        self._output_recording_status = StaticTypeOutputPort(
            "recording_status", [PortValueType(DataType.Uint8)]
        )
        self._output_current_file = StaticTypeOutputPort(
            "current_file", [PortValueType(DataType.String)]
        )

        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._activated = threading.Event()
        self._quit_save = threading.Event()
        self._save_worker_thread: threading.Thread | None = None
        self._recording_status = RecordingStatus.STOPPED
        self._values_queue: queue.Queue[list[Any]] = queue.Queue(maxsize=1000)
        self._input_values = input_values
        self._headers = headers
        self._value_type_list = value_type_list
        self._format = "text"

        self.inputs[input_values.name] = input_values
        self.inputs[input_start.name] = input_start
        self.inputs[input_stop.name] = input_stop
        self.outputs[self._output_recording_status.name] = self._output_recording_status
        self.outputs[self._output_current_file.name] = self._output_current_file

    def activate(self):
        self._main_loop = asyncio.get_running_loop()
        self._activated.set()
        self._dispatch_status(RecordingStatus.STOPPED)

    def finalize(self):
        self._quit_save.set()
        self._activated.set()
        if self._save_worker_thread is not None:
            self._save_worker_thread.join()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # ── Phase 1: Parse (local variables only, no self mutation) ──
        headers = self._headers
        if "headers" in properties:
            headers_str = properties["headers"]
            if not isinstance(headers_str, str):
                raise ValueError("headers must be a string")
            if headers_str.strip() == "":
                headers = []
            else:
                headers = [header.strip() for header in headers_str.split(",")]

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]
            for value_type in value_type_list:
                if value_type.shape != ():
                    raise ValueError(
                        f"value_type {value_type.name} must be scalar (no shape)"
                    )

        fmt = self._format
        if "format" in properties:
            fmt = str(properties["format"]).strip().lower()

        max_file_size_kb = int(self.properties["max_file_size_kb"])
        if "max_file_size_kb" in properties:
            max_file_size_kb = int(properties["max_file_size_kb"])

        max_file_count = int(self.properties["max_file_count"])
        if "max_file_count" in properties:
            max_file_count = int(properties["max_file_count"])

        file_name = str(self.properties["file_name"])
        if "file_name" in properties:
            file_name = str(properties["file_name"]).strip()

        # ── Phase 2: Validate (cross-field checks) ──
        if fmt not in ("csv", "text"):
            raise ValueError("format must be 'csv' or 'text'")
        if fmt == "text" and len(value_type_list) > 1:
            raise ValueError("text format supports only 1 column")
        if len(headers) > 0 and len(headers) != len(value_type_list):
            raise ValueError("headers and value_type_list must have the same length")

        # ── Phase 3: Prepare (pure, no side effects) ──
        new_input_values = self._input_values
        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)

        # ── Phase 4: Apply (all validation passed) ──
        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

        self._headers = headers
        self._value_type_list = value_type_list
        self._format = fmt
        self.properties["headers"] = ",".join(headers)
        self.properties["value_type_list"] = ",".join(
            [data_type.name for data_type in value_type_list]
        )
        self.properties["format"] = fmt
        self.properties["max_file_size_kb"] = max_file_size_kb
        self.properties["max_file_count"] = max_file_count
        self.properties["file_name"] = file_name

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _dispatch_status(self, status: RecordingStatus):
        self._output_recording_status.dispatch(
            [np.array([status.value], dtype=np.uint8)]
        )
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _dispatch_current_file(self, filename: str):
        self._output_current_file.dispatch(
            [np.array([filename], dtype=np.dtypes.StringDType())] # type: ignore
        )
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _on_input_start(self, _values: list[PortValue]):
        if self._recording_status != RecordingStatus.STOPPED:
            logger.warning("Not stopped")
            return

        parent_graph = self.parent_graph
        if parent_graph is None or parent_graph.persist is None:
            logger.error("persist is None")
            return

        data_dir = parent_graph.persist.data_dir_path
        file_name = str(self.properties["file_name"])
        max_size_kb = int(self.properties["max_file_size_kb"])
        max_count = int(self.properties["max_file_count"])

        self._quit_save.clear()
        self._save_worker_thread = threading.Thread(
            target=self._save_worker,
            args=(self._headers, data_dir, file_name, max_size_kb, max_count, self._format),
        )
        self._save_worker_thread.start()
        self._recording_status = RecordingStatus.RECORDING
        self._dispatch_status(RecordingStatus.RECORDING)

    def _on_input_stop(self, _values: list[PortValue]):
        if self._recording_status != RecordingStatus.RECORDING:
            logger.warning("Not recording")
            return
        self._quit_save.set()
        self._recording_status = RecordingStatus.STOPPING
        self._dispatch_status(RecordingStatus.STOPPING)

    def _on_input_values(self, values: list[PortValue]):
        if self._recording_status != RecordingStatus.RECORDING:
            return
        self._values_queue.put([v.copy() for v in values])

    def _on_save_worker_stopped(self):
        self._recording_status = RecordingStatus.STOPPED
        self._dispatch_status(RecordingStatus.STOPPED)

    def _save_worker(
        self,
        headers: list[str],
        data_dir: pathlib.Path,
        file_name: str,
        max_size_kb: int,
        max_count: int,
        fmt: str,
    ):
        self._activated.wait()
        if self._quit_save.is_set():
            return
        loop = self._main_loop
        assert loop is not None
        max_size_bytes = max_size_kb * 1024

        base_path = data_dir / file_name
        base_path.parent.mkdir(parents=True, exist_ok=True)
        loop.call_soon_threadsafe(
            self._dispatch_current_file, base_path.name
        )

        # Rotate if existing file already at size limit
        if base_path.exists() and base_path.stat().st_size >= max_size_bytes:
            self._rotate_files(data_dir, file_name, max_count)

        try:
            is_new = not base_path.exists() or base_path.stat().st_size == 0
            match fmt:
                case "csv":
                    file = base_path.open("a", newline="")
                case "text":
                    file = base_path.open("a")
                case _:
                    raise ValueError(f"Unknown format: {fmt}")
        except OSError as e:
            logger.error(f"Failed to open file {base_path}: {e}")
            loop.call_soon_threadsafe(self._on_save_worker_stopped)
            return

        try:
            match fmt:
                case "csv":
                    writer = csv.writer(file, lineterminator="\n")
                    if is_new and headers:
                        writer.writerow(headers)
                        file.flush()

                    while not self._quit_save.is_set():
                        try:
                            values = self._values_queue.get(timeout=1)
                        except queue.Empty:
                            continue

                        len_min = _broadcast_len(values)
                        try:
                            writer.writerows(
                                [arr[0 if len(arr) == 1 else i] for arr in values]
                                for i in range(len_min)
                            )
                            file.flush()
                        except OSError as e:
                            logger.warning(f"Write failed: {e}")
                            continue

                        # Check rotation
                        try:
                            if base_path.stat().st_size >= max_size_bytes:
                                file.close()
                                self._rotate_files(data_dir, file_name, max_count)
                                file = base_path.open("w", newline="")
                                writer = csv.writer(file, lineterminator="\n")
                                if headers:
                                    writer.writerow(headers)
                                    file.flush()
                        except OSError as e:
                            logger.warning(f"Rotation failed: {e}")

                case "text":
                    if is_new and headers:
                        file.write(headers[0] + "\n")
                        file.flush()

                    while not self._quit_save.is_set():
                        try:
                            values = self._values_queue.get(timeout=1)
                        except queue.Empty:
                            continue

                        arr = values[0]
                        try:
                            for i in range(len(arr)):
                                file.write(str(arr[i]) + "\n")
                            file.flush()
                        except OSError as e:
                            logger.warning(f"Write failed: {e}")
                            continue

                        # Check rotation
                        try:
                            if base_path.stat().st_size >= max_size_bytes:
                                file.close()
                                self._rotate_files(data_dir, file_name, max_count)
                                file = base_path.open("w")
                                if headers:
                                    file.write(headers[0] + "\n")
                                    file.flush()
                        except OSError as e:
                            logger.warning(f"Rotation failed: {e}")
        finally:
            file.close()

        logger.info("RotatingRecord save worker stopped")
        loop.call_soon_threadsafe(self._on_save_worker_stopped)

    @staticmethod
    def _rotate_files(
        data_dir: pathlib.Path, file_name: str, max_count: int
    ):
        """Cascade rename: file_name -> .1, .1 -> .2, ..., delete oldest."""
        base = data_dir / file_name
        for i in range(max_count - 1, 0, -1):
            src = data_dir / f"{file_name}.{i}"
            if not src.exists():
                continue
            if i >= max_count - 1:
                try:
                    src.unlink()
                    logger.info(f"Deleted old file: {src.name}")
                except OSError as e:
                    logger.warning(f"Failed to delete {src.name}: {e}")
            else:
                try:
                    src.rename(data_dir / f"{file_name}.{i + 1}")
                except OSError as e:
                    logger.warning(f"Failed to rename {src.name}: {e}")
        if base.exists():
            try:
                base.rename(data_dir / f"{file_name}.1")
            except OSError as e:
                logger.warning(f"Failed to rename {base.name}: {e}")
