#!/usr/bin/env python3
import csv
from pathlib import Path
from datetime import datetime, timedelta
import math
import numpy as np
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1].parents[0]
EXP1 = BASE / "EXP1(Rdoing_overlapping_and_double_check_numbers)" / "Datasets"
CONTRIB_DIR = EXP1 / "ContributorInfo"
OSS = EXP1 / "Filtered-OSS-Project-Info.csv"
OSS4SG = EXP1 / "Filtered-OSS4SG-Project-Info.csv"
OUTDIR = Path(__file__).resolve().parents[1] / 'exper8_out'
(OUTDIR / 'plots').mkdir(parents=True, exist_ok=True)
(OUTDIR / 'reports').mkdir(parents=True, exist_ok=True)

BUFFER_MONTHS = 5
WINDOW_MONTHS = 3
DATE_FMT = "%Y-%m-%d %H:%M:%S"
# Hard cutoff: ignore contributions after this date
CUTOFF_DATE = datetime(2024, 10, 31, 23, 59, 59)


def parse_dt(value: str):
    try:
        return datetime.strptime(value, DATE_FMT)
    except Exception:
        return None


def month_floor(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, 1)


def add_months(dt: datetime, n: int) -> datetime:
    y = dt.year + (dt.month - 1 + n) // 12
    m = (dt.month - 1 + n) % 12 + 1
    return datetime(y, m, 1)


def load_repo_lists():
    repos = []
    for path, cat in [(OSS, 'OSS'), (OSS4SG, 'OSS4SG')]:
        with path.open(encoding='utf-8', newline='') as f:
            r = csv.DictReader(f)
            for rec in r:
                name = (rec.get('name') or '').strip()
                if not name:
                    continue
                owner_repo = name
                repo = owner_repo.split('/')[-1]
                repos.append((owner_repo, repo, cat))
    return repos


def read_contrib_file(repo_name: str):
    # Files are like OpenFarmContributors.csv (repo part only)
    p = CONTRIB_DIR / f"{repo_name}Contributors.csv"
    if not p.exists():
        return None
    rows = []
    with p.open(encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        header = next(r, None)
        # Expect columns: User, Number of Contributions, First Contribution, Last Contribution, Active, ...
        for row in r:
            if len(row) < 5:
                continue
            first = parse_dt(row[2]) if row[2] else None
            last = parse_dt(row[3]) if row[3] else None
            rows.append((row[0], first, last))
    return rows


def compute_rates_for_repo(contribs):
    # contribs: list of (user, first_dt, last_dt)
    # Trim to cutoff window; drop users who joined strictly after cutoff
    trimmed = []
    for (u, f, l) in contribs:
        if f is None or l is None:
            continue
        if f > CUTOFF_DATE:
            # Joined after analysis window
            continue
        l2 = l if l <= CUTOFF_DATE else CUTOFF_DATE
        trimmed.append((u, f, l2))

    if not trimmed:
        return math.nan, math.nan
    min_first = min(f for (_, f, _) in trimmed)
    max_last = max(l for (_, _, l) in trimmed)
    start = month_floor(min_first)
    # Do not extend beyond cutoff month
    end = min(add_months(month_floor(max_last), 1), add_months(month_floor(CUTOFF_DATE), 1))
    # 5-month inactivity buffer relative to cutoff
    buf_cut = CUTOFF_DATE - timedelta(days=BUFFER_MONTHS * 30)

    join_rates = []
    leave_rates = []

    w = WINDOW_MONTHS
    # build monthly sequence
    months = []
    cur = start
    while cur < end:
        months.append(cur)
        cur = add_months(cur, 1)

    # Precompute effective last dates (replace recent last with now)
    eff = []
    now = CUTOFF_DATE
    for (u, f, l) in trimmed:
        L = now if l and l > buf_cut else l
        eff.append((u, f, L))

    for i in range(w - 1, len(months)):
        win_start = months[i - (w - 1)]
        win_end = add_months(months[i], 1)  # end is next month start
        # Active in window: first <= win_end and last >= win_start
        active = [c for c in eff if c[1] <= win_end and c[2] >= win_start]
        A = len(active)
        if A == 0:
            continue
        joins = sum(1 for (_, f, _) in eff if f >= win_start and f < win_end)
        leaves = sum(1 for (_, _, l) in eff if l >= win_start and l < win_end and l <= buf_cut)
        join_rates.append(joins / A)
        leave_rates.append(leaves / A)

    if not join_rates or not leave_rates:
        return math.nan, math.nan
    return float(np.mean(join_rates)), float(np.mean(leave_rates))


def main():
    repos = load_repo_lists()
    out_rows = []
    for owner_repo, repo, cat in repos:
        contribs = read_contrib_file(repo)
        if contribs is None:
            continue
        avg_join, avg_leave = compute_rates_for_repo(contribs)
        if not (math.isnan(avg_join) or math.isnan(avg_leave)):
            out_rows.append({'repo': owner_repo, 'category': cat, 'avg_join_rate': f"{avg_join:.6f}", 'avg_leave_rate': f"{avg_leave:.6f}"})

    # write CSV
    out_csv = OUTDIR / 'join_leave_rates_3mo_contributors.csv'
    with out_csv.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['repo','category','avg_join_rate','avg_leave_rate'])
        w.writeheader()
        w.writerows(out_rows)
    print('Saved', out_csv)

    # plots per category
    for cat in ('OSS','OSS4SG'):
        pts = [(float(r['avg_join_rate']), float(r['avg_leave_rate'])) for r in out_rows if r['category']==cat]
        if not pts:
            continue
        X = np.array(pts)
        join = X[:,0]; leave = X[:,1]
        med_join = float(np.median(join))
        med_leave = float(np.median(leave))

        fig, ax = plt.subplots(figsize=(6.5,5.0))
        # background quadrants
        ax.axhspan(med_join, 1, xmin=0, xmax=med_leave, facecolor='#e5f7e5', alpha=0.5)  # Attractive (top-left)
        ax.axhspan(0, med_join, xmin=0, xmax=med_leave, facecolor='#e6f2ff', alpha=0.5)  # Stable (bottom-left)
        ax.axhspan(med_join, 1, xmin=med_leave, xmax=1, facecolor='#fff2cc', alpha=0.5) # Unstable (top-right)
        ax.axhspan(0, med_join, xmin=med_leave, xmax=1, facecolor='#fdeaea', alpha=0.5) # Unattractive (bottom-right)

        ax.scatter(leave, join, s=12, c=('tab:blue' if cat=='OSS' else 'tab:red'), alpha=0.35, edgecolors='none')
        ax.axvline(med_leave, color='k', linestyle='--', linewidth=1)
        ax.axhline(med_join, color='k', linestyle='--', linewidth=1)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Average Leave Rate')
        ax.set_ylabel('Average Join Rate')
        ax.set_title(cat)
        outp = OUTDIR / 'plots' / f'join_leave_quadrant_{cat.lower()}_contributors.png'
        fig.tight_layout()
        fig.savefig(outp, dpi=200)
        plt.close(fig)
        print('Saved', outp)

    # combined
    try:
        import matplotlib.image as mpimg
        oss_img = mpimg.imread(OUTDIR/'plots'/'join_leave_quadrant_oss_contributors.png')
        sg_img = mpimg.imread(OUTDIR/'plots'/'join_leave_quadrant_oss4sg_contributors.png')
        fig, axes = plt.subplots(1,2, figsize=(12,5))
        for ax, img, t in zip(axes, [oss_img, sg_img], ['OSS','OSS4SG']):
            ax.imshow(img); ax.axis('off'); ax.set_title(t)
        outc = OUTDIR/'plots'/'join_leave_quadrants_contributors.png'
        fig.tight_layout(); fig.savefig(outc, dpi=200); plt.close(fig)
        print('Saved', outc)
    except Exception:
        pass

if __name__ == '__main__':
    main()
