"""Process supervisor node for launching and managing subprocesses."""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import threading
from enum import Enum
from typing import Any, Callable, Literal

import numpy as np

from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort, PortValue
from nonoha_core.data_type import DataType, PortValueType

logger = logging.getLogger(__name__)

RestartPolicy = Literal["none", "on_failure", "always"]


# ---------------------------------------------------------------------------
# ProcessSupervisor — standalone subprocess lifecycle manager
# ---------------------------------------------------------------------------


class ProcessState(Enum):
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    STOPPING = 3


class ProcessSupervisor:
    """Manages a subprocess lifecycle with restart policies.

    Independent of the nonoha node system. State changes and output are
    communicated via callbacks. All callbacks are invoked from worker threads.

    Thread safety:
    - ``_state``, ``_worker_thread``, and config fields are guarded by
      ``_lock``.
    - The subprocess (``Popen``) and reader threads are managed locally
      within the worker thread and are never accessed from outside.
    - Does not rely on GIL for correctness.
    """

    def __init__(
        self,
        on_state_changed: Callable[[ProcessState], None],
        on_stdout: Callable[[str], None],
        on_stderr: Callable[[str], None],
        on_exit: Callable[[int], None],
    ):
        self._on_state_changed = on_state_changed
        self._on_stdout = on_stdout
        self._on_stderr = on_stderr
        self._on_exit = on_exit

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # All fields below are guarded by self._lock
        self._state = ProcessState.STOPPED
        self._worker_thread: threading.Thread | None = None
        self._restart_policy: RestartPolicy = "none"
        self._restart_delay: float = 1.0
        self._max_restarts: int = 0
        self._stop_timeout: float = 5.0

    @property
    def state(self) -> ProcessState:
        with self._lock:
            return self._state

    def set_config(
        self,
        restart_policy: RestartPolicy,
        restart_delay: float,
        max_restarts: int,
        stop_timeout: float,
    ) -> None:
        """Update supervisor configuration. Thread-safe."""
        with self._lock:
            self._restart_policy = restart_policy
            self._restart_delay = restart_delay
            self._max_restarts = max_restarts
            self._stop_timeout = stop_timeout

    def start(
        self,
        command: str,
        args: list[str] | None = None,
        cwd: str | None = None,
    ) -> None:
        """Start the subprocess. Non-blocking."""
        with self._lock:
            if self._state != ProcessState.STOPPED:
                logger.warning(f"Cannot start: current state is {self._state.name}")
                return
            self._set_state(ProcessState.STARTING)
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker,
                args=(command, args or [], cwd),
                daemon=True,
            )
            self._worker_thread.start()

    def stop(self) -> None:
        """Request graceful stop. Non-blocking."""
        with self._lock:
            if self._state not in (ProcessState.RUNNING, ProcessState.STARTING):
                return
            self._set_state(ProcessState.STOPPING)
        self._stop_event.set()

    def shutdown(self, timeout: float = 5.0) -> None:
        """Synchronous shutdown. Blocks until worker exits or timeout."""
        self._stop_event.set()

        with self._lock:
            worker = self._worker_thread

        if worker is not None and worker.is_alive():
            worker.join(timeout=timeout)

        with self._lock:
            self._worker_thread = None
            if self._state != ProcessState.STOPPED:
                self._set_state(ProcessState.STOPPED)

    # -- Worker thread (process and readers are all local) --

    def _worker(self, command: str, args: list[str], cwd: str | None) -> None:
        restart_count = 0

        while True:
            exit_code = self._run_once(command, args, cwd)

            if self._stop_event.is_set():
                break

            if exit_code is None:
                break

            self._on_exit(exit_code)

            with self._lock:
                policy = self._restart_policy
                max_restarts = self._max_restarts
                delay = self._restart_delay

            if not self._should_restart(exit_code, restart_count, policy, max_restarts):
                with self._lock:
                    self._set_state(ProcessState.STOPPED)
                break

            restart_count += 1
            logger.info(
                f"Restarting process (attempt {restart_count}) after {delay}s"
            )

            if self._stop_event.wait(delay):
                with self._lock:
                    self._set_state(ProcessState.STOPPED)
                break

            with self._lock:
                self._set_state(ProcessState.STARTING)

    def _run_once(self, command: str, args: list[str], cwd: str | None) -> int | None:
        """Run the process once. Returns exit code, or None on startup failure.

        The subprocess and reader threads are local to this method and are
        never stored as instance variables.
        """
        cmd = [command, *args]
        readers: tuple[threading.Thread | None, threading.Thread | None] = (None, None)

        try:
            popen_kwargs: dict[str, Any] = {}
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            logger.info(f"Starting process: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or None,
                text=True,
                **popen_kwargs,
            )

            readers = self._start_reader_threads(process)

            logger.info(f"Process started (PID: {process.pid})")

            with self._lock:
                self._set_state(ProcessState.RUNNING)

        except FileNotFoundError:
            logger.error(f"Command not found: {command}")
            with self._lock:
                self._set_state(ProcessState.STOPPED)
            return None
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            with self._lock:
                self._set_state(ProcessState.STOPPED)
            return None

        # Monitor loop
        while not self._stop_event.is_set():
            exit_code = process.poll()
            if exit_code is not None:
                logger.info(f"Process exited (code: {exit_code})")
                self._join_reader_threads(readers, timeout=1.0)
                return exit_code

            self._stop_event.wait(0.1)

        # Stop requested
        with self._lock:
            stop_timeout = self._stop_timeout

        self._stop_process(process, stop_timeout)
        self._join_reader_threads(readers, timeout=2.0)

        exit_code = process.poll()
        with self._lock:
            self._set_state(ProcessState.STOPPED)

        if exit_code is not None:
            self._on_exit(exit_code)

        return None  # Stopped by request, not a restart candidate

    @staticmethod
    def _should_restart(
        exit_code: int,
        restart_count: int,
        policy: RestartPolicy,
        max_restarts: int,
    ) -> bool:
        if policy == "none":
            return False
        if policy == "on_failure" and exit_code == 0:
            return False
        if max_restarts > 0 and restart_count >= max_restarts:
            logger.warning(f"Max restarts ({max_restarts}) reached")
            return False
        return True

    @staticmethod
    def _stop_process(process: subprocess.Popen, timeout: float) -> None:
        """Graceful stop sequence, platform-aware."""
        if process.poll() is not None:
            return

        # Graceful stop
        try:
            if sys.platform == "win32":
                # CTRL_BREAK_EVENT (requires CREATE_NEW_PROCESS_GROUP)
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                process.terminate()  # SIGTERM
        except (ProcessLookupError, OSError):
            return

        try:
            process.wait(timeout=timeout)
            return
        except subprocess.TimeoutExpired:
            pass

        # Force kill
        logger.warning(f"Force killing process (PID: {process.pid})")
        try:
            process.kill()
            process.wait(timeout=5.0)
        except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
            logger.error("Failed to kill process")

    # -- Output reader threads --

    def _start_reader_threads(
        self, process: subprocess.Popen
    ) -> tuple[threading.Thread | None, threading.Thread | None]:
        """Create and start reader threads. Returns (stdout_thread, stderr_thread)."""
        stdout_thread: threading.Thread | None = None
        stderr_thread: threading.Thread | None = None

        if process.stdout is not None:
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(process.stdout, self._on_stdout),
                daemon=True,
            )
            stdout_thread.start()

        if process.stderr is not None:
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(process.stderr, self._on_stderr),
                daemon=True,
            )
            stderr_thread.start()

        return stdout_thread, stderr_thread

    @staticmethod
    def _join_reader_threads(
        readers: tuple[threading.Thread | None, threading.Thread | None],
        timeout: float = 2.0,
    ) -> None:
        """Join reader threads."""
        stdout_thread, stderr_thread = readers
        if stdout_thread is not None and stdout_thread.is_alive():
            stdout_thread.join(timeout=timeout)
        if stderr_thread is not None and stderr_thread.is_alive():
            stderr_thread.join(timeout=timeout)

    @staticmethod
    def _read_output(stream, callback: Callable[[str], None]) -> None:
        try:
            for line in stream:
                line = line.rstrip("\n\r")
                if line:
                    callback(line)
        except (ValueError, OSError):
            pass

    # -- State management --

    def _set_state(self, new_state: ProcessState) -> None:
        """Update state and notify. Must be called with lock held.

        The callback is intentionally invoked under the lock to guarantee
        that state-change notifications are serialized in the same order
        as state transitions.  The callback MUST be non-blocking and MUST
        NOT attempt to acquire ``self._lock`` (deadlock risk).
        """
        self._state = new_state
        self._on_state_changed(new_state)


# ---------------------------------------------------------------------------
# ProcessNode — nonoha node wrapping ProcessSupervisor
# ---------------------------------------------------------------------------


class ProcessNode(BaseNode):

    PROPERTIES = {
        "command": {
            "description": "Command to execute",
            "data_type": "str",
            "default_value": "",
        },
        "arguments": {
            "description": "Command arguments (space-separated)",
            "data_type": "str",
            "default_value": "",
        },
        "working_directory": {
            "description": "Working directory for the process",
            "data_type": "str",
            "default_value": "",
        },
        "restart_policy": {
            "description": "Restart policy: none, on_failure, always",
            "data_type": "str",
            "default_value": "none",
        },
        "restart_delay": {
            "description": "Delay before restart (seconds)",
            "data_type": "f64",
            "default_value": 1.0,
        },
        "max_restarts": {
            "description": "Maximum restart count (0 = unlimited)",
            "data_type": "i32",
            "default_value": 0,
        },
        "stop_timeout": {
            "description": "Seconds to wait before force kill",
            "data_type": "f64",
            "default_value": 5.0,
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Launch and supervise an external process",
            category="System",
            inputs={
                "start": "Start the process",
                "stop": "Stop the process",
            },
            outputs={
                "status": "Process state (0=STOPPED, 1=STARTING, 2=RUNNING, 3=STOPPING)",
                "stdout": "Process stdout lines",
                "stderr": "Process stderr lines",
                "exit_code": "Process exit code",
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "Process")

        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._supervisor: ProcessSupervisor | None = None

        # Input ports
        bool_type = PortValueType(DataType.Bool)

        input_start = StaticTypeInputPort("start", [bool_type])
        input_start.subscribe(id(self), self._on_input_start)
        self.inputs[input_start.name] = input_start

        input_stop = StaticTypeInputPort("stop", [bool_type])
        input_stop.subscribe(id(self), self._on_input_stop)
        self.inputs[input_stop.name] = input_stop

        # Output ports
        str_type = PortValueType(DataType.String)
        uint8_type = PortValueType(DataType.Uint8)
        int64_type = PortValueType(DataType.Int64)

        self._output_status = StaticTypeOutputPort("status", [uint8_type])
        self.outputs[self._output_status.name] = self._output_status

        self._output_stdout = StaticTypeOutputPort("stdout", [str_type])
        self.outputs[self._output_stdout.name] = self._output_stdout

        self._output_stderr = StaticTypeOutputPort("stderr", [str_type])
        self.outputs[self._output_stderr.name] = self._output_stderr

        self._output_exit_code = StaticTypeOutputPort("exit_code", [int64_type])
        self.outputs[self._output_exit_code.name] = self._output_exit_code

    def activate(self):
        self._main_loop = asyncio.get_running_loop()
        self._supervisor = ProcessSupervisor(
            on_state_changed=self._on_state_changed_from_thread,
            on_stdout=self._on_stdout_from_thread,
            on_stderr=self._on_stderr_from_thread,
            on_exit=self._on_exit_from_thread,
        )
        self._sync_supervisor_config()
        # Status port reflects the supervisor's current state at startup.
        # ProcessSupervisor.__init__ sets _state = STOPPED but does NOT call
        # _set_state, so without this explicit dispatch the status port stays
        # silent until the first real state transition. Mirrors the
        # dispatch_on_init contract used by RealNumberValue and other
        # state-bearing nodes.
        self._dispatch_status(self._supervisor.state)

    def finalize(self):
        if self._supervisor is not None:
            self._supervisor.shutdown(
                timeout=float(self.properties.get("stop_timeout", 5.0))
            )
            self._supervisor = None

    def set_properties(self, properties: dict):
        # ── Phase 1: Parse (local variables only, no self mutation) ──
        command = self.properties.get("command", "")
        if "command" in properties:
            command = properties["command"]
            if not isinstance(command, str):
                raise ValueError("command must be a string")

        arguments = self.properties.get("arguments", "")
        if "arguments" in properties:
            arguments = properties["arguments"]
            if not isinstance(arguments, str):
                raise ValueError("arguments must be a string")

        working_directory = self.properties.get("working_directory", "")
        if "working_directory" in properties:
            working_directory = properties["working_directory"]
            if not isinstance(working_directory, str):
                raise ValueError("working_directory must be a string")

        restart_policy = self.properties.get("restart_policy", "none")
        if "restart_policy" in properties:
            restart_policy = str(properties["restart_policy"]).strip().lower()

        restart_delay = float(self.properties.get("restart_delay", 1.0))
        if "restart_delay" in properties:
            restart_delay = float(properties["restart_delay"])

        max_restarts = int(self.properties.get("max_restarts", 0))
        if "max_restarts" in properties:
            max_restarts = int(properties["max_restarts"])

        stop_timeout = float(self.properties.get("stop_timeout", 5.0))
        if "stop_timeout" in properties:
            stop_timeout = float(properties["stop_timeout"])

        # ── Phase 2: Validate ──
        if restart_policy not in ("none", "on_failure", "always"):
            raise ValueError(
                f"restart_policy must be 'none', 'on_failure', or 'always', "
                f"got '{restart_policy}'"
            )
        if restart_delay < 0:
            raise ValueError("restart_delay must be >= 0")
        if max_restarts < 0:
            raise ValueError("max_restarts must be >= 0")
        if stop_timeout <= 0:
            raise ValueError("stop_timeout must be > 0")

        # ── Phase 3: Prepare ──
        # No derived objects to create for ProcessNode.

        # ── Phase 4: Apply (all validation passed) ──
        self.properties["command"] = command
        self.properties["arguments"] = arguments
        self.properties["working_directory"] = working_directory
        self.properties["restart_policy"] = restart_policy
        self.properties["restart_delay"] = restart_delay
        self.properties["max_restarts"] = max_restarts
        self.properties["stop_timeout"] = stop_timeout

        self._sync_supervisor_config()

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _sync_supervisor_config(self):
        if self._supervisor is None:
            return
        policy = self.properties.get("restart_policy", "none")
        if policy not in ("none", "on_failure", "always"):
            policy = "none"
        self._supervisor.set_config(
            restart_policy=policy,  # type: ignore[arg-type]
            restart_delay=float(self.properties.get("restart_delay", 1.0)),
            max_restarts=int(self.properties.get("max_restarts", 0)),
            stop_timeout=float(self.properties.get("stop_timeout", 5.0)),
        )

    def _start_process(self):
        if self._supervisor is None:
            return

        command = str(self.properties.get("command", ""))
        if not command:
            logger.warning("No command specified")
            return

        args_str = str(self.properties.get("arguments", ""))
        args = args_str.split() if args_str else []
        cwd = str(self.properties.get("working_directory", "")) or None

        self._supervisor.start(command, args, cwd)

    # -- Input port handlers --

    def _on_input_start(self, _values: list[PortValue]):
        self._start_process()

    def _on_input_stop(self, values: list[PortValue]):
        if self._supervisor is not None:
            self._supervisor.stop()

    # -- Thread-safe dispatch (callbacks from worker threads) --

    def _on_state_changed_from_thread(self, state: ProcessState):
        if self._main_loop is not None:
            self._main_loop.call_soon_threadsafe(self._dispatch_status, state)

    def _on_stdout_from_thread(self, line: str):
        if self._main_loop is not None:
            self._main_loop.call_soon_threadsafe(self._dispatch_stdout, line)

    def _on_stderr_from_thread(self, line: str):
        if self._main_loop is not None:
            self._main_loop.call_soon_threadsafe(self._dispatch_stderr, line)

    def _on_exit_from_thread(self, exit_code: int):
        if self._main_loop is not None:
            self._main_loop.call_soon_threadsafe(self._dispatch_exit_code, exit_code)

    # -- Output dispatch (asyncio thread) --

    def _dispatch_status(self, state: ProcessState):
        self._output_status.dispatch([np.array([state.value], dtype=np.uint8)])
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _dispatch_stdout(self, line: str):
        self._output_stdout.dispatch([np.array([line], dtype=np.dtypes.StringDType())])  # type: ignore
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _dispatch_stderr(self, line: str):
        self._output_stderr.dispatch([np.array([line], dtype=np.dtypes.StringDType())])  # type: ignore
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _dispatch_exit_code(self, exit_code: int):
        self._output_exit_code.dispatch([np.array([exit_code], dtype=np.int64)])
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()
