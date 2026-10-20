"""Tests for ProcessNode focusing on the status port contract.

Specifically: status must dispatch the supervisor's current state on
activate(), so downstream consumers see a known initial value instead
of waiting for the first real state transition.
"""

import asyncio

import numpy as np

from nonoha_engine.node_flow.nodes.process_nodes import ProcessNode, ProcessState


def test_process_node_port_structure():
    node = ProcessNode("test")
    assert "start" in node.inputs
    assert "stop" in node.inputs
    assert "status" in node.outputs
    assert "stdout" in node.outputs
    assert "stderr" in node.outputs
    assert "exit_code" in node.outputs


def test_process_node_status_dispatched_on_activate():
    """activate() must dispatch the initial STOPPED (=0) state to the
    status port so downstream consumers (e.g. Equal-based auto-restart
    chains) can react to the cold-boot state instead of staying
    uninformed until the first real state transition.
    """
    status_results: list[np.ndarray] = []

    async def run():
        node = ProcessNode("test")
        node.outputs["status"].subscribe(
            0, lambda v: status_results.append(v[0])
        )
        node.activate()
        node.finalize()

    asyncio.run(run())

    # Exactly one dispatch from activate(), with value = STOPPED (0).
    assert len(status_results) == 1
    arr = status_results[0]
    assert arr.shape == (1,)
    assert arr.dtype == np.uint8
    assert int(arr[0]) == ProcessState.STOPPED.value
    assert int(arr[0]) == 0
