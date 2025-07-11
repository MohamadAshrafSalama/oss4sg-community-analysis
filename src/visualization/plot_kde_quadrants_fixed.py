#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parents[1]
CSV = BASE / 'exper8_out' / 'join_leave_rates_3mo_contributors.csv'
PLOTS = BASE / 'exper8_out' / 'plots'
PLOTS.mkdir(parents=True, exist_ok=True)

# Fixed medians from paper
JOIN_MED = 0.182
LEAVE_MED = 0.164

# Styling params to mimic paper
BG_BEIGE = '#efeede'  # light beige background
GREEN_Q = 'palegreen'
RED_Q = 'salmon'
LINE_KW = dict(color='black', linestyle='--', linewidth=2, zorder=3)
KDE_LEVELS = 12
KDE_ALPHA = 0.55
BW_OSS = 0.8
BW_SG = 0.9
FONT = 'Arial'

# Load
_df = pd.read_csv(CSV)
for c in ('avg_join_rate','avg_leave_rate'):
    _df[c] = pd.to_numeric(_df[c], errors='coerce')
df = _df.dropna(subset=['avg_join_rate','avg_leave_rate']).copy()
df['SG'] = (df['category'] == 'OSS4SG').astype(int)


def add_quadrant_background(ax):
    # base beige background
    ax.set_facecolor(BG_BEIGE)
    # left-of-median column overlay (attractive side)
    ax.add_patch(Rectangle((0, 0), LEAVE_MED, 1, facecolor=GREEN_Q, alpha=0.18, zorder=0))
    # bottom row overlay (unattractive side)
    ax.add_patch(Rectangle((0, 0), 1, JOIN_MED, facecolor=RED_Q, alpha=0.18, zorder=0))
    # median lines
    ax.axhline(JOIN_MED, **LINE_KW)
    ax.axvline(LEAVE_MED, **LINE_KW)

    # Labels
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=14, color='green',
            fontweight='bold', va='top', fontname=FONT)
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=14, color='red',
            fontweight='bold', ha='right', fontname=FONT)
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=14, color='blue',
            fontweight='bold', va='bottom', fontname=FONT)
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=14, color='orange',
            fontweight='bold', ha='right', va='top', fontname=FONT)


def gaussian_kde_2d(x, y, grid_size=150, bw=0.10):
    """Compute a simple 2D Gaussian KDE on [0,1]x[0,1] without external deps.

    Parameters
    - x, y: 1D arrays in [0,1]
    - grid_size: grid resolution per axis
    - bw: bandwidth (fraction of range)
    Returns
    - X, Y meshgrid and density array Z
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    # Guard for empty input
    if x.size == 0:
        gx = gy = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(gx, gy)
        return X, Y, np.zeros_like(X)

    gx = gy = np.linspace(0, 1, grid_size)
    X, Y = np.meshgrid(gx, gy)

    # Vectorized Gaussian kernel sum
    # shape: (n, grid, grid)
    inv = 1.0 / (bw + 1e-12)
    dx = (X[None, :, :] - x[:, None, None]) * inv
    dy = (Y[None, :, :] - y[:, None, None]) * inv
    K = np.exp(-0.5 * (dx * dx + dy * dy))
    Z = K.sum(axis=0)
    # Normalize to probability density scale (2*pi*bw^2)
    Z /= (2.0 * np.pi * (bw ** 2) * max(len(x), 1))
    return X, Y, Z


def draw_panel(ax, data, title, cmap, bw):
    if not data.empty:
        X, Y, Z = gaussian_kde_2d(
            data['avg_leave_rate'].values,
            data['avg_join_rate'].values,
            grid_size=160,
            bw=bw,
        )
        # Mask extremely low density to mimic thresh
        zmax = Z.max() if np.isfinite(Z).any() else 0.0
        thresh = 0.05 * zmax if zmax > 0 else 0.0
        Zm = np.ma.masked_less_equal(Z, thresh)
        ax.contourf(X, Y, Zm, levels=KDE_LEVELS, cmap=cmap, alpha=KDE_ALPHA, zorder=2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontname=FONT)
    ax.set_xlabel('Average Leave Rate', fontname=FONT)
    ax.set_ylabel('Average Join Rate', fontname=FONT)
    for spine in ax.spines.values():
        spine.set_alpha(0.6)
    ax.grid(color='#b6b6b6', linewidth=0.8, alpha=0.6)
    add_quadrant_background(ax)


fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
oss = df[df['SG'] == 0]
sg = df[df['SG'] == 1]

# Ensure y label only on left
draw_panel(axs[0], oss, 'OSS', 'Blues', BW_OSS)
axs[1].set_ylabel('')
draw_panel(axs[1], sg, 'OSS4SG', 'Reds', BW_SG)

fig.tight_layout()
# Save both the original fixed filename and a styled variant
out_pdf = PLOTS / 'kde_quadrants_fixed_medians_contributors.pdf'
out_png = PLOTS / 'kde_quadrants_fixed_medians_contributors.png'
out_pdf2 = PLOTS / 'kde_quadrants_fixed_medians_contributors_styled.pdf'
out_png2 = PLOTS / 'kde_quadrants_fixed_medians_contributors_styled.png'
fig.savefig(out_pdf, format='pdf', dpi=300)
fig.savefig(out_png, format='png', dpi=300)
fig.savefig(out_pdf2, format='pdf', dpi=300)
fig.savefig(out_png2, format='png', dpi=300)
print('Saved', out_png)
print('Saved', out_png2)
