import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "Data"
MASTER = BASE / "projects_all.csv"
OUT = BASE / "projects_with_metrics.csv"

metrics_sources = [
    DATA / "OSS4SGprojects_metrics_2.csv",
    DATA / "OSSprojects_metrics_2.csv",
]

def owner_repo_from_metric_name(name: str):
    # Convert "Owner_Repo" -> "Owner/Repo" (only first underscore should be slash)
    if not name:
        return ""
    parts = name.split("_", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}"
    return name  # fallback

# Load master rows
with MASTER.open(newline='', encoding='utf-8') as f:
    master = list(csv.DictReader(f))

# Prepare output fieldnames
metric_fieldnames = None

# Index master by lowercased repo
idx = {row["repo"].lower(): row for row in master}

# Ensure category present for new rows
DEFAULT_CAT = "OSS"  # fallback if a new repo appears only in OSS metrics

for src in metrics_sources:
    with src.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        # capture metric columns once
        if metric_fieldnames is None:
            metric_fieldnames = [c for c in r.fieldnames if c != "name"]
        for rec in r:
            raw = rec.get("name", "").strip()
            repo = owner_repo_from_metric_name(raw)
            if not repo:
                continue
            key = repo.lower()
            row = idx.get(key)
            if row is None:
                # add new row if not in master
                row = {"repo": repo, "category": DEFAULT_CAT}
                master.append(row)
                idx[key] = row
            # attach metrics
            for c in metric_fieldnames:
                row[c] = rec.get(c, "")

# Write out
fieldnames = ["repo", "category"] + metric_fieldnames
with OUT.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(master)

print(f"Wrote {len(master)} rows to {OUT}")
