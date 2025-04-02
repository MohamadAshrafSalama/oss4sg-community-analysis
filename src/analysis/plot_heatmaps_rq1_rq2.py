import csv
import math
from pathlib import Path
from collections import defaultdict

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / "exper7_out"


def read_corr(set_name: str):
    # Use the combined RQ1+RQ2 correlation file
    p = OUTDIR / "corr" / f"{set_name}_rq1_rq2_spearman.csv"
    with p.open(encoding='utf-8') as f:
        rows = list(csv.reader(f))
    cols = rows[0][1:]
    n = len(cols)
    mat = [[0.0] * n for _ in range(n)]
    for i in range(1, len(rows)):
        vals = rows[i][1:]
        for j, v in enumerate(vals):
            try:
                mat[i - 1][j] = float(v)
            except Exception:
                mat[i - 1][j] = float('nan')
    return cols, mat


def read_clusters(set_name: str):
    # Try to read clusters file if it exists
    p = OUTDIR / "reports" / f"clusters_{set_name}_rq1_rq2.csv"
    clusters = defaultdict(list)
    if p.exists():
        with p.open(encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                cid_raw = row.get("cluster_id")
                try:
                    cid = int(cid_raw) if cid_raw not in (None, "") else 0
                except Exception:
                    cid = 0
                m = row.get("metric", "")
                if m:
                    clusters[cid].append(m)
    else:
        clusters[0] = []
    # order clusters: by size desc, then cluster id
    ordered = sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    order = []
    for _, members in ordered:
        order.extend(sorted(members))
    return order


def reorder(cols, mat, order):
    remaining = [c for c in cols if c not in order]
    full_order = [c for c in order if c in cols] + remaining
    idx = {c: i for i, c in enumerate(cols)}
    perm = [idx[c] for c in full_order]
    m2 = [[mat[i][j] for j in perm] for i in perm]
    return full_order, m2


def plot_heatmap(set_name: str, absval: bool = False):
    if plt is None:
        print("Matplotlib unavailable; skip plotting")
        return
    cols, mat = read_corr(set_name)
    order = read_clusters(set_name)
    cols_ord, mat_ord = reorder(cols, mat, order)

    data = []
    for row in mat_ord:
        new_row = []
        for v in row:
            if absval and not math.isnan(v):
                new_row.append(abs(v))
            else:
                new_row.append(v)
        data.append(new_row)

    vmin, vmax = ((0.0, 1.0) if absval else (-1.0, 1.0))

    fig = plt.figure(figsize=(14, 12))
    ax = fig.add_subplot(111)
    im = ax.imshow(data, cmap='coolwarm', vmin=vmin, vmax=vmax)
    ax.set_title(f"Spearman {'|rho|' if absval else 'rho'} – {set_name} (RQ1+RQ2)", fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(cols_ord)))
    ax.set_yticks(range(len(cols_ord)))
    ax.set_xticklabels(cols_ord, rotation=90, fontsize=8)
    ax.set_yticklabels(cols_ord, fontsize=8)

    # Draw cluster boundaries using cluster id transitions (if clusters file exists)
    cid_map = {}
    p = OUTDIR / "reports" / f"clusters_{set_name}_rq1_rq2.csv"
    if p.exists():
        with p.open(encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    cid = int(row.get('cluster_id') or 0)
                except Exception:
                    cid = 0
                cid_map[row.get('metric', '')] = cid
        last_cid = None
        for i, m in enumerate(cols_ord):
            cid = cid_map.get(m, 0)
            if last_cid is None:
                last_cid = cid
                continue
            if cid != last_cid:
                ax.axhline(i - 0.5, color='k', linewidth=0.6)
                ax.axvline(i - 0.5, color='k', linewidth=0.6)
                last_cid = cid

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    OUT = OUTDIR / "plots" / f"heatmap_{'abs_' if absval else ''}{set_name}_rq1_rq2.png"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    plt.close(fig)
    print('Saved', OUT)


if __name__ == '__main__':
    import sys
    set_name = sys.argv[1] if len(sys.argv) > 1 else 'raw'
    plot_heatmap(set_name, absval=False)
    plot_heatmap(set_name, absval=True)





