from bs4 import BeautifulSoup
import requests
import csv
import os

def find_leads(query: str, max_results: int = 10, output_path: str = "src/outreach/tracking/tracking.csv"):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    resp = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for g in soup.find_all("div", class_="g")[:max_results]:
        title = g.find("h3")
        link = g.find("a", href=True)
        snippet = g.find("div", class_="VwiC3b")
        if title and link:
            results.append({
                "name": title.get_text(),
                "url": link["href"],
                "snippet": snippet.get_text() if snippet else ""
            })
    file_exists = os.path.exists(output_path)
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "company", "first_contact_date", "last_reply", "stage", "notes"])
        if not file_exists:
            writer.writeheader()
        for r in results:
            writer.writerow({
                "name": r["name"],
                "email": "",
                "company": r["url"],
                "first_contact_date": "",
                "last_reply": "",
                "stage": "lead",
                "notes": r["snippet"][:120]
            })
    return results

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "small business invoicing manual"
    find_leads(q)
