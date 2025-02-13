import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "Data"
MASTER = BASE / "projects_with_metrics.csv"  # in-place update

pr_sources = [
    (DATA / "oss_pr_resolution_times.csv", "OSS"),
    (DATA / "oss4sg_pr_resolution_times.csv", "OSS4SG"),
]

# load master
with MASTER.open(newline=, encoding=utf-8) as f:
    rows = list(csv.DictReader(f))

# index by repo
idx = {r["repo"].lower(): r for r in rows}

for path, category in pr_sources:
    with path.open(newline=, encoding=utf-8) as f:
        r = csv.DictReader(f)
        for rec in r:
            repo = (rec.get("repo") or "").strip()
            if not repo:
                continue
            key = repo.lower()
            row = idx.get(key)
            if row is None:
                row = {"repo": repo, "category": category}
                rows.append(row)
                idx[key] = row
            # add/overwrite PR metrics
            row["num_prs"] = rec.get("num_prs", "")
            row["avg_resolution_time_hours"] = rec.get("avg_resolution_time_hours", "")
            row["median_resolution_time_hours"] = rec.get("median_resolution_time_hours", "")
            # if category differs and current is OSS but source is OSS4SG, upgrade
            if category == "OSS4SG" and row.get("category") == "OSS":
                row["category"] = "OSS4SG"

# write back in place preserving existing and new fields
fieldnames = list(rows[0].keys())
# ensure PR fields exist in header and ordered near the end
for c in ("num_prs", "avg_resolution_time_hours", "median_resolution_time_hours"):
    if c not in fieldnames:
        fieldnames.append(c)

with MASTER.open("w", newline=, encoding=utf-8) as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"Updated {MASTER} with PR metrics; rows={len(rows)}")
