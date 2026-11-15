from dataclasses import dataclass
from typing import Any

@dataclass
class RuntimeConfig:
    includes_fbc_commands: bool = False
    default_host: str = "127.0.0.1"
    default_port: int = 8000
    builtin_plugins: tuple = () # modules
    auto_set_process_priority: bool = True
    # Inspector WebSocket endpoint (live port sampling for editors). The
    # --inspector command-line option overrides it.
    inspector_enabled: bool = True
    # Where built-in plugins' static folders live in a frozen build
    # (<dir>/<plugin_id>/). None = <engine root>/plugin_static.
    plugin_static_path: str | None = None
