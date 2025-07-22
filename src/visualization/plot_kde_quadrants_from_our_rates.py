#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CSV = BASE / 'exper8_out' / 'join_leave_rates_3mo_contributors.csv'
OUTDIR = BASE / 'exper8_out' / 'plots'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Notebook medians
join_rate_median = 0.182
leave_rate_median = 0.164

# KDE tuning to suppress tiny islands
THRESH = 0.09      # slightly lower to bring back faint contours
BW = 1.10          # reduce smoothing a bit
GRID = 180         # modest grid for speed and smoothness

sns.set_style('whitegrid')

df = pd.read_csv(CSV)
for c in ('avg_join_rate','avg_leave_rate'):
    df[c] = pd.to_numeric(df[c], errors='coerce').clip(0,1)

df = df.dropna(subset=['avg_join_rate','avg_leave_rate','category']).copy()
map_cat = {'OSS4SG':'OSS4SG','OSS':'OSS'}
df['category'] = df['category'].map(map_cat)


def add_quadrant_labels_and_lines(ax, hide_legend=False):
    ax.axvspan(0, leave_rate_median, color='lightblue', alpha=0.15, zorder=0)
    ax.axvspan(leave_rate_median, 1, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(0, join_rate_median, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(join_rate_median, 1, color='lightgreen', alpha=0.15, zorder=0)

    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=14, color='green', fontweight='bold', va='top', fontname='Arial')
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=14, color='red', fontweight='bold', ha='right', fontname='Arial')
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=14, color='blue', fontweight='bold', va='bottom', fontname='Arial')
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=14, color='orange', fontweight='bold', ha='right', va='top')

    ax.axhline(join_rate_median, color='black', linestyle='--', zorder=1)
    ax.axvline(leave_rate_median, color='black', linestyle='--', zorder=1)
    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()


fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# OSS panel
sns.kdeplot(
    data=df[df['category']=='OSS'],
    x='avg_leave_rate', y='avg_join_rate',
    color='blue', fill=True, alpha=0.6,
    thresh=THRESH, levels=10, bw_adjust=BW,
    gridsize=GRID, cut=0, clip=((0,1),(0,1)), ax=axs[0], zorder=2
)
axs[0].set_xlim(0, 1); axs[0].set_ylim(0, 1)
axs[0].set_title('OSS Only - All Stages (cutoff applied)')
axs[0].set_xlabel('Average Leave Rate')
axs[0].set_ylabel('Average Join Rate')
add_quadrant_labels_and_lines(axs[0], hide_legend=True)

# OSS4SG panel
sns.kdeplot(
    data=df[df['category']=='OSS4SG'],
    x='avg_leave_rate', y='avg_join_rate',
    color='red', fill=True, alpha=0.6,
    thresh=THRESH, levels=10, bw_adjust=BW,
    gridsize=GRID, cut=0, clip=((0,1),(0,1)), ax=axs[1], zorder=2
)
axs[1].set_xlim(0, 1); axs[1].set_ylim(0, 1)
axs[1].set_title('OSS4SG Only - All Stages (cutoff applied)')
axs[1].set_xlabel('Average Leave Rate')
add_quadrant_labels_and_lines(axs[1])

plt.tight_layout()
PNG = OUTDIR / 'kde_plots_with_light_shaded_quadrants_from_our_rates_cutoff_smoothed.png'
PDF = OUTDIR / 'kde_plots_with_light_shaded_quadrants_from_our_rates_cutoff_smoothed.pdf'
plt.savefig(PNG, dpi=300)
plt.savefig(PDF, dpi=300)
print('Saved', PNG)
print('Saved', PDF)
