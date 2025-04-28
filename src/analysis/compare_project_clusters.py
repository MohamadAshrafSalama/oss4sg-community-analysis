#!/usr/bin/env python3
"""
Compare cluster assignments for each project-stage before and after MSN merging.
Creates a heatmap showing which projects changed clusters (red) vs stayed the same (green).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import interp1d

from pathlib import Path

# Settings
use_forced_k = True
forced_k = 4

BASE = Path(__file__).resolve().parent
original_file = BASE / "df_all_commits_with_stats_clean.csv"
msn_file = BASE / "df_all_commits_with_stats_msn_merged_clean.csv"

def get_cluster_assignments(file_path, label):
    """Run experiment and return cluster assignments for each (project, stage)."""
    print(f"\n{'='*80}")
    print(f"Processing: {label}")
    print(f"{'='*80}")
    
    df = pd.read_csv(file_path, parse_dates=['commit_date'])
    df = df.sort_values('commit_date')
    df['core_churn'] = np.where(df['is_core'] == True, df['churn'], 0.0)
    
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
    
    projects = df['project'].unique()
    all_filtered = []
    for project in projects:
        sub_df = df[df['project'] == project]
        labeled_sub_df = filter_and_label_stages(sub_df)
        if not labeled_sub_df.empty:
            all_filtered.append(labeled_sub_df)
    df_filtered = pd.concat(all_filtered, ignore_index=True)
    df_filtered = df_filtered.sort_values('commit_date')
    
    df_filtered['year_month'] = df_filtered['commit_date'].dt.to_period('M')
    monthly_stats = df_filtered.groupby(['project', 'stage', 'year_month']).agg({
        'churn': 'sum',
        'core_churn': 'sum'
    }).reset_index()
    monthly_stats = monthly_stats[monthly_stats['churn'] != 0].copy()
    monthly_stats['core_churn_ratio'] = monthly_stats['core_churn'] / monthly_stats['churn']
    monthly_stats.dropna(subset=['core_churn_ratio'], inplace=True)
    monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()
    
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
    
    interpolated_time_series = interpolate_time_series(time_series_collection)
    X = np.array([ts['core_churn_ratio'] for ts in interpolated_time_series])
    mask_nan = np.isnan(X).any(axis=1)
    if np.any(mask_nan):
        keep_rows = [i for i, flag in enumerate(mask_nan) if not flag]
        X = X[keep_rows]
        interpolated_time_series = [interpolated_time_series[i] for i in keep_rows]
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=forced_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    for i, ts in enumerate(interpolated_time_series):
        ts['cluster'] = cluster_labels[i]
    
    # Create DataFrame with project, stage, cluster
    assignments = []
    for ts in interpolated_time_series:
        assignments.append({
            'project': ts['project'],
            'stage': ts['stage'],
            'cluster': ts['cluster']
        })
    
    df_assignments = pd.DataFrame(assignments)
    return df_assignments

# Get cluster assignments from both experiments
print("Getting cluster assignments...")
original_assignments = get_cluster_assignments(original_file, "ORIGINAL")
msn_assignments = get_cluster_assignments(msn_file, "MSN-MERGED")

# Merge on project and stage
print("\nMerging assignments...")
comparison = original_assignments.merge(
    msn_assignments,
    on=['project', 'stage'],
    how='outer',
    suffixes=('_original', '_msn')
)

# Fill NaN with -1 for missing values (projects/stages that only exist in one)
comparison = comparison.fillna(-1)

# Create a combined key for sorting
comparison['project_stage'] = comparison['project'] + ' - ' + comparison['stage']
comparison = comparison.sort_values(['project', 'stage'])

# Create heatmap data
# Rows: project-stage combinations
# Columns: Original Cluster, MSN Cluster
heatmap_data = comparison[['cluster_original', 'cluster_msn']].values

# Create color mapping: green if same, red if different
# But we need numeric values for the heatmap, so we'll create a separate matrix
match_matrix = np.zeros((len(comparison), 2))
for i, row in comparison.iterrows():
    orig_cluster = row['cluster_original']
    msn_cluster = row['cluster_msn']
    # 1 = match (green), 0 = mismatch (red)
    match_matrix[i, 0] = 1 if orig_cluster == msn_cluster else 0
    match_matrix[i, 1] = 1 if orig_cluster == msn_cluster else 0

# Create the plot
fig, ax = plt.subplots(figsize=(8, max(12, len(comparison) * 0.15)))

# Create custom colormap: green for 1 (match), red for 0 (mismatch)
from matplotlib.colors import ListedColormap
colors = ['#ff4444', '#44ff44']  # Red for mismatch, Green for match
cmap = ListedColormap(colors)

# Plot heatmap
im = ax.imshow(match_matrix, aspect='auto', cmap=cmap, vmin=0, vmax=1)

# Set labels
ax.set_xticks([0, 1])
ax.set_xticklabels(['Original Cluster', 'MSN Cluster'])
ax.set_yticks(range(len(comparison)))
ax.set_yticklabels(comparison['project_stage'].values, fontsize=6)

# Add text annotations showing actual cluster numbers
for i in range(len(comparison)):
    orig_cluster = int(comparison.iloc[i]['cluster_original']) if comparison.iloc[i]['cluster_original'] != -1 else 'N/A'
    msn_cluster = int(comparison.iloc[i]['cluster_msn']) if comparison.iloc[i]['cluster_msn'] != -1 else 'N/A'
    ax.text(0, i, f'C{orig_cluster}', ha='center', va='center', fontsize=6, fontweight='bold')
    ax.text(1, i, f'C{msn_cluster}', ha='center', va='center', fontsize=6, fontweight='bold')

plt.title('Cluster Assignment Comparison: Original vs MSN-Merged\n(Green = Same Cluster, Red = Different Cluster)', 
          fontsize=12, fontweight='bold', pad=20)
plt.tight_layout()

output_file = BASE / "cluster_assignment_comparison_heatmap.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved heatmap to {output_file}")

# Print summary
total = len(comparison)
matches = (comparison['cluster_original'] == comparison['cluster_msn']).sum()
mismatches = total - matches
print(f"\nSummary:")
print(f"  Total project-stage combinations: {total}")
print(f"  Same cluster (green): {matches} ({matches/total*100:.1f}%)")
print(f"  Different cluster (red): {mismatches} ({mismatches/total*100:.1f}%)")

plt.close()






