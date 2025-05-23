#!/usr/bin/env python3
"""
Plot contributor distributions for all four identity resolution methods.
Shows unique contributors per project - creating v-shaped distributions.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# File paths
DATA_DIR = Path(__file__).parent
FILES = {
    '1. Distinct (Baseline)': DATA_DIR / '01_distinct_name_email_pairs.csv',
    '2. Email Baseline': DATA_DIR / '02_email_baseline_method.csv',
    '3. MSN Method': DATA_DIR / '03_msn_method.csv',
    '4. Full-Fat ML Method': DATA_DIR / '04_fullfat_ml_method.csv',
}

def count_contributors_per_project(df, method_name):
    """Count unique contributors per project for a given method."""
    if method_name == '1. Distinct (Baseline)':
        # For distinct method, count unique (name, email) pairs per project
        df['contributor_key'] = df['author_name'].astype(str) + '|' + df['author_email'].astype(str)
        counts = df.groupby('project')['contributor_key'].nunique()
    else:
        # For merged methods, count unique group_ids per project
        counts = df.groupby('project')['group_id'].nunique()
    return counts

def main():
    # Load all datasets
    datasets = {}
    print("Loading datasets...")
    for method_name, filepath in FILES.items():
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        datasets[method_name] = df
        print(f"  {method_name}: {len(df)} rows")

    # Count contributors per project for each method
    print("\nCounting contributors per project...")
    contributor_counts = {}
    for method_name, df in datasets.items():
        counts = count_contributors_per_project(df, method_name)
        contributor_counts[method_name] = counts
        
        # Calculate total unique contributors across all projects
        if method_name == '1. Distinct (Baseline)':
            total_unique = len(df)  # 63,214 total rows
        else:
            total_unique = len(df)  # Total rows = unique contributors per project
        
        print(f"{method_name}:")
        print(f"  Projects: {len(counts)}")
        print(f"  Total contributors (sum across projects): {counts.sum():,}")
        print(f"  Total rows in dataset: {total_unique:,}")
        print(f"  Median contributors/project: {counts.median():.0f}")
        print(f"  Mean contributors/project: {counts.mean():.1f}\n")

    # Create figure with 4 subplots in a row
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for idx, (method_name, counts) in enumerate(contributor_counts.items()):
        ax = axes[idx]
        
        # Create histogram with log scale for better visualization
        # Use linear bins but log scale axis
        max_count = int(counts.max())
        bins = np.arange(0, max_count + 50, 50)  # Bins of 50
        
        n, bins, patches = ax.hist(counts.values, bins=bins, color=colors[idx], 
                                   alpha=0.7, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel('Number of Contributors per Project', fontsize=11)
        ax.set_ylabel('Number of Projects', fontsize=11)
        
        # Extract method number and name
        method_label = method_name.split('. ')[1] if '. ' in method_name else method_name
        ax.set_title(f'{method_name}\nTotal: {counts.sum():,} contributors', 
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Add statistics text
        stats_text = (f'Projects: {len(counts)}\n'
                     f'Median: {counts.median():.0f}\n'
                     f'Mean: {counts.mean():.1f}\n'
                     f'Range: {counts.min()}-{counts.max()}')
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    plt.tight_layout()
    
    # Save figure
    output_path = DATA_DIR / 'contributor_distributions_vshaped.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    
    # Create a second figure with all methods overlaid
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    
    for idx, (method_name, counts) in enumerate(contributor_counts.items()):
        max_count = int(counts.max())
        bins = np.arange(0, max_count + 50, 50)
        label = method_name.split('. ')[1] if '. ' in method_name else method_name
        ax2.hist(counts.values, bins=bins, label=label, alpha=0.6, 
                edgecolor='black', linewidth=0.5)
    
    ax2.set_xlabel('Number of Contributors per Project', fontsize=12)
    ax2.set_ylabel('Number of Projects', fontsize=12)
    ax2.set_title('Contributor Distributions: All Methods Overlay', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10, loc='upper right')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    plt.tight_layout()
    output_path2 = DATA_DIR / 'contributor_distributions_overlay_vshaped.png'
    fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path2}")
    
    # Verify counts match README
    print("\n" + "="*70)
    print("Verification against README statistics:")
    print("="*70)
    print(f"{'Method':<30} {'Total Contributors':<20} {'Reduction':<15} {'% Reduced':<10}")
    print("-"*70)
    
    baseline_total = contributor_counts['1. Distinct (Baseline)'].sum()
    for method_name in ['1. Distinct (Baseline)', '2. Email Baseline', 
                        '3. MSN Method', '4. Full-Fat ML Method']:
        if method_name in contributor_counts:
            total = contributor_counts[method_name].sum()
            reduction = baseline_total - total
            pct_reduced = (reduction / baseline_total * 100) if baseline_total > 0 else 0
            method_label = method_name.split('. ')[1] if '. ' in method_name else method_name
            print(f"{method_label:<30} {total:<20,} {reduction:<15,} {pct_reduced:<10.1f}%")
    
    print("\nNote: These are totals summed across all projects.")
    print("A contributor appearing in N projects counts N times in the total.")

if __name__ == '__main__':
    main()

