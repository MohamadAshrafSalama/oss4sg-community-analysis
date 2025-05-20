#!/usr/bin/env python3
"""
Plot contributor distributions for all four identity resolution methods.
Shows unique contributors per project for each method.
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
    for method_name, filepath in FILES.items():
        print(f"Loading {method_name}...")
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        datasets[method_name] = df
        print(f"  Loaded {len(df)} rows")

    # Count contributors per project for each method
    print("\nCounting contributors per project...")
    contributor_counts = {}
    for method_name, df in datasets.items():
        counts = count_contributors_per_project(df, method_name)
        contributor_counts[method_name] = counts
        print(f"{method_name}: {len(counts)} projects, median {counts.median():.0f} contributors, "
              f"mean {counts.mean():.1f} contributors, total {counts.sum()} contributors")

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for idx, (method_name, counts) in enumerate(contributor_counts.items()):
        ax = axes[idx]
        
        # Create histogram
        bins = np.logspace(0, np.log10(counts.max() + 1), 50)  # Log scale bins
        ax.hist(counts.values, bins=bins, color=colors[idx], alpha=0.7, edgecolor='black', linewidth=0.5)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Number of Unique Contributors per Project', fontsize=10)
        ax.set_ylabel('Number of Projects', fontsize=10)
        ax.set_title(f'{method_name}\n(n={len(counts)} projects, total={counts.sum()} contributors)', 
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add statistics text
        stats_text = (f'Median: {counts.median():.0f}\n'
                     f'Mean: {counts.mean():.1f}\n'
                     f'Min: {counts.min()}\n'
                     f'Max: {counts.max()}')
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    
    # Save figure
    output_path = DATA_DIR / 'contributor_distributions_all_methods.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nSaved: {output_path}")
    
    # Also create a combined overlay plot
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    for idx, (method_name, counts) in enumerate(contributor_counts.items()):
        bins = np.logspace(0, np.log10(counts.max() + 1), 50)
        ax2.hist(counts.values, bins=bins, label=method_name, alpha=0.6, 
                edgecolor='black', linewidth=0.5)
    
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel('Number of Unique Contributors per Project', fontsize=12)
    ax2.set_ylabel('Number of Projects', fontsize=12)
    ax2.set_title('Contributor Distributions: All Methods Overlay', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    output_path2 = DATA_DIR / 'contributor_distributions_overlay.png'
    fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path2}")
    
    # Create summary statistics table
    summary_data = []
    for method_name, counts in contributor_counts.items():
        summary_data.append({
            'Method': method_name,
            'Total Projects': len(counts),
            'Total Contributors': int(counts.sum()),
            'Median Contributors/Project': round(counts.median(), 1),
            'Mean Contributors/Project': round(counts.mean(), 1),
            'Min Contributors': int(counts.min()),
            'Max Contributors': int(counts.max()),
            'Std Dev': round(counts.std(), 1),
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_csv = DATA_DIR / 'contributor_distribution_summary.csv'
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSummary statistics saved to: {summary_csv}")
    print("\nSummary Statistics:")
    print(summary_df.to_string(index=False))

if __name__ == '__main__':
    main()

