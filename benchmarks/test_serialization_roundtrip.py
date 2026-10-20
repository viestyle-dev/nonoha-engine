"""Benchmarks for full serialize + deserialize roundtrip (engine-level)."""

import numpy as np

from nonoha_core.port import port_values_to_bytes
from nonoha_core.data_type import DataType, PortValueType


def _build_input_frame(port_name: str, values: list[np.ndarray],
                       types: list[PortValueType]) -> bytes:
    """Build a binary WebSocket input event frame."""
    buf = bytearray()
    # Event type: 0x00 = input
    buf += b"\x00"
    # Port name
    name_bytes = port_name.encode("utf-8")
    buf += len(name_bytes).to_bytes(1, "big")
    buf += name_bytes
    # Values
    port_values_to_bytes(values, types, buf)
    return bytes(buf)


def test_roundtrip_f32_small(benchmark):
    """Serialize + build input frame for f32[10]."""
    values = [np.ones((1, 10), dtype=np.float32)]
    types = [PortValueType(DataType.Float32, (10,))]

    def do_roundtrip():
        return _build_input_frame("test", values, types)

    benchmark(do_roundtrip)


def test_roundtrip_f32_large(benchmark):
    """Serialize + build input frame for f32[10000]."""
    values = [np.ones((1, 10_000), dtype=np.float32)]
    types = [PortValueType(DataType.Float32, (10_000,))]

    def do_roundtrip():
        return _build_input_frame("test", values, types)

    benchmark(do_roundtrip)


def test_roundtrip_multi_value(benchmark):
    """Serialize + build input frame for 4 mixed-type values."""
    values = [
        np.ones((1, 100), dtype=np.float32),
        np.ones((1, 50), dtype=np.float64),
        np.ones((1, 200), dtype=np.int16),
        np.ones((1, 10), dtype=np.uint8),
    ]
    types = [
        PortValueType(DataType.Float32, (100,)),
        PortValueType(DataType.Float64, (50,)),
        PortValueType(DataType.Int16, (200,)),
        PortValueType(DataType.Uint8, (10,)),
    ]

    def do_roundtrip():
        return _build_input_frame("test", values, types)

    benchmark(do_roundtrip)
