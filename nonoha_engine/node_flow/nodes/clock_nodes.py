"""High-resolution clock node for engine environments with threading support.

Uses run_in_executor + time.sleep instead of asyncio.sleep for better
timing precision on Windows (avoids 15.6ms timer resolution limitation).
"""

import asyncio
import logging
import time

import numpy as np

from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort, PortValue
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType


logger = logging.getLogger(__name__)



class HiResClockNode(BaseNode):
    """High-resolution periodic trigger using thread-based sleep.

    Emits a boolean tick signal at a fixed rate. Unlike core ClockNode,
    uses run_in_executor + time.sleep for sub-millisecond timing precision
    on Windows.

    Input ports:
        enabled - Start/stop the clock (bool)

    Output ports:
        tick - Periodic trigger signal (bool, always True)
    """

    PROPERTIES = {
        "rate": {
            "description": "Tick rate (Hz)",
            "data_type": "f64",
            "default_value": 30.0,
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="High-resolution periodic trigger",
            category="Time",
            inputs={"enabled": "Start/stop the clock (bool)"},
            outputs={"tick": "Periodic trigger signal (bool)"},
        )

    def __init__(self, name: str):
        super().__init__(name, "HiResClock")

        self._rate = float(self.properties.get("rate", 30.0))
        self._tick_value = np.array([True], dtype=np.bool_)

        input_enabled = StaticTypeInputPort(
            "enabled", [PortValueType(DataType.Bool)]
        )
        input_enabled.subscribe(id(self), self._on_input_enabled)
        self.inputs[input_enabled.name] = input_enabled

        output_tick = StaticTypeOutputPort(
            "tick", [PortValueType(DataType.Bool)]
        )
        self._output_tick = output_tick
        self.outputs[output_tick.name] = output_tick

        self._timer_task: asyncio.Task | None = None

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if "rate" in properties:
            rate = float(properties["rate"])
            if rate <= 0:
                raise ValueError(f"rate must be greater than 0, got {rate}")
            self._rate = rate

        self.properties["rate"] = self._rate

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = asyncio.create_task(self._emit_tick())

    def _on_input_enabled(self, values: list[PortValue]):
        bool_array: np.ndarray = values[0]
        enabled = bool_array[-1]

        if enabled:
            if self._timer_task is None:
                self._timer_task = asyncio.create_task(self._emit_tick())
        else:
            if self._timer_task is not None:
                self._timer_task.cancel()
                self._timer_task = None

    async def _emit_tick(self):
        loop = asyncio.get_running_loop()
        try:
            while True:
                interval = 1.0 / self._rate
                await loop.run_in_executor(None, time.sleep, interval)

                self._output_tick.dispatch([self._tick_value])
                if self.parent_graph is not None:
                    self.parent_graph.flush_outputs()

        except asyncio.CancelledError:
            pass

    def finalize(self):
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None
