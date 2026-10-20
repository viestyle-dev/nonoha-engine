from dataclasses import dataclass
from typing import Any

@dataclass
class RuntimeConfig:
    includes_fbc_commands: bool = False
    default_host: str = "127.0.0.1"
    default_port: int = 8000
    builtin_plugins: tuple = () # modules
    auto_set_process_priority: bool = True
