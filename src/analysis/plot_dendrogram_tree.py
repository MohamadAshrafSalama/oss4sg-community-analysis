import csv, math
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import cm
except Exception:
    plt = None

BASE = Path(__file__).resolve().parents[1]
OUTDIR = BASE / 'exper7_out'


class Node:
    def __init__(self, id, left=None, right=None, height=0.0, label=None, size=1):
        self.id = id
        self.left = left
        self.right = right
        self.height = height
        self.label = label
        self.size = size
    def is_leaf(self):
        return self.left is None and self.right is None


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
                mat[i-1][j] = 0.0
    return cols, mat


def to_distance(corr):
    n = len(corr)
    D = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            c = corr[i][j]
            d = 1.0 - abs(c)
            D[i][j] = d
    return D


def average_linkage_tree(D, labels):
    n = len(D)
    nodes = {i: Node(i, label=labels[i], height=0.0, size=1) for i in range(n)}
    clusters = {i: [i] for i in range(n)}
    active = set(range(n))
    next_id = n
    def clust_dist(a_members, b_members):
        s = 0.0; cnt = 0
        for i in a_members:
            for j in b_members:
                if i == j: continue
                s += D[i][j]; cnt += 1
        return s/cnt if cnt>0 else 0.0
    while len(active) > 1:
        best = None
        act = list(active)
        for i in range(len(act)):
            for j in range(i+1, len(act)):
                a, b = act[i], act[j]
                da = clust_dist(clusters[a], clusters[b])
                if best is None or da < best[0]:
                    best = (da, a, b)
        h, a, b = best
        nodes[next_id] = Node(next_id, nodes[a], nodes[b], h, label=None, size=len(clusters[a])+len(clusters[b]))
        clusters[next_id] = clusters[a] + clusters[b]
        active.remove(a); active.remove(b); active.add(next_id)
        next_id += 1
    root_id = list(active)[0]
    return nodes[root_id]


def leaves_inorder(node):
    if node.is_leaf():
        return [node]
    return leaves_inorder(node.left) + leaves_inorder(node.right)


def draw_tree(ax, node, x_pos):
    if node.is_leaf():
        x = x_pos[node.id]
        return x, node.height
    xl, yl = draw_tree(ax, node.left, x_pos)
    xr, yr = draw_tree(ax, node.right, x_pos)
    y = node.height
    ax.plot([xl, xl], [yl, y], color='blue', linewidth=1)
    ax.plot([xr, xr], [yr, y], color='blue', linewidth=1)
    ax.plot([xl, xr], [y, y], color='blue', linewidth=1)
    return (xl + xr) / 2.0, y


def collect_clusters(node, cut):
    # return list of lists of leaf nodes
    leaves = []
    def get_leaves(n):
        if n.is_leaf():
            return [n]
        return get_leaves(n.left) + get_leaves(n.right)
    clusters = []
    def walk(n):
        if n.is_leaf():
            return
        if n.height <= cut:
            clusters.append(get_leaves(n))
        else:
            walk(n.left); walk(n.right)
    walk(node)
    return clusters


def plot_dendrogram(set_name: str, cut: float):
    if plt is None:
        print('Matplotlib unavailable; skip')
        return
    labels, corr = read_corr(set_name)
    D = to_distance(corr)
    root = average_linkage_tree(D, labels)
    leaf_nodes = leaves_inorder(root)
    x_pos = {leaf.id: i for i, leaf in enumerate(leaf_nodes)}

    fig, ax = plt.subplots(figsize=(12, 6))
    draw_tree(ax, root, x_pos)
    ax.axhline(cut, color='black', linestyle='--', linewidth=1)

    ax.set_xticks(range(len(leaf_nodes)))
    ax.set_xticklabels([lf.label for lf in leaf_nodes], rotation=90, fontsize=16)  # 2x original: 8 -> 16
    ax.set_ylabel('distance (1 - |rho|)', fontsize=24)  # 2x original: 12 -> 24
    ax.set_title(f'Average-linkage dendrogram – {set_name}', fontsize=24)  # 2x original: 12 -> 24
    ax.tick_params(axis='y', which='major', labelsize=24)  # 2x original: 12 -> 24

    # Color tick labels by cluster under cut
    clusters = collect_clusters(root, cut)
    colors = plt.cm.tab10.colors if hasattr(plt.cm, 'tab10') else [(0.8,0,0),(0,0.5,0),(0,0,0.8),(0.7,0.4,0)]
    color_cycle = list(colors) * 10
    leaf_to_color = {}
    for ci, comp in enumerate(clusters):
        for lf in comp:
            leaf_to_color[lf.id] = color_cycle[ci]
    for tick, lf in zip(ax.get_xticklabels(), leaf_nodes):
        c = leaf_to_color.get(lf.id)
        if c is not None:
            tick.set_color(c)

    # If cut corresponds to 0.7 correlation threshold, save as _085 (for backward compatibility)
    # cut = 0.3 means correlation threshold = 0.7, cut = 0.15 means correlation threshold = 0.85
    if abs(cut - 0.30) < 0.01:  # 0.7 threshold
        OUT = OUTDIR/'plots'/f'dendrogram_tree_{set_name}_085.png'
    elif abs(cut - 0.15) < 0.01:  # 0.85 threshold  
        OUT = OUTDIR/'plots'/f'dendrogram_tree_{set_name}_085.png'
    else:
        OUT = OUTDIR/'plots'/f'dendrogram_tree_{set_name}.png'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(OUT, dpi=200); plt.close(fig)
    print('Saved', OUT)

if __name__ == '__main__':
    import sys
    s = sys.argv[1] if len(sys.argv)>1 else 'raw'
    cut = float(sys.argv[2]) if len(sys.argv)>2 else 0.30
    plot_dendrogram(s, cut)
