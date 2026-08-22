from pathlib import Path
import csv
from datetime import datetime, timedelta

LEADS = Path(__file__).with_name("niche-leads.csv")
OUT = Path(__file__).with_name("campaign-output.md")

def load_leads():
    with LEADS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def render_email(template_path: Path, lead: dict) -> str:
    text = template_path.read_text(encoding="utf-8")
    text = text.replace("[Name]", lead.get("name", ""))
    text = text.replace("[specific detail]", lead.get("hint", ""))
    text = text.replace("[business]", lead.get("company", ""))
    return text

def main():
    leads = load_leads()
    base = datetime.now().date()
    emails = {
        0: Path(__file__).with_name("../../emails/1-cold.md"),
        3: Path(__file__).with_name("../../emails/2-followup.md"),
        8: Path(__file__).with_name("../../emails/3-discovery.md"),
        25: Path(__file__).with_name("../../emails/4-breakup.md"),
    }
    lines = ["# Campaign", f"- Start: {base}", ""]
    for i, lead in enumerate(leads, start=1):
        company_key = lead["company"].split()[0].lower()
        personalized = Path(__file__).with_name(f"../../emails/personalized/{company_key}.md")
        first = render_email(personalized if personalized.exists() else emails[0], lead)
        lines.append(f"## {i}. {lead['company']}")
        lines.append(f"- email: {lead.get('email', '')}")
        lines.append(f"- day 0: {first.strip()}")
        for day, tmpl in emails.items():
            lines.append(f"- day {day}: see {tmpl.name}")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)

if __name__ == "__main__":
    main()
