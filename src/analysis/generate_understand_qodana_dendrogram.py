#!/usr/bin/env python3
"""
Generate dendrogram analysis for Understand SciTools + Qodana metrics
Uses both CSV files: with and without codechars normalization
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
OUTPUT_DIR = BASE / "exper7_out" / "plots"
CORR_DIR = BASE / "exper7_out" / "corr"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CORR_DIR.mkdir(parents=True, exist_ok=True)

# Input files
CSV_WITHOUT_CHAR = BASE / "alpha_beta_qodana_understand_metrics.csv"
CSV_WITH_CHAR = BASE / "alpha_beta_qodana_understand_metrics_w_codechars.csv"

# Understand SciTools metrics (non-zero means)
understand_metrics = [
    'Cyclomatic_non_zero_mean',
    'MaxNesting_non_zero_mean',
    'MaxInheritanceTree_non_zero_mean',
    'RatioCommentToCode_non_zero_mean',
    'CountDeclMethodAll_non_zero_mean',
    'CountDeclFunction_non_zero_mean',
    'CountDeclMethod_non_zero_mean'
]

# Qodana metrics (only critical, high, moderate)
qodana_metrics_without_char = ['count_critical', 'count_high', 'count_moderate']
qodana_metrics_with_char = ['count_critical_ppm100M', 'count_high_ppm100M', 'count_moderate_ppm100M']

# Metric name mapping for display
METRIC_NAMES = {
    'Cyclomatic_non_zero_mean': 'Cyclomatic Complexity',
    'MaxNesting_non_zero_mean': 'Max Nesting Depth',
    'MaxInheritanceTree_non_zero_mean': 'Max Inheritance Depth',
    'RatioCommentToCode_non_zero_mean': 'Comment/Code Ratio',
    'CountDeclMethodAll_non_zero_mean': 'Total Methods/Class',
    'CountDeclFunction_non_zero_mean': 'Functions per File',
    'CountDeclMethod_non_zero_mean': 'Methods in Class',
    'count_critical': 'Critical',
    'count_high': 'High',
    'count_moderate': 'Moderate',
    'count_critical_ppm100M': 'Critical',
    'count_high_ppm100M': 'High',
    'count_moderate_ppm100M': 'Moderate',
}

def generate_dendrogram(csv_path, qodana_metrics, output_suffix):
    """Generate dendrogram for a given CSV file"""
    print(f"\n{'='*70}")
    print(f"PROCESSING: {csv_path.name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    
    # Combine all metrics
    all_metrics = understand_metrics + qodana_metrics
    
    # Check which metrics exist in the dataframe
    available_metrics = [m for m in all_metrics if m in df.columns]
    missing_metrics = [m for m in all_metrics if m not in df.columns]
    
    if missing_metrics:
        print(f"⚠ Warning: Missing metrics: {missing_metrics}")
    
    print(f"\nUsing {len(available_metrics)} metrics:")
    for m in available_metrics:
        print(f"  - {m}")
    
    # Filter out rows with missing values
    df_clean = df[available_metrics].dropna()
    print(f"\nRows with complete data: {len(df_clean)}")
    
    if len(df_clean) < 3:
        print("⚠ Error: Not enough data points for correlation analysis")
        return
    
    print(f"\nMetrics summary:")
    print(df_clean[available_metrics].describe())
    
    # Calculate Spearman correlation matrix
    print(f"\n{'='*70}")
    print("CALCULATING CORRELATION MATRIX")
    print(f"{'='*70}")
    
    n = len(available_metrics)
    corr_matrix = np.eye(n)  # Identity matrix (diagonal = 1.0)
    
    for i in range(n):
        for j in range(i+1, n):
            metric1 = available_metrics[i]
            metric2 = available_metrics[j]
            
            data1 = df_clean[metric1].values
            data2 = df_clean[metric2].values
            
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
    corr_csv = CORR_DIR / f'understand_qodana_spearman_{output_suffix}.csv'
    with open(corr_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric'] + available_metrics)
        for i, metric in enumerate(available_metrics):
            writer.writerow([metric] + [f"{corr_matrix[i, j]:.6f}" for j in range(n)])
    
    print(f"\n✓ Saved correlation matrix: {corr_csv}")
    
    # Create dendrogram
    print(f"\n{'='*70}")
    print("CREATING DENDOGRAM WITH 0.7 THRESHOLD")
    print(f"{'='*70}")
    
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
    for i, (metric, cluster_id) in enumerate(zip(available_metrics, clusters)):
        print(f"  {metric}: Cluster {cluster_id}")
    
    # Save cluster membership
    cluster_csv = BASE / "exper7_out" / "reports" / f'understand_qodana_clusters_{output_suffix}.csv'
    cluster_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(cluster_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cluster_id', 'metric'])
        for metric, cluster_id in zip(available_metrics, clusters):
            writer.writerow([cluster_id, metric])
    
    print(f"\n✓ Saved cluster membership: {cluster_csv}")
    
    # Plot dendrogram
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create display labels for metrics
    display_labels = [METRIC_NAMES.get(m, m) for m in available_metrics]
    
    # Create dendrogram - disable automatic coloring to control it ourselves
    dendrogram_result = dendrogram(Z, labels=display_labels, leaf_rotation=90, ax=ax, 
                                    leaf_font_size=10, 
                                    color_threshold=0)  # Disable automatic coloring
    
    # Add threshold line
    ax.axhline(y=cut_distance, color='red', linestyle='--', linewidth=2)
    
    # Set y-axis limits to show full range from 0 to 1.0
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    
    # Formatting
    ax.set_ylabel('Distance (1 - |ρ|)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
    # Remove "without_char" or "with_char" from title
    if output_suffix == "without_char":
        title = 'Dendrogram: Understand SciTools + Qodana Metrics\n(Spearman Correlation, Average Linkage)'
    else:
        title = f'Dendrogram: Understand SciTools + Qodana Metrics ({output_suffix})\n(Spearman Correlation, Average Linkage)'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.tick_params(axis='both', labelsize=10)
    
    # Color code highly correlated metrics (ρ ≥ 0.7) with same color
    leaf_order = dendrogram_result['leaves']
    leaf_labels_display = [display_labels[i] for i in leaf_order]
    leaf_labels_original = [available_metrics[i] for i in leaf_order]
    
    # Identify highly correlated pairs (ρ ≥ 0.7)
    high_corr_pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if abs(corr_matrix[i, j]) >= 0.7:
                high_corr_pairs.append((available_metrics[i], available_metrics[j]))
    
    # Create mapping from display labels to colors
    tick_colors = {}
    color_palette = ['blue', 'green', 'orange', 'purple', 'brown', 'red', 'cyan', 'magenta']
    color_idx = 0
    
    # Group highly correlated metrics (using original metric names for lookup)
    for metric1, metric2 in high_corr_pairs:
        display1 = METRIC_NAMES.get(metric1, metric1)
        display2 = METRIC_NAMES.get(metric2, metric2)
        if display1 not in tick_colors and display2 not in tick_colors:
            color = color_palette[color_idx % len(color_palette)]
            tick_colors[display1] = color
            tick_colors[display2] = color
            color_idx += 1
        elif display1 in tick_colors:
            tick_colors[display2] = tick_colors[display1]
        elif display2 in tick_colors:
            tick_colors[display1] = tick_colors[display2]
    
    # Apply colors to tick labels
    print(f"\nColoring highly correlated metrics:")
    for tick, label in zip(ax.get_xticklabels(), leaf_labels_display):
        if label in tick_colors:
            tick.set_color(tick_colors[label])
            tick.set_fontweight('bold')
            print(f"  {label}: {tick_colors[label]} (bold)")
    
    plt.tight_layout()
    
    # Save
    dendrogram_png = OUTPUT_DIR / f'dendrogram_understand_qodana_{output_suffix}_threshold0.7.png'
    dendrogram_pdf = OUTPUT_DIR / f'dendrogram_understand_qodana_{output_suffix}_threshold0.7.pdf'
    
    plt.savefig(dendrogram_png, dpi=300, bbox_inches='tight')
    plt.savefig(dendrogram_pdf, dpi=300, bbox_inches='tight')
    
    print(f"\n✓ Saved dendrogram: {dendrogram_png}")
    print(f"✓ Saved dendrogram: {dendrogram_pdf}")
    
    plt.close()
    
    return corr_csv, cluster_csv, dendrogram_png

# Generate dendrograms for both files
print("="*70)
print("UNDERSTAND SCITOOLS + QODANA METRICS DENDOGRAM ANALYSIS")
print("="*70)

# Without codechars
if CSV_WITHOUT_CHAR.exists():
    generate_dendrogram(CSV_WITHOUT_CHAR, qodana_metrics_without_char, "without_char")
else:
    print(f"⚠ File not found: {CSV_WITHOUT_CHAR}")

# With codechars
if CSV_WITH_CHAR.exists():
    generate_dendrogram(CSV_WITH_CHAR, qodana_metrics_with_char, "with_char")
else:
    print(f"⚠ File not found: {CSV_WITH_CHAR}")

print("\n" + "="*70)
print("✓ DENDOGRAM ANALYSIS COMPLETE!")
print("="*70)

