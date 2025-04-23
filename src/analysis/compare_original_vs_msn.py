#!/usr/bin/env python3
"""
Compare the experiment results: Original vs MSN-merged contributors.
Runs the experiment on both datasets and creates side-by-side comparison plots.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import interp1d

import os
from pathlib import Path

# -------------------------------------------------------------------------
# TOGGLE SETTINGS
# -------------------------------------------------------------------------
use_forced_k = True
forced_k = 4

# Paths
BASE = Path(__file__).resolve().parent
original_file = BASE / "df_all_commits_with_stats_clean.csv"
msn_file = BASE / "df_all_commits_with_stats_msn_merged_clean.csv"

def run_experiment(file_path, label):
    """Run the experiment on a given CSV file and return results."""
    print(f"\n{'='*80}")
    print(f"Running experiment: {label}")
    print(f"{'='*80}")
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path, parse_dates=['commit_date'])
    df = df.sort_values('commit_date')
    
    # Create core_churn column
    df['core_churn'] = np.where(df['is_core'] == True, df['churn'], 0.0)
    
    # Filter by stage
    def filter_and_label_stages(project_df):
        project_df = project_df.copy()
        if project_df.empty:
            return project_df
        project_start = project_df['commit_date'].min()
        project_end = project_df['commit_date'].max()
        total_years = (project_end - project_start).days / 365.0
        if total_years < 7:
            return project_df.iloc[0:0]
        early_end = project_start + pd.DateOffset(years=7)
        middle_end = early_end + pd.DateOffset(years=3)
        late_end = middle_end + pd.DateOffset(years=3)
        project_df['stage'] = ''
        mask_early = (project_df['commit_date'] >= project_start) & (project_df['commit_date'] < early_end)
        project_df.loc[mask_early, 'stage'] = 'early'
        if total_years >= 10:
            mask_mid = (project_df['commit_date'] >= early_end) & (project_df['commit_date'] < middle_end)
            project_df.loc[mask_mid, 'stage'] = 'middle'
        if total_years >= 13:
            mask_late = (project_df['commit_date'] >= middle_end) & (project_df['commit_date'] < late_end)
            project_df.loc[mask_late, 'stage'] = 'late'
        project_df = project_df[project_df['stage'] != '']
        return project_df
    
    print("Filtering projects by stage...")
    projects = df['project'].unique()
    all_filtered = []
    for project in projects:
        sub_df = df[df['project'] == project]
        labeled_sub_df = filter_and_label_stages(sub_df)
        if not labeled_sub_df.empty:
            all_filtered.append(labeled_sub_df)
    df_filtered = pd.concat(all_filtered, ignore_index=True)
    df_filtered = df_filtered.sort_values('commit_date')
    print(f"Filtered to {len(df_filtered):,} commits from {len(projects)} projects")
    
    # Create monthly time series
    print("Creating monthly time series...")
    df_filtered['year_month'] = df_filtered['commit_date'].dt.to_period('M')
    monthly_stats = df_filtered.groupby(['project', 'stage', 'year_month']).agg({
        'churn': 'sum',
        'core_churn': 'sum'
    }).reset_index()
    monthly_stats = monthly_stats[monthly_stats['churn'] != 0].copy()
    monthly_stats['core_churn_ratio'] = monthly_stats['core_churn'] / monthly_stats['churn']
    monthly_stats.dropna(subset=['core_churn_ratio'], inplace=True)
    monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()
    
    # Build time series collection
    print("Building time series collection...")
    time_series_collection = []
    unique_projects = monthly_stats['project'].unique()
    for project in unique_projects:
        stages_for_project = monthly_stats[monthly_stats['project'] == project]['stage'].unique()
        for stg in stages_for_project:
            sub = monthly_stats[(monthly_stats['project'] == project) & (monthly_stats['stage'] == stg)].copy()
            if not sub.empty:
                sub_sorted = sub.sort_values('date')
                time_series_collection.append({
                    'project': project,
                    'stage': stg,
                    'time_series': sub_sorted,
                    'label': f"{project} - {stg}"
                })
    print(f"Created {len(time_series_collection)} time series")
    
    # Interpolate
    def interpolate_time_series(ts_collection):
        valid_lengths = [len(item['time_series']) for item in ts_collection if len(item['time_series']) >= 2]
        if not valid_lengths:
            return []
        max_len = max(valid_lengths)
        result = []
        for item in ts_collection:
            ts = item['time_series']
            if len(ts) < 2:
                continue
            x = np.arange(len(ts))
            x_new = np.linspace(0, len(ts) - 1, max_len)
            y = ts['core_churn_ratio'].values
            f = interp1d(x, y, kind='linear', bounds_error=False, fill_value='extrapolate')
            y_new = f(x_new)
            if np.isnan(y_new).any():
                continue
            result.append({
                'project': item['project'],
                'stage': item['stage'],
                'core_churn_ratio': y_new,
                'label': item['label']
            })
        return result
    
    print("Interpolating time series...")
    interpolated_time_series = interpolate_time_series(time_series_collection)
    print(f"Interpolated to {len(interpolated_time_series)} time series")
    
    # Prepare for clustering
    X = np.array([ts['core_churn_ratio'] for ts in interpolated_time_series])
    mask_nan = np.isnan(X).any(axis=1)
    if np.any(mask_nan):
        keep_rows = [i for i, flag in enumerate(mask_nan) if not flag]
        X = X[keep_rows]
        interpolated_time_series = [interpolated_time_series[i] for i in keep_rows]
    
    # KMeans
    print("Running KMeans clustering...")
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=forced_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    if len(set(cluster_labels)) > 1:
        best_score = silhouette_score(X_scaled, cluster_labels)
    else:
        best_score = -1
    
    for i, ts in enumerate(interpolated_time_series):
        ts['cluster'] = cluster_labels[i]
    
    # Compute centroids
    def compute_medoids(X_scaled, labels, n_clusters):
        medoids = {}
        for c in range(n_clusters):
            idx_in_cluster = np.where(labels == c)[0]
            if len(idx_in_cluster) == 0:
                continue
            if len(idx_in_cluster) == 1:
                medoids[c] = (idx_in_cluster[0], X_scaled[idx_in_cluster[0]])
            else:
                cluster_data = X_scaled[idx_in_cluster]
                dist_matrix = pairwise_distances(cluster_data, metric='euclidean')
                sum_dists = dist_matrix.sum(axis=1)
                medoid_idx_local = np.argmin(sum_dists)
                global_idx = idx_in_cluster[medoid_idx_local]
                medoids[c] = (global_idx, X_scaled[global_idx])
        return medoids
    
    centroids = []
    for c_id in range(forced_k):
        cluster_points = X_scaled[cluster_labels == c_id]
        if len(cluster_points) == 0:
            continue
        centroid_scaled = cluster_points.mean(axis=0)
        centroid_orig = scaler.inverse_transform(centroid_scaled.reshape(1, -1))[0]
        centroids.append((c_id, centroid_scaled, centroid_orig))
    
    # Stage-cluster counts
    stage_cluster_counts = {}
    for ts in interpolated_time_series:
        stg = ts['stage']
        cl = ts['cluster']
        if stg not in stage_cluster_counts:
            stage_cluster_counts[stg] = {}
        if cl not in stage_cluster_counts[stg]:
            stage_cluster_counts[stg][cl] = 0
        stage_cluster_counts[stg][cl] += 1
    
    stage_cluster_percentages = {}
    for stg, c_dict in stage_cluster_counts.items():
        total = sum(c_dict.values())
        stage_cluster_percentages[stg] = {cl: (count/total)*100 for cl, count in c_dict.items()}
    
    return {
        'interpolated_time_series': interpolated_time_series,
        'centroids': centroids,
        'stage_cluster_counts': stage_cluster_counts,
        'stage_cluster_percentages': stage_cluster_percentages,
        'best_score': best_score,
        'num_commits': len(df_filtered),
        'num_projects': len(projects),
        'num_time_series': len(interpolated_time_series)
    }

# Run both experiments
results_original = run_experiment(original_file, "ORIGINAL")
results_msn = run_experiment(msn_file, "MSN-MERGED")

# Create comparison plots
print(f"\n{'='*80}")
print("Creating comparison plots...")
print(f"{'='*80}")

# 1. Comparison: 4x1 centroids side by side (original vs MSN)
fig, axes = plt.subplots(4, 2, figsize=(16, 16))

for c_id in range(forced_k):
    # Original
    centroid_orig_data = None
    for (cid, centroid_scaled, centroid_orig) in results_original['centroids']:
        if cid == c_id:
            centroid_orig_data = centroid_orig
            break
    
    # MSN
    centroid_msn_data = None
    for (cid, centroid_scaled, centroid_orig) in results_msn['centroids']:
        if cid == c_id:
            centroid_msn_data = centroid_orig
            break
    
    # Left plot (Original)
    if centroid_orig_data is not None:
        ax = axes[c_id, 0]
        ax.plot(centroid_orig_data, linewidth=3, color=f'C{c_id}')
        ax.set_title(f"Original - Cluster {c_id}", fontsize=12, fontweight='bold')
        ax.set_ylabel("Core Churn Ratio", fontsize=10)
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle='--', alpha=0.7)
    
    # Right plot (MSN)
    if centroid_msn_data is not None:
        ax = axes[c_id, 1]
        ax.plot(centroid_msn_data, linewidth=3, color=f'C{c_id}')
        ax.set_title(f"MSN-Merged - Cluster {c_id}", fontsize=12, fontweight='bold')
        ax.set_ylabel("Core Churn Ratio", fontsize=10)
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle='--', alpha=0.7)

axes[3, 0].set_xlabel("Time (normalized)", fontsize=10)
axes[3, 1].set_xlabel("Time (normalized)", fontsize=10)

plt.tight_layout()
output_file = BASE / "centroids_comparison_original_vs_msn.png"
plt.savefig(output_file, dpi=300)
print(f"Saved comparison plot to {output_file}")
plt.close()

# 2. Comparison: Stage-cluster distribution
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

stages = sorted(set(list(results_original['stage_cluster_percentages'].keys()) + 
                   list(results_msn['stage_cluster_percentages'].keys())))
clusters = range(forced_k)
width = 0.8 / forced_k
x_positions = np.arange(len(stages))

# Original
ax = axes[0]
for i, cl in enumerate(clusters):
    bar_heights = []
    for stg in stages:
        bar_heights.append(results_original['stage_cluster_percentages'].get(stg, {}).get(cl, 0.0))
    ax.bar(x_positions + i*width - 0.4 + width/2, bar_heights, width,
           label=f"Cluster {cl}", color=f"C{cl}")
ax.set_xticks(x_positions)
ax.set_xticklabels(stages)
ax.set_xlabel("Project Stage")
ax.set_ylabel("Percentage of Time Series")
ax.set_title("Original - Cluster Distribution by Stage")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.7)

# MSN
ax = axes[1]
for i, cl in enumerate(clusters):
    bar_heights = []
    for stg in stages:
        bar_heights.append(results_msn['stage_cluster_percentages'].get(stg, {}).get(cl, 0.0))
    ax.bar(x_positions + i*width - 0.4 + width/2, bar_heights, width,
           label=f"Cluster {cl}", color=f"C{cl}")
ax.set_xticks(x_positions)
ax.set_xticklabels(stages)
ax.set_xlabel("Project Stage")
ax.set_ylabel("Percentage of Time Series")
ax.set_title("MSN-Merged - Cluster Distribution by Stage")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
output_file2 = BASE / "stage_cluster_distribution_comparison.png"
plt.savefig(output_file2, dpi=300)
print(f"Saved comparison plot to {output_file2}")
plt.close()

# Print summary
print(f"\n{'='*80}")
print("SUMMARY COMPARISON")
print(f"{'='*80}")
print(f"\nOriginal:")
print(f"  Commits: {results_original['num_commits']:,}")
print(f"  Projects: {results_original['num_projects']}")
print(f"  Time series: {results_original['num_time_series']}")
print(f"  Silhouette score: {results_original['best_score']:.3f}")

print(f"\nMSN-Merged:")
print(f"  Commits: {results_msn['num_commits']:,}")
print(f"  Projects: {results_msn['num_projects']}")
print(f"  Time series: {results_msn['num_time_series']}")
print(f"  Silhouette score: {results_msn['best_score']:.3f}")

print(f"\nStage-cluster percentages - Original:")
for stg, pct_dict in results_original['stage_cluster_percentages'].items():
    print(f"  {stg}: {pct_dict}")

print(f"\nStage-cluster percentages - MSN:")
for stg, pct_dict in results_msn['stage_cluster_percentages'].items():
    print(f"  {stg}: {pct_dict}")

print("\nDONE.")

