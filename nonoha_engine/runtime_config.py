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
    # The folder holding the app's files: flows/default.vnf, editor_html/
    # and plugins/ are found under it unless --vnf, --editor-html or
    # --plugins name them. None: the folder of the program that was started
    # (sys.argv[0]). A launcher that can be started by name from PATH (where
    # argv[0] is a bare name) states it, so the engine never reads those
    # from the current directory.
    app_dir: str | None = None
    # Extra browser origins ("https://dash.example.com") and host names
    # (".ngrok-free.app" = the domain and its subdomains) the request guard
    # accepts. --allow-origin / --allow-host add to them.
    allow_origins: tuple[str, ...] = ()
    allow_hosts: tuple[str, ...] = ()
    # The .env with this deployment's environment values (--env-file
    # overrides). None: with app_id, <per-user dir>/nonoha/apps/<app_id>/.env;
    # without, no .env at all (the OS environment only). An app that is
    # distributed sets app_id (or env_file), so its users' keys never sit
    # next to the executable.
    env_file: str | None = None
    # An app's identity ([A-Za-z0-9._-]); picks its per-user folder
    app_id: str | None = None
