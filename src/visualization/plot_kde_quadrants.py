#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

BASE = Path(__file__).resolve().parents[1]
CSV = BASE / 'exper8_out' / 'join_leave_rates_3mo_contributors.csv'
PLOTS = BASE / 'exper8_out' / 'plots'
PLOTS.mkdir(parents=True, exist_ok=True)

# Load data
df = pd.read_csv(CSV)
# Coerce to numeric
for c in ('avg_join_rate','avg_leave_rate'):
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df.dropna(subset=['avg_join_rate','avg_leave_rate']).copy()
# SG flag: 1 for OSS4SG, 0 for OSS
df['SG'] = (df['category'] == 'OSS4SG').astype(int)

# Compute medians across all projects
join_rate_median = float(df['avg_join_rate'].median())
leave_rate_median = float(df['avg_leave_rate'].median())

sns.set_style('whitegrid')
sg_palette = sns.color_palette('Set1', 2)

# Helper to draw background shading, labels and median lines
def add_quadrant_labels_and_lines(ax, hide_legend=False):
    # Shaded areas for the quadrants (Stable bottom-left, Unstable top-right, etc.)
    ax.axvspan(0, leave_rate_median, color='lightblue', alpha=0.15, zorder=0)   # Stable
    ax.axvspan(leave_rate_median, 1, color='lightcoral', alpha=0.15, zorder=0) # Unstable
    ax.axhspan(0, join_rate_median, color='lightcoral', alpha=0.15, zorder=0)  # Unattractive
    ax.axhspan(join_rate_median, 1, color='lightgreen', alpha=0.15, zorder=0)  # Attractive

    # Labels
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=14, color='green', fontweight='bold', va='top')
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=14, color='red', fontweight='bold', ha='right')
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=14, color='blue', fontweight='bold', va='bottom')
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=14, color='orange', fontweight='bold', ha='right', va='top')

    # Median lines
    ax.axhline(join_rate_median, color='black', linestyle='--', zorder=1)
    ax.axvline(leave_rate_median, color='black', linestyle='--', zorder=1)

    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# OSS only (SG=0)
oss = df[df['SG'] == 0]
sns.kdeplot(
    data=oss,
    x='avg_leave_rate',
    y='avg_join_rate',
    color='blue',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[0],
    zorder=2,
)
axs[0].set_xlim(0, 1)
axs[0].set_ylim(0, 1)
axs[0].set_title('OSS Only - All Stages')
axs[0].set_xlabel('Average Leave Rate')
axs[0].set_ylabel('Average Join Rate')
add_quadrant_labels_and_lines(axs[0], hide_legend=True)

# OSS4SG only (SG=1)
sg = df[df['SG'] == 1]
sns.kdeplot(
    data=sg,
    x='avg_leave_rate',
    y='avg_join_rate',
    color='red',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[1],
    zorder=2,
)
axs[1].set_xlim(0, 1)
axs[1].set_ylim(0, 1)
axs[1].set_title('OSS4SG Only - All Stages')
axs[1].set_xlabel('Average Leave Rate')
add_quadrant_labels_and_lines(axs[1])

plt.tight_layout()

# Save as high-res PDF and PNG
pdf_path = PLOTS / 'kde_plots_with_light_shaded_quadrants_contributors.pdf'
png_path = PLOTS / 'kde_plots_with_light_shaded_quadrants_contributors.png'
plt.savefig(pdf_path, format='pdf', dpi=300)
plt.savefig(png_path, format='png', dpi=300)
print('Saved', pdf_path)
print('Saved', png_path)
