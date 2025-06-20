#!/usr/bin/env python3
"""
Test Kruskal-Wallis using raw contributor data (not aggregated per project).
This might explain the H=84.72 result.
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

EXP12_DIR = Path(__file__).parent.parent / "Experiment 12"

def main():
    print("="*80)
    print("TESTING WITH RAW CONTRIBUTOR DATA (Not Aggregated Per Project)")
    print("="*80)
    print("\nThis uses each contributor as a data point, not each project.")
    
    # Load raw data files
    files = {
        'Distinct': EXP12_DIR / '01_distinct_name_email_pairs.csv',
        'Email': EXP12_DIR / '02_email_baseline_method.csv',
        'MSN': EXP12_DIR / '03_msn_method.csv',
        'ML': EXP12_DIR / '04_fullfat_ml_method.csv',
    }
    
    print("\nLoading raw data files...")
    raw_data = {}
    
    for method, filepath in files.items():
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        raw_data[method] = df
        print(f"  {method:10s}: {len(df)} rows (contributors)")
    
    # Method 1: Use all contributors (not per-project)
    print("\n" + "="*80)
    print("METHOD 1: All Contributors - Using Row Counts")
    print("="*80)
    print("\nThis treats each row as a contributor and counts them.")
    print("This is NOT the same as per-project counts!")
    
    # For distinct: each row is already a contributor
    # For others: each row is a group_id (already a contributor)
    
    # Create a value for each contributor (could be project count they appear in)
    contributor_values = {}
    
    for method, df in raw_data.items():
        if method == 'Distinct':
            # Count how many projects each (name, email) appears in
            proj_counts = df.groupby(['author_name', 'author_email'])['project'].nunique()
            contributor_values[method] = proj_counts.values
        else:
            # Count how many projects each group_id appears in
            proj_counts = df.groupby('group_id')['project'].nunique()
            contributor_values[method] = proj_counts.values
    
    print("\nContributor-level statistics:")
    for method, values in contributor_values.items():
        print(f"  {method:10s}: {len(values)} contributors, "
              f"mean projects/contributor = {values.mean():.3f}")
    
    # Run Kruskal-Wallis on contributor-level data
    stat_4, pval_4 = kruskal(
        contributor_values['Distinct'],
        contributor_values['Email'],
        contributor_values['MSN'],
        contributor_values['ML']
    )
    
    print(f"\n4 methods: H = {stat_4:.6f}, p = {pval_4:.6f}")
    print(f"           p (scientific) = {pval_4:.4e}")
    
    stat_3, pval_3 = kruskal(
        contributor_values['Email'],
        contributor_values['MSN'],
        contributor_values['ML']
    )
    
    print(f"3 methods: H = {stat_3:.6f}, p = {pval_3:.6f}")
    print(f"           p (scientific) = {pval_3:.4e}")
    
    # Method 2: Use contributor counts per project (what we did before)
    print("\n" + "="*80)
    print("METHOD 2: Per-Project Counts (What We Did Before)")
    print("="*80)
    
    project_counts = {}
    for method, df in raw_data.items():
        if method == 'Distinct':
            counts = df.groupby('project').size()
        else:
            counts = df.groupby('project')['group_id'].nunique()
        project_counts[method] = counts
    
    # Find common projects
    common_projects = set(project_counts['Distinct'].index)
    for method in ['Email', 'MSN', 'ML']:
        common_projects = common_projects.intersection(set(project_counts[method].index))
    
    common_projects = sorted(common_projects)
    print(f"\nCommon projects: {len(common_projects)}")
    
    aligned_counts = {}
    for method, counts in project_counts.items():
        aligned_counts[method] = [counts.get(proj, 0) for proj in common_projects]
    
    stat_4_proj, pval_4_proj = kruskal(
        aligned_counts['Distinct'],
        aligned_counts['Email'],
        aligned_counts['MSN'],
        aligned_counts['ML']
    )
    
    print(f"\n4 methods (per-project): H = {stat_4_proj:.6f}, p = {pval_4_proj:.6f}")
    
    stat_3_proj, pval_3_proj = kruskal(
        aligned_counts['Email'],
        aligned_counts['MSN'],
        aligned_counts['ML']
    )
    
    print(f"3 methods (per-project): H = {stat_3_proj:.6f}, p = {pval_3_proj:.6f}")
    
    # Method 3: Maybe they're using total contributor counts as a single value?
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print("\nResults:")
    print(f"  Contributor-level (4 methods): H = {stat_4:.2f}, p = {pval_4:.4e}")
    print(f"  Contributor-level (3 methods): H = {stat_3:.2f}, p = {pval_3:.4e}")
    print(f"  Per-project (4 methods):       H = {stat_4_proj:.2f}, p = {pval_4_proj:.4e}")
    print(f"  Per-project (3 methods):       H = {stat_3_proj:.2f}, p = {pval_3_proj:.4e}")
    print(f"\n  Your result:                  H = 84.72, p = 1.2e-15")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    print("\nThe H=84.72 you're seeing is MUCH higher than our results.")
    print("This suggests a different analysis approach.")
    print("\nPossible explanations:")
    print("  1. Using contributor-level data with different encoding")
    print("  2. Using a different statistical test or formula")
    print("  3. Using transformed/normalized data")
    print("  4. Including different projects or filtering")
    print("\nCan you share:")
    print("  - How you're loading/preparing the data?")
    print("  - What exactly are the 4 (or 3) inputs to kruskal()?")
    print("  - Are you using per-project counts or raw contributor data?")

if __name__ == '__main__':
    main()

