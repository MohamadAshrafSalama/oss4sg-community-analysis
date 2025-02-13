import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parents[0]
COMMITS = ROOT / "master_commits.csv"
MASTER = ROOT / "Experement7(corrolation analysis)" / "projects_with_metrics.csv"

# Map project name from commits to owner/repo used in master by replacing first underscore with /
# Example: BlackArch_blackarch -> BlackArch/blackarch

def to_owner_repo(project_name: str) -> str:
    if not project_name:
        return ""
    parts = project_name.split("_", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}"
    return project_name

# Streaming aggregation: sum of lengths and counts
sums = {}
counts = {}

with COMMITS.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for rec in reader:
        proj = rec.get("project", "").strip()
        msg = rec.get("message", "")
        if not proj or msg is None:
            continue
        key = to_owner_repo(proj).lower()
        # length in characters
        L = len(msg)
        sums[key] = sums.get(key, 0) + L
        counts[key] = counts.get(key, 0) + 1

# Load master and merge
with MASTER.open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

for row in rows:
    key = row["repo"].lower()
    if key in counts and counts[key] > 0:
        row["avg_commit_msg_len"] = f"{sums[key] / counts[key]:.6f}"

# Write back
fieldnames = list(rows[0].keys())
if "avg_commit_msg_len" not in fieldnames:
    fieldnames.append("avg_commit_msg_len")

with MASTER.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print("Merged avg_commit_msg_len into", MASTER)
