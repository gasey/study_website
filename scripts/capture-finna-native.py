#!/usr/bin/env python3
"""Save a native QA capture only while the requested Finna app owns focus."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct
import xml.etree.ElementTree as ET


def adb(*args):
    return subprocess.check_output(["adb", "-d", *args])


def focused(package):
    ime = adb("shell", "dumpsys", "input_method").decode()
    visibility = re.search(r"mImeWindowVis=(\d+)", ime)
    if "mInputShown=true" in ime or (visibility and int(visibility[1]) & 2):
        return False  # Keyboard/clipboard overlays can retain the app's focus.
    return any(
        "mCurrentFocus=" in line and package + "/" in line
        for line in adb("shell", "dumpsys", "window").decode().splitlines()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("label")
    parser.add_argument("--orientation", choices=("portrait", "landscape"))
    parser.add_argument("--dynamic-hierarchy", action="store_true",
                        help="Use the prepared read-only Finna Dev dumper for active countdowns")
    parser.add_argument("--package", choices=(
        "in.hawayu.finna", "in.hawayu.finna.dev", "in.hawayu.finna.staging",
    ), default="in.hawayu.finna")
    args = parser.parse_args()
    assert re.fullmatch(r"[a-z0-9-]+", args.label)
    assert args.report.is_dir()
    assert focused(args.package), "Requested Finna app must own focus"
    if args.dynamic_hierarchy:
        assert args.package == "in.hawayu.finna.dev", "Dynamic dumper is scoped to Finna Dev"
    remote = "/data/local/tmp/finna-dynamic-qa.xml" if args.dynamic_hierarchy else "/data/local/tmp/finna-native-qa.xml"
    try:
        if args.dynamic_hierarchy:
            adb("shell", "rm", "-f", remote)
            result = adb("shell", "uiautomator", "runtest",
                         "/system/framework/android.test.base.jar",
                         "/data/local/tmp/finna-dynamic-dump.jar", "-c", "FinnaDynamicDump")
            assert b"OK (1 test)" in result and b"INSTRUMENTATION_STATUS_CODE: 0" in result, "Dynamic dump failed"
            assert b"unexpected exception" not in result and b"FAILURES" not in result, "Dynamic dump failed"
        else:
            adb("shell", "uiautomator", "dump", remote)
        xml = adb("exec-out", "cat", remote)
    finally:
        adb("shell", "rm", "-f", remote)
    assert focused(args.package), "Focus changed during UI capture"
    root = ET.fromstring(xml)
    assert any(n.get("package") == args.package for n in root.iter("node"))
    png = adb("exec-out", "screencap", "-p")
    assert focused(args.package), "Focus changed during screenshot capture"
    width, height = struct.unpack(">II", png[16:24])
    if args.orientation:
        assert (width > height) == (args.orientation == "landscape"), "Orientation has not changed yet"
    paths = []
    for suffix, data in (("xml", xml), ("png", png)):
        path = args.report / f"{args.label}.{suffix}"
        assert not path.exists(), f"Preserve earlier capture: {path.name}"
        path.write_bytes(data)
        paths.append(path)
    result = {
        "package": args.package,
        "focus_verified_before_and_after": True,
        "keyboard_hidden": True,
        "hierarchy_method": "dynamic-dev-read-only" if args.dynamic_hierarchy else "uiautomator-dump",
        "width": width,
        "height": height,
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }
    (args.report / f"{args.label}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
