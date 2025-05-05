#!/usr/bin/env python3
"""
Verify total unique contributor counts across all projects for each method.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent

FILES = {
    '1. Distinct (Baseline)': DATA_DIR / '01_distinct_name_email_pairs.csv',
    '2. Email Baseline': DATA_DIR / '02_email_baseline_method.csv',
    '3. MSN Method': DATA_DIR / '03_msn_method.csv',
    '4. Full-Fat ML Method': DATA_DIR / '04_fullfat_ml_method.csv',
}

def count_unique_contributors(df, method_name):
    """Count total unique contributors across all projects."""
    if method_name == '1. Distinct (Baseline)':
        # For distinct method, count unique (name, email) pairs
        df['contributor_key'] = df['author_name'].astype(str) + '|' + df['author_email'].astype(str)
        unique_count = df['contributor_key'].nunique()
    else:
        # For merged methods, count unique (group_id, project) pairs
        # This represents unique contributors per project
        unique_count = len(df)
    return unique_count

def main():
    print("Counting unique contributors for each method:\n")
    
    results = []
    for method_name, filepath in FILES.items():
        print(f"Loading {method_name}...")
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        
        if method_name == '1. Distinct (Baseline)':
            # Total unique (name, email) pairs
            unique_count = df.drop_duplicates(subset=['author_name', 'author_email']).shape[0]
        else:
            # Total rows = unique contributors (one row per contributor per project)
            unique_count = len(df)
        
        results.append({
            'Method': method_name,
            'Unique Contributors': unique_count,
            'Total Rows': len(df)
        })
        print(f"  Unique contributors: {unique_count:,}")
        print(f"  Total rows: {len(df):,}\n")
    
    # Calculate reductions
    baseline_count = results[0]['Unique Contributors']
    print(f"\n{'Method':<30} {'Contributors':<15} {'Reduction':<12} {'% Reduced':<12}")
    print("-" * 70)
    
    for r in results:
        reduction = baseline_count - r['Unique Contributors']
        pct_reduced = (reduction / baseline_count * 100) if baseline_count > 0 else 0
        print(f"{r['Method']:<30} {r['Unique Contributors']:<15,} {reduction:<12,} {pct_reduced:<12.1f}%")
    
    # Save to CSV
    summary_df = pd.DataFrame(results)
    summary_df['Reduction'] = baseline_count - summary_df['Unique Contributors']
    summary_df['% Reduced'] = (summary_df['Reduction'] / baseline_count * 100).round(1)
    summary_df.to_csv(DATA_DIR / 'unique_contributor_counts.csv', index=False)
    print(f"\nSaved to: {DATA_DIR / 'unique_contributor_counts.csv'}")

if __name__ == '__main__':
    main()

