"""The graph endpoint (app <-> graph WebSocket): decoding, and failures that
must not close the connection."""

import asyncio
import logging

import numpy as np
import pytest

from nonoha_core.data_type import DataType, PortValueType
from nonoha_core.port import StaticTypeInputPort, port_values_to_bytes

from nonoha_engine.node_flow.node import NodeGraph


def make(types, name="in"):
    graph = NodeGraph("g", {})
    port = StaticTypeInputPort(name, types)
    received = []
    port.subscribe(1, lambda values: received.append(values))
    graph.add_input_port(port)
    return graph, port, received


def message(name: str, values, types) -> bytes:
    encoded = name.encode()
    return bytes(bytes([0, len(encoded)]) + encoded + port_values_to_bytes(values, types, bytearray()))


NUMERIC = [
    (DataType.Bool, np.bool_), (DataType.Int8, np.int8), (DataType.Uint8, np.uint8),
    (DataType.Int16, np.int16), (DataType.Uint16, np.uint16), (DataType.Int32, np.int32),
    (DataType.Uint32, np.uint32), (DataType.Int64, np.int64), (DataType.Uint64, np.uint64),
    (DataType.Float32, np.float32), (DataType.Float64, np.float64),
]


@pytest.mark.parametrize("data_type, np_type", NUMERIC)
@pytest.mark.parametrize("shape", [(), (3,), (2, 4)])
@pytest.mark.parametrize("batch", [1, 4])
def test_every_type_arrives_with_its_batch_and_shape(data_type, np_type, shape, batch):
    types = [PortValueType(data_type, shape)]
    graph, port, received = make(types)
    sent = (np.arange(batch * int(np.prod(shape, dtype=int))) % 2 == 1) if data_type == DataType.Bool else np.arange(batch * int(np.prod(shape, dtype=int)))
    sent = sent.astype(np_type).reshape(batch, *shape)
    graph.handle_endpoint_event(message("in", [sent], types))
    (got,) = received[-1]
    assert got.shape == (batch, *shape)  # Int8 included (it was not reshaped)
    assert got.dtype.kind == np.dtype(np_type).kind and got.dtype.itemsize == np.dtype(np_type).itemsize
    np.testing.assert_array_equal(got, sent)


def test_strings_and_several_values():
    types = [PortValueType(DataType.String, (2,)), PortValueType(DataType.Float32)]
    graph, port, received = make(types)
    strings = np.array([["a", "日本"]], dtype=np.dtypes.StringDType())
    graph.handle_endpoint_event(message("in", [strings, np.array([1.5], np.float32)], types))
    got = received[-1]
    assert got[0].tolist() == [["a", "日本"]] and got[1].tolist() == [1.5]


def test_a_port_name_in_another_script(caplog):
    types = [PortValueType(DataType.Float32)]
    graph, port, received = make(types, name="入力")
    graph.handle_endpoint_event(message("入力", [np.array([2.0], np.float32)], types))
    assert received[-1][0].tolist() == [2.0]


def test_a_type_mismatch_is_refused_with_both_types(caplog):
    graph, port, received = make([PortValueType(DataType.Float32, (3,))])
    with caplog.at_level("WARNING"):
        graph.handle_endpoint_event(message("in", [np.ones((1, 2), np.float32)], [PortValueType(DataType.Float32, (2,))]))
    assert not received
    assert "Data type mismatch: [f32[3]] != [f32[2]]" in caplog.text


def test_malformed_and_unknown_messages_are_logged_not_raised(caplog):
    graph, port, received = make([PortValueType(DataType.Float32)])
    with caplog.at_level("WARNING"):
        graph.handle_endpoint_event(bytes([0, 2]) + b"in" + bytes([1, 200]))  # truncated
        graph.handle_endpoint_event(bytes([0, 3]) + b"out" + bytes([0]))  # no such port
    assert not received and "Failed to parse input event" in caplog.text


class _Socket:
    """A WebSocket that delivers ``messages`` and then disconnects."""

    def __init__(self, messages):
        self._messages = list(messages)
        self.closed = False

    async def accept(self):
        pass

    async def receive(self):
        if self._messages:
            return {"type": "websocket.receive", "bytes": self._messages.pop(0)}
        return {"type": "websocket.disconnect"}


@pytest.mark.parametrize("error", [ValueError, RuntimeError, KeyError])
def test_a_failing_node_does_not_close_the_connection(error, caplog):
    types = [PortValueType(DataType.Float32)]
    graph, port, _ = make(types)
    calls = []

    def failing(values):
        calls.append(values)
        raise error("a broken node")

    port.subscribe(2, failing)
    socket = _Socket([message("in", [np.array([float(i)], np.float32)], types) for i in range(5)])
    with caplog.at_level("ERROR"):
        asyncio.run(graph.handle_websocket_endpoint(socket))
    assert len(calls) == 5  # every message was still handled
    assert len([r for r in caplog.records if r.exc_info]) == 1  # one traceback, the rest counted
    assert socket not in graph._active_web_sockets
