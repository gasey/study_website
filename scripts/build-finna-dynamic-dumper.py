#!/usr/bin/env python3
"""Build a read-only, Finna Dev scoped UI hierarchy helper; never installs an app.

Push the resulting jar to /data/local/tmp/finna-dynamic-dump.jar for the native
capture script's --dynamic-hierarchy option. Remove it after the QA session.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, default=Path(os.environ.get(
        'ANDROID_HOME', str(Path.home() / 'Android/Sdk'))))
    parser.add_argument('--platform', default='android-36')
    parser.add_argument('--junit', type=Path, default=Path('/usr/share/java/junit4.jar'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'android/FinnaDynamicDump.java'
    android = args.sdk / 'platforms' / args.platform / 'android.jar'
    automation = args.sdk / 'platforms' / args.platform / 'uiautomator.jar'
    for path in (source, android, automation, args.junit):
        assert path.is_file(), f'Missing build input: {path}'
    tools = sorted((p for p in (args.sdk / 'build-tools').iterdir()
                    if p.name.replace('.', '').isdigit() and (p / 'd8').is_file()),
                   key=lambda p: tuple(map(int, p.name.split('.'))))
    assert tools, 'No Android d8 build tool installed'
    output = args.output.resolve()
    assert not output.exists(), f'Preserve existing artifact: {output}'
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='finna-dynamic-dump-build-') as directory:
        build = Path(directory)
        (build / 'classes').mkdir()
        (build / 'dex').mkdir()
        classpath = os.pathsep.join(map(str, (android, automation, args.junit)))
        commands = [
            ['javac', '--release', '8', '-cp', classpath, '-d', str(build / 'classes'), str(source)],
            ['jar', 'cf', str(build / 'classes.jar'), '-C', str(build / 'classes'), '.'],
            [str(tools[-1] / 'd8'), '--lib', str(android), '--lib', str(automation),
             '--lib', str(args.junit), '--output', str(build / 'dex'), str(build / 'classes.jar')],
            ['jar', 'cf', str(output), '-C', str(build / 'dex'), 'classes.dex'],
        ]
        for command in commands:
            subprocess.run(command, check=True)
    print(f'Built read-only Finna Dev hierarchy helper: {output}')


if __name__ == '__main__':
    main()
