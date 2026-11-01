#!/usr/bin/env python3
"""Download the exact client-side Python runtime needed for offline builds."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "pyodide"
BASE = "https://testingcf.jsdelivr.net/pyodide/v0.26.4/full"
OUT.mkdir(parents=True, exist_ok=True)


def download(name: str) -> None:
    target = OUT / name
    if target.exists() and target.stat().st_size > 0:
        return
    partial = target.with_suffix(target.suffix + '.part')
    print(f"Downloading {name}…", flush=True)
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=240) as response:
        partial.write_bytes(response.read())
    partial.replace(target)


core = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
with ThreadPoolExecutor(max_workers=5) as pool:
    list(pool.map(download, core))

lock = json.loads((OUT / "pyodide-lock.json").read_text())
needed = set()


def add_package(name: str) -> None:
    if name in needed:
        return
    package = lock["packages"].get(name)
    if not package:
        raise RuntimeError(f"Pyodide package not found: {name}")
    needed.add(name)
    for dependency in package.get("depends", []):
        add_package(dependency)


for package in ("numpy", "scipy", "scikit-learn", "opencv-python"):
    add_package(package)

packages = [lock["packages"][name]["file_name"] for name in sorted(needed)]
with ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(download, packages))

files = core + packages
(OUT / "manifest.json").write_text(json.dumps({"files": files}, indent=2))
print(f"Offline Python runtime ready: {len(files)} files, {sum((OUT / f).stat().st_size for f in files) / 1e6:.1f} MB")
