"""MoneyWin pipeline tracker — the CSV is the source of truth.

Thin, dependency-free helpers over the pipeline CSV used by the outreach
scripts and by the Hermes ``moneywin`` plugin (which reads the same file
directly). Paths resolve from the repo root, so these work from any cwd.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = REPO_ROOT / "client-packs" / "first-client-action-kit" / "tracking" / "first-10-leads.csv"

FIELDS = ["name", "email", "company", "website", "hint", "stage", "notes"]

STAGES = ("new", "contacted", "replied", "call", "proposal", "won", "lost")


def load_leads(path: Path = CSV_PATH) -> List[Dict[str, str]]:
    """Read the pipeline. Returns ``[]`` when the file does not exist yet."""
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    for row in rows:
        for field in FIELDS:
            row.setdefault(field, "")
    return rows


def save_leads(leads: List[Dict[str, str]], path: Path = CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)


def find_lead(name: str, leads: List[Dict[str, str]] | None = None) -> Dict[str, str] | None:
    """Case-insensitive exact match on the business name."""
    rows = load_leads() if leads is None else leads
    target = name.strip().lower()
    for row in rows:
        if (row.get("name") or "").lower() == target:
            return row
    return None


def mark_contacted(name: str, notes: str = "") -> Dict[str, str] | None:
    """Stamp today as the outreach start date and move the lead to ``contacted``.

    The date is appended to ``notes`` as ``contacted YYYY-MM-DD`` — that stamp is
    what the sequence scheduler (Hermes ``mw_due``) reads to decide which email
    a lead is due for.
    """
    leads = load_leads()
    row = find_lead(name, leads)
    if row is None:
        return None
    stamp = f"contacted {date.today().isoformat()}"
    row["notes"] = (row.get("notes", "") + " | " + stamp).strip(" |")
    row["stage"] = "contacted"
    if notes:
        row["notes"] = (row["notes"] + " | " + notes).strip(" |")
    save_leads(leads)
    return row


def set_stage(name: str, stage: str, notes: str = "") -> Dict[str, str] | None:
    """Move a lead to ``stage`` (one of ``STAGES``), optionally appending a note."""
    if stage not in STAGES:
        raise ValueError(f"gecersiz stage: {stage!r} (gecerli: {', '.join(STAGES)})")
    leads = load_leads()
    row = find_lead(name, leads)
    if row is None:
        return None
    row["stage"] = stage
    if notes:
        row["notes"] = (row.get("notes", "") + " | " + notes).strip(" |")
    save_leads(leads)
    return row


def main(argv: List[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="MoneyWin pipeline tracker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_contact = sub.add_parser("mark", help="Stamp today's date and set stage=contacted")
    p_contact.add_argument("name")
    p_contact.add_argument("--notes", default="")

    p_stage = sub.add_parser("stage", help="Set a lead's stage")
    p_stage.add_argument("name")
    p_stage.add_argument("stage", choices=STAGES)
    p_stage.add_argument("--notes", default="")

    sub.add_parser("list", help="Print leads")

    args = ap.parse_args(argv)

    if args.cmd == "mark":
        row = mark_contacted(args.name, args.notes)
        if row is None:
            print(f"lead bulunamadi: {args.name!r}")
            return 1
        print(f"{row['name']}: stage={row['stage']} notes={row['notes']}")
        return 0

    if args.cmd == "stage":
        row = set_stage(args.name, args.stage, args.notes)
        if row is None:
            print(f"lead bulunamadi: {args.name!r}")
            return 1
        print(f"{row['name']}: stage={row['stage']}")
        return 0

    for row in load_leads():
        print(f"{row.get('stage',''):10} {row.get('name','')} <{row.get('email','')}> {row.get('hint','')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
