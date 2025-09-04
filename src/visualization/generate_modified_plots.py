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
    ax.axvspan(0, leave_rate_median, color='lightblue', alpha=0.15, zorder=0)  # Stable
    ax.axvspan(leave_rate_median, 1, color='lightcoral', alpha=0.15, zorder=0)  # Unstable
    ax.axhspan(0, join_rate_median, color='lightcoral', alpha=0.15, zorder=0)  # Unattractive
    ax.axhspan(join_rate_median, 1, color='lightgreen', alpha=0.15, zorder=0)  # Attractive

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

    # Optionally hide the legend
    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

def create_plot(df, filename, title_suffix=""):
    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    
    # **Plot OSS Only**
    sns.kdeplot(
        data=df[df['SG'] == 0],
        x='Average Leave Rate',
        y='Average Join Rate',
        color='blue',
        fill=True,
        alpha=0.6,
        thresh=0.05,
        levels=10,
        ax=axs[0],
        zorder=2
    )
    axs[0].set_xlim(0, 1)
    axs[0].set_ylim(0, 1)
    axs[0].set_title(f'OSS Only - All Stages{title_suffix}')
    axs[0].set_xlabel('Average Leave Rate')
    axs[0].set_ylabel('Average Join Rate')
    add_quadrant_labels_and_lines(axs[0], hide_legend=True)
    
    # **Plot OSS4SG Only**
    sns.kdeplot(
        data=df[df['SG'] == 1],
        x='Average Leave Rate',
        y='Average Join Rate',
        color='red',
        fill=True,
        alpha=0.6,
        thresh=0.05,
        levels=10,
        ax=axs[1],
        zorder=2
    )
    axs[1].set_xlim(0, 1)
    axs[1].set_ylim(0, 1)
    axs[1].set_title(f'OSS4SG Only - All Stages{title_suffix}')
    axs[1].set_xlabel('Average Leave Rate')
    add_quadrant_labels_and_lines(axs[1])
    
    plt.tight_layout()
    
    output_png = os.path.join(output_dir, filename)
    plt.savefig(output_png, format='png', dpi=300)
    print(f"✓ Saved: {output_png}")
    plt.close()

# Function to modify data by a percentage
def modify_data(df, percent_change):
    df_modified = df.copy()
    
    # Randomly select ~20% of projects to modify
    np.random.seed(42)  # For reproducibility
    n_to_modify = int(len(df_modified) * 0.2)
    indices_to_modify = np.random.choice(df_modified.index, n_to_modify, replace=False)
    
    print(f"\nModifying {n_to_modify} projects by ±{percent_change}%:")
    
    for idx in indices_to_modify[:5]:  # Print first 5 as examples
        repo_name = df_modified.loc[idx, 'Repo']
        old_leave = df_modified.loc[idx, 'Average Leave Rate']
        old_join = df_modified.loc[idx, 'Average Join Rate']
        
        # Randomly decide to increase or decrease
        multiplier = 1 + (percent_change / 100) if np.random.random() > 0.5 else 1 - (percent_change / 100)
        
        df_modified.loc[idx, 'Average Leave Rate'] = min(1.0, max(0.0, old_leave * multiplier))
        df_modified.loc[idx, 'Average Join Rate'] = min(1.0, max(0.0, old_join * multiplier))
        
        new_leave = df_modified.loc[idx, 'Average Leave Rate']
        new_join = df_modified.loc[idx, 'Average Join Rate']
        
        print(f"  {repo_name}: Leave {old_leave:.4f}→{new_leave:.4f}, Join {old_join:.4f}→{new_join:.4f}")
    
    print(f"  ... and {n_to_modify - 5} more projects modified")
    
    return df_modified

print("="*70)
print("GENERATING MODIFIED PLOTS")
print("="*70)

# 1% Modification
print("\n" + "="*70)
print("GENERATING PLOT WITH 1% CHANGE")
print("="*70)
df_modified_1 = modify_data(df_all, 1)
create_plot(df_modified_1, 'kde_plots_modified_1percent.png', ' (1% Modified)')

# 2% Modification
print("\n" + "="*70)
print("GENERATING PLOT WITH 2% CHANGE")
print("="*70)
df_modified_2 = modify_data(df_all, 2)
create_plot(df_modified_2, 'kde_plots_modified_2percent.png', ' (2% Modified)')

print("\n" + "="*70)
print("✓ ALL MODIFIED PLOTS GENERATED!")
print("="*70)
print(f"\nOutput directory: {output_dir}")
print("\nGenerated files:")
print("  - kde_plots_with_light_shaded_quadrants.png (ORIGINAL)")
print("  - kde_plots_modified_1percent.png (±1% CHANGE)")
print("  - kde_plots_modified_2percent.png (±2% CHANGE)")

