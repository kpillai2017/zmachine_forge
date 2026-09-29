"""Tool 8: fetch_test_stories - download the conformance stories listed in
stories/urls.txt (optional sha256 pin per line). Zips are unpacked, keeping
only story files. Missing stories make dependent eval cases SKIP, not fail."""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

from zbuilder.paths import STORIES_DIR
from zbuilder.tools.fetch_spec import _download

# stories (plain or in a Blorb, ADR-061), sources, expected output
KEEP_SUFFIXES = (".z5", ".z6", ".z7", ".z8", ".zblorb", ".zlb", ".blb",
                 ".inf", ".out5", ".out8")


def read_url_list(path: Path) -> list[tuple[str, str | None]]:
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        entries.append((parts[0], parts[1] if len(parts) > 1 else None))
    return entries


def fetch_stories(stories_dir: Path = STORIES_DIR) -> list[str]:
    report = []
    for url, pinned in read_url_list(stories_dir / "urls.txt"):
        name = url.rsplit("/", 1)[1]
        try:
            data = _download(url, timeout=60)
        except Exception as exc:
            report.append(f"FAILED {name}: {exc}")
            continue
        digest = hashlib.sha256(data).hexdigest()
        if pinned and pinned != digest:
            report.append(f"CHECKSUM MISMATCH {name}: expected {pinned}, got {digest}")
            continue
        if name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for member in zf.namelist():
                    base = Path(member).name
                    if base.lower().endswith(KEEP_SUFFIXES):
                        (stories_dir / base).write_bytes(zf.read(member))
                        report.append(f"ok {base} (from {name})")
        else:
            (stories_dir / name).write_bytes(data)
            report.append(f"ok {name}")
        if not pinned:
            report.append(f"   pin with: {url} {digest}")
    return report
