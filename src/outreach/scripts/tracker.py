import csv
from datetime import date

CSV_PATH = "src/outreach/tracking/tracking.csv"

def load_leads(path=CSV_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_leads(leads, path=CSV_PATH):
    fieldnames = ["name", "email", "company", "first_contact_date", "last_reply", "stage", "notes"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

def mark_contacted(name):
    leads = load_leads()
    for lead in leads:
        if lead["name"] == name:
            lead["first_contact_date"] = str(date.today())
            lead["stage"] = "contacted"
    save_leads(leads)

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "mark":
        mark_contacted(sys.argv[2])
