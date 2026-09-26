"""Tools 2 + 4: build_spec_index / spec_lookup.

HTML pages -> plain-text sections (one file per page) -> paragraphs tagged
with a LOCATOR ("§4.3.2", "§15 call_vs", "Appendix C") -> a tiny BM25 index.

Why BM25 and not embeddings: queries are exact spec terms ("call_vs",
"packed address", "§12.3.1"); exact lookup + BM25 beats dense recall here.
Standard library only.
"""
from __future__ import annotations

import html
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from zbuilder.paths import SPEC_CACHE, SPEC_INDEX, SPEC_SECTIONS

TOKEN_RE = re.compile(r"[a-z0-9_]+")


@dataclass
class Passage:
    locator: str
    page: str
    text: str


def html_to_text(page_html: str) -> str:
    """Very small HTML -> text converter that keeps paragraph structure."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", page_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|h\d|tr|li|pre|div|table)>", "\n\n", text)
    text = re.sub(r"(?i)<a\s+name=\"([^\"]+)\"[^>]*>", r"\n[[anchor:\1]]", text)
    text = re.sub(r"(?i)<h\d[^>]*id=\"([^\"]+)\"[^>]*>", r"\n[[anchor:\1]]", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", text)
    return text.strip()


def _page_prefix(page: str) -> str:
    m = re.match(r"sect(\d+)", page)
    if m:
        return f"§{int(m.group(1))}"
    m = re.match(r"app([a-z])", page)
    if m:
        return f"Appendix {m.group(1).upper()}"
    return page.replace(".html", "")


def split_passages(page: str, text: str) -> list[Passage]:
    """Split into paragraphs; a paragraph that starts with a section number
    like '4.3.2' sets the locator. In §15 opcode anchors set '§15 <name>'."""
    prefix = _page_prefix(page)
    locator = prefix
    out: list[Passage] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        anchor = re.search(r"\[\[anchor:([^\]]+)\]\]", para)
        if anchor and page.startswith("sect15"):
            locator = f"§15 {anchor.group(1)}"
        num = re.match(r"(\d+(?:\.\d+)+)\b", para)
        if num and prefix.startswith("§") and num.group(1).split(".")[0] == prefix[1:]:
            locator = f"§{num.group(1)}"
        clean = re.sub(r"\[\[anchor:[^\]]+\]\]", "", para).strip()
        if not clean:
            continue
        if out and out[-1].locator == locator:      # same section: one passage
            out[-1] = Passage(locator, page, out[-1].text + "\n\n" + clean)
        else:
            out.append(Passage(locator, page, clean))
    return out


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_spec_index(cache_dir: Path = SPEC_CACHE, sections_dir: Path = SPEC_SECTIONS,
                     index_path: Path = SPEC_INDEX, fingerprint: str = "") -> int:
    sections_dir.mkdir(parents=True, exist_ok=True)
    passages: list[Passage] = []
    for page_path in sorted(cache_dir.glob("*.html")):
        text = html_to_text(page_path.read_text(encoding="latin-1"))
        (sections_dir / (page_path.stem + ".txt")).write_text(text)
        passages.extend(split_passages(page_path.name, text))
    index_path.write_text(json.dumps({"fingerprint": fingerprint,
                                      "passages": [asdict(p) for p in passages]}))
    return len(passages)


class SpecIndex:
    """BM25 over passages + exact locator lookup."""

    def __init__(self, index_path: Path = SPEC_INDEX, k1: float = 1.5, b: float = 0.75):
        data = json.loads(index_path.read_text())
        self.fingerprint = data.get("fingerprint", "")
        self.passages = [Passage(**p) for p in data["passages"]]
        self.docs = [Counter(tokenize(p.locator + " " + p.text)) for p in self.passages]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(1, len(self.lengths))
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def by_locator(self, locator: str) -> list[Passage]:
        loc = locator.strip()
        if not loc.startswith(("§", "Appendix")):
            loc = "§15 " + loc if not re.match(r"\d", loc) else "§" + loc
        return [p for p in self.passages
                if p.locator == loc or p.locator.startswith(loc + ".")]

    def search(self, query: str, k: int = 5) -> list[tuple[float, Passage]]:
        terms = tokenize(query)
        scored = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for t in terms:
                if t not in doc:
                    continue
                tf = doc[t]
                norm = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len)
                score += self.idf.get(t, 0.0) * tf * (self.k1 + 1) / norm
            if score > 0:
                scored.append((score, self.passages[i]))
        scored.sort(key=lambda s: -s[0])
        return scored[:k]

    def lookup(self, query: str, k: int = 5) -> list[dict]:
        """Exact § / opcode lookup first, then BM25. Empty list = not in spec."""
        exact = self.by_locator(query)
        if exact:
            return [{"locator": p.locator, "text": p.text, "score": 99.0} for p in exact[:k]]
        return [{"locator": p.locator, "text": p.text, "score": round(s, 2)}
                for s, p in self.search(query, k)]
