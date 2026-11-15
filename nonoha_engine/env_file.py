"""The ``.env`` file: where a deployment keeps its environment values.

Grammar (a common dotenv subset; the Hub and CLI implement the same):

- blank lines and lines starting with ``#`` are kept as they are
- ``[export ]NAME=VALUE`` with ``NAME`` matching ``[A-Za-z_][A-Za-z0-9_]*``
- ``VALUE`` is ``"double quoted"`` (escapes ``\\\\ \\" \\n \\r \\t``),
  ``'single quoted'`` (literal) or unquoted (up to `` #``, trimmed)
- no ``${VAR}`` interpolation; the last definition of a name wins

Writes change only the line of one name, keep every other line, and go
through a temporary file and ``os.replace`` so a crash never leaves a torn
file. On POSIX the file is created ``0600``.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_LINE = re.compile(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)")
_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}
APP_ID = re.compile(r"[A-Za-z0-9._-]+")


class EnvFileError(Exception):
    """The file could not be written (read-only file system, permissions)."""


def _parse_value(raw: str) -> str:
    text = raw.strip()
    if text.startswith('"'):
        out: list[str] = []
        i = 1
        while i < len(text):
            ch = text[i]
            if ch == "\\" and i + 1 < len(text):
                nxt = text[i + 1]
                out.append(_ESCAPES.get(nxt, "\\" + nxt))
                i += 2
                continue
            if ch == '"':
                break
            out.append(ch)
            i += 1
        return "".join(out)
    if text.startswith("'"):
        end = text.find("'", 1)
        return text[1:end] if end > 0 else text[1:]
    comment = text.find(" #")
    if comment >= 0:
        text = text[:comment]
    return text.rstrip()


def _line_name(line: str) -> str | None:
    match = _LINE.match(line)
    return match.group(1) if match else None


def parse(text: str) -> dict[str, str]:
    """Name -> value for every definition in ``text`` (the last one wins)."""
    values: dict[str, str] = {}
    for line in text.lstrip("﻿").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _LINE.match(line)
        if match:
            values[match.group(1)] = _parse_value(match.group(2))
    return values


def read(path: Path) -> dict[str, str]:
    """The values in ``path``; empty when it does not exist."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    return parse(text)


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def rewrite(text: str, name: str, value: str | None) -> str:
    """``text`` with ``name`` set to ``value`` (None removes it); other lines kept."""
    lines = text.lstrip("﻿").splitlines()
    out: list[str] = []
    placed = False
    for line in lines:
        if _line_name(line) == name and not line.strip().startswith("#"):
            if value is not None and not placed:
                out.append(f"{name}={quote(value)}")
                placed = True
            continue  # drop the old definition and later duplicates
        out.append(line)
    if value is not None and not placed:
        out.append(f"{name}={quote(value)}")
    return "\n".join(out) + "\n" if out else ""


def write_value(path: Path, name: str, value: str | None) -> None:
    """Set (or remove) one name in ``path`` atomically."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            text = ""
        data = rewrite(text, name, value).encode("utf-8")
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise
        if sys.platform != "win32":
            os.chmod(path, 0o600)
    except OSError as e:
        raise EnvFileError(f"Cannot write {path}: {e.strerror or e}") from None


def is_writable(path: Path) -> bool:
    """Whether ``path`` can be written (or created) by this process."""
    if path.exists():
        return os.access(path, os.W_OK) and os.access(path.parent, os.W_OK)
    parent = path.parent
    while not parent.exists():
        if parent.parent == parent:
            return False
        parent = parent.parent
    return os.access(parent, os.W_OK)


def per_user_dir() -> Path:
    """Where built apps keep per-user files: ``<base>/nonoha/apps``."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = xdg if os.path.isabs(xdg) else str(Path.home() / ".config")
    return Path(base) / "nonoha" / "apps"


def resolve(
    explicit: str | None,
    app_id: str | None,
    vnf_path: Path,
    frozen: bool,
) -> Path | None:
    """The one ``.env`` this engine uses, or None.

    1. an explicit path (``--env-file``, ``RuntimeConfig.env_file``)
    2. a built app: ``<per-user dir>/<app_id>/.env``, never next to the
       executable (a zipped build would ship the user's keys)
    3. development: the workspace root above the ``flows/`` folder holding
       the VNF. The working directory is never searched, so starting the
       engine elsewhere cannot pick up an unrelated ``.env``.
    """
    if explicit:
        return Path(explicit).expanduser().resolve()
    if app_id:
        if not APP_ID.fullmatch(app_id) or app_id in (".", ".."):
            raise ValueError(f"Invalid app_id {app_id!r}: use letters, digits, '.', '_' and '-'")
        return per_user_dir() / app_id / ".env"
    if frozen:
        return None
    vnf = vnf_path.resolve()
    if vnf.parent.name == "flows":
        return vnf.parent.parent / ".env"
    return None
