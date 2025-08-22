import os
import pandas as pd
import matplotlib.pyplot as plt

# Set the directory where the CSV files are located
directory = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/OSS4SG_MSR-main-2/Datasets/GraphInfo'

# File paths for Active Users, Join Rate, and Leave Rate SG and Not SG
active_users_files = [
    os.path.join(directory, 'Average Active Users for each window (Early Repos).csv'),
    os.path.join(directory, 'Average Active Users for each window (Mid Repos).csv'),
    os.path.join(directory, 'Average Active Users for each window (Late Repos).csv')
]

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

# Function to print column names of each file
def print_column_names(file_list):
    for file in file_list:
        df = pd.read_csv(file)
        print(f"Columns in {file}: {df.columns}")

# Print column names to identify the correct ones
print("Column names in files:")
print_column_names(active_users_files)
print_column_names(join_rate_files)
print_column_names(leave_rate_files)

# Function to load CSV and extract SG and Not SG columns
def load_and_concat(file_list):
    sg_data = []
    not_sg_data = []
    
    for file in file_list:
        df = pd.read_csv(file)
        sg_data.append(df['SG'])  # Using 'SG' as before
        not_sg_data.append(df['Not SG'])  # Using 'Not SG' as before
    
    # Concatenate data
    sg_concat = pd.concat(sg_data, axis=0, ignore_index=True)
    not_sg_concat = pd.concat(not_sg_data, axis=0, ignore_index=True)
    
    return sg_concat, not_sg_concat

# Function to plot concatenated data and save as high-resolution PDF
def plot_concatenated_with_shade(sg_data, not_sg_data, title, ylabel, stage_lengths, filename):
    plt.figure(figsize=(12, 6))

    x_values = range(len(sg_data))
    
    # Plot data
    plt.plot(x_values, sg_data, label='OSS4SG', color='orange', linewidth=2)  # Renamed label from 'SG' to 'OSS4SG'
    plt.plot(x_values, not_sg_data, label='OSS', color='blue', linewidth=2)  # Renamed 'Not SG' to 'OSS'

    # Add shaded areas for early, mid, and late stages
    early_end = stage_lengths[0]
    mid_end = early_end + stage_lengths[1]
    late_end = mid_end + stage_lengths[2]

    plt.axvspan(0, early_end, color='lightblue', alpha=0.3, label='Early Stage')
    plt.axvspan(early_end, mid_end, color='lightgreen', alpha=0.3, label='Mid Stage')
    plt.axvspan(mid_end, late_end, color='lightcoral', alpha=0.3, label='Late Stage')

    # Set titles, labels, and legend
    plt.title(title)
    plt.xlabel('Time Window (Window = 3 Months)')
    plt.ylabel(ylabel)
    plt.legend(loc='upper right')  # Changed legend to top-right corner
    plt.grid(True)

    # Set axis limits
    plt.xlim(0, len(sg_data))
    plt.ylim(0, max(max(sg_data), max(not_sg_data)) * 1.1)
    
    # +2 to X and Y axis tick labels
    plt.tick_params(axis='both', which='major', labelsize=14)  # +2: 12 -> 14

    plt.tight_layout()

    # Output directory
    output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save as high-resolution PDF
    pdf_path = os.path.join(output_dir, filename.replace('.pdf', '.pdf'))
    png_path = os.path.join(output_dir, filename.replace('.pdf', '.png'))
    
    plt.savefig(pdf_path, format='pdf', dpi=300)
    plt.savefig(png_path, format='png', dpi=300)
    
    print(f"✓ Saved: {pdf_path}")
    print(f"✓ Saved: {png_path}")
    
    plt.close()

# Load and concatenate the data for SG and Not SG for all three metrics
print("\n" + "="*70)
print("LOADING DATA")
print("="*70)

sg_active_users, not_sg_active_users = load_and_concat(active_users_files)
sg_join_rate, not_sg_join_rate = load_and_concat(join_rate_files)
sg_leave_rate, not_sg_leave_rate = load_and_concat(leave_rate_files)

# Define the number of windows for each stage (early, mid, late)
early_stage_length = len(pd.read_csv(active_users_files[0]))
mid_stage_length = len(pd.read_csv(active_users_files[1]))
late_stage_length = len(pd.read_csv(active_users_files[2]))

print(f"\nStage lengths:")
print(f"  Early: {early_stage_length} windows")
print(f"  Mid: {mid_stage_length} windows")
print(f"  Late: {late_stage_length} windows")
print(f"  Total: {early_stage_length + mid_stage_length + late_stage_length} windows")

# Create combined 2x1 figure (join on top, leave below)
print("\n" + "="*70)
print("GENERATING COMBINED 2x1 PLOT")
print("="*70)

stage_lengths = [early_stage_length, mid_stage_length, late_stage_length]
early_end = stage_lengths[0]
mid_end = early_end + stage_lengths[1]
late_end = mid_end + stage_lengths[2]

# Create figure with 2 subplots (2 rows, 1 column)
fig, axes = plt.subplots(2, 1, figsize=(12, 12), sharex=True)

# Top plot: Join Rate
ax = axes[0]
x_values = range(len(sg_join_rate))
ax.plot(x_values, sg_join_rate, label='OSS4SG', color='orange', linewidth=2)
ax.plot(x_values, not_sg_join_rate, label='OSS', color='blue', linewidth=2)
ax.axvspan(0, early_end, color='lightblue', alpha=0.3, label='Early Stage')
ax.axvspan(early_end, mid_end, color='lightgreen', alpha=0.3, label='Mid Stage')
ax.axvspan(mid_end, late_end, color='lightcoral', alpha=0.3, label='Late Stage')
ax.set_ylabel('Average Join Rate', fontsize=16)  # +2 more: 14 -> 16
ax.legend(loc='upper right', fontsize=16)  # +2 more: 14 -> 16
ax.grid(True)
ax.set_xlim(0, len(sg_join_rate))
ax.set_ylim(0, max(max(sg_join_rate), max(not_sg_join_rate)) * 1.1)
ax.tick_params(axis='both', which='major', labelsize=16)  # +2 more: 14 -> 16

# Bottom plot: Leave Rate
ax = axes[1]
x_values = range(len(sg_leave_rate))
ax.plot(x_values, sg_leave_rate, label='OSS4SG', color='orange', linewidth=2)
ax.plot(x_values, not_sg_leave_rate, label='OSS', color='blue', linewidth=2)
ax.axvspan(0, early_end, color='lightblue', alpha=0.3, label='Early Stage')
ax.axvspan(early_end, mid_end, color='lightgreen', alpha=0.3, label='Mid Stage')
ax.axvspan(mid_end, late_end, color='lightcoral', alpha=0.3, label='Late Stage')
ax.set_xlabel('Time Window (Window = 3 Months)', fontsize=16)  # +2 more: 14 -> 16
ax.set_ylabel('Average Leave Rate', fontsize=16)  # +2 more: 14 -> 16
ax.legend(loc='upper right', fontsize=16)  # +2 more: 14 -> 16
ax.grid(True)
ax.set_xlim(0, len(sg_leave_rate))
ax.set_ylim(0, max(max(sg_leave_rate), max(not_sg_leave_rate)) * 1.1)
ax.tick_params(axis='both', which='major', labelsize=16)  # +2 more: 14 -> 16

plt.tight_layout()

# Output directory
output_dir = '/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/recreating plots/output_plots'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save combined figure
combined_pdf = os.path.join(output_dir, 'join_leave_rate_combined.pdf')
combined_png = os.path.join(output_dir, 'join_leave_rate_combined.png')
plt.savefig(combined_pdf, format='pdf', dpi=300, bbox_inches='tight')
plt.savefig(combined_png, format='png', dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {combined_pdf}")
print(f"✓ Saved: {combined_png}")
plt.close()

print("\n" + "="*70)
print("✓ COMBINED 2x1 PLOT GENERATED!")
print("="*70)
print("\nGenerated file:")
print("  - join_leave_rate_combined.pdf/png")






