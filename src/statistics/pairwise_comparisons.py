#!/usr/bin/env python3
"""
Pairwise statistical comparisons between all four methods.
Uses Mann-Whitney U test (Wilcoxon rank-sum) for pairwise comparisons
with Bonferroni correction for multiple comparisons.
"""

import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
from scipy.stats import kruskal
from pathlib import Path
import itertools

EXP21_DIR = Path(__file__).parent

def main():
    print("="*80)
    print("PAIRWISE STATISTICAL COMPARISONS")
    print("="*80)
    
    # Load all 4 contributor count files
    files = {
        '1. Distinct': EXP21_DIR / 'distinct_contributor_counts.csv',
        '2. Email': EXP21_DIR / 'email_contributor_counts.csv',
        '3. MSN': EXP21_DIR / 'msn_contributor_counts.csv',
        '4. ML': EXP21_DIR / 'ml_contributor_counts.csv',
    }
    
    print("\nLoading data...")
    datasets = {}
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        df = df.sort_values('project').reset_index(drop=True)
        datasets[method] = df['contributor_count'].values
        print(f"  {method:15s}: {len(df)} projects, mean = {df['contributor_count'].mean():.1f}")
    
    # Align to common projects (ML has 2 fewer projects)
    # Get projects from each dataset
    project_dfs = {}
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        project_dfs[method] = df
    
    # Find common projects
    all_projects = set(project_dfs['1. Distinct']['project'])
    for method in ['2. Email', '3. MSN', '4. ML']:
        all_projects = all_projects.intersection(set(project_dfs[method]['project']))
    
    common_projects = sorted(all_projects)
    print(f"\nCommon projects across all methods: {len(common_projects)}")
    
    # Align all datasets to common projects
    aligned_datasets = {}
    for method, df in project_dfs.items():
        df_aligned = df[df['project'].isin(common_projects)].sort_values('project')
        aligned_datasets[method] = df_aligned['contributor_count'].values
    
    print("\n" + "="*80)
    print("OVERALL KRUSKAL-WALLIS TEST (All 4 groups)")
    print("="*80)
    
    statistic, pvalue = kruskal(
        aligned_datasets['1. Distinct'],
        aligned_datasets['2. Email'],
        aligned_datasets['3. MSN'],
        aligned_datasets['4. ML']
    )
    
    print(f"\nTest Statistic (H): {statistic:.6f}")
    print(f"p-value:            {pvalue:.6f}")
    alpha = 0.05
    if pvalue < alpha:
        print(f"Result: SIGNIFICANT (p < {alpha})")
        print("→ At least one pair differs significantly")
    else:
        print(f"Result: NOT SIGNIFICANT (p >= {alpha})")
        print("→ No evidence of differences among groups")
    
    print("\n" + "="*80)
    print("PAIRWISE COMPARISONS (Mann-Whitney U Test)")
    print("="*80)
    print("\nComparing each pair of methods...")
    print("Using Bonferroni correction for multiple comparisons (α = 0.05)")
    
    # Generate all pairwise comparisons
    methods = ['1. Distinct', '2. Email', '3. MSN', '4. ML']
    pairs = list(itertools.combinations(methods, 2))
    
    # Bonferroni correction: divide alpha by number of comparisons
    num_comparisons = len(pairs)
    bonferroni_alpha = 0.05 / num_comparisons
    
    print(f"\nNumber of pairwise comparisons: {num_comparisons}")
    print(f"Bonferroni-corrected alpha: {bonferroni_alpha:.6f}")
    print(f"Original alpha: 0.05")
    
    results = []
    
    for method1, method2 in pairs:
        data1 = aligned_datasets[method1]
        data2 = aligned_datasets[method2]
        
        # Mann-Whitney U test (two-sided)
        statistic, pvalue = mannwhitneyu(data1, data2, alternative='two-sided')
        
        # Determine significance
        significant_uncorrected = pvalue < 0.05
        significant_corrected = pvalue < bonferroni_alpha
        
        results.append({
            'Method 1': method1,
            'Method 2': method2,
            'U Statistic': statistic,
            'p-value': pvalue,
            'p-value (scientific)': f"{pvalue:.4e}",
            'Significant (uncorrected)': 'Yes' if significant_uncorrected else 'No',
            'Significant (Bonferroni)': 'Yes' if significant_corrected else 'No',
            'Mean 1': f"{data1.mean():.2f}",
            'Mean 2': f"{data2.mean():.2f}",
            'Median 1': f"{np.median(data1):.1f}",
            'Median 2': f"{np.median(data2):.1f}",
        })
    
    results_df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("PAIRWISE COMPARISON RESULTS")
    print("="*80)
    print("\n" + results_df.to_string(index=False))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\nSignificant differences (uncorrected α = 0.05):")
    sig_uncorrected = results_df[results_df['Significant (uncorrected)'] == 'Yes']
    if len(sig_uncorrected) > 0:
        for _, row in sig_uncorrected.iterrows():
            print(f"  ✓ {row['Method 1']} vs {row['Method 2']}: p = {row['p-value']:.6f}")
    else:
        print("  None")
    
    print(f"\nSignificant differences (Bonferroni-corrected α = {bonferroni_alpha:.6f}):")
    sig_corrected = results_df[results_df['Significant (Bonferroni)'] == 'Yes']
    if len(sig_corrected) > 0:
        for _, row in sig_corrected.iterrows():
            print(f"  ✓ {row['Method 1']} vs {row['Method 2']}: p = {row['p-value']:.6f}")
    else:
        print("  None")
        print(f"  → No pairs are significantly different after correction for {num_comparisons} comparisons")
    
    # Save results
    output_path = EXP21_DIR / 'pairwise_comparison_results.csv'
    results_df.to_csv(output_path, index=False)
    print(f"\n✓ Saved detailed results to: {output_path}")
    
    # Create a simplified comparison table
    print("\n" + "="*80)
    print("KEY COMPARISONS")
    print("="*80)
    print("\n1. Distinct vs Email Baseline:")
    r = results_df[(results_df['Method 1'] == '1. Distinct') & (results_df['Method 2'] == '2. Email')].iloc[0]
    print(f"   p-value: {r['p-value']:.6f} {'(SIGNIFICANT)' if r['Significant (Bonferroni)'] == 'Yes' else '(not significant)'}")
    
    print("\n2. Email Baseline vs MSN:")
    r = results_df[(results_df['Method 1'] == '2. Email') & (results_df['Method 2'] == '3. MSN')].iloc[0]
    print(f"   p-value: {r['p-value']:.6f} {'(SIGNIFICANT)' if r['Significant (Bonferroni)'] == 'Yes' else '(not significant)'}")
    
    print("\n3. MSN vs ML:")
    r = results_df[(results_df['Method 1'] == '3. MSN') & (results_df['Method 2'] == '4. ML')].iloc[0]
    print(f"   p-value: {r['p-value']:.6f} {'(SIGNIFICANT)' if r['Significant (Bonferroni)'] == 'Yes' else '(not significant)'}")
    
    print("\n4. Distinct vs ML:")
    r = results_df[(results_df['Method 1'] == '1. Distinct') & (results_df['Method 2'] == '4. ML')].iloc[0]
    print(f"   p-value: {r['p-value']:.6f} {'(SIGNIFICANT)' if r['Significant (Bonferroni)'] == 'Yes' else '(not significant)'}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

