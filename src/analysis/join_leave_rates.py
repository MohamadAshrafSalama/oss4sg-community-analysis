#!/usr/bin/env python3
import csv
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
import math
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1].parents[0]
COMMITS = ROOT / 'master_commits.csv'
OUTDIR = Path(__file__).resolve().parents[1] / 'exper7_out'
OUTDIR.mkdir(parents=True, exist_ok=True)

DATE_FMT = '%Y-%m-%d %H:%M:%S %z'
WINDOW_MONTHS = 3

# Parse commit rows streaming
# Expect columns: project, category, commit, author_name, author_email, date, message

def month_floor(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, 1, tzinfo=dt.tzinfo)

def add_months(dt: datetime, n: int) -> datetime:
    y = dt.year + (dt.month - 1 + n) // 12
    m = (dt.month - 1 + n) % 12 + 1
    return datetime(y, m, 1, tzinfo=dt.tzinfo)

# We'll compute per-project per-month active contributor sets using email+name key
# Then compute rolling 3-month windows: join rate = new entrants / active, leave rate = leavers / active

project_month_to_authors: dict[tuple[str, str], set[str]] = defaultdict(set)
project_category: dict[str, str] = {}

with COMMITS.open('r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    for rec in reader:
        proj = (rec.get('project') or '').strip()
        if not proj:
            continue
        cat = (rec.get('category') or '').strip() or 'OSS'
        project_category.setdefault(proj, cat)
        date_raw = rec.get('date') or ''
        try:
            dt = datetime.strptime(date_raw, DATE_FMT)
        except Exception:
            # try fallback without tz
            try:
                dt = datetime.strptime(date_raw.split(' +')[0], '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=None)
            except Exception:
                continue
        month_key_dt = month_floor(dt)
        month_key = month_key_dt.strftime('%Y-%m')
        author = (rec.get('author_email') or rec.get('author_name') or '').strip().lower()
        if not author:
            continue
        project_month_to_authors[(proj, month_key)].add(author)

# Build timeline per project
per_project_months = defaultdict(list)
for (proj, m), s in project_month_to_authors.items():
    per_project_months[proj].append(m)
for proj in per_project_months:
    months = sorted(set(per_project_months[proj]))
    per_project_months[proj] = months

# Compute rolling window join/leave rates
# For each window W of 3 months, active set A = union authors in W
# Previous window P = union authors in previous 3 months
# Joiners = |A \ P| / |A|
# Leavers = |P \ A| / |P|  (use previous base to reflect leaving)

results = []
for proj, months in per_project_months.items():
    if len(months) == 0:
        continue
    # Build map month->authors for quick lookup
    m_to_auth = defaultdict(set)
    for m in months:
        m_to_auth[m] = project_month_to_authors[(proj, m)]
    # Ensure continuous monthly sequence from min to max
    y0, m0 = map(int, months[0].split('-'))
    y1, m1 = map(int, months[-1].split('-'))
    seq = []
    y, m = y0, m0
    while (y < y1) or (y == y1 and m <= m1):
        seq.append(f'{y:04d}-{m:02d}')
        m += 1
        if m == 13:
            m = 1
            y += 1
    # Helper to get union over a slice of months
    def union_over(idx_start: int, idx_end_inclusive: int) -> set[str]:
        u: set[str] = set()
        for i in range(idx_start, idx_end_inclusive + 1):
            mon = seq[i]
            u |= m_to_auth.get(mon, set())
        return u
    w = WINDOW_MONTHS
    join_rates = []
    leave_rates = []
    for i in range(w-1, len(seq)):
        # current window [i-w+1 .. i]
        cur_start = i - (w - 1)
        cur_end = i
        prev_end = cur_start - 1
        prev_start = prev_end - (w - 1)
        A = union_over(cur_start, cur_end)
        if prev_start >= 0:
            P = union_over(prev_start, prev_end)
        else:
            P = set()
        if len(A) > 0:
            join = len(A - P) / len(A)
        else:
            join = math.nan
        if len(P) > 0:
            leave = len(P - A) / len(P)
        else:
            leave = math.nan
        if not math.isnan(join):
            join_rates.append(join)
        if not math.isnan(leave):
            leave_rates.append(leave)
    if join_rates or leave_rates:
        avg_join = sum(join_rates)/len(join_rates) if join_rates else math.nan
        avg_leave = sum(leave_rates)/len(leave_rates) if leave_rates else math.nan
        results.append({
            'repo': proj,
            'category': project_category.get(proj, ''),
            'avg_join_rate': f'{avg_join:.6f}' if not math.isnan(avg_join) else '',
            'avg_leave_rate': f'{avg_leave:.6f}' if not math.isnan(avg_leave) else ''
        })

# Save per-project CSV
OUTCSV = OUTDIR / 'join_leave_rates_3mo.csv'
with OUTCSV.open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['repo','category','avg_join_rate','avg_leave_rate'])
    w.writeheader()
    w.writerows(results)
print('Saved', OUTCSV)

# Plot quadrant figure per category with medians
import numpy as np
import matplotlib.pyplot as plt

for cat in ('OSS','OSS4SG'):
    pts = [(float(r['avg_join_rate']), float(r['avg_leave_rate'])) for r in results if r['category']==cat and r['avg_join_rate']!='' and r['avg_leave_rate']!='']
    if not pts:
        continue
    X = np.array(pts)
    join = X[:,0]; leave = X[:,1]
    med_join = float(np.median(join))
    med_leave = float(np.median(leave))

    fig, ax = plt.subplots(figsize=(6.5,5.0))
    # background quadrants
    ax.axvspan(0, med_leave, 0, med_join, facecolor='#e5f7e5', alpha=0.6) # Attractive (low leave, high join)
    ax.axvspan(med_leave, 1, 0, med_join, facecolor='#fff2cc', alpha=0.6)   # Unstable
    ax.axvspan(0, med_leave, 0, 0.2, facecolor='#e6f2ff', alpha=0.6)        # Stable-ish bottom-left (for visual)
    ax.axvspan(med_leave, 1, 0, 0.2, facecolor='#fdeaea', alpha=0.6)        # Unattractive-ish

    ax.scatter(leave, join, s=10, c=('tab:blue' if cat=='OSS' else 'tab:red'), alpha=0.35, edgecolors='none')
    ax.axvline(med_leave, color='k', linestyle='--', linewidth=1)
    ax.axhline(med_join, color='k', linestyle='--', linewidth=1)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Average Leave Rate')
    ax.set_ylabel('Average Join Rate')
    ax.set_title(cat)

    OUTP = OUTDIR / 'plots'
    OUTP.mkdir(parents=True, exist_ok=True)
    out = OUTP / f'join_leave_quadrant_{cat.lower()}.png'
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print('Saved', out)

# Combined figure side-by-side
imgs = []
try:
    import matplotlib.image as mpimg
    oss_img = mpimg.imread(OUTDIR/'plots'/'join_leave_quadrant_oss.png')
    sg_img = mpimg.imread(OUTDIR/'plots'/'join_leave_quadrant_oss4sg.png')
    imgs = [oss_img, sg_img]
except Exception:
    imgs = []

if imgs:
    fig, axes = plt.subplots(1,2, figsize=(12,5))
    titles = ['OSS', 'OSS4SG']
    for ax, img, t in zip(axes, imgs, titles):
        ax.imshow(img)
        ax.axis('off')
        ax.set_title(t)
    out = OUTDIR/'plots'/'join_leave_quadrants.png'
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print('Saved', out)
