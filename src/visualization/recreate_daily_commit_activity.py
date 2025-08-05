import pandas as pd

import matplotlib.pyplot as plt

from scipy.signal import savgol_filter
 
# ---------------------------

# 0. Load Dataset and Filter by Date

# ---------------------------

df_all = pd.read_csv("/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/EXP1(Rdoing_overlapping_and_double_check_numbers)/df_all_commits_with_stats.csv")

df_all['commit_date'] = pd.to_datetime(df_all['commit_date'])
 
 
 
 
# Define a cutoff date and make it timezone-aware (UTC)

cutoff_date = pd.to_datetime("2013-04-01").tz_localize("UTC")
 
 
 
 
# Filter commits on or after the cutoff date.

df_all = df_all[df_all["commit_date"] >= cutoff_date].copy()
 
# ---------------------------

# 1. Create Daily Aggregations

# ---------------------------

# For Core commits

daily_agg_core = (
    df_all[df_all["is_core"] == True]
    .groupby(["category", "day_of_year"])
    .size()
    .reset_index(name="num_commits")
)

# For Non-Core commits

daily_agg_noncore = (
    df_all[df_all["is_core"] == False]
    .groupby(["category", "day_of_year"])
    .size()
    .reset_index(name="num_commits")
)
 
# ---------------------------

# 2. Normalize the Daily Counts per Category using Min–Max Normalization

# ---------------------------

for agg in [daily_agg_core, daily_agg_noncore]:
    agg["normalized"] = 0.0
    for cat in ["OSS", "OSS4SG"]:
        subset = agg[agg["category"] == cat]
        min_val = subset["num_commits"].min()
        max_val = subset["num_commits"].max()
        if max_val > min_val:
            norm_vals = (subset["num_commits"] - min_val) / (max_val - min_val)
        else:
            norm_vals = 0.0
        agg.loc[agg["category"] == cat, "normalized"] = norm_vals
 
# ---------------------------

# 3. Optional: Define a Trimming Function to Remove Edge Days

# ---------------------------

def trim_data(df, days_to_trim=10):
    max_day = df['day_of_year'].max()
    return df[(df['day_of_year'] > days_to_trim) & (df['day_of_year'] <= (max_day - days_to_trim))]
 
daily_agg_core_trimmed = trim_data(daily_agg_core, days_to_trim=10)

daily_agg_noncore_trimmed = trim_data(daily_agg_noncore, days_to_trim=10)
 
# ---------------------------

# 4. Smoothing Function with Circular (Wrap) Mode

# ---------------------------

def smooth_curve(x_vals, y_vals, window=31, poly=2):
    w_len = window if (len(y_vals) >= window and window % 2 == 1) else min(len(y_vals), 3)
    return savgol_filter(y_vals, w_len, poly, mode='wrap') if w_len >= 3 else y_vals
 
# ---------------------------

# 5. Define a Simple Color Mapping for Categories

# ---------------------------

color_mapping = {
    "OSS": "#1f77b4",    # Blue
    "OSS4SG": "#ff7f0e"   # Orange
}
 
# ---------------------------

# 6. Plotting: Two Subplots (Core and Non-Core) - Stacked Vertically

# ---------------------------

plt.rcParams["figure.figsize"] = (12, 12)

fig, axes = plt.subplots(2, 1, figsize=(12, 12))
 
def plot_normalized_data(ax, data, label_suffix):
    for cat in ["OSS", "OSS4SG"]:
        sub = data[data["category"] == cat].sort_values("day_of_year")
        x = sub["day_of_year"].values
        y = sub["normalized"].values
        y_smooth = smooth_curve(x, y, window=31, poly=2)
        ax.plot(x, y_smooth, label=f"{cat} {label_suffix}",
                color=color_mapping.get(cat, "grey"), linewidth=2)
    ax.set_xlabel("Day of Year (1..365)", fontsize=16)  # +2 more: 14 -> 16
    ax.set_ylabel("Normalized Commits", fontsize=16)  # +2 more: 14 -> 16
    ax.legend(fontsize=14, loc='upper right')  # +2 more: 12 -> 14
    ax.grid(True, linestyle="--", alpha=0.5)
    # +2 more to X and Y axis tick labels
    ax.tick_params(axis='x', labelsize=16)  # +2 more: 14 -> 16
    ax.tick_params(axis='y', labelsize=16)  # +2 more: 14 -> 16
 
# Top plot: Core
plot_normalized_data(axes[0], daily_agg_core_trimmed, label_suffix="- Core")
axes[0].set_title("Daily - Core", fontsize=18)  # +2 more: 16 -> 18

# Bottom plot: Non-Core
plot_normalized_data(axes[1], daily_agg_noncore_trimmed, label_suffix="- Non-Core")
axes[1].set_title("Daily - Non-Core", fontsize=18)  # +2 more: 16 -> 18
 
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.savefig("daily_commit_activity_normalized.png", dpi=300, bbox_inches='tight')
plt.show()

from scipy.stats import mannwhitneyu

# Extract the four series from trimmed data
oss_core = daily_agg_core_trimmed[daily_agg_core_trimmed['category'] == 'OSS']['normalized']
oss4sg_core = daily_agg_core_trimmed[daily_agg_core_trimmed['category'] == 'OSS4SG']['normalized']
oss_noncore = daily_agg_noncore_trimmed[daily_agg_noncore_trimmed['category'] == 'OSS']['normalized']
oss4sg_noncore = daily_agg_noncore_trimmed[daily_agg_noncore_trimmed['category'] == 'OSS4SG']['normalized']

# Perform Mann-Whitney U tests for key comparisons
# 1. Core: OSS vs OSS4SG
stat_core, p_core = mannwhitneyu(oss_core, oss4sg_core, alternative='two-sided')

# 2. Non-Core: OSS vs OSS4SG
stat_noncore, p_noncore = mannwhitneyu(oss_noncore, oss4sg_noncore, alternative='two-sided')

# 3. OSS: Core vs Non-Core
stat_oss, p_oss = mannwhitneyu(oss_core, oss_noncore, alternative='two-sided')

# 4. OSS4SG: Core vs Non-Core
stat_oss4sg, p_oss4sg = mannwhitneyu(oss4sg_core, oss4sg_noncore, alternative='two-sided')

# Display results
print("Mann-Whitney U Test Results:")
print(f"1. Core: OSS vs OSS4SG: U={stat_core:.1f}, p={p_core:.4f}")
print(f"2. Non-Core: OSS vs OSS4SG: U={stat_noncore:.1f}, p={p_noncore:.4f}")
print(f"3. OSS: Core vs Non-Core: U={stat_oss:.1f}, p={p_oss:.4f}")
print(f"4. OSS4SG: Core vs Non-Core: U={stat_oss4sg:.1f}, p={p_oss4sg:.4f}")

print("\nPlot saved as: daily_commit_activity_normalized.png")

