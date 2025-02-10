import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "Data"
MASTER = BASE / "projects_with_metrics.csv"

info_sources = [
    (DATA / "Filtered-OSS-Project-Info.csv", "OSS"),
    (DATA / "Filtered-OSS4SG-Project-Info.csv", "OSS4SG"),
]

DROP_FIELDS = {
    "description", "topics", "contributors", "authenticatedContributors", "coreContributors",
    "startDate", "lastContribution", "language", "SDG"
}

# Numeric fields to keep (and coerce)
KEEP_FIELDS = {
    "lifespan", "numStars", "numSubscribers", "numForks", "numContributors",
    "numAuthenticatedContributors", "numAnonymousContributors", "numNotAuthenticatedContributors",
    "numOneTimeContributors", "numAuthenticatedOneTimeContributors", "numCoreContributors",
    "numCommits", "numOpenIssues", "numClosedIssues", "numOpenPullRequests",
    "numClosedPullRequests", "numMergedPullRequests"
}

# load master
with MASTER.open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

idx = {r["repo"].lower(): r for r in rows}

for path, category in info_sources:
    with path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for rec in r:
            repo = (rec.get("name") or "").strip()
            if not repo:
                continue
            key = repo.lower()
            row = idx.get(key)
            if row is None:
                row = {"repo": repo, "category": category}
                rows.append(row)
                idx[key] = row
            else:
                if category == "OSS4SG" and row.get("category") == "OSS":
                    row["category"] = "OSS4SG"
            # attach numeric fields
            for k in KEEP_FIELDS:
                val = rec.get(k)
                if val is None or val == "" or val == "None":
                    continue
                row[k] = val

# write back with extended header (append KEEP_FIELDS if missing)
fieldnames = list(rows[0].keys())
for k in KEEP_FIELDS:
    if k not in fieldnames:
        fieldnames.append(k)

with MASTER.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"Updated {MASTER} with project info fields; rows={len(rows)}")
