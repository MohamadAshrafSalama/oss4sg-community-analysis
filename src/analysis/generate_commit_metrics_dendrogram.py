#!/usr/bin/env python3
"""
Generate dendrogram analysis for Commit Count, Commit Additions, Commit Deletions
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.stats import spearmanr
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "Data"
OUTPUT_DIR = BASE / "exper7_out" / "plots"
CORR_DIR = BASE / "exper7_out" / "corr"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CORR_DIR.mkdir(parents=True, exist_ok=True)

# Input file
COMMIT_METRICS_CSV = DATA_DIR / "commit_metrics_per_project.csv"

print("="*70)
print("LOADING COMMIT METRICS DATA")
print("="*70)

df = pd.read_csv(COMMIT_METRICS_CSV)
print(f"Loaded {len(df)} projects")

# Filter out projects with zero commits
df = df[df['Commit Count'] > 0].copy()
print(f"Projects with commits: {len(df)}")

metrics = ['Commit Count', 'Commit Additions', 'Commit Deletions']
print(f"\nMetrics: {metrics}")

print(f"\nMetrics summary:")
print(df[metrics].describe())

# Calculate Spearman correlation matrix
print("\n" + "="*70)
print("CALCULATING CORRELATION MATRIX")
print("="*70)

n = len(metrics)
corr_matrix = np.eye(n)  # Identity matrix (diagonal = 1.0)

for i in range(n):
    for j in range(i+1, n):
        metric1 = metrics[i]
        metric2 = metrics[j]
        
        # Get paired values (remove NaN)
        data1 = df[metric1].values
        data2 = df[metric2].values
        
        # Remove NaN pairs
        valid_mask = ~(np.isnan(data1) | np.isnan(data2))
        if valid_mask.sum() > 0:
            corr, pvalue = spearmanr(data1[valid_mask], data2[valid_mask])
            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr
            print(f"  {metric1} vs {metric2}: ρ = {corr:.4f} (p={pvalue:.4f})")
        else:
            corr_matrix[i, j] = np.nan
            corr_matrix[j, i] = np.nan

# Save correlation matrix
corr_csv = CORR_DIR / 'commit_metrics_spearman.csv'
with open(corr_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['metric'] + metrics)
    for i, metric in enumerate(metrics):
        writer.writerow([metric] + [f"{corr_matrix[i, j]:.6f}" for j in range(n)])

print(f"\n✓ Saved correlation matrix: {corr_csv}")

# Create dendrogram
print("\n" + "="*70)
print("CREATING DENDOGRAM WITH 0.7 THRESHOLD")
print("="*70)

# Convert correlation to distance (1 - |correlation|)
abs_corr = np.abs(corr_matrix)
distance_matrix = 1.0 - abs_corr

# Make distance matrix symmetric and handle NaN
for i in range(n):
    for j in range(n):
        if np.isnan(distance_matrix[i, j]):
            distance_matrix[i, j] = 1.0
        if i == j:
            distance_matrix[i, j] = 0.0

# Convert to condensed form for linkage
condensed_dist = []
for i in range(n):
    for j in range(i+1, n):
        condensed_dist.append(distance_matrix[i, j])

# Perform hierarchical clustering
Z = linkage(condensed_dist, method='average')

# Create clusters at 0.7 threshold
cut_distance = 1.0 - 0.7  # 0.3 distance corresponds to 0.7 correlation
clusters = fcluster(Z, cut_distance, criterion='distance')

print(f"\nClusters at 0.7 threshold:")
for i, (metric, cluster_id) in enumerate(zip(metrics, clusters)):
    print(f"  {metric}: Cluster {cluster_id}")

# Save cluster membership
cluster_csv = BASE / "exper7_out" / "reports" / "commit_metrics_clusters.csv"
cluster_csv.parent.mkdir(parents=True, exist_ok=True)
with open(cluster_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['cluster_id', 'metric'])
    for metric, cluster_id in zip(metrics, clusters):
        writer.writerow([cluster_id, metric])

print(f"\n✓ Saved cluster membership: {cluster_csv}")

# Plot dendrogram
fig, ax = plt.subplots(figsize=(10, 8))

# Create dendrogram
dendrogram_result = dendrogram(Z, labels=metrics, leaf_rotation=0, ax=ax, 
                                leaf_font_size=14,
                                color_threshold=0)  # Disable automatic coloring

# Add threshold line
ax.axhline(y=cut_distance, color='red', linestyle='--', linewidth=2)

# Set y-axis limits to show range from 0 to 0.4
ax.set_ylim(0, 0.4)
ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4])

# Formatting
ax.set_ylabel('Distance (1 - |ρ|)', fontsize=14, fontweight='bold')
ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
ax.set_title('Dendrogram: Commit Count, Commit Additions, Commit Deletions\n(Spearman Correlation, Average Linkage)', 
             fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, linestyle='--')
ax.tick_params(axis='both', labelsize=12)

# Color code highly correlated metrics (ρ ≥ 0.7) with same color
# Get the leaf order from dendrogram
leaf_order = dendrogram_result['leaves']
leaf_labels = [metrics[i] for i in leaf_order]

# Identify highly correlated pairs (ρ ≥ 0.7)
high_corr_pairs = []
for i in range(n):
    for j in range(i+1, n):
        if abs(corr_matrix[i, j]) >= 0.7:
            high_corr_pairs.append((metrics[i], metrics[j]))

# Color tick labels: if two metrics are highly correlated, use same color
tick_colors = {}
color_palette = ['blue', 'green', 'orange', 'purple', 'brown']
color_idx = 0

# Group highly correlated metrics
for metric1, metric2 in high_corr_pairs:
    if metric1 not in tick_colors and metric2 not in tick_colors:
        color = color_palette[color_idx % len(color_palette)]
        tick_colors[metric1] = color
        tick_colors[metric2] = color
        color_idx += 1
    elif metric1 in tick_colors:
        tick_colors[metric2] = tick_colors[metric1]
    elif metric2 in tick_colors:
        tick_colors[metric1] = tick_colors[metric2]

# Apply colors to tick labels
for tick, label in zip(ax.get_xticklabels(), leaf_labels):
    if label in tick_colors:
        tick.set_color(tick_colors[label])
        tick.set_fontweight('bold')

plt.tight_layout()

# Save
dendrogram_png = OUTPUT_DIR / 'dendrogram_commit_metrics_threshold0.7.png'
dendrogram_pdf = OUTPUT_DIR / 'dendrogram_commit_metrics_threshold0.7.pdf'

plt.savefig(dendrogram_png, dpi=300, bbox_inches='tight')
plt.savefig(dendrogram_pdf, dpi=300, bbox_inches='tight')

print(f"\n✓ Saved dendrogram: {dendrogram_png}")
print(f"✓ Saved dendrogram: {dendrogram_pdf}")

plt.close()

print("\n" + "="*70)
print("✓ DENDOGRAM ANALYSIS COMPLETE!")
print("="*70)
print(f"\nOutput files:")
print(f"  - {dendrogram_png.name}")
print(f"  - {dendrogram_pdf.name}")
print(f"  - {corr_csv.name}")
print(f"  - {cluster_csv.name}")

