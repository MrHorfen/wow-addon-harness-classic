#!/usr/bin/env python3
"""Build installable folders for each client flavor from one source tree."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addon" / "AHProbe"
TOC = ADDON / "AHProbe.toc"

FLAVORS = {
    "legacy": ("11509", ""),
    "modern": ("16001", "-modern"),
}


def parse_toc(path: Path) -> list[str]:
    files: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        files.append(entry.replace("\\", "/"))
    return files


def package(flavor: str, out_dir: Path) -> Path:
    interface, suffix = FLAVORS[flavor]
    destination = out_dir / f"AHProbe-{flavor}" / "AHProbe"

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    files = parse_toc(TOC)
    for relative in files:
        source = ADDON / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    lines = TOC.read_text(encoding="utf-8-sig").splitlines()
    version_match = re.search(r"^##\s*Version:\s*(\S+)", "\n".join(lines), re.MULTILINE)
    if not version_match:
        raise RuntimeError("cannot read version from toc")
    version = version_match.group(1).removesuffix("-modern") + suffix

    output: list[str] = []
    for line in lines:
        if line.startswith("## Interface:"):
            line = f"## Interface: {interface}"
        elif line.startswith("## Version:"):
            line = f"## Version: {version}"
        output.append(line)

    (destination / "AHProbe.toc").write_text(
        "\n".join(output) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"packaged {flavor}: {destination} ({len(files)} Lua files)")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flavor", choices=sorted(FLAVORS), required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    package(args.flavor, args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
