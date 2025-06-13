#!/usr/bin/env python3
"""
Verify and display the Kruskal-Wallis test results.
This demonstrates that we test all 4 groups at once (not pairwise).
"""

import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path

EXP21_DIR = Path(__file__).parent

def main():
    print("="*70)
    print("KRUSKAL-WALLIS TEST: Statistical Comparison of 4 Methods")
    print("="*70)
    print("\nLoading contributor count files...")
    
    # Load all 4 contributor count files
    files = {
        'distinct': EXP21_DIR / 'distinct_contributor_counts.csv',
        'email': EXP21_DIR / 'email_contributor_counts.csv',
        'msn': EXP21_DIR / 'msn_contributor_counts.csv',
        'ml': EXP21_DIR / 'ml_contributor_counts.csv',
    }
    
    datasets = {}
    for method, filepath in files.items():
        df = pd.read_csv(filepath)
        # Sort by project to ensure alignment
        df = df.sort_values('project').reset_index(drop=True)
        datasets[method] = df['contributor_count'].values
        print(f"  {method:10s}: {len(df)} projects, mean = {df['contributor_count'].mean():.1f}")
    
    print("\n" + "="*70)
    print("CORRECT APPROACH: Testing all 4 groups at once")
    print("="*70)
    print("\nRunning Kruskal-Wallis test with all 4 methods simultaneously:")
    print("  kruskal(counts_distinct, counts_email, counts_msn, counts_ml)")
    print()
    
    # CORRECT: Test all 4 groups at once
    statistic, pvalue = kruskal(
        datasets['distinct'],
        datasets['email'],
        datasets['msn'],
        datasets['ml']
    )
    
    print("Test Results:")
    print(f"  Test Statistic (H): {statistic:.6f}")
    print(f"  p-value:            {pvalue:.6f}")
    print(f"  p-value (scientific): {pvalue:.4e}")
    
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)
    
    alpha = 0.05
    print(f"\nAlpha level: {alpha}")
    print(f"p-value: {pvalue:.6f}")
    
    if pvalue < alpha:
        print(f"\n✓ p < {alpha} → REJECT null hypothesis")
        print("\nConclusion: There IS a statistically significant difference")
        print("            among at least one pair of the four methods.")
        print("\nNext step: Perform post-hoc tests (e.g., Dunn's test) to")
        print("           identify which specific pairs are different.")
    else:
        print(f"\n✓ p >= {alpha} → FAIL TO REJECT null hypothesis")
        print("\nConclusion: There is NO statistically significant difference")
        print("            among the four methods in terms of contributor counts per project.")
        print("\nThis means:")
        print("  • The merging methods reduce counts proportionally across all projects")
        print("  • The distribution patterns are preserved across methods")
        print("  • No post-hoc tests are needed (since overall test is not significant)")
    
    print("\n" + "="*70)
    print("WHY NOT PAIRWISE TESTS?")
    print("="*70)
    print("\n✗ INCORRECT approach (would cause multiple comparisons problem):")
    print("  kruskal(counts_distinct, counts_email)  # Test 1")
    print("  kruskal(counts_distinct, counts_msn)    # Test 2")
    print("  kruskal(counts_distinct, counts_ml)     # Test 3")
    print("  ... (6 total pairwise tests)")
    print("\n  Problem: Multiple tests increase false positive rate")
    print("           Each test has 5% chance of false positive")
    print("           6 tests = much higher overall false positive rate")
    print("\n✓ CORRECT approach (what we did):")
    print("  kruskal(counts_distinct, counts_email, counts_msn, counts_ml)")
    print("\n  Benefit: Single test with reliable p-value")
    print("           Acts as 'gatekeeper' to avoid multiple comparisons problem")
    print("           If significant, THEN do post-hoc tests")
    
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    summary_data = []
    for method, counts in datasets.items():
        summary_data.append({
            'Method': method.upper(),
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
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()

