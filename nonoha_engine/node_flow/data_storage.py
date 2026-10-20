import errno
import json
import os
import pathlib
import shutil
import time
import uuid
from collections.abc import Iterator


def purge_trash_entry(path: pathlib.Path) -> None:
    """Remove a trash entry (file or directory).

    Used by background purge tasks — errors are swallowed since the caller
    has already returned a 204 to the user. shutil.rmtree only handles
    directories, so files need explicit unlink.
    """
    try:
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


class DataStorage:
    HIDDEN_DIRS = frozenset({".trash", ".uploads"})
    MAX_CHUNK_SIZE = 8 * 1024 * 1024
    DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self, data_dir: pathlib.Path, *, readonly: bool = False):
        self._data_dir = data_dir
        self._readonly = readonly

    @property
    def data_dir(self) -> pathlib.Path:
        return self._data_dir

    @property
    def readonly(self) -> bool:
        return self._readonly

    def _check_writable(self) -> None:
        if self._readonly:
            raise PermissionError("Data storage is read-only")

    def validate_path(self, file_path: str, *, writable: bool = False) -> pathlib.Path:
        parts = file_path.split("/") if file_path else []
        if ".." in parts:
            raise ValueError("Invalid path")
        if any(p in self.HIDDEN_DIRS for p in parts):
            raise ValueError("Invalid path")
        if writable:
            if any(p == "" for p in parts) and file_path:
                raise ValueError("Invalid path")
            if parts and parts[-1] in (".", ".."):
                raise ValueError("Invalid path")
        target = (self._data_dir / file_path).resolve()
        if not str(target).startswith(str(self._data_dir.resolve())):
            raise ValueError("Invalid path")
        return target

    def list_directory(self, target: pathlib.Path, file_path: str) -> dict:
        if not target.exists():
            return {"type": "directory", "path": file_path, "entries": []}
        entries = []
        for entry in sorted(target.iterdir(), key=lambda e: e.name):
            if entry.name in self.HIDDEN_DIRS:
                continue
            if entry.is_dir():
                entries.append({"name": entry.name, "type": "directory"})
            elif entry.is_file():
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "type": "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
        return {"type": "directory", "path": file_path, "entries": entries}

    def get_file_info(
        self, target: pathlib.Path, graph_name: str, file_path: str
    ) -> dict:
        stat = target.stat()
        rel_path = file_path if file_path else target.name
        return {
            "type": "file",
            "name": target.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "download_url": f"/node-flow/graphs/{graph_name}/data/{rel_path}?raw",
        }

    def trash_move(self, target: pathlib.Path) -> pathlib.Path:
        self._check_writable()
        trash_dir = self._data_dir / ".trash"
        trash_name = f"{int(time.time())}-{uuid.uuid4().hex}-{target.name}"
        trash_target = trash_dir / trash_name
        trash_dir.mkdir(parents=True, exist_ok=True)
        try:
            target.rename(trash_target)
        except OSError as e:
            if e.errno == errno.EXDEV:
                raise
            raise
        return trash_target

    def abort_upload(self, upload_id: str) -> bool:
        self._check_writable()
        uploads_dir = self._data_dir / ".uploads"
        meta_path = uploads_dir / f"{upload_id}.meta.json"
        tmp_path = uploads_dir / f"{upload_id}.tmp"
        if not meta_path.exists():
            return False
        tmp_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        return True

    def create_directory(self, target: pathlib.Path) -> dict:
        self._check_writable()
        if target.exists():
            raise FileExistsError("Already exists")
        try:
            target.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise FileExistsError("Already exists")
        rel = target.relative_to(self._data_dir.resolve()).as_posix()
        return {"type": "directory", "name": target.name, "path": rel}

    def write_file_atomic(
        self,
        target: pathlib.Path,
        source_file,
        *,
        overwrite: bool = False,
    ) -> tuple[dict, bool]:
        self._check_writable()
        is_existing = target.exists()
        if is_existing:
            if target.is_dir():
                raise IsADirectoryError("Target is a directory")
            if target.is_file() and not overwrite:
                raise FileExistsError("File exists; pass ?overwrite=true")

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_name = f".upload-{uuid.uuid4().hex}.tmp"
        tmp_path = target.parent / tmp_name
        try:
            with open(tmp_path, "wb") as out:
                shutil.copyfileobj(source_file, out, length=1 << 20)
            os.replace(str(tmp_path), str(target))
        except BaseException:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        stat = target.stat()
        is_overwrite = is_existing and target.is_file()
        return (
            {
                "type": "file",
                "name": target.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            },
            is_overwrite,
        )

    def init_resumable(
        self, target: pathlib.Path, file_path: str, size: int, overwrite: bool
    ) -> dict:
        self._check_writable()
        is_existing = target.exists()
        if is_existing and not overwrite:
            if target.is_file():
                raise FileExistsError("File exists; pass ?overwrite=true")
            if target.is_dir():
                raise IsADirectoryError("Target is a directory")

        new_upload_id = uuid.uuid4().hex
        uploads_dir = self._data_dir / ".uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        (uploads_dir / f"{new_upload_id}.tmp").touch()
        with open(uploads_dir / f"{new_upload_id}.meta.json", "w") as f:
            json.dump(
                {
                    "target_path": file_path,
                    "size": size,
                    "overwrite": overwrite,
                    "created_at": time.time(),
                },
                f,
            )
        return {"upload_id": new_upload_id, "chunk_size": self.DEFAULT_CHUNK_SIZE}

    def write_chunk(self, upload_id: str, offset: int, data: bytes) -> int:
        self._check_writable()
        uploads_dir = self._data_dir / ".uploads"
        meta_path = uploads_dir / f"{upload_id}.meta.json"
        if not meta_path.exists():
            raise FileNotFoundError("Upload session not found")
        if len(data) > self.MAX_CHUNK_SIZE:
            raise ValueError(f"Chunk too large: max {self.MAX_CHUNK_SIZE} bytes")
        tmp_path = uploads_dir / f"{upload_id}.tmp"
        current_size = tmp_path.stat().st_size
        if offset != current_size:
            raise ValueError(f"Expected offset {current_size}, got {offset}")
        with open(tmp_path, "r+b") as f:
            f.seek(offset)
            f.write(data)
        return tmp_path.stat().st_size

    def complete_resumable(self, upload_id: str) -> tuple[dict, bool]:
        self._check_writable()
        uploads_dir = self._data_dir / ".uploads"
        meta_path = uploads_dir / f"{upload_id}.meta.json"
        tmp_path = uploads_dir / f"{upload_id}.tmp"
        if not meta_path.exists():
            raise FileNotFoundError("Upload session not found")

        with open(meta_path) as f:
            meta = json.load(f)
        expected_size = meta["size"]
        overwrite = meta["overwrite"]
        target_path_str = meta["target_path"]
        actual_size = tmp_path.stat().st_size
        if actual_size != expected_size:
            raise ValueError(
                f"Incomplete upload: expected {expected_size} bytes, got {actual_size}"
            )
        target = (self._data_dir / target_path_str).resolve()
        is_overwrite = target.exists() and target.is_file()
        if target.exists() and not overwrite:
            raise FileExistsError("File exists; pass ?overwrite=true")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(tmp_path), str(target))
        meta_path.unlink(missing_ok=True)
        stat = target.stat()
        return (
            {
                "type": "file",
                "name": target.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            },
            is_overwrite,
        )

    def get_upload_offset(self, upload_id: str) -> int | None:
        uploads_dir = self._data_dir / ".uploads"
        meta_path = uploads_dir / f"{upload_id}.meta.json"
        tmp_path = uploads_dir / f"{upload_id}.tmp"
        if not meta_path.exists():
            return None
        return tmp_path.stat().st_size

    def purge_stale(self, uploads_max_age: float = 86400) -> int:
        """Synchronously remove stale .trash and .uploads entries.

        Returns count of removed entries. Wrap in asyncio.to_thread() if
        non-blocking is needed.
        """
        count = 0
        for path in self._iter_stale(uploads_max_age):
            purge_trash_entry(path)
            count += 1
        return count

    def _iter_stale(self, uploads_max_age: float) -> Iterator[pathlib.Path]:
        """Internal: yield paths eligible for cleanup."""
        if not self._data_dir.exists():
            return
        for hidden_name in (".trash", ".uploads"):
            hidden_dir = self._data_dir / hidden_name
            if not hidden_dir.is_dir():
                continue
            cutoff = time.time() - uploads_max_age
            for entry in list(hidden_dir.iterdir()):
                if hidden_name == ".trash" or entry.stat().st_mtime < cutoff:
                    yield entry
