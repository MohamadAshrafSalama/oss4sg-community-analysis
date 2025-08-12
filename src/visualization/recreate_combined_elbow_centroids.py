import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples, pairwise_distances
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import interp1d

import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# -------------------------------------------------------------------------
# TOGGLE SETTINGS
# -------------------------------------------------------------------------
use_forced_k = True  # If True, we skip silhouette approach and just use 'forced_k'
forced_k = 4          # If use_forced_k=True, pick whichever you want: 3, 4, etc.

# Path to your data
file_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/EXP1(Rdoing_overlapping_and_double_check_numbers)/df_all_commits_with_stats.csv"

# -------------------------------------------------------------------------
# 1. Read & Prep
# -------------------------------------------------------------------------
df = pd.read_csv(file_path)

df['commit_date'] = pd.to_datetime(df['commit_date'])
df = df.sort_values('commit_date')

# Create a column "core_churn" which is churn *only* for core commits
# If is_core == True => core_churn = churn, else 0
df['core_churn'] = np.where(df['is_core'] == True, df['churn'], 0.0)

# -------------------------------------------------------------------------
# 2. Strict Stage Logic
#    - If total lifetime < 7 years => discard project entirely
#    - Otherwise keep only these exact slices:
#         early = [start, start+7)
#         middle = [start+7, start+10)
#         late = [start+10, start+13)
# -------------------------------------------------------------------------
def filter_and_label_stages(project_df):
    """
    Given all commits for a single project, returns a new df with
    stage labels assigned to each commit. We discard any commits
    outside the relevant slice or if total years <7.
    """
    project_df = project_df.copy()
    if project_df.empty:
        return project_df

    project_start = project_df['commit_date'].min()
    project_end   = project_df['commit_date'].max()
    total_years   = (project_end - project_start).days / 365.0

    # If <7 years, discard entire project
    if total_years < 7:
        return project_df.iloc[0:0]  # empty

    # Build cutoff dates:
    early_end   = project_start + pd.DateOffset(years=7)
    middle_end  = early_end + pd.DateOffset(years=3)   # start+10
    late_end    = middle_end + pd.DateOffset(years=3)  # start+13

    # We'll create a 'stage' column. By default, empty string => discard
    project_df['stage'] = ''

    # Always keep 'early' if >=7 total years => [start, start+7)
    # Commits in that range => stage = 'early'
    mask_early = (project_df['commit_date'] >= project_start) & \
                 (project_df['commit_date'] < early_end)
    project_df.loc[mask_early, 'stage'] = 'early'

    # Keep 'middle' only if total_years >=10 => [start+7, start+10)
    if total_years >= 10:
        mask_mid = (project_df['commit_date'] >= early_end) & \
                   (project_df['commit_date'] < middle_end)
        project_df.loc[mask_mid, 'stage'] = 'middle'

    # Keep 'late' only if total_years >=13 => [start+10, start+13)
    if total_years >= 13:
        mask_late = (project_df['commit_date'] >= middle_end) & \
                    (project_df['commit_date'] < late_end)
        project_df.loc[mask_late, 'stage'] = 'late'

    # Discard anything not labeled (outside final window if project is older than 13, or partial leftover if <10 or <13)
    project_df = project_df[project_df['stage'] != '']

    return project_df

# -------------------------------------------------------------------------
# 3. Apply to each project; build a new DataFrame
# -------------------------------------------------------------------------
projects = df['project'].unique()
all_filtered = []

for project in projects:
    sub_df = df[df['project'] == project]
    labeled_sub_df = filter_and_label_stages(sub_df)
    if not labeled_sub_df.empty:
        all_filtered.append(labeled_sub_df)

df_filtered = pd.concat(all_filtered, ignore_index=True)
df_filtered = df_filtered.sort_values('commit_date')

# -------------------------------------------------------------------------
# 4. Create monthly time series
#    Group by (project, stage, month) => sum churn & core_churn
#    Then drop months with churn=0 to avoid ratio=NaN
# -------------------------------------------------------------------------
df_filtered['year_month'] = df_filtered['commit_date'].dt.to_period('M')

monthly_stats = df_filtered.groupby(['project', 'stage', 'year_month']).agg({
    'churn': 'sum',       # sum of total churn for that month
    'core_churn': 'sum'   # sum of churn from core commits
}).reset_index()

# Drop rows where churn=0
monthly_stats = monthly_stats[monthly_stats['churn'] != 0].copy()

# ratio
monthly_stats['core_churn_ratio'] = monthly_stats['core_churn'] / monthly_stats['churn']

# Drop any leftover NaN
monthly_stats.dropna(subset=['core_churn_ratio'], inplace=True)

# Convert to Timestamp for sorting
monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()

# -------------------------------------------------------------------------
# 5. Build (project, stage) time series
# -------------------------------------------------------------------------
time_series_collection = []
unique_projects = monthly_stats['project'].unique()

for project in unique_projects:
    stages_for_project = monthly_stats[monthly_stats['project'] == project]['stage'].unique()
    for stg in stages_for_project:
        sub = monthly_stats[(monthly_stats['project'] == project) &
                            (monthly_stats['stage'] == stg)].copy()
        if not sub.empty:
            sub_sorted = sub.sort_values('date')
            time_series_collection.append({
                'project': project,
                'stage': stg,
                'time_series': sub_sorted,
                'label': f"{project} - {stg}"
            })

# -------------------------------------------------------------------------
# 6. Interpolate each time series to a fixed length (linear interpolation)
#    - skip series <2 points
# -------------------------------------------------------------------------
def interpolate_time_series(ts_collection):
    """
    Returns a list of dicts, each with:
      - project
      - stage
      - core_churn_ratio (interpolated array)
      - label
    All time series are interpolated to the length = max_length among them.
    """
    # find max length among series that have >=2 points
    valid_lengths = [len(item['time_series']) for item in ts_collection if len(item['time_series']) >= 2]
    if not valid_lengths:
        return []
    max_len = max(valid_lengths)

    result = []
    for item in ts_collection:
        ts = item['time_series']
        if len(ts) < 2:
            # skip single-point or empty
            continue
        x = np.arange(len(ts))  # 0..len(ts)-1
        x_new = np.linspace(0, len(ts) - 1, max_len)
        y = ts['core_churn_ratio'].values

        f = interp1d(x, y, kind='linear', bounds_error=False, fill_value='extrapolate')
        y_new = f(x_new)
        if np.isnan(y_new).any():
            # skip if interpolation produced NaN for some reason
            continue

        result.append({
            'project': item['project'],
            'stage': item['stage'],
            'core_churn_ratio': y_new,
            'label': item['label']
        })
    return result

interpolated_time_series = interpolate_time_series(time_series_collection)

# -------------------------------------------------------------------------
# 7. Prepare matrix X for clustering => each row is a time series
# -------------------------------------------------------------------------
if len(interpolated_time_series) < 2:
    print("Not enough valid time series after filtering. Exiting.")
    exit()

X = np.array([ts['core_churn_ratio'] for ts in interpolated_time_series])
# Double-check for any remaining NaN
mask_nan = np.isnan(X).any(axis=1)
if np.any(mask_nan):
    # drop those
    keep_rows = [i for i, flag in enumerate(mask_nan) if not flag]
    X = X[keep_rows]
    interpolated_time_series = [interpolated_time_series[i] for i in keep_rows]

if len(interpolated_time_series) < 2:
    print("Not enough rows for KMeans after removing NaNs. Exiting.")
    exit()

# -------------------------------------------------------------------------
# 8. Scale & KMeans
# -------------------------------------------------------------------------
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

if use_forced_k:
    best_k = forced_k
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    if len(set(cluster_labels)) > 1:
        best_score = silhouette_score(X_scaled, cluster_labels)
    else:
        best_score = -1
else:
    possible_ks = range(2, min(10, len(X_scaled) + 1))
    best_k, best_score = 2, -1
    sil_scores = []
    for k in possible_ks:
        kmeans_tmp = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_tmp = kmeans_tmp.fit_predict(X_scaled)
        if len(set(labels_tmp)) > 1:
            score = silhouette_score(X_scaled, labels_tmp)
        else:
            score = -1
        sil_scores.append((k, score))
    if sil_scores:
        best_k, best_score = max(sil_scores, key=lambda x: x[1])

    # final KMeans
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

# Attach cluster info
for i, ts in enumerate(interpolated_time_series):
    ts['cluster'] = cluster_labels[i]

# -------------------------------------------------------------------------
# 9. Compute centroids & medoids
# -------------------------------------------------------------------------
def compute_medoids(X_scaled, labels, n_clusters):
    medoids = {}
    for c in range(n_clusters):
        idx_in_cluster = np.where(labels == c)[0]
        if len(idx_in_cluster) == 0:
            continue
        if len(idx_in_cluster) == 1:
            # single point => trivially the medoid
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
for c_id in range(best_k):
    cluster_points = X_scaled[cluster_labels == c_id]
    if len(cluster_points) == 0:
        continue
    centroid_scaled = cluster_points.mean(axis=0)
    centroid_orig   = scaler.inverse_transform(centroid_scaled.reshape(1, -1))[0]
    centroids.append((c_id, centroid_scaled, centroid_orig))

medoids_dict = compute_medoids(X_scaled, cluster_labels, best_k)
medoids_list = []
for c in sorted(medoids_dict.keys()):
    g_idx, med_scaled = medoids_dict[c]
    med_orig = scaler.inverse_transform(med_scaled.reshape(1, -1))[0]
    medoids_list.append((c, g_idx, med_scaled, med_orig))

# -----------------------------
# (Assuming previous code up to obtaining X_scaled, cluster_labels, and centroids)
# -----------------------------

# --- ELBOW METHOD ---
inertias = []
k_range = range(1, 11)
for k in k_range:
    kmeans_elbow = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans_elbow.fit(X_scaled)
    inertias.append(kmeans_elbow.inertia_)

# --- Compute Silhouette Score per Cluster for k=4 ---
# We assume forced_k=4 was used, so cluster_labels has been assigned accordingly.
sample_silhouette_scores = silhouette_samples(X_scaled, cluster_labels)
cluster_silhouette_scores = {}
for cluster in np.unique(cluster_labels):
    cluster_mask = (cluster_labels == cluster)
    cluster_score = np.mean(sample_silhouette_scores[cluster_mask])
    cluster_silhouette_scores[cluster] = cluster_score

# Format the silhouette scores text
silhouette_text = f"Silhouette Scores (k={best_k}):\n" + "\n".join(
    [f"Cluster {cluster}: {cluster_silhouette_scores[cluster]:.3f}" for cluster in sorted(cluster_silhouette_scores)]
)

# --- SMOOTHED CENTROIDS ---
window_size = 3  # adjust the smoothing window as needed

# Compute smoothed centroids first
smoothed_centroids_raw = []
for (c_id, centroid_scaled, centroid_orig) in centroids:
    # Smooth using a simple moving average
    smoothed = np.convolve(centroid_orig, np.ones(window_size)/window_size, mode='same')
    smoothed_centroids_raw.append((c_id, smoothed))

# Analyze patterns to classify and sort clusters
def classify_cluster_pattern(smoothed_centroid):
    """Classify cluster pattern based on its characteristics"""
    avg_val = np.mean(smoothed_centroid)
    start_val = np.mean(smoothed_centroid[:len(smoothed_centroid)//4])
    end_val = np.mean(smoothed_centroid[-len(smoothed_centroid)//4:])
    slope = end_val - start_val
    variance = np.var(smoothed_centroid)
    
    # Classify based on characteristics
    if avg_val < 0.3 and variance < 0.01:
        return "Low Core Activity", 0
    elif slope > 0.2:
        return "Increasing Core Activity", 1
    elif avg_val > 0.6 and variance < 0.01:
        return "High Constant Core", 2
    elif slope < -0.2:
        return "Declining Core Activity", 3
    else:
        # Fallback: sort by average value
        if avg_val < 0.4:
            return "Low Core Activity", 0
        elif slope > 0:
            return "Increasing Core Activity", 1
        elif avg_val > 0.6:
            return "High Constant Core", 2
        else:
            return "Declining Core Activity", 3

# Classify and sort clusters
classified_clusters = []
for c_id, smoothed in smoothed_centroids_raw:
    pattern_name, pattern_order = classify_cluster_pattern(smoothed)
    classified_clusters.append((pattern_order, c_id, smoothed, pattern_name))

# Sort by pattern order
classified_clusters.sort(key=lambda x: x[0])

# Create sorted list with new order (0, 1, 2, 3)
smoothed_centroids = []
cluster_id_mapping = {}  # Maps old cluster ID to new display order
for new_order, (pattern_order, old_c_id, smoothed, pattern_name) in enumerate(classified_clusters):
    smoothed_centroids.append((new_order, smoothed))
    cluster_id_mapping[old_c_id] = new_order

# Define cluster names mapping (now in correct order)
cluster_names = {
    0: "Low Core Activity",
    1: "Increasing Core Activity",
    2: "High Constant Core",
    3: "Declining Core Activity"
}

# Define colors for each cluster (in order)
cluster_colors = {
    0: 'tab:blue',      # Blue for Low Core Activity
    1: 'tab:orange',    # Orange for Increasing Core Activity
    2: 'tab:green',     # Green for High Constant Core
    3: 'tab:red'        # Red for Declining Core Activity
}

# Determine global y-axis limits
global_y_min, global_y_max = np.inf, -np.inf
for (new_order, smoothed) in smoothed_centroids:
    global_y_min = min(global_y_min, np.min(smoothed))
    global_y_max = max(global_y_max, np.max(smoothed))

# Create a common x-axis range (assumes all centroids have the same length)
x_range = np.arange(len(smoothed_centroids[0][1]))

# -----------------------------
# CREATE COMBINED FIGURE WITH GridSpec
# -----------------------------
fig = plt.figure(figsize=(14, 8))
# Outer GridSpec: 1 row, 2 columns; left for elbow plot, right for smoothed centroids
outer_gs = gridspec.GridSpec(1, 2, width_ratios=[1, 2], wspace=0.3)

# Left subplot: Elbow Plot
ax_elbow = fig.add_subplot(outer_gs[0, 0])
ax_elbow.plot(k_range, inertias, marker='o')
ax_elbow.set_xlabel('Number of Clusters (k)', fontsize=14)  # default 12+2
ax_elbow.set_ylabel('Inertia', fontsize=14)  # default 12+2
ax_elbow.set_title('Elbow Method For Optimal k', fontsize=14)  # default 12+2
ax_elbow.set_xticks(list(k_range))
ax_elbow.grid(True, linestyle='--', alpha=0.7)

# +2 to X and Y axis tick labels for elbow plot
ax_elbow.tick_params(axis='x', labelsize=14)  # +2: 12 -> 14
ax_elbow.tick_params(axis='y', labelsize=14)  # +2: 12 -> 14

# Silhouette scores text box removed

# Right subplot: Create inner GridSpec for 4 vertically stacked subplots
inner_gs = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=outer_gs[0, 1], hspace=0.4)

for i, (c_id, smoothed) in enumerate(smoothed_centroids):
    ax = fig.add_subplot(inner_gs[i, 0])
    # Use the correct color for each cluster
    color = cluster_colors.get(c_id, f"C{c_id}")
    ax.plot(x_range, smoothed, linewidth=2, color=color)
    # Title includes cluster number and its name (original 10 + 2 = 12)
    ax.set_title(f"Cluster {c_id}: {cluster_names.get(c_id, f'Cluster {c_id}')}", fontsize=12)
    ax.set_xlim(x_range[0], x_range[-1])
    ax.set_ylim(global_y_min, global_y_max)
    ax.grid(True, linestyle='--', alpha=0.7)
    # +2 to X and Y axis tick labels
    ax.tick_params(axis='x', labelsize=14)  # +2: 12 -> 14
    ax.tick_params(axis='y', labelsize=14)  # +2: 12 -> 14
    # Remove x tick labels for all but the bottom subplot
    if i < 3:
        ax.set_xticklabels([])

# Add common x and y labels for the right column (original 12 + 2 = 14)
fig.text(0.73, 0.04, "Months", ha="center", fontsize=14)
fig.text(0.37, 0.5, "Core Churn Ratio", va="center", rotation="vertical", fontsize=14)

plt.tight_layout(rect=[0.03, 0.03, 1, 1])
plt.savefig("combined_elbow_smoothed_centroids.png", dpi=300)
plt.show()

print("Plot saved as: combined_elbow_smoothed_centroids.png")

