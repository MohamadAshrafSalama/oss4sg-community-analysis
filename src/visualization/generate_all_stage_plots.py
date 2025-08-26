import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Define the directories
data_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

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

# Function to create plots for a given stage
def create_stage_plots(stage_name, filename):
    print(f"\n{'='*60}")
    print(f"Processing: {stage_name}")
    print('='*60)
    
    # Load the data
    df = pd.read_csv(os.path.join(data_dir, filename))
    
    print(f"Total projects: {len(df)}")
    print(f"OSS projects (SG=0): {len(df[df['SG'] == 0])}")
    print(f"OSS4SG projects (SG=1): {len(df[df['SG'] == 1])}")
    
    # Calculate medians
    join_rate_median = df['Average Join Rate'].median()
    leave_rate_median = df['Average Leave Rate'].median()
    
    print(f"Join Rate Median: {join_rate_median:.3f}")
    print(f"Leave Rate Median: {leave_rate_median:.3f}")
    
    # Create figure with 2 subplots
    fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    
    # Plot OSS Only (SG=0)
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
    axs[0].set_title(f'OSS Only - {stage_name}', fontsize=16, fontweight='bold')
    axs[0].set_xlabel('Average Leave Rate', fontsize=12)
    axs[0].set_ylabel('Average Join Rate', fontsize=12)
    add_quadrant_labels_and_lines(axs[0], join_rate_median, leave_rate_median, hide_legend=True)
    
    # Plot OSS4SG Only (SG=1)
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
    axs[1].set_title(f'OSS4SG Only - {stage_name}', fontsize=16, fontweight='bold')
    axs[1].set_xlabel('Average Leave Rate', fontsize=12)
    add_quadrant_labels_and_lines(axs[1], join_rate_median, leave_rate_median)
    
    plt.tight_layout()
    
    # Save the plots
    stage_slug = stage_name.lower().replace(' ', '_')
    output_pdf = os.path.join(output_dir, f'kde_plots_{stage_slug}.pdf')
    output_png = os.path.join(output_dir, f'kde_plots_{stage_slug}.png')
    
    plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_png, format='png', dpi=300, bbox_inches='tight')
    
    print(f"✓ Saved: {output_pdf}")
    print(f"✓ Saved: {output_png}")
    
    plt.close()

# Process all stages
stages = [
    ('All Stages', 'Join Rate vs Leave Rate for all stages.csv'),
    ('Early Stage', 'Join Rate vs Leave Rate for early stages.csv'),
    ('Mid Stage', 'Join Rate vs Leave Rate for mid stages.csv'),
    ('Late Stage', 'Join Rate vs Leave Rate for late stages.csv')
]

for stage_name, filename in stages:
    try:
        create_stage_plots(stage_name, filename)
    except Exception as e:
        print(f"Error processing {stage_name}: {e}")

print("\n" + "="*60)
print("✓ ALL PLOTS GENERATED SUCCESSFULLY!")
print("="*60)
print(f"\nOutput directory: {output_dir}")

