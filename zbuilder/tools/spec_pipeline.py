"""One call that runs the Spec Analyst's deterministic pipeline:
fetch -> index -> opcodes.json (+ fingerprint everywhere)."""
from __future__ import annotations

from zbuilder.paths import OPCODES_JSON, SPEC_CACHE, SPEC_DIR
from zbuilder.tools.fetch_spec import fetch_spec, spec_fingerprint
from zbuilder.tools.opcode_table import build_opcode_json
from zbuilder.tools.spec_index import build_spec_index


def build_spec(force: bool = False) -> dict:
    SPEC_DIR.mkdir(exist_ok=True)
    report = fetch_spec(force=force)
    fp = spec_fingerprint()
    n_passages = build_spec_index(fingerprint=fp)
    data = build_opcode_json(SPEC_CACHE / "sect14.html", OPCODES_JSON, version=5, fingerprint=fp)
    return {"fetched": report.pages_fetched, "cached": report.pages_cached,
            "changed": report.changed, "errors": report.errors,
            "fingerprint": fp, "passages": n_passages, "v5_opcodes": data["count"]}
