import argparse
import asyncio
import json
import sys
from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.responses import FileResponse
from starlette.staticfiles import NotModifiedResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import time
import logging
import traceback
from fastapi.middleware.cors import CORSMiddleware
import pathlib
import threading
import queue
import signal

from nonoha_core.node_registry import NodeRegistry
import nonoha_core.nodes
import sci_nodes

import nonoha_engine.node_flow.router
import nonoha_engine.node_flow.node_flow
from nonoha_engine.node_flow.nodes import (
    clock_nodes,
    graph_nodes,
    record_nodes,
    process_nodes,
)

# import nonoha_engine.webrtc_gateway.router

from .plugin_management.plugin_host import PluginHost
from .runtime_config import RuntimeConfig


__version__ = "0.11.0a7"

logger = logging.getLogger(__name__)


def _set_process_priority():
    """Set process priority and scheduling parameters for optimal real-time performance."""
    if sys.platform == "win32":
        _set_process_priority_windows()
    # macOS/Linux: currently no action needed


def _set_process_priority_windows():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    handle = kernel32.GetCurrentProcess()

    # --- Process priority ---
    kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetPriorityClass.restype = wintypes.BOOL
    ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
    if kernel32.SetPriorityClass(handle, ABOVE_NORMAL_PRIORITY_CLASS):
        logger.info("Process priority set to ABOVE_NORMAL_PRIORITY_CLASS")
    else:
        logger.warning(
            f"Failed to set process priority: error {ctypes.GetLastError()}"
        )

    # --- Disable CPU execution speed throttling (Windows 11+) ---
    # Windows 11 applies EcoQoS (CPU frequency reduction / E-core scheduling)
    # to processes without visible windows. When the engine is launched with
    # CREATE_NO_WINDOW (e.g. from a GUI host app like nonoha-hub), this
    # throttling degrades asyncio event loop responsiveness and WebSocket
    # throughput. Explicitly opting out ensures consistent CPU performance.
    class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
        _fields_ = [
            ("Version", wintypes.ULONG),
            ("ControlMask", wintypes.ULONG),
            ("StateMask", wintypes.ULONG),
        ]

    state = PROCESS_POWER_THROTTLING_STATE()
    state.Version = 1  # PROCESS_POWER_THROTTLING_CURRENT_VERSION
    state.ControlMask = 0x1  # PROCESS_POWER_THROTTLING_EXECUTION_SPEED
    state.StateMask = 0  # 0 = disable throttling

    kernel32.SetProcessInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
    ]
    kernel32.SetProcessInformation.restype = wintypes.BOOL

    if kernel32.SetProcessInformation(
        handle,
        4,  # ProcessPowerThrottling
        ctypes.byref(state),
        ctypes.sizeof(state),
    ):
        logger.info("CPU execution speed throttling disabled")
    else:
        logger.warning(
            f"Failed to disable CPU throttling: error {ctypes.GetLastError()}"
        )


class EditorStaticFiles(StaticFiles):
    """StaticFiles with Cache-Control headers for Next.js static export."""

    def file_response(self, full_path, stat_result, scope, status_code=200):
        request_headers = Headers(scope=scope)
        response = FileResponse(full_path, status_code=status_code, stat_result=stat_result)

        # Cache-ControlをETag比較前に設定 → NotModifiedResponseにも引き継がれる
        path_str = str(full_path)
        if "/_next/static/" in path_str or "\\_next\\static\\" in path_str:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache"

        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response


class AppStaticFiles(StaticFiles):
    """StaticFiles with no-cache for VNF workspace app files."""

    def file_response(self, full_path, stat_result, scope, status_code=200):
        request_headers = Headers(scope=scope)
        response = FileResponse(full_path, status_code=status_code, stat_result=stat_result)
        response.headers["Cache-Control"] = "no-cache"

        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response


def _register_all_nodes(
    node_registry: NodeRegistry,
    plugin_host: PluginHost,
    runtime_config: RuntimeConfig,
    plugins_path: pathlib.Path | None = None,
):
    """Register all nodes: core, engine, builtin plugins, dynamic plugins."""
    # === Core Nodes ===
    nonoha_core.nodes.register_nodes(node_registry)

    # === Engine Nodes ===
    node_registry.register_node("HiResClock", clock_nodes.HiResClockNode)

    # scipy filter/resample nodes come from the shared sci-nodes package
    # (packages/sci-nodes submodule), also used by nonoha-embedded.
    sci_nodes.register_nodes(node_registry)

    node_registry.register_node("PortValuesSend", graph_nodes.PortValuesSendNode)

    node_registry.register_node("Record", record_nodes.RecordNode)
    node_registry.register_node("Replay", record_nodes.ReplayNode)
    node_registry.register_node("RotatingRecord", record_nodes.RotatingRecordNode)

    node_registry.register_node("Process", process_nodes.ProcessNode)

    # === Plugins ===
    if runtime_config.builtin_plugins:
        plugin_host.load_builtin_plugins(runtime_config.builtin_plugins, node_registry)

    if plugins_path is not None:
        plugin_host.load_plugins(plugins_path, node_registry)


async def _generate_app(
    node_registry: NodeRegistry,
    node_flow_instance: nonoha_engine.node_flow.node_flow.NodeFlow,
    engine_root_path: pathlib.Path,
    vnf_file_path: pathlib.Path,
    plugin_host: PluginHost,
    runtime_config: RuntimeConfig,
    plugins_path: pathlib.Path | None = None,
    editor_html_path: pathlib.Path | None = None,
) -> tuple[FastAPI, bool, bool]:  # Returns app, has_editor_html, has_app_html

    _register_all_nodes(node_registry, plugin_host, runtime_config, plugins_path)

    await node_flow_instance.load_node_flow_from_path(vnf_file_path)

    app = FastAPI()

    @app.get("/")
    async def get_root():
        return {
            "node_flow_url": "/node_flow",
        }

    app.include_router(
        nonoha_engine.node_flow.router.generate_router(node_flow_instance)
    )

    # app.include_router(nonoha_engine.webrtc_gateway.router.generate_router())

    has_editor_html = editor_html_path is not None and editor_html_path.exists()
    if has_editor_html:
        app.mount(
            "/editor",
            EditorStaticFiles(directory=editor_html_path, html=True),
            name="editor",
        )

    app_html_path = vnf_file_path / "app"
    has_app_html = app_html_path.exists()
    if has_app_html:
        app.mount(
            "/app",
            AppStaticFiles(directory=app_html_path, html=True),
            name="app",
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app, has_editor_html, has_app_html


def command_fbc(args):
    from nonoha_engine.file_binary_converts import file_binary_converts

    if args.command == "encode":
        with open(args.input_file, "r") as f:
            text = f.read()

        # start_time = time.time()
        encoded = file_binary_converts.encode(text)
        # end_time = time.time()
        # logging.info(f"Encoding time: {end_time - start_time}")
        with open(args.output_file, "wb") as f:
            f.write(encoded)
    elif args.command == "decode":
        with open(args.input_file, "rb") as f:
            data = f.read()
        decoded = file_binary_converts.decode(data)
        with open(args.output_file, "w") as f:
            f.write(decoded)


async def command_catalog(runtime_config: RuntimeConfig, args):
    """Write the node catalog as JSON to a file."""
    node_registry = NodeRegistry()
    plugin_host = PluginHost()

    plugins_path = (
        pathlib.Path(args.plugins_path) if args.plugins_path is not None else None
    )

    _register_all_nodes(node_registry, plugin_host, runtime_config, plugins_path)

    # Serialize catalog in the same format as GET /node-flow/catalog/nodes
    catalog = []
    for defn in node_registry.node_definitions.values():
        m = defn.metadata
        catalog.append(
            {
                "type": defn.type_name,
                "description": m.description,
                "category": m.category,
                "inputs": [
                    {
                        "name": p.name, "description": p.description, "types": p.value_types,
                        **({"value_names": p.value_names} if any(n is not None for n in p.value_names) else {}),
                    }
                    for p in m.inputs
                ],
                "outputs": [
                    {
                        "name": p.name, "description": p.description, "types": p.value_types,
                        **({"value_names": p.value_names} if any(n is not None for n in p.value_names) else {}),
                    }
                    for p in m.outputs
                ],
                "properties": {
                    name: {"default": prop.default, "description": prop.description}
                    for name, prop in m.properties.items()
                },
            }
        )

    output_path = pathlib.Path(args.output)
    output_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2))
    print(
        f"Catalog written to {output_path} ({len(catalog)} nodes)", file=sys.stderr
    )

    # Finalize plugins to ensure proper C++ extension cleanup
    await plugin_host.finalize()


def stdin_monitor(command_queue: queue.Queue, shutdown_event: threading.Event):
    """Monitor stdin for commands in a separate thread"""
    logging.info("Starting stdin monitor thread")
    while not shutdown_event.is_set():
        try:
            line = sys.stdin.readline()
            if not line:  # EOF (stdin closed or /dev/null)
                break
            command = line.strip()
            logging.info(f"Stdin command received: {command}")
            if command == "quit":
                logging.info("Shutdown command received from stdin")
                command_queue.put("shutdown")
                break
        except Exception as e:
            logging.error(f"Error reading stdin: {e}")
            break
    logging.info("Stdin monitor thread exiting")


async def main(runtime_config: RuntimeConfig):
    # Set up signal handler to convert SIGINT to graceful shutdown
    shutdown_event_signal = asyncio.Event()

    def signal_handler(signum, frame):
        logging.info(f"Signal {signum} received, initiating graceful shutdown...")
        shutdown_event_signal.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)  # CTRL+BREAK on Windows
    else:
        signal.signal(signal.SIGTERM, signal_handler)  # systemd stop etc.

    # Parse arguments first to get log level
    parser = argparse.ArgumentParser(
        description=f"nonoha engine v{__version__}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"nonoha-engine {__version__}",
        help="Show version information",
    )

    parser.add_argument(
        "--host",
        type=str,
        default=runtime_config.default_host,
        help="Bind socket to this host (0.0.0.0 for external access, 127.0.0.1 for local only)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=runtime_config.default_port,
        help="Port number to listen for connections",
    )

    parser.add_argument(
        "--vnf",
        type=str,
        default=None,
        help="VNF file path",
        dest="vnf_file_path",
    )

    parser.add_argument(
        "--plugins",
        type=str,
        default=None,
        help="Path to the plugins directory",
        dest="plugins_path",
    )

    parser.add_argument(
        "--editor-html",
        type=str,
        default=None,
        help="Path to the editor_html directory (overrides auto-detection from engine root)",
        dest="editor_html_path",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
        dest="log_level",
    )

    parser.add_argument(
        "--debug-save-log",
        action="store_true",
        help="Save logs to file automatically for debugging (logs/nonoha_engine_YYYYMMDD_HHMMSS_PID.log)",
        dest="debug_save_log",
    )

    parser.add_argument(
        "--readonly",
        action="store_true",
        help="Read-only mode: changes are not persisted to disk",
    )

    subparsers = parser.add_subparsers(dest="subparser")

    if runtime_config.includes_fbc_commands:
        parser_fbc = subparsers.add_parser("fbc", help="VIE File Binary utils")
        parser_fbc.add_argument(
            "command",
            choices=["encode", "decode"],
            help="Command to execute",
        )
        parser_fbc.add_argument(
            "input_file",
            help="Input file to encode/decode",
        )
        parser_fbc.add_argument(
            "output_file",
            help="Output file to encode/decode",
        )

    catalog_parser = subparsers.add_parser(
        "catalog",
        help="Write node catalog as JSON to a file",
    )
    catalog_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path for JSON catalog",
    )

    args = parser.parse_args()

    # === Subcommand early dispatch (before server initialization) ===
    if args.subparser == "catalog":
        await command_catalog(runtime_config, args)
        return
    if runtime_config.includes_fbc_commands and args.subparser == "fbc":
        command_fbc(args)
        return

    # === Server initialization below ===

    # Set up logging with the specified level
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
    handlers = []

    # Console handler - always enabled
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, args.log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler - only if --debug-save-log is specified
    if args.debug_save_log:
        # Create logs directory
        log_dir = pathlib.Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Generate automatic log file name with timestamp and PID
        log_file_name = (
            f"nonoha_engine_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.log"
        )
        log_file_path = log_dir / log_file_name

        # File handler - uses the same log level as console
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, args.log_level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

        # Log to console that we're logging to file
        print(f"Debug logging enabled: {log_file_path.absolute()}")

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()), handlers=handlers
    )

    # Set process priority for optimal real-time performance
    if runtime_config.auto_set_process_priority:
        _set_process_priority()

    engine_root_path = pathlib.Path(sys.argv[0]).parent

    # Resolve editor_html path: CLI argument takes priority, fallback to engine_root_path/editor_html
    if args.editor_html_path is not None:
        editor_html_path = pathlib.Path(args.editor_html_path)
    else:
        editor_html_path = engine_root_path / "editor_html"

    # Set default VNF file path if not provided
    if args.vnf_file_path is None:
        args.vnf_file_path = str(engine_root_path / "flows/default.vnf")

    logging.info(f"nonoha-engine v{__version__}")
    logging.info(f"Engine root path: {engine_root_path}")
    # logging.info(f"{sys.argv}")
    # print(sys.getrecursionlimit())

    logging.info(f"Process ID: {os.getpid()}")

    node_registry = NodeRegistry()
    node_flow_instance = nonoha_engine.node_flow.node_flow.NodeFlow(node_registry)
    node_flow_instance.readonly = args.readonly
    if args.readonly:
        logging.info("Read-only mode enabled")

    plugin_host = PluginHost()

    # Create command queue and shutdown event for stdin monitoring
    command_queue = queue.Queue()
    shutdown_event = threading.Event()

    # Start stdin monitor thread as daemon
    # Daemon thread will automatically terminate when main program exits
    stdin_thread = threading.Thread(
        target=stdin_monitor,
        args=(command_queue, shutdown_event),
        daemon=True,  # Important: daemon thread won't block program exit
    )
    stdin_thread.start()

    server = None
    try:
        app, has_editor_html, has_app_html = await _generate_app(
            node_registry,
            node_flow_instance,
            engine_root_path,
            pathlib.Path(args.vnf_file_path),
            plugin_host,
            runtime_config,
            pathlib.Path(args.plugins_path) if args.plugins_path else None,
            editor_html_path=editor_html_path,
        )
        config = uvicorn.Config(
            app,
            host=args.host,
            port=args.port,
            loop="asyncio",
            ws="websockets-sansio",
            ws_per_message_deflate=False,
        )
        server = uvicorn.Server(config)

        # Start server task
        server_task = asyncio.create_task(server.serve())

        # Wait for server to be ready to get actual port
        while not server.started:
            await asyncio.sleep(0.1)

        # Cleanup stale .trash and .uploads in all graph data dirs
        for graph in node_flow_instance.graphs.values():
            storage = graph.data_storage
            if storage is None:
                continue
            asyncio.create_task(asyncio.to_thread(storage.purge_stale))

        # Get actual port (important when args.port is 0)
        actual_port = args.port
        if server.servers and server.servers[0].sockets:
            actual_port = server.servers[0].sockets[0].getsockname()[1]

        server_uri = f"{args.host}:{actual_port}"
        # Use 127.0.0.1 for inspector when binding to all interfaces (0.0.0.0)
        inspector_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
        inspector_uri = f"{inspector_host}:{actual_port}"

        logger.info(
            f"\n"
            f"═════════════════════════════════════════════\n"
            f"nonoha-engine v{__version__}\n"
            f"─────────────────────────────────────────────\n"
            f"API Server:\n"
            f"  • Binding: http://{server_uri}\n"
            + (
                f"─────────────────────────────────────────────\n"
                f"Inspector GUI:\n"
                f"  • http://{inspector_uri}/editor?engine-uri={inspector_uri}\n"
                if has_editor_html
                else ""
            )
            + (
                f"─────────────────────────────────────────────\n"
                f"Custom App:\n"
                f"  • http://{inspector_uri}/app\n"
                if has_app_html
                else ""
            )
            + f"─────────────────────────────────────────────\n"
            f"Press Ctrl+C to stop\n"
            f"═════════════════════════════════════════════\n"
        )

        # Check for shutdown commands while server is running
        while not server_task.done():
            # Check for signal-based shutdown
            if shutdown_event_signal.is_set():
                logging.info("Shutdown signal received, stopping server...")
                server.should_exit = True
                break

            # Check for stdin command
            try:
                # Check command queue with timeout
                command = command_queue.get_nowait()
                if command == "shutdown":
                    logging.info("Initiating graceful shutdown from stdin command...")
                    server.should_exit = True
                    break
            except queue.Empty:
                pass

            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.1)

        # Wait for server to finish
        try:
            await server_task
        except asyncio.CancelledError:
            logging.info("Server task cancelled")
            raise
    except KeyboardInterrupt:
        logging.info("main() - KeyboardInterrupt")
    except asyncio.CancelledError:
        logging.info("main() - asyncio.CancelledError")
    except BaseException as e:
        logging.error(f"main() - Unexpected error: {e}")
        logging.error(traceback.format_exc())
    except:
        logging.error("main() - Unknown error occurred")
    finally:
        # Signal stdin thread to stop
        shutdown_event.set()

        logging.info("Exiting main(). See you ;)")
        logging.info("Finalizing... please wait.")

        node_flow_instance.finalize()
        await plugin_host.finalize()
        logging.info("Finishing... please wait")

        await asyncio.sleep(3)

        logging.info("Finished. Bye ;)")

    # sys.exit(0)


def run(runtime_config: RuntimeConfig):
    loop = asyncio.get_event_loop()

    try:
        # asyncio.run(main()) # <- 終了時に非同期のfinalize()がすべて実行されない.
        loop.run_until_complete(main(runtime_config))
    except KeyboardInterrupt:
        logging.info("run() - KeyboardInterrupt")
        pass

    logger.info("run() - Exit")
