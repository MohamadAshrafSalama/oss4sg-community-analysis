import csv, math
from pathlib import Path
from itertools import combinations
from typing import List

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform

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


def to_distance(abs_corr: List[List[float]]):
    n = len(abs_corr)
    D = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            c = abs_corr[i][j]
            if math.isnan(c):
                d = 1.0
            else:
                d = 1.0 - abs(c)
            D[i][j] = d
    return D


def cluster_and_plot(set_name: str, cut_d: float = 0.30):
    cols, corr = read_corr(set_name)
    n = len(cols)
    # abs correlation matrix for distance
    abs_corr = [[abs(corr[i][j]) for j in range(n)] for i in range(n)]
    D = to_distance(abs_corr)
    # condensed form
    condensed = []
    for i in range(n):
        for j in range(i+1, n):
            condensed.append(D[i][j])
    Z = linkage(condensed, method='average')
    # clusters
    cl = fcluster(Z, cut_d, criterion='distance')
    # save cluster membership
    rep_dir = OUTDIR/"reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    cl_csv = rep_dir/f"clusters_{set_name}.csv"
    with cl_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","metric"])
        for m, cid in sorted(zip(cols, cl), key=lambda x: (x[1], x[0])):
            w.writerow([cid, m])
    # dendrogram plot
    if plt is not None:
        plt.figure(figsize=(12, 6))
        dendrogram(Z, labels=cols, leaf_rotation=90)
        plt.axhline(y=cut_d, color='red', linestyle='--', linewidth=1)
        OUT = OUTDIR/"plots"/f"dendrogram_{set_name}.png"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(OUT, dpi=200)
        plt.close()
    print("Saved clusters:", cl_csv)

if __name__ == '__main__':
    import sys
    set_name = sys.argv[1] if len(sys.argv)>1 else 'raw'
    cut_d = float(sys.argv[2]) if len(sys.argv)>2 else 0.30
    cluster_and_plot(set_name, cut_d)
