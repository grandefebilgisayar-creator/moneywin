"""MoneyWin lead sourcing — turn a raw business list into pipeline rows.

The old version scraped Google search HTML and appended rows with a different
schema to a different file, so nothing it produced could actually be emailed.
This version does the part that is reliable: it takes businesses you have
already identified (from a market, a directory, a chamber of commerce list)
and appends them to the real pipeline CSV with the real schema, skipping
anything already there.

Input — one business per line, fields separated by ``|``::

    Sunshine Cafe | https://sunshine-cafe.example | manual inventory + promo posts

Or run against a file::

    python lead_finder.py --file candidates.txt

The ``hint`` column is mandatory in practice: it is the one specific detail the
cold email personalizes on, and a row without one is not sendable.

This tool deliberately does not invent email addresses. Use the website column
to find the contact address, then confirm it before sending.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional

# The pipeline CSV is the single source of truth. Resolved relative to the repo
# root (the parent of src/), so it works from any cwd.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO_ROOT / "client-packs" / "first-client-action-kit" / "tracking" / "first-10-leads.csv"

FIELDS = ["name", "email", "company", "website", "hint", "stage", "notes"]


def read_candidates(text: str) -> List[Dict[str, str]]:
    """Parse ``name | website | hint`` lines, skipping blanks and comments."""
    out: List[Dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[0]:
            print(f"  atlandi (en az 'ad | website' gerekli): {line!r}", file=sys.stderr)
            continue
        name = parts[0]
        website = parts[1]
        hint = parts[2] if len(parts) > 2 else ""
        if website and not website.startswith(("http://", "https://")):
            website = "https://" + website
        out.append({"name": name, "website": website, "hint": hint})
    return out


def load_existing(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def add_candidates(candidates: List[Dict[str, str]], csv_path: Path = DEFAULT_CSV) -> Dict[str, object]:
    """Append new candidates to the pipeline CSV. Returns a summary."""
    existing = load_existing(csv_path)
    known_sites = {r.get("website", "").lower().rstrip("/") for r in existing if r.get("website")}
    known_names = {r.get("name", "").lower() for r in existing if r.get("name")}

    added: List[str] = []
    skipped_dup: List[str] = []
    missing_hint: List[str] = []

    for cand in candidates:
        site = cand["website"].lower().rstrip("/")
        if (site and site in known_sites) or cand["name"].lower() in known_names:
            skipped_dup.append(cand["name"])
            continue
        if not cand["hint"]:
            # Keep the row, but flag it: an unhinted lead cannot be personalized.
            missing_hint.append(cand["name"])
        existing.append({
            "name": cand["name"], "email": "", "company": "",
            "website": cand["website"], "hint": cand["hint"],
            "stage": "new", "notes": "",
        })
        known_sites.add(site)
        known_names.add(cand["name"].lower())
        added.append(cand["name"])

    if added:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing)

    return {
        "added": added,
        "added_count": len(added),
        "skipped_duplicates": skipped_dup,
        "missing_hint": missing_hint,
        "csv": str(csv_path),
        "pipeline_total": len(existing),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Append candidate businesses to the MoneyWin pipeline CSV.")
    ap.add_argument("--file", "-f", help="Text file with one 'name | website | hint' business per line.")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="Pipeline CSV path (default: first-10-leads.csv).")
    ap.add_argument("lines", nargs="*", help="Inline 'name | website | hint' entries.")
    args = ap.parse_args(argv)

    chunks: List[str] = list(args.lines)
    if args.file:
        try:
            chunks.extend(Path(args.file).read_text(encoding="utf-8").splitlines())
        except OSError as exc:
            print(f"dosya okunamadi: {exc}", file=sys.stderr)
            return 2
    if not chunks:
        ap.print_help()
        return 1

    result = add_candidates(read_candidates("\n".join(chunks)), Path(args.csv))
    print(f"eklendi: {result['added_count']}  | pipeline toplam: {result['pipeline_total']}")
    if result["added"]:
        print("  yeni: " + ", ".join(result["added"]))
    if result["skipped_duplicates"]:
        print("  atlandi (zaten var): " + ", ".join(result["skipped_duplicates"]))
    if result["missing_hint"]:
        print("  uyari — hint bos, email kisisellestirilemez: " + ", ".join(result["missing_hint"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
