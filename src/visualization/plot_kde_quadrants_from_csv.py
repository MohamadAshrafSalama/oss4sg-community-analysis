#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'Join Rate vs Leave Rate for all stages.csv'
OUTDIR = BASE / 'exper8_out' / 'plots'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Fixed medians from paper
JOIN_MED = 0.182
LEAVE_MED = 0.164

BG_BEIGE = '#efeede'
GREEN_Q = 'palegreen'
RED_Q = 'salmon'
LINE_KW = dict(color='black', linestyle='--', linewidth=2, zorder=3)
KDE_LEVELS = 12
KDE_ALPHA = 0.55
BW_OSS = 0.10
BW_SG = 0.12
FONT = 'Arial'

df = pd.read_csv(INPUT)
# Normalize column names to expected ones
lr_col = 'Average Leave Rate'
jr_col = 'Average Join Rate'
sg_col = 'SG'
for c in [lr_col, jr_col]:
    df[c] = pd.to_numeric(df[c], errors='coerce').clip(0,1)

df = df.dropna(subset=[lr_col, jr_col, sg_col]).copy()

def gaussian_kde_2d(x, y, grid_size=160, bw=0.10):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size == 0:
        g = np.linspace(0,1,grid_size)
        X,Y = np.meshgrid(g,g)
        return X,Y,np.zeros_like(X)
    gx = gy = np.linspace(0,1,grid_size)
    X,Y = np.meshgrid(gx,gy)
    inv = 1.0/(bw+1e-12)
    dx = (X[None,:,:]-x[:,None,None])*inv
    dy = (Y[None,:,:]-y[:,None,None])*inv
    K = np.exp(-0.5*(dx*dx+dy*dy))
    Z = K.sum(axis=0)
    Z /= (2.0*np.pi*(bw**2)*max(len(x),1))
    return X,Y,Z


def add_quadrant_background(ax):
    ax.set_facecolor(BG_BEIGE)
    ax.add_patch(Rectangle((0,0), LEAVE_MED, 1, facecolor=GREEN_Q, alpha=0.18, zorder=0))
    ax.add_patch(Rectangle((0,0), 1, JOIN_MED, facecolor=RED_Q, alpha=0.18, zorder=0))
    ax.axhline(JOIN_MED, **LINE_KW)
    ax.axvline(LEAVE_MED, **LINE_KW)
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=14, color='green', fontweight='bold', va='top', fontname=FONT)
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=14, color='red', fontweight='bold', ha='right', fontname=FONT)
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=14, color='blue', fontweight='bold', va='bottom', fontname=FONT)
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=14, color='orange', fontweight='bold', ha='right', va='top', fontname=FONT)


def draw_panel(ax, data, title, cmap, bw):
    if not data.empty:
        X,Y,Z = gaussian_kde_2d(data[lr_col].values, data[jr_col].values, grid_size=160, bw=bw)
        zmax = Z.max() if np.isfinite(Z).any() else 0.0
        thresh = 0.05*zmax if zmax>0 else 0.0
        Zm = np.ma.masked_less_equal(Z, thresh)
        ax.contourf(X,Y,Zm, levels=KDE_LEVELS, cmap=cmap, alpha=KDE_ALPHA, zorder=2)
    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.set_title(title, fontname=FONT)
    ax.set_xlabel('Average Leave Rate', fontname=FONT)
    ax.set_ylabel('Average Join Rate', fontname=FONT)
    for s in ax.spines.values(): s.set_alpha(0.6)
    ax.grid(color='#b6b6b6', linewidth=0.8, alpha=0.6)
    add_quadrant_background(ax)

fig, axs = plt.subplots(1,2, figsize=(14,6), sharey=True)
oss = df[df[sg_col]==0]
sg = df[df[sg_col]==1]

draw_panel(axs[0], oss, 'OSS', 'Blues', BW_OSS)
axs[1].set_ylabel('')
draw_panel(axs[1], sg, 'OSS4SG', 'Reds', BW_SG)

fig.tight_layout()
(png1 := OUTDIR/'kde_quadrants_fixed_medians_from_original_csv.png')
(pdf1 := OUTDIR/'kde_quadrants_fixed_medians_from_original_csv.pdf')
fig.savefig(png1, dpi=300)
fig.savefig(pdf1)
print('Saved', png1)
print('Saved', pdf1)
