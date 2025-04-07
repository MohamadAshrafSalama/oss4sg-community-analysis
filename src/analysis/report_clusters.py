import csv
from pathlib import Path
from collections import defaultdict, deque

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / "exper7_out"


def read_corr(set_name: str):
    p = OUTDIR/"corr"/f"{set_name}_spearman.csv"
    with p.open(encoding='utf-8') as f:
        rows = list(csv.reader(f))
    cols = rows[0][1:]
    n = len(cols)
    mat = [[0.0]*n for _ in range(n)]
    for i in range(1, len(rows)):
        vals = rows[i][1:]
        for j, v in enumerate(vals):
            try:
                mat[i-1][j] = float(v)
            except Exception:
                mat[i-1][j] = float('nan')
    return cols, mat


def build_clusters(cols, mat, thr=0.7):
    n = len(cols)
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            v = mat[i][j]
            if v != v:  # NaN
                continue
            if abs(v) >= thr:
                adj[i].append(j)
                adj[j].append(i)
    # connected components
    seen = [False]*n
    clusters = []
    for i in range(n):
        if seen[i]:
            continue
        q = deque([i])
        seen[i] = True
        comp = [i]
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
                    comp.append(v)
        clusters.append(sorted(comp))
    # map to (cluster_id -> list of metrics)
    clusters_sorted = sorted(clusters, key=lambda c: (-(len(c)), [cols[i] for i in c]))
    out = []
    for cid, comp in enumerate(clusters_sorted, start=1):
        for i in comp:
            out.append((cid, cols[i]))
    return out


def main(set_name: str, thr: float):
    cols, mat = read_corr(set_name)
    pairs = build_clusters(cols, mat, thr)
    rep = OUTDIR/"reports"/f"clusters_{set_name}.csv"
    rep.parent.mkdir(parents=True, exist_ok=True)
    with rep.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","metric"])
        for cid, m in pairs:
            w.writerow([cid, m])
    print("Saved:", rep)

if __name__ == '__main__':
    import sys
    s = sys.argv[1] if len(sys.argv)>1 else 'raw'
    thr = float(sys.argv[2]) if len(sys.argv)>2 else 0.7
    main(s, thr)
