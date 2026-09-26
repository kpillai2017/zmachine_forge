"""Tool 1: fetch_spec - crawl the Standard 1.1 index and cache every linked
page in the same directory. Page names are DISCOVERED, never hard-coded.

Standard library only (urllib), so it runs before any dependency install.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from zbuilder.paths import ALLOWED_HOSTS, DEFAULT_SPEC_URL, SPEC_CACHE

MANIFEST = "manifest.json"


@dataclass
class FetchReport:
    pages_fetched: int = 0
    pages_cached: int = 0
    changed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _check_host(url: str) -> None:
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise PermissionError(f"host not allowlisted: {host}")


def _download(url: str, timeout: float = 20.0) -> bytes:
    _check_host(url)
    req = urllib.request.Request(url, headers={"User-Agent": "zbuilder/0.1 (study project)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (allowlisted)
        return resp.read()


def discover_pages(index_html: str, index_url: str) -> list[str]:
    """Return absolute URLs of .html pages linked from the index that live in
    the SAME directory as the index (sections, appendices, preface...)."""
    base_dir = index_url.rsplit("/", 1)[0] + "/"
    found: list[str] = []
    for href in re.findall(r'href="([^"#]+\.html)(?:#[^"]*)?"', index_html, flags=re.I):
        url = urllib.parse.urljoin(index_url, href)
        if url.startswith(base_dir) and url not in found:
            found.append(url)
    return found


def fetch_spec(index_url: str = DEFAULT_SPEC_URL, cache_dir: Path = SPEC_CACHE,
               force: bool = False) -> FetchReport:
    """Fetch the index + all same-directory pages into cache_dir.

    Offline behaviour: if the index can't be downloaded but a cache exists,
    the cache is used; with no cache a clear error is raised.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / MANIFEST
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    report = FetchReport()

    def get(url: str) -> str | None:
        name = url.rsplit("/", 1)[1]
        target = cache_dir / name
        if target.exists() and not force:
            report.pages_cached += 1
            return target.read_text(encoding="latin-1")
        try:
            data = _download(url)
        except Exception as exc:  # network down etc.
            if target.exists():
                report.pages_cached += 1
                return target.read_text(encoding="latin-1")
            report.errors.append(f"{url}: {exc}")
            return None
        digest = hashlib.sha256(data).hexdigest()
        if manifest.get(name, {}).get("sha256") != digest:
            report.changed.append(name)
        manifest[name] = {"url": url, "sha256": digest}
        target.write_bytes(data)
        report.pages_fetched += 1
        return data.decode("latin-1")

    index_html = get(index_url)
    if index_html is None:
        raise RuntimeError("Spec not cached and could not be downloaded - run once while online.")
    for url in discover_pages(index_html, index_url):
        get(url)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return report


def spec_fingerprint(cache_dir: Path = SPEC_CACHE) -> str:
    """A single hash over all cached pages - used to invalidate derived files."""
    manifest_path = cache_dir / MANIFEST
    if not manifest_path.exists():
        return ""
    manifest = json.loads(manifest_path.read_text())
    joined = "".join(f"{k}:{v['sha256']}" for k, v in sorted(manifest.items()))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]
