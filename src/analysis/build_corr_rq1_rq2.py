import csv, math
from pathlib import Path
from itertools import combinations

BASE = Path(__file__).resolve().parents[1]
MASTER = BASE / "projects_with_metrics.csv"
COMMIT_METRICS = BASE / "Data" / "commit_metrics_per_project.csv"
OUTDIR = BASE / "exper7_out"

# RQ1 metrics (original)
RAW_COLS_RQ1 = [
    # Popularity
    "numStars","numSubscribers","numForks",
    # Community
    "numContributors","numCoreContributors",
    # Contributions (from RQ1 - note: numCommits may differ from Commit Count in RQ2)
    "numCommits","numOpenPullRequests","numClosedPullRequests","numMergedPullRequests",
    "numOpenIssues","numClosedIssues","avg_resolution_time_hours",
    # Readability
    "avg_commit_msg_len","Comment Lines","Comment Characters","Ratio Code to Comments","Code Chars to Comment Chars",
    # Project size
    "Lines of Code","Non Comment Lines","Characters","Code Characters","Readme Characters","Repo Size MB",
]

# RQ2 metrics (commit metrics)
RAW_COLS_RQ2 = [
    "Commit Count",      # May differ from numCommits
    "Commit Additions",
    "Commit Deletions",
]

# Combined metrics (RQ1 + RQ2)
RAW_COLS = RAW_COLS_RQ1 + RAW_COLS_RQ2

NORM_REPLACE = {
    "numCommits": "numCommits_per_codechar",
    "numOpenPullRequests": "numOpenPullRequests_per_codechar",
    "numClosedPullRequests": "numClosedPullRequests_per_codechar",
    "numMergedPullRequests": "numMergedPullRequests_per_codechar",
    "numOpenIssues": "numOpenIssues_per_codechar",
    "numClosedIssues": "numClosedIssues_per_codechar",
    "numContributors": "numContributors_per_codechar",
    "numCoreContributors": "numCoreContributors_per_codechar",
    # RQ2 normalized metrics
    "Commit Count": "Commit Count_per_codechar",
    "Commit Additions": "Commit Additions_per_codechar",
    "Commit Deletions": "Commit Deletions_per_codechar",
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

def merge_commit_metrics(rq1_rows, rq1_header):
    """Merge RQ2 commit metrics into RQ1 data"""
    # Load RQ2 commit metrics
    commit_data = {}
    if COMMIT_METRICS.exists():
        with COMMIT_METRICS.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            commit_rows = list(reader)
        
        # Create a mapping from repo to commit metrics
        for row in commit_rows:
            repo = row.get('repo', '')
            if repo:
                commit_data[repo] = {
                    'Commit Count': row.get('Commit Count', ''),
                    'Commit Additions': row.get('Commit Additions', ''),
                    'Commit Deletions': row.get('Commit Deletions', ''),
                }
        print(f"  Loaded commit metrics for {len(commit_data)} projects")
    else:
        print(f"  Warning: Commit metrics file not found: {COMMIT_METRICS}")
    
    # Add commit metrics columns to header if not present
    merged_header = list(rq1_header)
    for col in RAW_COLS_RQ2:
        if col not in merged_header:
            merged_header.append(col)
    
    # Add commit metrics to each row (rows are already dicts from DictReader)
    merged_rows = []
    for row in rq1_rows:
        new_row = dict(row)  # Copy the row
        repo = new_row.get('repo', '')
        
        # Add commit metrics if available
        if repo in commit_data:
            for col in RAW_COLS_RQ2:
                new_row[col] = commit_data[repo].get(col, '')
        else:
            for col in RAW_COLS_RQ2:
                new_row[col] = ''
        
        merged_rows.append(new_row)
    
    return merged_header, merged_rows

def compute_normalized_metrics(header, rows):
    """Compute normalized metrics (per code character)"""
    # Find code characters column
    if 'Code Characters' not in header:
        print("Warning: 'Code Characters' column not found, cannot compute normalized metrics")
        return header, rows
    
    # Create new header with normalized columns
    new_header = list(header)
    for col in RAW_COLS:
        if col in NORM_REPLACE and NORM_REPLACE[col] not in new_header:
            new_header.append(NORM_REPLACE[col])
    
    # Compute normalized metrics (rows are already dicts)
    new_rows = []
    for row in rows:
        new_row = dict(row)  # Copy the row
        code_chars_str = new_row.get('Code Characters', '')
        
        try:
            code_chars = float(code_chars_str) if code_chars_str else 0.0
        except (ValueError, TypeError):
            code_chars = 0.0
        
        # Compute normalized metrics
        for col in RAW_COLS:
            if col in NORM_REPLACE:
                norm_col = NORM_REPLACE[col]
                if norm_col not in new_row:
                    col_val_str = new_row.get(col, '')
                    try:
                        col_val = float(col_val_str) if col_val_str else None
                        if col_val is not None and code_chars > 0:
                            new_row[norm_col] = f"{col_val / code_chars:.12f}"
                        else:
                            new_row[norm_col] = ''
                    except (ValueError, TypeError):
                        new_row[norm_col] = ''
        
        new_rows.append(new_row)
    
    return new_header, new_rows

def build_corr(set_name: str):
    # define columns
    if set_name == 'raw':
        cols = RAW_COLS
    else:
        cols = [NORM_REPLACE.get(c, c) for c in RAW_COLS]
    
    # load RQ1 csv
    with MASTER.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames or []
    
    # Merge RQ2 commit metrics
    print(f"Merging RQ2 commit metrics into RQ1 data...")
    header, rows = merge_commit_metrics(rows, header)
    print(f"  Merged data: {len(rows)} projects")
    
    # Compute normalized metrics if needed
    if set_name == 'norm':
        print(f"Computing normalized metrics...")
        header, rows = compute_normalized_metrics(header, rows)
    
    # Load columns
    data = load_columns(header, rows, cols)
    
    # Check which columns are available
    available_cols = [c for c in cols if any(v is not None for v in data.get(c, []))]
    missing_cols = [c for c in cols if c not in available_cols]
    
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
    
    if len(available_cols) < 2:
        print(f"Error: Not enough columns available for correlation analysis")
        return
    
    print(f"Using {len(available_cols)} metrics for correlation analysis")
    
    # ranks for Spearman
    ranks = {c: rank_array(data[c]) for c in available_cols}
    
    # corr matrix
    n = len(available_cols)
    mat = [[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            rho = pearson_pair(ranks[available_cols[i]], ranks[available_cols[j]])
            mat[i][j] = rho
            mat[j][i] = rho
    
    # save correlation CSV
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR/"corr").mkdir(parents=True, exist_ok=True)
    out_csv = OUTDIR/"corr"/f"{set_name}_rq1_rq2_spearman.csv"
    with out_csv.open("w", newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["metric"]+available_cols)
        for i, c in enumerate(available_cols):
            w.writerow([c]+[f"{mat[i][j]:.6f}" for j in range(n)])
    
    # top-10 absolute pairs
    pairs = []
    for i, j in combinations(range(n), 2):
        val = mat[i][j]
        if not math.isnan(val):
            pairs.append((abs(val), available_cols[i], available_cols[j], val))
    pairs.sort(reverse=True)
    top_txt = OUTDIR/"reports"/f"top_pairs_{set_name}_rq1_rq2.txt"
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
        print("Usage: python scripts/build_corr_rq1_rq2.py [raw|norm]")
        sys.exit(1)
    build_corr(set_name)

