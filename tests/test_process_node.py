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


def test_output_that_is_not_utf8_does_not_stop_the_reader(tmp_path):
    """A byte that is not UTF-8 becomes U+FFFD; the lines after it still
    arrive and the child runs to its end (its pipe is still read)."""
    import sys
    import time

    script = tmp_path / "child.py"
    script.write_text(
        "import sys\n"
        "sys.stdout.buffer.write(b'\\xff\\xfe broken\\n'); sys.stdout.flush()\n"
        "print('after', flush=True)\n"
        "for i in range(2000): print('x' * 60, flush=False)\n"  # more than a pipe buffer
        "print('end', flush=True)\n",
        encoding="utf-8",
    )
    lines: list[str] = []
    codes: list[int] = []

    async def run():
        node = ProcessNode("p")
        node.set_properties({"command": sys.executable, "arguments": str(script)})
        node.outputs["stdout"].subscribe(1, lambda v: lines.append(str(v[0][0])))
        node.outputs["exit_code"].subscribe(1, lambda v: codes.append(int(v[0][0])))
        node.activate()
        node.inputs["start"].dispatch([np.array([True])])
        deadline = time.monotonic() + 15
        while not codes and time.monotonic() < deadline:
            await asyncio.sleep(0.05)
        node.finalize()

    asyncio.run(run())
    assert codes == [0]
    assert "�" in lines[0] and "after" in lines and lines[-1] == "end"
