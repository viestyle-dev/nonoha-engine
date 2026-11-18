"""The ``.env`` file: where a deployment keeps its environment values.

Grammar (a common dotenv subset; the Hub and CLI implement the same):

- blank lines and lines starting with ``#`` are kept as they are
- ``[export ]NAME=VALUE`` with ``NAME`` matching ``[A-Za-z_][A-Za-z0-9_]*``
- ``VALUE`` is ``"double quoted"`` (escapes ``\\\\ \\" \\n \\r \\t``),
  ``'single quoted'`` (literal) or unquoted (up to `` #``, trimmed)
- no ``${VAR}`` interpolation; the last definition of a name wins

Writes change only the line of one name, keep every other line, and go
through a temporary file and ``os.replace`` so a crash never leaves a torn
file. On POSIX the file is created ``0600``. A write that changes nothing
writes nothing; a symbolic link is followed (its target is replaced).
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

_LINE = re.compile(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)")
_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}
APP_ID = re.compile(r"[A-Za-z0-9._-]+")


class EnvFileError(Exception):
    """The file could not be read (not UTF-8, a folder, permissions) or
    written (read-only file system, permissions)."""


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


def _read_text(path: Path) -> str:
    """The file's text; "" when it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        raise EnvFileError(f"Cannot read {path}: not UTF-8 (save it as UTF-8)") from None
    except OSError as e:
        raise EnvFileError(f"Cannot read {path}: {e.strerror or e}") from None


def read(path: Path) -> dict[str, str]:
    """The values in ``path``; empty when it does not exist."""
    return parse(_read_text(path))


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


def write_value(path: Path, name: str, value: str | None) -> bool:
    """Set (or remove) one name in ``path`` atomically; False when that
    changes nothing (then nothing is written, nor any folder made)."""
    if path.is_symlink():
        path = path.resolve()
    text = _read_text(path)  # a file that cannot be read is never overwritten
    new_text = rewrite(text, name, value)
    if new_text == text:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # A new, uniquely named file (O_EXCL; 0600 on POSIX): never a
        # leftover of a crashed writer, never shared with another writer
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(new_text.encode("utf-8"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise
    except OSError as e:
        raise EnvFileError(f"Cannot write {path}: {e.strerror or e}") from None
    return True


def is_writable(path: Path) -> bool:
    """Whether ``path`` can be written (or created) by this process.

    On Windows ``os.access`` checks the read-only attribute, not the ACL: a
    file it calls writable can still refuse the write, which then fails with
    its reason (``EnvFileError``).
    """
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
        # Always ~/.config, not $XDG_CONFIG_HOME: set only in an interactive
        # shell, it would move the keys depending on how the app was started
        # (a terminal or a service). --env-file chooses another place.
        base = str(Path.home() / ".config")
    return Path(base) / "nonoha" / "apps"


def resolve(explicit: str | None, app_id: str | None) -> Path | None:
    """The one ``.env`` this engine uses, or None.

    1. an explicit path (``--env-file``, ``RuntimeConfig.env_file``)
    2. an app with ``app_id``: ``<per-user dir>/<app_id>/.env``, never next
       to the executable (a zipped build would ship the user's keys)
    3. otherwise none: the engine does not guess (a workspace's launcher
       passes ``--env-file <workspace>/.env``)
    """
    if explicit:
        return Path(explicit).expanduser().resolve()
    if app_id:
        if not APP_ID.fullmatch(app_id) or app_id in (".", ".."):
            raise ValueError(f"Invalid app_id {app_id!r}: use letters, digits, '.', '_' and '-'")
        return per_user_dir() / app_id / ".env"
    return None
