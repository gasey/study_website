#!/usr/bin/env python3
"""Losslessly gzip old review snapshots after verifying their SHA-256 names.

Keeps the newest N plain JSON backups untouched. For every older snapshot,
write and fsync a temporary gzip archive, verify its decompressed SHA-256,
atomically install the archive, and only then remove the original JSON file.
Existing gzip archives are validated before duplicate JSON files are removed.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


HASH = re.compile(r"^[0-9a-f]{64}$")


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest_gzip(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def archive_one(raw: Path, *, dry_run: bool) -> dict:
    expected = raw.stem
    if not HASH.fullmatch(expected):
        raise ValueError(f"Not a SHA-256-named snapshot: {raw.name}")
    archived = raw.with_suffix(".json.gz")
    if dry_run:
        return {"file": raw.name,
                "action": "remove-verified-duplicate" if archived.exists() else "compress",
                "bytes": raw.stat().st_size}

    if archived.exists():
        if digest_file(raw) != expected:
            raise ValueError(f"Snapshot content does not match its SHA-256 name: {raw.name}")
        if digest_gzip(archived) != expected:
            raise ValueError(f"Existing gzip archive failed SHA-256 validation: {archived.name}")
        size = raw.stat().st_size
        raw.unlink()
        return {"file": raw.name, "action": "removed-verified-duplicate", "bytes": size}

    fd, tmp_name = tempfile.mkstemp(prefix=f".{expected}.", suffix=".tmp", dir=raw.parent)
    tmp = Path(tmp_name)
    try:
        raw_hash = hashlib.sha256()
        with os.fdopen(fd, "wb") as target, raw.open("rb") as source:
            with gzip.GzipFile(fileobj=target, mode="wb", compresslevel=3, mtime=0) as zipped:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    raw_hash.update(block)
                    zipped.write(block)
            target.flush()
            os.fsync(target.fileno())
        if raw_hash.hexdigest() != expected:
            raise ValueError(f"Snapshot content does not match its SHA-256 name: {raw.name}")
        if digest_gzip(tmp) != expected:
            raise ValueError(f"Compressed archive failed SHA-256 validation: {raw.name}")
        os.replace(tmp, archived)
        raw_size = raw.stat().st_size
        raw.unlink()
        dir_fd = os.open(raw.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        return {"file": raw.name, "action": "compressed", "bytes": raw_size,
                "archive_bytes": archived.stat().st_size}
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_dir", type=Path)
    parser.add_argument("--keep-latest", type=int, default=10,
                        help="leave this many newest raw JSON snapshots untouched")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.keep_latest < 0:
        parser.error("--keep-latest must be non-negative")
    directory = args.backup_dir.resolve()
    if not directory.is_dir():
        parser.error(f"Not a backup directory: {directory}")
    raw_files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    keep = set(raw_files[:args.keep_latest])
    actions = []
    for raw in reversed(raw_files):
        if raw in keep:
            continue
        actions.append(archive_one(raw, dry_run=args.dry_run))
    print(json.dumps({"backup_dir": str(directory), "dry_run": args.dry_run,
                      "kept_raw": len(keep), "processed": len(actions),
                      "bytes_reclaimable_or_reclaimed": sum(a["bytes"] for a in actions),
                      "actions": actions}, indent=2))


if __name__ == "__main__":
    main()
