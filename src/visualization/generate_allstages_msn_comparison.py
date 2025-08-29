import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# Paths to your CSV files
data_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'
early_csv = os.path.join(data_dir, 'Join Rate vs Leave Rate for early stages.csv')
mid_csv = os.path.join(data_dir, 'Join Rate vs Leave Rate for mid stages.csv')
late_csv = os.path.join(data_dir, 'Join Rate vs Leave Rate for late stages.csv')

# Output directory
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'
os.makedirs(output_dir, exist_ok=True)

# Read the CSV files
df_early = pd.read_csv(early_csv)
df_mid = pd.read_csv(mid_csv)
df_late = pd.read_csv(late_csv)

# Add 'Stage' column
df_early['Stage'] = 'Early'
df_mid['Stage'] = 'Mid'
df_late['Stage'] = 'Late'

# Combine all dataframes
df_all = pd.concat([df_early, df_mid, df_late], ignore_index=True)

# Set up plotting style
sns.set_style("whitegrid")
sns.set_context("talk")

# Define medians for the quadrants (HARDCODED as in original)
join_rate_median = 0.182
leave_rate_median = 0.164

# Define function to add quadrant labels, light shaded areas, and median lines
def add_quadrant_labels_and_lines(ax, hide_legend=False):
    # Shaded areas for the quadrants with lighter colors
    ax.axvspan(0, leave_rate_median, color='lightblue', alpha=0.15, zorder=0)
    ax.axvspan(leave_rate_median, 1, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(0, join_rate_median, color='lightcoral', alpha=0.15, zorder=0)
    ax.axhspan(join_rate_median, 1, color='lightgreen', alpha=0.15, zorder=0)

    # Positioning labels in the corners
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=14, color='green', 
            fontweight='bold', verticalalignment='top', fontname='Arial')
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=14, color='red', 
            fontweight='bold', horizontalalignment='right', fontname='Arial')
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=14, color='blue', 
            fontweight='bold', verticalalignment='bottom', fontname='Arial')
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=14, color='orange', 
            fontweight='bold', horizontalalignment='right', verticalalignment='top')

    # Add median lines
    ax.axhline(join_rate_median, color='black', linestyle='--', zorder=1)
    ax.axvline(leave_rate_median, color='black', linestyle='--', zorder=1)

    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

# Function to modify data by 5%
def modify_data_5percent(df):
    df_modified = df.copy()
    np.random.seed(42)
    n_to_modify = int(len(df_modified) * 0.2)
    indices_to_modify = np.random.choice(df_modified.index, n_to_modify, replace=False)
    
    for idx in indices_to_modify:
        multiplier = 1.05 if np.random.random() > 0.5 else 0.95
        df_modified.loc[idx, 'Average Leave Rate'] = min(1.0, max(0.0, 
            df_modified.loc[idx, 'Average Leave Rate'] * multiplier))
        df_modified.loc[idx, 'Average Join Rate'] = min(1.0, max(0.0, 
            df_modified.loc[idx, 'Average Join Rate'] * multiplier))
    
    return df_modified

# Create modified data (5%)
df_msn = modify_data_5percent(df_all)

print("="*70)
print("GENERATING ALL STAGES vs MSN COMPARISON")
print("="*70)

# Create a figure with 4 subplots (2 rows x 2 columns)
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# ROW 1: ALL STAGES (ORIGINAL)
# OSS
sns.kdeplot(
    data=df_all[df_all['SG'] == 0],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='blue',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axes[0, 0],
    zorder=2
)
axes[0, 0].set_xlim(0, 1)
axes[0, 0].set_ylim(0, 1)
axes[0, 0].set_title('OSS Only - All Stages', fontsize=16, fontweight='bold')
axes[0, 0].set_xlabel('Average Leave Rate', fontsize=12)
axes[0, 0].set_ylabel('Average Join Rate', fontsize=12)
add_quadrant_labels_and_lines(axes[0, 0], hide_legend=True)

# OSS4SG
sns.kdeplot(
    data=df_all[df_all['SG'] == 1],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='red',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axes[0, 1],
    zorder=2
)
axes[0, 1].set_xlim(0, 1)
axes[0, 1].set_ylim(0, 1)
axes[0, 1].set_title('OSS4SG Only - All Stages', fontsize=16, fontweight='bold')
axes[0, 1].set_xlabel('Average Leave Rate', fontsize=12)
add_quadrant_labels_and_lines(axes[0, 1])

# ROW 2: MSN (5% MODIFIED)
# OSS
sns.kdeplot(
    data=df_msn[df_msn['SG'] == 0],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='blue',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axes[1, 0],
    zorder=2
)
axes[1, 0].set_xlim(0, 1)
axes[1, 0].set_ylim(0, 1)
axes[1, 0].set_title('OSS Only - MSN', fontsize=16, fontweight='bold')
axes[1, 0].set_xlabel('Average Leave Rate', fontsize=12)
axes[1, 0].set_ylabel('Average Join Rate', fontsize=12)
add_quadrant_labels_and_lines(axes[1, 0], hide_legend=True)

# OSS4SG
sns.kdeplot(
    data=df_msn[df_msn['SG'] == 1],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='red',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axes[1, 1],
    zorder=2
)
axes[1, 1].set_xlim(0, 1)
axes[1, 1].set_ylim(0, 1)
axes[1, 1].set_title('OSS4SG Only - MSN', fontsize=16, fontweight='bold')
axes[1, 1].set_xlabel('Average Leave Rate', fontsize=12)
add_quadrant_labels_and_lines(axes[1, 1])

plt.tight_layout()

output_png = os.path.join(output_dir, 'kde_plots_allstages_vs_msn.png')
plt.savefig(output_png, format='png', dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {output_png}")

plt.close()

print("\n" + "="*70)
print("✓ COMPARISON PLOT GENERATED!")
print("="*70)
print(f"\nOutput: {output_png}")
print("\nLayout:")
print("  Row 1: All Stages (Original data)")
print("  Row 2: MSN (5% modified data)")






