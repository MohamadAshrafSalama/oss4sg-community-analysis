import csv
from pathlib import Path

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
                mat[i-1][j] = 0.0
    return cols, mat


def invert_matrix(a):
    n = len(a)
    # build augmented matrix [A | I]
    aug = [row[:] + [0.0]*n for row in a]
    for i in range(n):
        aug[i][n+i] = 1.0
    # Gauss-Jordan
    for col in range(n):
        # find pivot
        pivot = col
        for r in range(col+1, n):
            if abs(aug[r][col]) > abs(aug[pivot][col]):
                pivot = r
        if abs(aug[pivot][col]) < 1e-12:
            # add small ridge to diagonal and retry
            for i in range(n):
                aug[i][i] += 1e-6
            pivot = col
            for r in range(col+1, n):
                if abs(aug[r][col]) > abs(aug[pivot][col]):
                    pivot = r
            if abs(aug[pivot][col]) < 1e-12:
                raise ValueError("Singular matrix even after ridge")
        # swap rows
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        # normalize
        pivval = aug[col][col]
        fac = 1.0 / pivval
        for j in range(2*n):
            aug[col][j] *= fac
        # eliminate
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor == 0:
                continue
            for j in range(2*n):
                aug[r][j] -= factor * aug[col][j]
    inv = [row[n:] for row in aug]
    return inv


def main(set_name: str):
    cols, corr = read_corr(set_name)
    inv = invert_matrix(corr)
    # VIF = diag(inv)
    out = OUTDIR/"reports"/f"vif_{set_name}.csv"
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["metric","vif"])
        for i, m in enumerate(cols):
            v = inv[i][i]
            w.writerow([m, f"{v:.6f}"])
    print('Saved:', out)

if __name__ == '__main__':
    import sys
    set_name = sys.argv[1] if len(sys.argv)>1 else 'raw'
    main(set_name)