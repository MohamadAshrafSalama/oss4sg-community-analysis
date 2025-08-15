import pandas as pd
import numpy as np
from scipy.stats import f_oneway
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import os

files = {
    "early": "recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo/Join Rate vs Leave Rate for early stages.csv",
    "mid":   "recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo/Join Rate vs Leave Rate for mid stages.csv",
    "late":  "recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo/Join Rate vs Leave Rate for late stages.csv"
}

results = {}
for stage, path in files.items():
    df = pd.read_csv(path)
    df["JoinRatio"] = (df["Average Join Rate"] - df["Average Leave Rate"]) / (df["Average Join Rate"] + df["Average Leave Rate"])
    results[f"{stage}_oss4sg"] = df[df["SG"] == 1][["Repo", "JoinRatio"]]
    results[f"{stage}_oss"] = df[df["SG"] == 0][["Repo", "JoinRatio"]]

data_tuples = []
for key in results:
    for jr in results[key]['JoinRatio'].dropna().values:
        data_tuples.append((key, jr))

def scott_knott(data, alpha=0.05):
    df = pd.DataFrame(data, columns=['group', 'value'])
    group_means = df.groupby('group')['value'].mean()
    sorted_groups = group_means.sort_values().index.tolist()
    
    def split_cluster(cluster):
        if len(cluster) <= 1:
            return [cluster]
        group_values = {g: df[df['group'] == g]['value'].values for g in cluster}
        best_split, max_f = None, -np.inf
        for i in range(1, len(cluster)):
            left_values = np.concatenate([group_values[g] for g in cluster[:i]])
            right_values = np.concatenate([group_values[g] for g in cluster[i:]])
            F, p = f_oneway(left_values, right_values)
            if F > max_f:
                max_f = F
                best_split = i
        if best_split is None:
            return [cluster]
        left_split = cluster[:best_split]
        right_split = cluster[best_split:]
        left_values = np.concatenate([group_values[g] for g in left_split])
        right_values = np.concatenate([group_values[g] for g in right_split])
        F, p = f_oneway(left_values, right_values)
        return split_cluster(left_split) + split_cluster(right_split) if p < alpha else [cluster]
    
    final_clusters = split_cluster(sorted_groups)
    cluster_labels = {}
    for cluster_id, cluster in enumerate(final_clusters, 1):
        for group in cluster:
            cluster_labels[group] = cluster_id
    return cluster_labels

df = pd.DataFrame(data_tuples, columns=['group', 'value'])
df['cluster'] = df['group'].map(scott_knott(data_tuples))
group_order = df.groupby('group')['value'].mean().sort_values().index

plt.figure(figsize=(12, 6))
sns.boxplot(x='group', y='value', data=df, order=group_order, hue='cluster', palette='Set1', dodge=False)
plt.xticks(rotation=45)
# Remove title
plt.xlabel('Group', fontsize=14)  # +2: 12 -> 14
plt.ylabel('Retention Ratio', fontsize=14)  # +2: 12 -> 14
plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14, title_fontsize=14)  # +2: 12 -> 14
# Make X-axis labels smaller, keep Y-axis numbers +2
plt.tick_params(axis='x', which='major', labelsize=14)  # +2: 12 -> 14 (smaller for group names)
plt.tick_params(axis='y', which='major', labelsize=14)  # +2: 12 -> 14
plt.tight_layout()
output_path = os.path.abspath('scott_knott_retention.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_path}")
plt.close()

plt.figure(figsize=(12, 6))
sns.boxplot(x='group', y='value', data=df, order=group_order, hue='cluster', palette='Set1', dodge=False)
plt.xticks(rotation=45)
# Remove title
plt.xlabel('Group', fontsize=14)  # +2: 12 -> 14
plt.ylabel('Retention Ratio', fontsize=14)  # +2: 12 -> 14
plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14, title_fontsize=14)  # +2: 12 -> 14
# Make X-axis labels smaller, keep Y-axis numbers +2
plt.tick_params(axis='x', which='major', labelsize=14)  # +2: 12 -> 14 (smaller for group names)
plt.tick_params(axis='y', which='major', labelsize=14)  # +2: 12 -> 14
plt.tight_layout()
output_path = os.path.abspath('scott_knott_retention_msn.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_path}")
plt.close()

