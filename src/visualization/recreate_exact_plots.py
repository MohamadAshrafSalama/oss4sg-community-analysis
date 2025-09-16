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

print("Data loaded successfully!")
print(f"Total projects in df_all: {len(df_all)}")
print(f"OSS projects (SG=0): {len(df_all[df_all['SG'] == 0])}")
print(f"OSS4SG projects (SG=1): {len(df_all[df_all['SG'] == 1])}")
print("\ndf_all preview:")
print(df_all.head())

# Define medians for the quadrants (HARDCODED as in original)
join_rate_median = 0.182
leave_rate_median = 0.164

print(f"\nUsing hardcoded medians:")
print(f"Join Rate Median: {join_rate_median}")
print(f"Leave Rate Median: {leave_rate_median}")

# Define function to add quadrant labels, light shaded areas, and median lines
def add_quadrant_labels_and_lines(ax, hide_legend=False):
    # Shaded areas for the quadrants with lighter colors
    ax.axvspan(0, leave_rate_median, color='lightblue', alpha=0.15, zorder=0)  # Stable
    ax.axvspan(leave_rate_median, 1, color='lightcoral', alpha=0.15, zorder=0)  # Unstable
    ax.axhspan(0, join_rate_median, color='lightcoral', alpha=0.15, zorder=0)  # Unattractive
    ax.axhspan(join_rate_median, 1, color='lightgreen', alpha=0.15, zorder=0)  # Attractive

    # Positioning labels in the corners (original 14 + 2 = 16)
    ax.text(0.05, 0.95, 'Attractive', transform=ax.transAxes, fontsize=16, color='green', 
            fontweight='bold', verticalalignment='top', fontname='Arial')
    ax.text(0.95, 0.05, 'Unattractive', transform=ax.transAxes, fontsize=16, color='red', 
            fontweight='bold', horizontalalignment='right', fontname='Arial')
    ax.text(0.05, 0.05, 'Stable', transform=ax.transAxes, fontsize=16, color='blue', 
            fontweight='bold', verticalalignment='bottom', fontname='Arial')
    ax.text(0.75, 0.95, 'Unstable', transform=ax.transAxes, fontsize=16, color='orange', 
            fontweight='bold', horizontalalignment='right', verticalalignment='top')

    # Add median lines
    ax.axhline(join_rate_median, color='black', linestyle='--', zorder=1)
    ax.axvline(leave_rate_median, color='black', linestyle='--', zorder=1)

    # Optionally hide the legend
    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

# **Remove the Combined Graph**
# Original: fig, axs = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
# Updated to have only 2 subplots
fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# **Plot OSS Only (assuming SG=0 in the dataset for OSS)**
sns.kdeplot(
    data=df_all[df_all['SG'] == 0],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='blue',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[0],
    zorder=2  # Ensure KDE is drawn above shading
)
axs[0].set_xlim(0, 1)
axs[0].set_ylim(0, 1)
# Add OSS label above the plot (original 16 + 2 = 18)
axs[0].text(0.5, 1.05, 'OSS', transform=axs[0].transAxes, fontsize=18, 
            fontweight='bold', ha='center', va='bottom')
axs[0].set_xlabel('Average Leave Rate', fontsize=14)  # default 12+2
axs[0].set_ylabel('Average Join Rate', fontsize=14)  # default 12+2
# +2 to X and Y axis tick labels
axs[0].tick_params(axis='both', which='major', labelsize=14)  # +2: 12 -> 14
add_quadrant_labels_and_lines(axs[0], hide_legend=True)

# **Plot OSS4SG Only (assuming SG=1 in the dataset for OSS4SG)**
sns.kdeplot(
    data=df_all[df_all['SG'] == 1],
    x='Average Leave Rate',
    y='Average Join Rate',
    color='red',
    fill=True,
    alpha=0.6,
    thresh=0.05,
    levels=10,
    ax=axs[1],
    zorder=2  # Ensure KDE is drawn above shading
)
axs[1].set_xlim(0, 1)
axs[1].set_ylim(0, 1)
# Add OSS4SG label above the plot (original 16 + 2 = 18)
axs[1].text(0.5, 1.05, 'OSS4SG', transform=axs[1].transAxes, fontsize=18, 
            fontweight='bold', ha='center', va='bottom')
axs[1].set_xlabel('Average Leave Rate', fontsize=14)  # default 12+2
# +2 to X and Y axis tick labels
axs[1].tick_params(axis='both', which='major', labelsize=14)  # +2: 12 -> 14
add_quadrant_labels_and_lines(axs[1])

plt.tight_layout()

# Save the plot as a high-resolution PDF
output_pdf = os.path.join(output_dir, 'kde_plots_with_light_shaded_quadrants.pdf')
plt.savefig(output_pdf, format='pdf', dpi=300)
print(f"\n✓ Plot saved to: {output_pdf}")

# Also save as PNG
output_png = os.path.join(output_dir, 'kde_plots_with_light_shaded_quadrants.png')
plt.savefig(output_png, format='png', dpi=300)
print(f"✓ Plot saved to: {output_png}")

plt.show()

print("\n✓ Plot generation complete (using combined early+mid+late data)!")

