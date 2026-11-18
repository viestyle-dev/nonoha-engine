"""Environment values of a running engine: load the ``.env``, report and change it.

Values never leave the engine: the status lists names and where a value
comes from, never the value. Writes accept only names a node of a loaded
graph declares (``NodeDoc.env``), not reserved names, and not names the OS
environment already sets (it wins, as with dotenv).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nonoha_core import environment

from . import env_file

logger = logging.getLogger(__name__)


class EnvSettingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass
class Declared:
    description: str = ""
    url: str = ""
    declared_by: list[str] = field(default_factory=list)


def declared_env(node_flow: Any) -> dict[str, Declared]:
    """Names the nodes of loaded graphs declare with their current properties."""
    declared: dict[str, Declared] = {}
    for graph_name in node_flow.graph_names:
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            continue
        for node in graph.nodes.values():
            try:
                doc = type(node).describe(node.properties)
            except Exception:  # a node's docs must not break the status
                logger.debug(f"describe() failed for {graph_name}/{node.name}", exc_info=True)
                continue
            if doc is None:
                continue
            for env in doc.env:
                entry = declared.get(env.name)
                if entry is None:
                    entry = declared[env.name] = Declared(env.description, env.url)
                entry.declared_by.append(f"{graph_name}/{node.name}")
    return declared


class EnvSettings:
    """The engine's ``.env``: loaded once at start, then changed by clients.

    A write goes in three steps so the file I/O can leave the event loop:
    ``require_write`` (checks, on the loop: it reads the declared names),
    ``env_file.write_value`` (the file, in a thread), ``apply_write`` (what
    nodes read, on the loop).
    """

    def __init__(self, path: Path | None, readonly: bool = False):
        self.path = path
        self.readonly = readonly  # --readonly: the file is never changed
        self._from_file: set[str] = set()  # put into os.environ at start
        self._file_names: set[str] = set()  # defined in the file, as last read or written
        self._read_error: str | None = None  # the file exists but could not be read

    def load_into_process(self) -> None:
        """At start, before plugins load and threads run: file -> os.environ.

        Names the OS already sets win and are left alone.
        """
        if self.path is None:
            logger.info("Environment file: none")
            return
        try:
            values = env_file.read(self.path)
        except env_file.EnvFileError as e:
            # The engine starts without it; the file is left untouched
            self._read_error = str(e)
            logger.warning(f"{e}: starting without its values")
            return
        self._file_names = set(values)
        for name, value in values.items():
            if name in os.environ:
                continue
            os.environ[name] = value
            self._from_file.add(name)
        logger.info(f"Environment file: {self.path} ({len(values)} value(s))")

    # --- status ---

    def _set_by_os(self, name: str) -> bool:
        return name in os.environ and name not in self._from_file

    def file_is_writable(self) -> bool:
        return (
            self.path is not None
            and not self.readonly
            and self._read_error is None
            and env_file.is_writable(self.path)
        )

    def status(self, declared: dict[str, Declared]) -> dict:
        file_writable = self.file_is_writable()
        names = sorted(set(declared) | self._file_names)
        items = []
        for name in names:
            info = declared.get(name, Declared())
            set_ = environment.get(name) is not None
            if self._set_by_os(name):
                source = "os"
            elif set_:
                source = "file"
            else:
                source = "none"
            reason = self._write_refusal(name, declared, file_writable)
            items.append(
                {
                    "name": name,
                    "description": info.description,
                    "url": info.url,
                    "declared_by": info.declared_by,
                    "set": set_,
                    "source": source,
                    "writable": reason is None,
                    **({"reason": reason} if reason else {}),
                }
            )
        return {
            "file": str(self.path) if self.path is not None else None,
            "writable": file_writable,
            "items": items,
        }

    def _write_refusal(self, name: str, declared: dict[str, Declared], file_writable: bool) -> str | None:
        reason = environment.name_refusal(name)
        if reason:
            return reason
        if name not in declared:
            return "No node in the loaded graphs uses this name"
        if self._set_by_os(name):
            return "Set in the OS environment, which takes precedence"
        if self.path is None:
            return "This engine has no environment file"
        if self.readonly:
            return "Read-only mode (--readonly): the environment file is not changed"
        if self._read_error is not None:
            return self._read_error
        if not file_writable:
            return "The environment file is read-only"
        return None

    # --- changes ---

    def require_write(self, name: str, value: str | None, declared: dict[str, Declared]) -> Path:
        """The file to write ``name`` into, or ``EnvSettingError`` saying why
        not. Reads only memory: runs on the event loop."""
        reason = environment.name_refusal(name)
        if reason:
            raise EnvSettingError(400, reason)
        if value is not None:
            reason = environment.value_refusal(value)
            if reason:
                raise EnvSettingError(400, reason)
        reason = self._write_refusal(name, declared, self.file_is_writable())
        if reason:
            raise EnvSettingError(409 if self.path is None or self._read_error else 403, reason)
        assert self.path is not None
        return self.path

    def apply_write(self, name: str, value: str | None) -> None:
        """After the file was written: nodes see the change."""
        environment.update({name: value})
        if value is None:
            self._file_names.discard(name)
        else:
            self._file_names.add(name)
        logger.info(f"Environment value {name} {'set' if value is not None else 'removed'} ({self.path})")

    def set_value(self, name: str, value: str, declared: dict[str, Declared]) -> None:
        """Store ``value`` for ``name`` (all three steps, here)."""
        self._write(name, value, declared)

    def remove_value(self, name: str, declared: dict[str, Declared]) -> None:
        """Remove ``name`` from the file; nodes then read it as unset."""
        self._write(name, None, declared)

    def _write(self, name: str, value: str | None, declared: dict[str, Declared]) -> None:
        path = self.require_write(name, value, declared)
        try:
            env_file.write_value(path, name, value)
        except env_file.EnvFileError as e:
            raise EnvSettingError(409, str(e)) from None
        self.apply_write(name, value)
