import pandas as pd
import numpy as np
from scipy.stats import f_oneway
import matplotlib.pyplot as plt
import seaborn as sns

# Define file paths
base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/EXP1(Rdoing_overlapping_and_double_check_numbers)/Datasets/GraphInfo"

files = {
    "early": f"{base_path}/Join Rate vs Leave Rate for early stages.csv",
    "mid":   f"{base_path}/Join Rate vs Leave Rate for mid stages.csv",
    "late":  f"{base_path}/Join Rate vs Leave Rate for late stages.csv"
}

# Dictionary to hold DataFrames for each group
results = {}

print("="*80)
print("STEP 1: Loading data and calculating JoinRatio")
print("="*80)

for stage, path in files.items():
    try:
        df = pd.read_csv(path)
        print(f"\n{stage.upper()} stage: Loaded {len(df)} projects")
        print(f"Columns: {df.columns.tolist()}")
        
        # Compute join ratio = Average Join Rate / (Average Join Rate + Average Leave Rate)
        df["JoinRatio"] = df["Average Join Rate"] / (df["Average Join Rate"] + df["Average Leave Rate"])
        
        # Split by SG: SG==1 -> OSS4SG; SG==0 -> OSS
        df_oss4sg = df[df["SG"] == 1]
        df_oss    = df[df["SG"] == 0]
        
        # Save the results in the dictionary
        results[f"{stage}_oss4sg"] = df_oss4sg[["Repo", "JoinRatio"]]
        results[f"{stage}_oss"] = df_oss[["Repo", "JoinRatio"]]
        
        print(f"  - OSS4SG: {len(df_oss4sg)} projects")
        print(f"  - OSS: {len(df_oss)} projects")
        
    except Exception as e:
        print(f"Error processing {path}: {e}")

# Print summary of groups
print("\n" + "="*80)
print("GROUPS CREATED:")
print("="*80)
for key, df_group in results.items():
    print(f"{key:20s}: {len(df_group):3d} projects, {df_group['JoinRatio'].notna().sum():3d} valid JoinRatio values")

# Create data tuples for Scott-Knott
print("\n" + "="*80)
print("STEP 2: Preparing data for Scott-Knott clustering")
print("="*80)

data_tuples = []
for key in results:
    join_ratios = results[key]['JoinRatio'].dropna().values
    for jr in join_ratios:
        data_tuples.append((key, jr))

print(f"Total data points: {len(data_tuples)}")

# Create DataFrame
df_scott = pd.DataFrame(data_tuples, columns=['group', 'value'])

# Scott-Knott clustering function
def scott_knott(data, alpha=0.05):
    """
    Perform Scott-Knott clustering on grouped data.
    
    Parameters:
    - data: List of tuples (group_name, value)
    - alpha: Significance level for F-test
    
    Returns:
    - Dictionary mapping group names to cluster IDs
    """
    df = pd.DataFrame(data, columns=['group', 'value'])
    group_means = df.groupby('group')['value'].mean()
    sorted_groups = group_means.sort_values().index.tolist()
    
    clusters = [sorted_groups]
    
    def split_cluster(cluster):
        if len(cluster) <= 1:
            return [cluster]
        
        group_values = {g: df[df['group'] == g]['value'].values for g in cluster}
        best_split = None
        max_f = -np.inf
        
        # Try all possible splits
        for i in range(1, len(cluster)):
            left = cluster[:i]
            right = cluster[i:]
            
            left_values = np.concatenate([group_values[g] for g in left])
            right_values = np.concatenate([group_values[g] for g in right])
            
            F, p = f_oneway(left_values, right_values)
            if F > max_f:
                max_f = F
                best_split = i
        
        if best_split is None:
            return [cluster]
        
        # Test if best split is significant
        left_split = cluster[:best_split]
        right_split = cluster[best_split:]
        left_values = np.concatenate([group_values[g] for g in left_split])
        right_values = np.concatenate([group_values[g] for g in right_split])
        F, p = f_oneway(left_values, right_values)
        
        if p < alpha:
            # Split is significant, recurse
            return split_cluster(left_split) + split_cluster(right_split)
        else:
            # No significant split
            return [cluster]
    
    final_clusters = split_cluster(sorted_groups)
    
    # Create cluster labels
    cluster_labels = {}
    for cluster_id, cluster in enumerate(final_clusters, 1):
        for group in cluster:
            cluster_labels[group] = cluster_id
    
    return cluster_labels, final_clusters

print("\n" + "="*80)
print("STEP 3: Running Scott-Knott clustering")
print("="*80)

cluster_labels, final_clusters = scott_knott(data_tuples, alpha=0.05)
df_scott['cluster'] = df_scott['group'].map(cluster_labels)

print(f"\nNumber of clusters found: {len(final_clusters)}")
print("\nCluster assignments:")
for cluster_id, cluster_groups in enumerate(final_clusters, 1):
    print(f"\nCluster {cluster_id}:")
    for group in cluster_groups:
        mean_val = df_scott[df_scott['group'] == group]['value'].mean()
        print(f"  {group:20s}: mean = {mean_val:.4f}")

# Calculate summary statistics per group
print("\n" + "="*80)
print("GROUP STATISTICS:")
print("="*80)
group_stats = df_scott.groupby('group')['value'].agg(['count', 'mean', 'std', 'min', 'max'])
print(group_stats.to_string())

# Create visualization
print("\n" + "="*80)
print("STEP 4: Creating visualization")
print("="*80)

group_order = df_scott.groupby('group')['value'].mean().sort_values().index

plt.figure(figsize=(14, 8))
sns.boxplot(
    x='group', 
    y='value', 
    data=df_scott, 
    order=group_order, 
    hue='cluster', 
    palette='Set1', 
    dodge=False
)
plt.xticks(rotation=45, ha='right')
plt.title('Scott-Knott Clustering of Join Ratio by Stage and Category', fontsize=14, fontweight='bold')
plt.xlabel('Group', fontsize=12)
plt.ylabel('Join Ratio', fontsize=12)
plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Save the plot
output_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/scott_knott_join_ratio.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Plot saved to: {output_path}")

plt.show()

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)

