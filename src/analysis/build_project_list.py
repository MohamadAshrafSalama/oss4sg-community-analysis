import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "Data"
OUT = BASE / "projects_all.csv"

sources = [
    (DATA / "Filtered-OSS-Project-Info.csv", "OSS"),
    (DATA / "Filtered-OSS4SG-Project-Info.csv", "OSS4SG"),
]

seen = set()
rows = []
for path, category in sources:
    with path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for rec in r:
            name = (rec.get("name") or rec.get("repo") or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                # if duplicate across lists, prefer OSS4SG label if present
                if category == "OSS4SG":
                    for row in rows:
                        if row["repo"].lower() == key:
                            row["category"] = "OSS4SG"
                            break
                continue
            seen.add(key)
            rows.append({"repo": name, "category": category})

rows.sort(key=lambda x: x["repo"].lower())

with OUT.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=["repo", "category"])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUT}")
