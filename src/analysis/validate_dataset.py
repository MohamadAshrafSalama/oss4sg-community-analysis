import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / "projects_with_metrics.csv"
OUTDIR = BASE / "exper7_out"
REPORT = OUTDIR / "reports" / "checks.txt"

RAW_METRICS = [
    "numStars","numSubscribers","numForks",
    "numContributors","numCoreContributors",
    "numCommits","numOpenPullRequests","numClosedPullRequests","numMergedPullRequests",
    "numOpenIssues","numClosedIssues","avg_resolution_time_hours",
    "avg_commit_msg_len","Comment Lines","Comment Characters","Ratio Code to Comments","Code Chars to Comment Chars",
    "Lines of Code","Non Comment Lines","Characters","Code Characters","Readme Characters","Repo Size MB",
]

NORM_COUNTS = [
    "numCommits_per_codechar","numOpenPullRequests_per_codechar","numClosedPullRequests_per_codechar",
    "numMergedPullRequests_per_codechar","numOpenIssues_per_codechar","numClosedIssues_per_codechar",
    "numContributors_per_codechar","numCoreContributors_per_codechar",
]

DERIVED = ["total_issues","total_issues_per_codechar"]

NUMERIC = set(RAW_METRICS) | set(NORM_COUNTS)

# Load rows
with MASTER.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    header = reader.fieldnames or []

# Derive totals
for r in rows:
    def to_f(x):
        try:
            return float(x)
        except Exception:
            return None
    oi = to_f(r.get("numOpenIssues"))
    ci = to_f(r.get("numClosedIssues"))
    if oi is not None and ci is not None:
        r["total_issues"] = f"{oi+ci:.6f}"
    else:
        r["total_issues"] = ""
    cc = to_f(r.get("Code Characters"))
    total_issues_val = to_f(r.get("total_issues"))
    if cc and cc > 0 and total_issues_val is not None:
        r["total_issues_per_codechar"] = f"{total_issues_val / cc:.12f}"
    else:
        r["total_issues_per_codechar"] = ""

# Extend header if needed
for c in DERIVED:
    if c not in header:
        header.append(c)

# Coerce numeric columns and count NAs
na_counts = {c: 0 for c in NUMERIC | set(DERIVED)}
for r in rows:
    for c in NUMERIC | set(DERIVED):
        if c not in r:
            r[c] = ""
        v = r.get(c, "")
        if v == "":
            na_counts[c] += 1
        else:
            try:
                float(v)
            except Exception:
                na_counts[c] += 1

# Write back augmented CSV
with MASTER.open("w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    w.writerows(rows)

# Write report
REPORT.parent.mkdir(parents=True, exist_ok=True)
with REPORT.open("w", encoding='utf-8') as rf:
    rf.write("Validation & Coercion Report\n")
    rf.write(f"Rows: {len(rows)}\n\n")
    rf.write("NA counts (blank or non-numeric) in numeric/derived columns:\n")
    for k in sorted(na_counts.keys()):
        rf.write(f"- {k}: {na_counts[k]}\n")
    rf.write("\nSample rows (first 3) with derived totals:\n")
    for r in rows[:3]:
        rf.write(f"  {r.get('repo')}: total_issues={r.get('total_issues')} total_issues_per_codechar={r.get('total_issues_per_codechar')}\n")

print("Wrote:", MASTER)
print("Report:", REPORT)
