#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'Join Rate vs Leave Rate for all stages.csv'
OUTDIR = BASE / 'exper8_out' / 'plots'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Fixed medians from paper
join_rate_median = 0.182
leave_rate_median = 0.164

# Load
df = pd.read_csv(INPUT)
for c in ('Average Join Rate','Average Leave Rate'):
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df.dropna(subset=['Average Join Rate','Average Leave Rate','SG'])

sns.set_style('whitegrid')

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

fig, axs = plt.subplots(1,2, figsize=(12,6), sharey=True)

sns.kdeplot(
    data=df[df['SG']==0],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='blue',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[0],
    zorder=2
)
axs[0].set_xlim(0,1); axs[0].set_ylim(0,1)
axs[0].set_title('OSS Only - All Stages')
axs[0].set_xlabel('Average Leave Rate')
axs[0].set_ylabel('Average Join Rate')
add_quadrant_labels_and_lines(axs[0], hide_legend=True)

sns.kdeplot(
    data=df[df['SG']==1],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='red',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[1],
    zorder=2
)
axs[1].set_xlim(0,1); axs[1].set_ylim(0,1)
axs[1].set_title('OSS4SG Only - All Stages')
axs[1].set_xlabel('Average Leave Rate')
add_quadrant_labels_and_lines(axs[1])

plt.tight_layout()
# Save with notebook-style filenames
plt.savefig(OUTDIR / 'kde_plots_with_light_shaded_quadrants.png', dpi=300)
plt.savefig(OUTDIR / 'kde_plots_with_light_shaded_quadrants.pdf', dpi=300)
print('Saved', OUTDIR / 'kde_plots_with_light_shaded_quadrants.png')
