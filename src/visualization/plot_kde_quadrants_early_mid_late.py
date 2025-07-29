#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
DATA_DIR = ROOT / "EXP1(Rdoing_overlapping_and_double_check_numbers)" / 'Datasets' / 'GraphInfo'
OUTDIR = BASE / 'exper8_out' / 'plots'
OUTDIR.mkdir(parents=True, exist_ok=True)

files = {
    'Early': DATA_DIR / 'Join Rate vs Leave Rate for early stages.csv',
    'Mid': DATA_DIR / 'Join Rate vs Leave Rate for mid stages.csv',
    'Late': DATA_DIR / 'Join Rate vs Leave Rate for late stages.csv',
}

DEFAULT_JOIN_MED = 0.182
DEFAULT_LEAVE_MED = 0.164

sns.set_style('whitegrid')


def add_quadrant_labels_and_lines(ax, join_rate_median, leave_rate_median, hide_legend=False):
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


def plot_stage(stage, df, out_prefix):
    # Compute stage-specific medians across both groups
    join_rate_median = df['Average Join Rate'].median() if not df.empty else DEFAULT_JOIN_MED
    leave_rate_median = df['Average Leave Rate'].median() if not df.empty else DEFAULT_LEAVE_MED
    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    # OSS
    sns.kdeplot(
        data=df[df['SG'] == 0],
        x='Average Leave Rate',
        y='Average Join Rate',
        color='blue', fill=True, alpha=0.6, thresh=0.05, levels=10, bw_adjust=1.0, ax=axs[0], zorder=2
    )
    axs[0].set_xlim(0, 1); axs[0].set_ylim(0, 1)
    axs[0].set_title(f'OSS Only - {stage} Stage')
    axs[0].set_xlabel('Average Leave Rate')
    axs[0].set_ylabel('Average Join Rate')
    add_quadrant_labels_and_lines(axs[0], join_rate_median, leave_rate_median, hide_legend=True)

    # OSS4SG
    sns.kdeplot(
        data=df[df['SG'] == 1],
        x='Average Leave Rate',
        y='Average Join Rate',
        color='red', fill=True, alpha=0.6, thresh=0.05, levels=10, bw_adjust=1.0, ax=axs[1], zorder=2
    )
    axs[1].set_xlim(0, 1); axs[1].set_ylim(0, 1)
    axs[1].set_title(f'OSS4SG Only - {stage} Stage')
    axs[1].set_xlabel('Average Leave Rate')
    add_quadrant_labels_and_lines(axs[1], join_rate_median, leave_rate_median)

    plt.tight_layout()
    fig.savefig(OUTDIR / f'{out_prefix}_{stage.lower()}.png', dpi=300)
    fig.savefig(OUTDIR / f'{out_prefix}_{stage.lower()}.pdf', dpi=300)
    plt.close(fig)


def main():
    for stage, path in files.items():
        if not path.exists():
            print('Missing:', path)
            continue
        df = pd.read_csv(path)
        # Coerce numeric
        for c in ('Average Join Rate','Average Leave Rate'):
            df[c] = pd.to_numeric(df[c], errors='coerce')
        df = df.dropna(subset=['Average Join Rate','Average Leave Rate','SG'])
        plot_stage(stage, df, 'kde_quadrants_from_stage_csv')

if __name__ == '__main__':
    main()
