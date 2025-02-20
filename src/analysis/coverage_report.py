import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / 'projects_with_metrics.csv'
OUT = BASE / 'exper7_out' / 'reports' / 'coverage.csv'

RAW_COLS = [
    'numStars','numSubscribers','numForks',
    'numContributors','numCoreContributors',
    'numCommits','numOpenPullRequests','numClosedPullRequests','numMergedPullRequests',
    'numOpenIssues','numClosedIssues','avg_resolution_time_hours',
    'avg_commit_msg_len','Comment Lines','Comment Characters','Ratio Code to Comments','Code Chars to Comment Chars',
    'Lines of Code','Non Comment Lines','Characters','Code Characters','Readme Characters','Repo Size MB',
]
NORM_COLS = [
    'numCommits_per_codechar','numOpenPullRequests_per_codechar','numClosedPullRequests_per_codechar',
    'numMergedPullRequests_per_codechar','numOpenIssues_per_codechar','numClosedIssues_per_codechar',
    'numContributors_per_codechar','numCoreContributors_per_codechar',
]
DERIVED = ['total_issues','total_issues_per_codechar']

with MASTER.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    rows = list(r)

cols = RAW_COLS + NORM_COLS + DERIVED

def is_num(x):
    if x is None or x == '':
        return False
    try:
        float(x)
        return True
    except Exception:
        return False

report = []
report.append(['metric','non_empty','numeric','rows'])
R = len(rows)
for c in cols:
    ne = sum(1 for row in rows if (row.get(c) not in (None,'')))
    num = sum(1 for row in rows if is_num(row.get(c)))
    report.append([c, str(ne), str(num), str(R)])

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerows(report)
print('Saved', OUT)
