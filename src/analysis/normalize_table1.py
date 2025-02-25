import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / "projects_with_metrics.csv"

# Columns to normalize by Code Characters (per-code-char density)
NORM_COLS = [
    "numCommits",
    "num_prs",
    "numOpenPullRequests",
    "numClosedPullRequests",
    "numMergedPullRequests",
    "numOpenIssues",
    "numClosedIssues",
    "numContributors",
    "numCoreContributors",
    "numAuthenticatedContributors",
    "numAnonymousContributors",
    "numNotAuthenticatedContributors",
    "numOneTimeContributors",
    "numAuthenticatedOneTimeContributors",
]

CODE_CHARS = "Code Characters"

with MASTER.open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# Build new header
fieldnames = list(rows[0].keys())
for c in NORM_COLS:
    norm_name = f"{c}_per_codechar"
    if norm_name not in fieldnames:
        fieldnames.append(norm_name)

# Normalize
for row in rows:
    try:
        code_chars = float(row.get(CODE_CHARS, "") or 0)
    except ValueError:
        code_chars = 0.0
    for c in NORM_COLS:
        val_raw = row.get(c)
        norm_name = f"{c}_per_codechar"
        out = ""
        if val_raw not in (None, ""):
            try:
                num = float(val_raw)
                if code_chars > 0:
                    out = f"{num / code_chars:.12f}"
                else:
                    out = ""
            except ValueError:
                out = ""
        row[norm_name] = out

with MASTER.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print("Added normalized columns (per code character) for Table 1 counts.")
