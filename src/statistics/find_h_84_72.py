#!/usr/bin/env python3
"""
Try to reproduce H=84.72 by testing different data preparation methods.
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

EXP21_DIR = Path(__file__).parent

def main():
    print("="*80)
    print("ATTEMPTING TO REPRODUCE H = 84.72")
    print("="*80)
    
    # Load contributor count files
    files = {
        'Distinct': EXP21_DIR / 'distinct_contributor_counts.csv',
        'Email': EXP21_DIR / 'email_contributor_counts.csv',
        'MSN': EXP21_DIR / 'msn_contributor_counts.csv',
        'ML': EXP21_DIR / 'ml_contributor_counts.csv',
    }
    
    datasets = {}
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        datasets[method] = df.set_index('project')
    
    print("\nDataset sizes:")
    for method, df in datasets.items():
        print(f"  {method:10s}: {len(df)} projects")
    
    # Try different alignment methods
    print("\n" + "="*80)
    print("TESTING DIFFERENT ALIGNMENT METHODS")
    print("="*80)
    
    # Method 1: All projects, fill missing with 0
    print("\n1. All projects (fill missing with 0):")
    all_projects = set(datasets['Distinct'].index)
    for method in ['Email', 'MSN', 'ML']:
        all_projects = all_projects.union(set(datasets[method].index))
    all_projects = sorted(all_projects)
    
    filled_4 = {}
    for method in ['Distinct', 'Email', 'MSN', 'ML']:
        filled_4[method] = [datasets[method].get(proj, 0) for proj in all_projects]
    
    stat, pval = kruskal(*[filled_4[m] for m in ['Distinct', 'Email', 'MSN', 'ML']])
    print(f"   4 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    stat, pval = kruskal(*[filled_4[m] for m in ['Email', 'MSN', 'ML']])
    print(f"   3 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    # Method 2: All projects, fill missing with NaN (then drop)
    print("\n2. All projects (drop missing):")
    dropped_4 = {}
    for method in ['Distinct', 'Email', 'MSN', 'ML']:
        values = [datasets[method].get(proj, np.nan) for proj in all_projects]
        dropped_4[method] = [v for v in values if not np.isnan(v)]
    
    print(f"   Sample sizes after dropping:")
    for method in ['Distinct', 'Email', 'MSN', 'ML']:
        print(f"     {method:10s}: {len(dropped_4[method])} projects")
    
    stat, pval = kruskal(*[dropped_4[m] for m in ['Distinct', 'Email', 'MSN', 'ML']])
    print(f"   4 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    stat, pval = kruskal(*[dropped_4[m] for m in ['Email', 'MSN', 'ML']])
    print(f"   3 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    # Method 3: Common projects only (what we did)
    print("\n3. Common projects only (our method):")
    common_projects = set(datasets['Distinct'].index)
    for method in ['Email', 'MSN', 'ML']:
        common_projects = common_projects.intersection(set(datasets[method].index))
    common_projects = sorted(common_projects)
    
    common_4 = {}
    for method in ['Distinct', 'Email', 'MSN', 'ML']:
        common_4[method] = [datasets[method].get(proj) for proj in common_projects]
    
    stat, pval = kruskal(*[common_4[m] for m in ['Distinct', 'Email', 'MSN', 'ML']])
    print(f"   4 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    stat, pval = kruskal(*[common_4[m] for m in ['Email', 'MSN', 'ML']])
    print(f"   3 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    # Method 4: Maybe using log-transformed counts?
    print("\n4. Log-transformed counts (common projects):")
    log_4 = {}
    for method in ['Distinct', 'Email', 'MSN', 'ML']:
        values = np.array(common_4[method])
        log_4[method] = np.log1p(values)  # log(1+x) to handle zeros
    
    stat, pval = kruskal(*[log_4[m] for m in ['Distinct', 'Email', 'MSN', 'ML']])
    print(f"   4 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    stat, pval = kruskal(*[log_4[m] for m in ['Email', 'MSN', 'ML']])
    print(f"   3 methods: H = {stat:.2f}, p = {pval:.4e}")
    
    # Method 5: Check if using raw total counts (not per-project)
    print("\n5. Using total contributor counts (not per-project):")
    totals = {
        'Distinct': [datasets['Distinct']['contributor_count'].sum()],
        'Email': [datasets['Email']['contributor_count'].sum()],
        'MSN': [datasets['MSN']['contributor_count'].sum()],
        'ML': [datasets['ML']['contributor_count'].sum()],
    }
    print(f"   This would be invalid (single value per method)")
    print(f"   Distinct: {totals['Distinct'][0]}, Email: {totals['Email'][0]}, "
          f"MSN: {totals['MSN'][0]}, ML: {totals['ML'][0]}")
    
    # Method 6: Maybe using projects where all 4 methods have data, but different order?
    print("\n6. Using all 275 projects from Distinct/Email/MSN (excluding ML missing ones):")
    projects_275 = sorted(set(datasets['Distinct'].index) & 
                         set(datasets['Email'].index) & 
                         set(datasets['MSN'].index))
    
    aligned_275 = {}
    for method in ['Distinct', 'Email', 'MSN']:
        aligned_275[method] = [datasets[method].get(proj) for proj in projects_275]
    
    # ML only has 273 projects
    ml_projects = sorted(set(datasets['ML'].index))
    aligned_275['ML'] = [datasets['ML'].get(proj, 0) for proj in projects_275]
    
    stat, pval = kruskal(
        aligned_275['Distinct'],
        aligned_275['Email'],
        aligned_275['MSN'],
        aligned_275['ML']
    )
    print(f"   4 methods (275 projects, ML filled with 0 for 2 missing): H = {stat:.2f}, p = {pval:.4e}")
    
    # Check values
    print(f"\n   Values in ML (should have 2 zeros): {aligned_275['ML'].count(0)} zeros")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nYour result: H = 84.72, p = 1.2e-15")
    print("\nNone of our methods reproduce H = 84.72.")
    print("\nTo help identify the issue, can you share:")
    print("  1. The exact code you're using to run kruskal()?")
    print("  2. The length of each input array to kruskal()?")
    print("  3. A sample of the first few values in each array?")
    print("  4. Are you using the contributor count CSVs or raw data files?")

if __name__ == '__main__':
    main()

