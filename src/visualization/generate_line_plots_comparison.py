import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set the directory where the CSV files are located
directory = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'

# File paths for Join Rate and Leave Rate
join_rate_files = [
    os.path.join(directory, 'Average Join Rate for each window (Early Repos).csv'),
    os.path.join(directory, 'Average Join Rate for each window (Mid Repos).csv'),
    os.path.join(directory, 'Average Join Rate for each window (Late Repos).csv')
]

leave_rate_files = [
    os.path.join(directory, 'Average Leave Rate for each window (Early Repos).csv'),
    os.path.join(directory, 'Average Leave Rate for each window (Mid Repos).csv'),
    os.path.join(directory, 'Average Leave Rate for each window (Late Repos).csv')
]

# Function to load CSV and extract SG and Not SG columns
def load_and_concat(file_list):
    sg_data = []
    not_sg_data = []
    
    for file in file_list:
        df = pd.read_csv(file)
        sg_data.append(df['SG'])
        not_sg_data.append(df['Not SG'])
    
    sg_concat = pd.concat(sg_data, axis=0, ignore_index=True)
    not_sg_concat = pd.concat(not_sg_data, axis=0, ignore_index=True)
    
    return sg_concat, not_sg_concat

# Function to modify data by ±2%
def modify_data_2percent(sg_data, not_sg_data):
    np.random.seed(42)
    
    # Modify ~20% of data points
    n_to_modify = int(len(sg_data) * 0.2)
    indices_to_modify = np.random.choice(len(sg_data), n_to_modify, replace=False)
    
    sg_modified = sg_data.copy()
    not_sg_modified = not_sg_data.copy()
    
    for idx in indices_to_modify:
        # Randomly increase or decrease by 2%
        sg_multiplier = 1.02 if np.random.random() > 0.5 else 0.98
        not_sg_multiplier = 1.02 if np.random.random() > 0.5 else 0.98
        
        sg_modified.iloc[idx] = sg_modified.iloc[idx] * sg_multiplier
        not_sg_modified.iloc[idx] = not_sg_modified.iloc[idx] * not_sg_multiplier
    
    return sg_modified, not_sg_modified

# Function to plot on a given axis
def plot_on_axis(ax, sg_data, not_sg_data, title, ylabel, stage_lengths, show_ylabel=True):
    x_values = range(len(sg_data))
    
    # Plot data
    ax.plot(x_values, sg_data, label='OSS4SG', color='orange', linewidth=2)
    ax.plot(x_values, not_sg_data, label='OSS', color='blue', linewidth=2)
    
    # Add shaded areas for early, mid, and late stages
    early_end = stage_lengths[0]
    mid_end = early_end + stage_lengths[1]
    late_end = mid_end + stage_lengths[2]
    
    ax.axvspan(0, early_end, color='lightblue', alpha=0.3, label='Early Stage')
    ax.axvspan(early_end, mid_end, color='lightgreen', alpha=0.3, label='Mid Stage')
    ax.axvspan(mid_end, late_end, color='lightcoral', alpha=0.3, label='Late Stage')
    
    # Set titles, labels, and legend
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Time Window (Window = 3 Months)', fontsize=11)
    if show_ylabel:
        ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True)
    
    # Set axis limits
    ax.set_xlim(0, len(sg_data))
    ax.set_ylim(0, max(max(sg_data), max(not_sg_data)) * 1.1)

# Load data
print("="*70)
print("LOADING DATA")
print("="*70)

sg_join_rate, not_sg_join_rate = load_and_concat(join_rate_files)
sg_leave_rate, not_sg_leave_rate = load_and_concat(leave_rate_files)

# Define stage lengths
early_stage_length = len(pd.read_csv(join_rate_files[0]))
mid_stage_length = len(pd.read_csv(join_rate_files[1]))
late_stage_length = len(pd.read_csv(join_rate_files[2]))

stage_lengths = [early_stage_length, mid_stage_length, late_stage_length]

print(f"\nStage lengths:")
print(f"  Early: {early_stage_length} windows")
print(f"  Mid: {mid_stage_length} windows")
print(f"  Late: {late_stage_length} windows")

# Create modified data (MSN - 2% variation)
print("\n" + "="*70)
print("CREATING MSN DATA (±2% MODIFICATION)")
print("="*70)

sg_join_rate_msn, not_sg_join_rate_msn = modify_data_2percent(sg_join_rate, not_sg_join_rate)
sg_leave_rate_msn, not_sg_leave_rate_msn = modify_data_2percent(sg_leave_rate, not_sg_leave_rate)

print("✓ Data modified")

# Create 2x2 comparison plot
print("\n" + "="*70)
print("GENERATING 2x2 COMPARISON PLOT")
print("="*70)

fig, axes = plt.subplots(2, 2, figsize=(18, 12))

# Row 1: Join Rate
# Original
plot_on_axis(
    axes[0, 0],
    sg_join_rate,
    not_sg_join_rate,
    'Average Join Rate - All Stages',
    'Average Join Rate',
    stage_lengths,
    show_ylabel=True
)

# MSN
plot_on_axis(
    axes[0, 1],
    sg_join_rate_msn,
    not_sg_join_rate_msn,
    'Average Join Rate - MSN',
    'Average Join Rate',
    stage_lengths,
    show_ylabel=False
)

# Row 2: Leave Rate
# Original
plot_on_axis(
    axes[1, 0],
    sg_leave_rate,
    not_sg_leave_rate,
    'Average Leave Rate - All Stages',
    'Average Leave Rate',
    stage_lengths,
    show_ylabel=True
)

# MSN
plot_on_axis(
    axes[1, 1],
    sg_leave_rate_msn,
    not_sg_leave_rate_msn,
    'Average Leave Rate - MSN',
    'Average Leave Rate',
    stage_lengths,
    show_ylabel=False
)

plt.tight_layout()

# Save the plot
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'
output_png = os.path.join(output_dir, 'line_plots_allstages_vs_msn.png')
output_pdf = os.path.join(output_dir, 'line_plots_allstages_vs_msn.pdf')

plt.savefig(output_png, format='png', dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')

print(f"\n✓ Saved: {output_png}")
print(f"✓ Saved: {output_pdf}")

plt.close()

print("\n" + "="*70)
print("✓ COMPARISON PLOT GENERATED!")
print("="*70)
print("\nLayout:")
print("  Row 1 - Left: Join Rate (All Stages)")
print("  Row 1 - Right: Join Rate (MSN)")
print("  Row 2 - Left: Leave Rate (All Stages)")
print("  Row 2 - Right: Leave Rate (MSN)")






