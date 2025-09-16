import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

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

print(f"Using hardcoded medians:")
print(f"Join Rate Median: {join_rate_median}")
print(f"Leave Rate Median: {leave_rate_median}")

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

# Function to create and save plots for a given dataframe and stage name
def create_plots(df, stage_name, filename_suffix):
    print(f"\n{'='*60}")
    print(f"Creating plot: {stage_name}")
    print(f"Total projects: {len(df)}")
    print(f"OSS projects (SG=0): {len(df[df['SG'] == 0])}")
    print(f"OSS4SG projects (SG=1): {len(df[df['SG'] == 1])}")
    print('='*60)
    
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
    axs[0].set_title(f'OSS Only - {stage_name}')
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
    axs[1].set_title(f'OSS4SG Only - {stage_name}')
    axs[1].set_xlabel('Average Leave Rate')
    add_quadrant_labels_and_lines(axs[1])
    
    plt.tight_layout()
    
    # Save the plots
    output_pdf = os.path.join(output_dir, f'kde_plots_{filename_suffix}.pdf')
    output_png = os.path.join(output_dir, f'kde_plots_{filename_suffix}.png')
    
    plt.savefig(output_pdf, format='pdf', dpi=300)
    plt.savefig(output_png, format='png', dpi=300)
    
    print(f"✓ Saved: {output_pdf}")
    print(f"✓ Saved: {output_png}")
    
    plt.close()

# Create all plots
print("\n" + "="*60)
print("GENERATING ALL PLOTS")
print("="*60)

# 1. All Stages (combined)
create_plots(df_all, 'All Stages', 'all_stages_combined')

# 2. Early Stage
create_plots(df_early, 'Early Stage', 'early_stage')

# 3. Mid Stage
create_plots(df_mid, 'Mid Stage', 'mid_stage')

# 4. Late Stage
create_plots(df_late, 'Late Stage', 'late_stage')

print("\n" + "="*60)
print("✓ ALL PLOTS GENERATED SUCCESSFULLY!")
print("="*60)
print(f"\nOutput directory: {output_dir}")
print("\nGenerated files:")
print("  - kde_plots_all_stages_combined.pdf/png")
print("  - kde_plots_early_stage.pdf/png")
print("  - kde_plots_mid_stage.pdf/png")
print("  - kde_plots_late_stage.pdf/png")

