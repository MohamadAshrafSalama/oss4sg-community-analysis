#!/usr/bin/env python3
"""
Build contributor count files for each method and run Kruskal-Wallis test.
Each output file has one row per project with the contributor count for that method.
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

# Paths
EXP12_DIR = Path(__file__).parent.parent / "Experiment 12"
EXP21_DIR = Path(__file__).parent

# Input files
INPUT_FILES = {
    'distinct': EXP12_DIR / '01_distinct_name_email_pairs.csv',
    'email': EXP12_DIR / '02_email_baseline_method.csv',
    'msn': EXP12_DIR / '03_msn_method.csv',
    'ml': EXP12_DIR / '04_fullfat_ml_method.csv',
}

# Output files
OUTPUT_FILES = {
    'distinct': EXP21_DIR / 'distinct_contributor_counts.csv',
    'email': EXP21_DIR / 'email_contributor_counts.csv',
    'msn': EXP21_DIR / 'msn_contributor_counts.csv',
    'ml': EXP21_DIR / 'ml_contributor_counts.csv',
}

def count_contributors_per_project(df, method_name):
    """Count contributors per project for a given method."""
    if method_name == 'distinct':
        # For distinct method, count rows per project
        counts = df.groupby('project').size()
    else:
        # For merged methods, count unique group_ids per project
        counts = df.groupby('project')['group_id'].nunique()
    return counts

def main():
    print("Step 1: Loading data files...")
    datasets = {}
    for method_name, filepath in INPUT_FILES.items():
        print(f"  Loading {method_name}...")
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        datasets[method_name] = df
        print(f"    Loaded {len(df)} rows")

    print("\nStep 2: Calculating contributor counts per project...")
    contributor_counts = {}
    
    for method_name, df in datasets.items():
        counts = count_contributors_per_project(df, method_name)
        contributor_counts[method_name] = counts
        
        # Create DataFrame with project and count
        counts_df = pd.DataFrame({
            'project': counts.index,
            'contributor_count': counts.values
        })
        
        # Sort by project name for consistency
        counts_df = counts_df.sort_values('project').reset_index(drop=True)
        
        # Save to CSV
        output_path = OUTPUT_FILES[method_name]
        counts_df.to_csv(output_path, index=False)
        print(f"  {method_name}: {len(counts_df)} projects, "
              f"total contributors: {counts_df['contributor_count'].sum():,}, "
              f"saved to {output_path.name}")
        print(f"    Min: {counts_df['contributor_count'].min()}, "
              f"Max: {counts_df['contributor_count'].max()}, "
              f"Mean: {counts_df['contributor_count'].mean():.1f}, "
              f"Median: {counts_df['contributor_count'].median():.1f}")

    print("\nStep 3: Verifying all files have the same projects...")
    # Get project sets
    project_sets = {method: set(counts.index) for method, counts in contributor_counts.items()}
    
    # Check if all have the same projects
    all_projects = set.union(*project_sets.values())
    common_projects = set.intersection(*project_sets.values())
    
    print(f"  Total unique projects across all methods: {len(all_projects)}")
    print(f"  Common projects in all methods: {len(common_projects)}")
    
    if len(common_projects) != len(all_projects):
        print(f"  WARNING: Some projects are missing in some methods!")
        for method, projects in project_sets.items():
            missing = all_projects - projects
            if missing:
                print(f"    {method} missing: {len(missing)} projects")
    
    print("\nStep 4: Running Kruskal-Wallis test...")
    
    # Align all counts to common projects (in same order)
    common_projects_sorted = sorted(common_projects)
    
    counts_lists = {}
    for method_name in ['distinct', 'email', 'msn', 'ml']:
        counts = contributor_counts[method_name]
        # Get counts for common projects only, in sorted order
        counts_list = [counts.get(proj, 0) for proj in common_projects_sorted]
        counts_lists[method_name] = counts_list
    
    # Run Kruskal-Wallis test
    statistic, pvalue = kruskal(
        counts_lists['distinct'],
        counts_lists['email'],
        counts_lists['msn'],
        counts_lists['ml']
    )
    
    print(f"\nKruskal-Wallis Test Results:")
    print(f"  Test statistic (H): {statistic:.4f}")
    print(f"  p-value: {pvalue:.6f}")
    print(f"  p-value (scientific): {pvalue:.4e}")
    
    # Interpretation
    print(f"\nStep 5: Interpretation:")
    alpha = 0.05
    if pvalue < alpha:
        print(f"  Result: REJECT null hypothesis (p < {alpha})")
        print(f"  Conclusion: There IS a statistically significant difference")
        print(f"              between the four methods in terms of contributor counts per project.")
    else:
        print(f"  Result: FAIL TO REJECT null hypothesis (p >= {alpha})")
        print(f"  Conclusion: There is NO statistically significant difference")
        print(f"              between the four methods in terms of contributor counts per project.")
    
    # Save test results
    results_df = pd.DataFrame({
        'method': ['distinct', 'email', 'msn', 'ml'],
        'n_projects': [len(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'total_contributors': [sum(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'mean_count': [np.mean(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'median_count': [np.median(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'min_count': [min(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'max_count': [max(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
        'std_count': [np.std(counts_lists[m]) for m in ['distinct', 'email', 'msn', 'ml']],
    })
    
    results_path = EXP21_DIR / 'kruskal_wallis_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\nSaved detailed results to: {results_path}")
    
    # Save test statistics
    test_stats = pd.DataFrame({
        'test': ['Kruskal-Wallis'],
        'statistic': [statistic],
        'p_value': [pvalue],
        'alpha': [alpha],
        'significant': [pvalue < alpha],
        'n_groups': [4],
        'n_observations': [len(common_projects_sorted) * 4],
    })
    
    test_stats_path = EXP21_DIR / 'kruskal_wallis_test_statistics.csv'
    test_stats.to_csv(test_stats_path, index=False)
    print(f"Saved test statistics to: {test_stats_path}")
    
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)
    print(results_df.to_string(index=False))
    print("\n" + "="*70)

if __name__ == '__main__':
    main()

