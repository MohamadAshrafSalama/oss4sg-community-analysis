import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.stats import spearmanr
import csv
import math

# Directories
data_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'
os.makedirs(output_dir, exist_ok=True)

print("="*70)
print("LOADING DATA FOR CORRELATION ANALYSIS")
print("="*70)

# Load the "Join Rate vs Leave Rate for all stages" CSV
join_leave_file = os.path.join(data_dir, 'Join Rate vs Leave Rate for all stages.csv')
df_join_leave = pd.read_csv(join_leave_file)

print(f"Loaded {len(df_join_leave)} projects from join/leave rate file")

# Load Active Users data for each stage and combine
active_users_files = [
    os.path.join(data_dir, 'Average Active Users for each window (Early Repos).csv'),
    os.path.join(data_dir, 'Average Active Users for each window (Mid Repos).csv'),
    os.path.join(data_dir, 'Average Active Users for each window (Late Repos).csv')
]

# Calculate average active users per repo across all windows
avg_active_users_sg = sum([pd.read_csv(f)['SG'].mean() for f in active_users_files]) / len(active_users_files)
avg_active_users_not_sg = sum([pd.read_csv(f)['Not SG'].mean() for f in active_users_files]) / len(active_users_files)

print(f"\nAverage Active Users - SG: {avg_active_users_sg:.2f}")
print(f"Average Active Users - Not SG: {avg_active_users_not_sg:.2f}")

# Create per-repo dataset
repo_metrics = []
for _, row in df_join_leave.iterrows():
    repo = row['Repo']
    join_rate = row['Average Join Rate']
    leave_rate = row['Average Leave Rate']
    sg = row['SG']
    
    # Use appropriate active users average based on SG
    active_users = avg_active_users_sg if sg == 1 else avg_active_users_not_sg
    
    repo_metrics.append({
        'Repo': repo,
        'Join Rate': join_rate,
        'Leave Rate': leave_rate,
        'Active Users': active_users
    })

df_metrics = pd.DataFrame(repo_metrics)

print(f"\nCreated metrics dataframe with {len(df_metrics)} repos")
print(f"\nMetrics summary:")
print(df_metrics[['Join Rate', 'Leave Rate', 'Active Users']].describe())

# Calculate Spearman correlation matrix
print("\n" + "="*70)
print("CALCULATING CORRELATION MATRIX")
print("="*70)

metrics = ['Join Rate', 'Leave Rate', 'Active Users']
n = len(metrics)

# Calculate Spearman correlation
corr_matrix = np.eye(n)  # Identity matrix (diagonal = 1.0)

for i in range(n):
    for j in range(i+1, n):
        metric1 = metrics[i]
        metric2 = metrics[j]
        
        # Get paired values (remove NaN)
        data1 = df_metrics[metric1].values
        data2 = df_metrics[metric2].values
        
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
corr_csv = os.path.join(output_dir, 'JoinRate_LeaveRate_ActiveUsers_spearman_correlation.csv')
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
cluster_csv = os.path.join(output_dir, 'JoinRate_LeaveRate_ActiveUsers_clusters.csv')
with open(cluster_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['cluster_id', 'metric'])
    for metric, cluster_id in zip(metrics, clusters):
        writer.writerow([cluster_id, metric])

print(f"\n✓ Saved cluster membership: {cluster_csv}")

# Plot dendrogram with clear naming
fig, ax = plt.subplots(figsize=(12, 8))

# Create dendrogram
dendrogram(Z, labels=metrics, leaf_rotation=90, ax=ax, 
           leaf_font_size=14)

# Add threshold line
ax.axhline(y=cut_distance, color='red', linestyle='--', linewidth=2, 
           label='Threshold (|ρ| ≥ 0.7)')

# Formatting
ax.set_ylabel('Distance (1 - |ρ|)', fontsize=14, fontweight='bold')
ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
ax.set_title('Dendrogram: Join Rate, Leave Rate, Active Users\n(Spearman Correlation, Average Linkage)', 
             fontsize=16, fontweight='bold', pad=20)
ax.legend(fontsize=12, loc='upper left')
ax.grid(True, alpha=0.3, linestyle='--')
ax.tick_params(axis='both', labelsize=12)

# Add correlation values as text annotations
# Calculate positions for text
for i, (label1, label2) in enumerate([('Join Rate', 'Leave Rate'), 
                                        ('Join Rate', 'Active Users'),
                                        ('Leave Rate', 'Active Users')]):
    idx1 = metrics.index(label1)
    idx2 = metrics.index(label2)
    corr_val = corr_matrix[idx1, idx2]
    ax.text(0.02, 0.95 - i*0.08, f'{label1} vs {label2}: ρ = {corr_val:.4f}', 
            transform=ax.transAxes, fontsize=11, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

# Save with clear naming
dendrogram_png = os.path.join(output_dir, 'Dendrogram_JoinRate_LeaveRate_ActiveUsers_threshold0.7.png')
dendrogram_pdf = os.path.join(output_dir, 'Dendrogram_JoinRate_LeaveRate_ActiveUsers_threshold0.7.pdf')

plt.savefig(dendrogram_png, dpi=300, bbox_inches='tight')
plt.savefig(dendrogram_pdf, dpi=300, bbox_inches='tight')

print(f"\n✓ Saved dendrogram: {dendrogram_png}")
print(f"✓ Saved dendrogram: {dendrogram_pdf}")

plt.close()

print("\n" + "="*70)
print("✓ CORRELATION ANALYSIS COMPLETE!")
print("="*70)
print(f"\nOutput files:")
print(f"  - {os.path.basename(dendrogram_png)}")
print(f"  - {os.path.basename(dendrogram_pdf)}")
print(f"  - {os.path.basename(corr_csv)}")
print(f"  - {os.path.basename(cluster_csv)}")
