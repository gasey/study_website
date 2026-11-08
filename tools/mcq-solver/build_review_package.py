#!/usr/bin/env python3
"""Build an allowlisted, portable source ZIP; never traverses runtime state."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent


def contents(root=ROOT):
    files = {}
    for name in ('LICENSE', 'pyproject.toml', 'requirements.lock', 'config.example.toml', '.env.example', '.gitignore'):
        files[name] = (root / name).read_bytes()
    files['README.md'] = (root / 'standalone/README.md').read_bytes()
    for folder in ('mcq_solver', 'tests'):
        for path in sorted((root / folder).rglob('*.py')):
            if path.is_symlink() or not path.is_file():
                raise ValueError('Unsafe package source')
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    # Owner-specific source/config and runtime files are never selected at all.
    # Known private names and paths additionally protect against copied comments.
    private = re.compile(rb'(?:/home/hruaia|hawayu\.in|152\.67\.31\.231|@gmail\.com|BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|sk-[A-Za-z0-9_-]{20,})')
    for name, data in files.items():
        if private.search(data):
            raise ValueError('Private information in selected source: ' + name)
    return files


def build(output, root=ROOT):
    files = contents(root)
    manifest = {'project': 'personal-mcq-solver', 'license': 'MIT',
                'status': 'prepared_for_owner_review_not_published',
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files['MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo('personal-mcq-solver/' + name, date_time=(2026, 11, 6, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return {'archive': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'files': len(files), 'published': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.out.absolute()), indent=2))
