import csv, math
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / 'exper7_out'


def read_corr(set_name: str):
    p = OUTDIR/'corr'/f'{set_name}_spearman.csv'
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


def to_distance(corr):
    n = len(corr)
    D = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            c = corr[i][j]
            d = 1.0 - abs(c) if not math.isnan(c) else 1.0
            D[i][j] = d
    return D


def average_linkage(D):
    # naive O(n^3) average-linkage clustering; returns merges [(i,j,height,size)]
    n = len(D)
    clusters = {i:[i] for i in range(n)}
    active = set(range(n))
    next_id = n
    merges = []
    # distance between clusters as average of pairwise
    def clust_dist(a_members, b_members):
        s = 0.0; cnt = 0
        for i in a_members:
            for j in b_members:
                if i==j: continue
                s += D[i][j]; cnt += 1
        return s/cnt if cnt>0 else 0.0
    # work on dynamic copy of distances using member lists
    while len(active) > 1:
        best = None
        act_list = list(active)
        for i_idx in range(len(act_list)):
            for j_idx in range(i_idx+1, len(act_list)):
                a = act_list[i_idx]; b = act_list[j_idx]
                da = clust_dist(clusters[a], clusters[b])
                if best is None or da < best[0]:
                    best = (da, a, b)
        h, a, b = best
        # record merge; size = |a|+|b|
        merges.append((a, b, h, len(clusters[a]) + len(clusters[b])))
        # new cluster id
        clusters[next_id] = clusters[a] + clusters[b]
        active.add(next_id)
        # remove a,b
        active.remove(a); active.remove(b)
        next_id += 1
    return merges


def plot_dendrogram(set_name: str):
    if plt is None:
        print('Matplotlib unavailable; skip')
        return
    cols, corr = read_corr(set_name)
    D = to_distance(corr)
    merges = average_linkage(D)
    # build basic dendrogram coordinates (simple plotting: merge heights vs steps)
    # For readability, just plot merge heights as a line plot; label last merges.
    heights = [m[2] for m in merges]
    x = list(range(1, len(heights)+1))
    plt.figure(figsize=(10,4))
    plt.plot(x, heights, '-o', markersize=2)
    plt.title(f'Average-linkage dendrogram (distance = 1-|rho|) – {set_name}')
    plt.xlabel('merge step'); plt.ylabel('distance')
    OUT = OUTDIR/'plots'/f'dendrogram_simple_{set_name}.png'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(OUT, dpi=200); plt.close()
    print('Saved', OUT)

if __name__ == '__main__':
    import sys
    s = sys.argv[1] if len(sys.argv)>1 else 'raw'
    plot_dendrogram(s)
