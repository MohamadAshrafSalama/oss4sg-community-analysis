import csv, math
from pathlib import Path
from itertools import combinations

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / "projects_with_metrics.csv"
OUTDIR = BASE / "exper7_out"

RAW_COLS = [
    # Popularity
    "numStars","numSubscribers","numForks",
    # Community
    "numContributors","numCoreContributors",
    # Contributions
    "numCommits","numOpenPullRequests","numClosedPullRequests","numMergedPullRequests",
    "numOpenIssues","numClosedIssues","avg_resolution_time_hours",
    # Readability
    "avg_commit_msg_len","Comment Lines","Comment Characters","Ratio Code to Comments","Code Chars to Comment Chars",
    # Project size
    "Lines of Code","Non Comment Lines","Characters","Code Characters","Readme Characters","Repo Size MB",
]

NORM_REPLACE = {
    "numCommits": "numCommits_per_codechar",
    "numOpenPullRequests": "numOpenPullRequests_per_codechar",
    "numClosedPullRequests": "numClosedPullRequests_per_codechar",
    "numMergedPullRequests": "numMergedPullRequests_per_codechar",
    "numOpenIssues": "numOpenIssues_per_codechar",
    "numClosedIssues": "numClosedIssues_per_codechar",
    "numContributors": "numContributors_per_codechar",
    "numCoreContributors": "numCoreContributors_per_codechar",
}

# Spearman via ranks + Pearson on ranks (pairwise)
def rank_array(values):
    # values: list of floats with possible None
    # returns list of ranks (float) or None where missing; average ties
    pairs = [(v, i) for i, v in enumerate(values) if v is not None]
    if not pairs:
        return [None]*len(values)
    pairs.sort(key=lambda x: x[0])
    ranks = [None]*len(values)
    i = 0
    n = len(pairs)
    while i < n:
        j = i
        while j+1 < n and pairs[j+1][0] == pairs[i][0]:
            j += 1
        # average rank from i..j (1-based ranks)
        avg_r = (i + j)/2 + 1
        for k in range(i, j+1):
            ranks[pairs[k][1]] = avg_r
        i = j+1
    return ranks

def pearson_pair(x, y):
    # x, y lists of floats or None; compute Pearson on paired non-missing
    xs, ys = [], []
    for a, b in zip(x, y):
        if a is not None and b is not None:
            xs.append(a); ys.append(b)
    m = len(xs)
    if m < 3:
        return float('nan')
    mean_x = sum(xs)/m
    mean_y = sum(ys)/m
    num = sum((a-mean_x)*(b-mean_y) for a, b in zip(xs, ys))
    denx = math.sqrt(sum((a-mean_x)**2 for a in xs))
    deny = math.sqrt(sum((b-mean_y)**2 for b in ys))
    if denx == 0 or deny == 0:
        return float('nan')
    return num/(denx*deny)

def load_columns(header, rows, cols):
    data = {}
    for c in cols:
        idx = header.index(c) if c in header else -1
        vals = []
        for r in rows:
            v = r.get(c, "") if idx != -1 else ""
            try:
                vals.append(float(v) if v != "" else None)
            except Exception:
                vals.append(None)
        data[c] = vals
    return data

def build_corr(set_name: str):
    # define columns
    if set_name == 'raw':
        cols = RAW_COLS
    else:
        cols = [NORM_REPLACE.get(c, c) for c in RAW_COLS]
    # load csv
    with MASTER.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames or []
    data = load_columns(header, rows, cols)
    # ranks for Spearman
    ranks = {c: rank_array(data[c]) for c in cols}
    # corr matrix
    n = len(cols)
    mat = [[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            rho = pearson_pair(ranks[cols[i]], ranks[cols[j]])
            mat[i][j] = rho
            mat[j][i] = rho
    # save correlation CSV
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR/"corr").mkdir(parents=True, exist_ok=True)
    out_csv = OUTDIR/"corr"/f"{set_name}_spearman.csv"
    with out_csv.open("w", newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["metric"]+cols)
        for i, c in enumerate(cols):
            w.writerow([c]+[f"{mat[i][j]:.6f}" for j in range(n)])
    # top-10 absolute pairs
    pairs = []
    for i, j in combinations(range(n), 2):
        val = mat[i][j]
        if not math.isnan(val):
            pairs.append((abs(val), cols[i], cols[j], val))
    pairs.sort(reverse=True)
    top_txt = OUTDIR/"reports"/f"top_pairs_{set_name}.txt"
    top_txt.parent.mkdir(parents=True, exist_ok=True)
    with top_txt.open("w", encoding='utf-8') as f:
        f.write("Top |rho| pairs (Spearman):\n")
        for k in range(min(10, len(pairs))):
            a = pairs[k]
            f.write(f"{a[1]} vs {a[2]}: rho={a[3]:.4f} |rho|={a[0]:.4f}\n")
    print("Saved:", out_csv)
    print("Top pairs:", top_txt)

if __name__ == '__main__':
    import sys
    set_name = 'raw'
    if len(sys.argv) > 1:
        set_name = sys.argv[1]
    if set_name not in ('raw','norm'):
        print("Usage: python scripts/build_corr.py [raw|norm]")
        sys.exit(1)
    build_corr(set_name)
