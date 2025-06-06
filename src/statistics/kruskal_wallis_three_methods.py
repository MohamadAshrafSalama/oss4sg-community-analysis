#!/usr/bin/env python3
"""
Kruskal-Wallis test comparing only the three merging methods:
- Email Baseline
- MSN Method
- ML Method
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

EXP21_DIR = Path(__file__).parent

def main():
    print("="*80)
    print("KRUSKAL-WALLIS TEST: Three Merging Methods Only")
    print("="*80)
    print("\nMethods being compared:")
    print("  1. Email Baseline")
    print("  2. MSN Method")
    print("  3. ML Method")
    print("\n(Excluding Distinct baseline)")
    
    # Load the three merging method files
    files = {
        'Email': EXP21_DIR / 'email_contributor_counts.csv',
        'MSN': EXP21_DIR / 'msn_contributor_counts.csv',
        'ML': EXP21_DIR / 'ml_contributor_counts.csv',
    }
    
    print("\nLoading data...")
    datasets = {}
    project_dfs = {}
    
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        project_dfs[method] = df
        datasets[method] = df['contributor_count'].values
        print(f"  {method:10s}: {len(df)} projects, mean = {df['contributor_count'].mean():.1f}")
    
    # Find common projects
    all_projects = set(project_dfs['Email']['project'])
    for method in ['MSN', 'ML']:
        all_projects = all_projects.intersection(set(project_dfs[method]['project']))
    
    common_projects = sorted(all_projects)
    print(f"\nCommon projects across all three methods: {len(common_projects)}")
    
    # Align all datasets to common projects
    aligned_datasets = {}
    for method, df in project_dfs.items():
        df_aligned = df[df['project'].isin(common_projects)].sort_values('project')
        aligned_datasets[method] = df_aligned['contributor_count'].values
    
    print("\n" + "="*80)
    print("KRUSKAL-WALLIS TEST (3 groups)")
    print("="*80)
    
    # Run Kruskal-Wallis test with 3 groups
    statistic, pvalue = kruskal(
        aligned_datasets['Email'],
        aligned_datasets['MSN'],
        aligned_datasets['ML']
    )
    
    print(f"\nTest Statistic (H): {statistic:.6f}")
    print(f"p-value:            {pvalue:.6f}")
    print(f"p-value (scientific): {pvalue:.4e}")
    
    alpha = 0.05
    print(f"\nAlpha level: {alpha}")
    
    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)
    
    if pvalue < alpha:
        print(f"\n✓ p < {alpha} → REJECT null hypothesis")
        print("\nConclusion: There IS a statistically significant difference")
        print("            among at least one pair of the three merging methods.")
        print("\nNext step: Perform post-hoc tests (e.g., Dunn's test) to")
        print("           identify which specific pairs are different.")
    else:
        print(f"\n✓ p >= {alpha} → FAIL TO REJECT null hypothesis")
        print("\nConclusion: There is NO statistically significant difference")
        print("            among the three merging methods (Email, MSN, ML)")
        print("            in terms of contributor counts per project.")
        print("\nThis means:")
        print("  • Email Baseline, MSN, and ML produce statistically similar")
        print("    contributor count distributions")
        print("  • The additional sophistication of MSN and ML does not")
        print("    significantly change the distribution pattern")
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    summary_data = []
    for method, counts in aligned_datasets.items():
        summary_data.append({
            'Method': method,
            'N Projects': len(counts),
            'Total Contributors': int(counts.sum()),
            'Mean': f"{counts.mean():.2f}",
            'Median': f"{np.median(counts):.1f}",
            'Min': int(counts.min()),
            'Max': int(counts.max()),
            'Std Dev': f"{counts.std():.2f}",
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Save results
    results_path = EXP21_DIR / 'kruskal_wallis_three_methods_results.csv'
    summary_df.to_csv(results_path, index=False)
    
    test_stats = pd.DataFrame({
        'test': ['Kruskal-Wallis (3 methods)'],
        'n_groups': [3],
        'statistic': [statistic],
        'p_value': [pvalue],
        'alpha': [alpha],
        'significant': [pvalue < alpha],
        'n_observations': [len(common_projects) * 3],
    })
    
    test_stats_path = EXP21_DIR / 'kruskal_wallis_three_methods_test_stats.csv'
    test_stats.to_csv(test_stats_path, index=False)
    
    print(f"\n✓ Saved results to: {results_path}")
    print(f"✓ Saved test statistics to: {test_stats_path}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

