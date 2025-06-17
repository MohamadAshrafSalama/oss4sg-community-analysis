#!/usr/bin/env python3
"""
Investigate the discrepancy in Kruskal-Wallis results.
Check different ways of aligning/using the data.
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

EXP21_DIR = Path(__file__).parent

def main():
    print("="*80)
    print("INVESTIGATING KRUSKAL-WALLIS DISCREPANCY")
    print("="*80)
    
    # Load all files
    files = {
        'Distinct': EXP21_DIR / 'distinct_contributor_counts.csv',
        'Email': EXP21_DIR / 'email_contributor_counts.csv',
        'MSN': EXP21_DIR / 'msn_contributor_counts.csv',
        'ML': EXP21_DIR / 'ml_contributor_counts.csv',
    }
    
    datasets = {}
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        datasets[method] = df
    
    print("\nDataset sizes:")
    for method, df in datasets.items():
        print(f"  {method:10s}: {len(df)} projects")
    
    # Method 1: Align to common projects (what we did before)
    print("\n" + "="*80)
    print("METHOD 1: Aligned to Common Projects (Our Previous Approach)")
    print("="*80)
    
    all_projects = set(datasets['Distinct']['project'])
    for method in ['Email', 'MSN', 'ML']:
        all_projects = all_projects.intersection(set(datasets[method]['project']))
    
    common_projects = sorted(all_projects)
    print(f"\nCommon projects: {len(common_projects)}")
    
    aligned_4 = {}
    for method, df in datasets.items():
        df_aligned = df[df['project'].isin(common_projects)].sort_values('project')
        aligned_4[method] = df_aligned['contributor_count'].values
    
    stat_4, pval_4 = kruskal(
        aligned_4['Distinct'],
        aligned_4['Email'],
        aligned_4['MSN'],
        aligned_4['ML']
    )
    print(f"4 methods: H = {stat_4:.6f}, p = {pval_4:.6f}")
    
    stat_3, pval_3 = kruskal(
        aligned_4['Email'],
        aligned_4['MSN'],
        aligned_4['ML']
    )
    print(f"3 methods: H = {stat_3:.6f}, p = {pval_3:.6f}")
    
    # Method 2: Use all projects (not aligned) - might have different lengths
    print("\n" + "="*80)
    print("METHOD 2: Using All Projects (Not Aligned - Different Lengths)")
    print("="*80)
    print("\nWARNING: This will have different sample sizes per method!")
    
    all_4 = {}
    for method, df in datasets.items():
        df_sorted = df.sort_values('project')
        all_4[method] = df_sorted['contributor_count'].values
    
    print(f"\nSample sizes:")
    for method, counts in all_4.items():
        print(f"  {method:10s}: {len(counts)} projects")
    
    try:
        stat_4_all, pval_4_all = kruskal(
            all_4['Distinct'],
            all_4['Email'],
            all_4['MSN'],
            all_4['ML']
        )
        print(f"\n4 methods: H = {stat_4_all:.6f}, p = {pval_4_all:.6f}")
        print(f"           p (scientific) = {pval_4_all:.4e}")
    except Exception as e:
        print(f"\nError with 4 methods: {e}")
    
    try:
        stat_3_all, pval_3_all = kruskal(
            all_4['Email'],
            all_4['MSN'],
            all_4['ML']
        )
        print(f"3 methods: H = {stat_3_all:.6f}, p = {pval_3_all:.6f}")
        print(f"           p (scientific) = {pval_3_all:.4e}")
    except Exception as e:
        print(f"\nError with 3 methods: {e}")
    
    # Method 3: Check if they're using raw counts vs per-project counts
    print("\n" + "="*80)
    print("METHOD 3: Using Raw Data (Not Aggregated Per Project)")
    print("="*80)
    print("Checking if using raw contributor lists instead of counts...")
    
    # Load raw data from Experiment 12
    EXP12_DIR = Path(__file__).parent.parent / "Experiment 12"
    raw_files = {
        'Distinct': EXP12_DIR / '01_distinct_name_email_pairs.csv',
        'Email': EXP12_DIR / '02_email_baseline_method.csv',
        'MSN': EXP12_DIR / '03_msn_method.csv',
        'ML': EXP12_DIR / '04_fullfat_ml_method.csv',
    }
    
    print("\nLoading raw data files...")
    raw_datasets = {}
    for method, filepath in raw_files.items():
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        raw_datasets[method] = df
        print(f"  {method:10s}: {len(df)} rows")
    
    # Count contributors per project from raw data
    print("\nCounting contributors per project from raw data...")
    raw_counts = {}
    for method, df in raw_datasets.items():
        if method == 'Distinct':
            counts = df.groupby('project').size()
        else:
            counts = df.groupby('project')['group_id'].nunique()
        raw_counts[method] = counts
    
    # Find common projects in raw data
    raw_common = set(raw_counts['Distinct'].index)
    for method in ['Email', 'MSN', 'ML']:
        raw_common = raw_common.intersection(set(raw_counts[method].index))
    
    raw_common = sorted(raw_common)
    print(f"Common projects in raw data: {len(raw_common)}")
    
    # Align raw counts
    raw_aligned = {}
    for method, counts in raw_counts.items():
        aligned_list = [counts.get(proj, 0) for proj in raw_common]
        raw_aligned[method] = aligned_list
    
    stat_4_raw, pval_4_raw = kruskal(
        raw_aligned['Distinct'],
        raw_aligned['Email'],
        raw_aligned['MSN'],
        raw_aligned['ML']
    )
    print(f"\n4 methods (from raw): H = {stat_4_raw:.6f}, p = {pval_4_raw:.6f}")
    print(f"                      p (scientific) = {pval_4_raw:.4e}")
    
    stat_3_raw, pval_3_raw = kruskal(
        raw_aligned['Email'],
        raw_aligned['MSN'],
        raw_aligned['ML']
    )
    print(f"3 methods (from raw): H = {stat_3_raw:.6f}, p = {pval_3_raw:.6f}")
    print(f"                      p (scientific) = {pval_3_raw:.4e}")
    
    # Check what might give H=84.72
    print("\n" + "="*80)
    print("SEARCHING FOR H ≈ 84.72")
    print("="*80)
    
    results = [
        ("4 methods (aligned common)", stat_4, pval_4),
        ("3 methods (aligned common)", stat_3, pval_3),
        ("4 methods (from raw)", stat_4_raw, pval_4_raw),
        ("3 methods (from raw)", stat_3_raw, pval_3_raw),
    ]
    
    if 'stat_4_all' in locals():
        results.append(("4 methods (all projects)", stat_4_all, pval_4_all))
    if 'stat_3_all' in locals():
        results.append(("3 methods (all projects)", stat_3_all, pval_3_all))
    
    print("\nAll results:")
    for name, h, p in results:
        print(f"  {name:30s}: H = {h:8.2f}, p = {p:.4e}")
    
    # Check if using total counts (sum) instead of per-project counts
    print("\n" + "="*80)
    print("CHECKING: Maybe using total contributor counts?")
    print("="*80)
    
    total_counts = {}
    for method, df in datasets.items():
        total_counts[method] = [df['contributor_count'].sum()]
    
    print("Total contributors per method:")
    for method, counts in total_counts.items():
        print(f"  {method:10s}: {counts[0]:,}")
    
    print("\n(This would be a single value per method, not suitable for Kruskal-Wallis)")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("\nIf you're seeing H = 84.72, it might be because:")
    print("  1. Using all projects without alignment (different sample sizes)")
    print("  2. Using a different data source or preprocessing")
    print("  3. Including projects that appear in some methods but not others")
    print("\nPlease check how the data is being aligned/selected before the test.")

if __name__ == '__main__':
    main()

