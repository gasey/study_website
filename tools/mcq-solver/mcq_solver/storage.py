"""Owner-only state, atomic writes and Unix process locks."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from .errors import SolverError


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def private_dir(path: Path):
    if path.is_symlink():
        raise SolverError("unsafe_path")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    s = path.stat()
    if s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) & 0o077:
        raise SolverError("unsafe_permissions")


def read_private(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as f:
        s = os.fstat(f.fileno())
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) & 0o077:
            raise SolverError("unsafe_permissions")
        return json.load(f)


def atomic_json(path: Path, data):
    private_dir(path.parent)
    if path.is_symlink():
        raise SolverError("unsafe_path")
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(path: Path, *, blocking=True):
    private_dir(path.parent)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            raise SolverError("worker_busy") from None
        yield
    finally:
        os.close(fd)
