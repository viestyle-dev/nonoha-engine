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
    # Extra browser origins ("https://dash.example.com") and host names
    # (".ngrok-free.app" = the domain and its subdomains) the request guard
    # accepts. --allow-origin / --allow-host add to them.
    allow_origins: tuple[str, ...] = ()
    allow_hosts: tuple[str, ...] = ()
    # The .env with this deployment's environment values. None: a built app
    # with app_id uses <per-user dir>/nonoha/apps/<app_id>/.env; development
    # uses <workspace>/.env (above the flows/ folder). --env-file overrides.
    env_file: str | None = None
    # A built app's identity ([A-Za-z0-9._-]); picks its per-user folder
    app_id: str | None = None
