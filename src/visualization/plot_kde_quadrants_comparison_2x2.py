#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ORIG = BASE / 'Join Rate vs Leave Rate for all stages.csv'
OUR = BASE / 'exper8_out' / 'join_leave_rates_3mo_contributors.csv'
OUTDIR = BASE / 'exper8_out' / 'plots'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Fixed medians from the notebook/paper
JOIN_MED = 0.182
LEAVE_MED = 0.164

sns.set_style('whitegrid')

# KDE params
TOP_THRESH = 0.05  # original data unchanged
TOP_BW = 1.0
BOT_THRESH = 0.09  # apply slightly stronger filtering to our data only
BOT_BW = 1.15
GRID = 180


def add_quadrant(ax, hide_legend=False):
    ax.axvspan(0, LEAVE_MED, color='lightblue', alpha=0.15, zorder=0)
    ax.axvspan(LEAVE_MED, 1, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(0, JOIN_MED, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(JOIN_MED, 1, color='lightgreen', alpha=0.15, zorder=0)
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=12, color='green', fontweight='bold', va='top', fontname='Arial')
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=12, color='red', fontweight='bold', ha='right', fontname='Arial')
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=12, color='blue', fontweight='bold', va='bottom', fontname='Arial')
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=12, color='orange', fontweight='bold', ha='right', va='top')
    ax.axhline(JOIN_MED, color='black', linestyle='--', zorder=1)
    ax.axvline(LEAVE_MED, color='black', linestyle='--', zorder=1)
    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()


def load_original():
    df = pd.read_csv(ORIG)
    for c in ('Average Join Rate','Average Leave Rate'):
        df[c] = pd.to_numeric(df[c], errors='coerce').clip(0,1)
    df = df.dropna(subset=['Average Join Rate','Average Leave Rate','SG']).copy()
    return df


def load_our():
    df = pd.read_csv(OUR)
    for c in ('avg_join_rate','avg_leave_rate'):
        df[c] = pd.to_numeric(df[c], errors='coerce').clip(0,1)
    df = df.dropna(subset=['avg_join_rate','avg_leave_rate','category']).copy()
    return df


def main():
    dfo = load_original()
    dfr = load_our()

    fig, axs = plt.subplots(2, 2, figsize=(12, 10), sharey=True, sharex=True)

    # Top-left: Original OSS
    sns.kdeplot(
        data=dfo[dfo['SG']==0], x='Average Leave Rate', y='Average Join Rate',
        color='blue', fill=True, alpha=0.6, thresh=TOP_THRESH, levels=10,
        bw_adjust=TOP_BW, gridsize=GRID, cut=0, clip=((0,1),(0,1)),
        ax=axs[0,0], zorder=2
    )
    axs[0,0].set_xlim(0,1); axs[0,0].set_ylim(0,1)
    axs[0,0].set_title('Original OSS')
    axs[0,0].set_ylabel('Average Join Rate')
    add_quadrant(axs[0,0], hide_legend=True)

    # Top-right: Original OSS4SG
    sns.kdeplot(
        data=dfo[dfo['SG']==1], x='Average Leave Rate', y='Average Join Rate',
        color='red', fill=True, alpha=0.6, thresh=TOP_THRESH, levels=10,
        bw_adjust=TOP_BW, gridsize=GRID, cut=0, clip=((0,1),(0,1)),
        ax=axs[0,1], zorder=2
    )
    axs[0,1].set_xlim(0,1); axs[0,1].set_ylim(0,1)
    axs[0,1].set_title('Original OSS4SG')
    add_quadrant(axs[0,1])

    # Bottom-left: Our data OSS (cutoff applied)
    sns.kdeplot(
        data=dfr[dfr['category']=='OSS'], x='avg_leave_rate', y='avg_join_rate',
        color='blue', fill=True, alpha=0.6, thresh=BOT_THRESH, levels=10,
        bw_adjust=BOT_BW, gridsize=GRID, cut=0, clip=((0,1),(0,1)),
        ax=axs[1,0], zorder=2
    )
    axs[1,0].set_xlim(0,1); axs[1,0].set_ylim(0,1)
    axs[1,0].set_title('Our Data OSS (cutoff)')
    axs[1,0].set_xlabel('Average Leave Rate')
    axs[1,0].set_ylabel('Average Join Rate')
    add_quadrant(axs[1,0], hide_legend=True)

    # Bottom-right: Our data OSS4SG (cutoff applied)
    sns.kdeplot(
        data=dfr[dfr['category']=='OSS4SG'], x='avg_leave_rate', y='avg_join_rate',
        color='red', fill=True, alpha=0.6, thresh=BOT_THRESH, levels=10,
        bw_adjust=BOT_BW, gridsize=GRID, cut=0, clip=((0,1),(0,1)),
        ax=axs[1,1], zorder=2
    )
    axs[1,1].set_xlim(0,1); axs[1,1].set_ylim(0,1)
    axs[1,1].set_title('Our Data OSS4SG (cutoff)')
    axs[1,1].set_xlabel('Average Leave Rate')
    add_quadrant(axs[1,1])

    fig.tight_layout()
    out_png = OUTDIR / 'kde_quadrants_comparison_2x2.png'
    out_pdf = OUTDIR / 'kde_quadrants_comparison_2x2.pdf'
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf, dpi=300)
    print('Saved', out_png)
    print('Saved', out_pdf)

if __name__ == '__main__':
    main()
