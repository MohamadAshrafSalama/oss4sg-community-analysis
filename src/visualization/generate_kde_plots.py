import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Define the directories
data_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the data
df_all = pd.read_csv(os.path.join(data_dir, 'Join Rate vs Leave Rate for all stages.csv'))

print("Data loaded successfully!")
print(f"Total projects: {len(df_all)}")
print(f"OSS projects (SG=0): {len(df_all[df_all['SG'] == 0])}")
print(f"OSS4SG projects (SG=1): {len(df_all[df_all['SG'] == 1])}")
print("\nData preview:")
print(df_all.head())
print("\nData statistics:")
print(df_all.describe())

# Define medians for the quadrants
join_rate_median = df_all['Average Join Rate'].median()
leave_rate_median = df_all['Average Leave Rate'].median()

print(f"\nMedians:")
print(f"Join Rate Median: {join_rate_median:.3f}")
print(f"Leave Rate Median: {leave_rate_median:.3f}")

# Define function to add quadrant labels, light shaded areas, and median lines
def add_quadrant_labels_and_lines(ax, join_median, leave_median, hide_legend=False):
    # Shaded areas for the quadrants with lighter colors
    ax.axvspan(0, leave_median, color='lightblue', alpha=0.15, zorder=0)  # Stable
    ax.axvspan(leave_median, 1, color='lightcoral', alpha=0.15, zorder=0)  # Unstable
    ax.axhspan(0, join_median, color='lightcoral', alpha=0.15, zorder=0)  # Unattractive
    ax.axhspan(join_median, 1, color='lightgreen', alpha=0.15, zorder=0)  # Attractive

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
    ax.axhline(join_median, color='black', linestyle='--', zorder=1)
    ax.axvline(leave_median, color='black', linestyle='--', zorder=1)

    # Optionally hide the legend
    if hide_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

# Create figure with 2 subplots
fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# Plot OSS Only (SG=0)
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
axs[0].set_title('OSS Only - All Stages', fontsize=16, fontweight='bold')
axs[0].set_xlabel('Average Leave Rate', fontsize=12)
axs[0].set_ylabel('Average Join Rate', fontsize=12)
add_quadrant_labels_and_lines(axs[0], join_rate_median, leave_rate_median, hide_legend=True)

# Plot OSS4SG Only (SG=1)
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
axs[1].set_title('OSS4SG Only - All Stages', fontsize=16, fontweight='bold')
axs[1].set_xlabel('Average Leave Rate', fontsize=12)
add_quadrant_labels_and_lines(axs[1], join_rate_median, leave_rate_median)

plt.tight_layout()

# Save the plot as a high-resolution PDF
output_pdf = os.path.join(output_dir, 'kde_plots_all_stages.pdf')
plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')
print(f"\nPlot saved to: {output_pdf}")

# Also save as PNG for easy viewing
output_png = os.path.join(output_dir, 'kde_plots_all_stages.png')
plt.savefig(output_png, format='png', dpi=300, bbox_inches='tight')
print(f"Plot saved to: {output_png}")

plt.show()

print("\n✓ Plot generation complete!")

