#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import Tuple, Dict
import pandas as pd

# Paths (absolute by default; adjust if the project root changes)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Inputs
RAW_PAIRS = os.path.join(PROJECT_ROOT, 'Experiment 3', 'name_email_pairs.csv')
EMAIL_BASELINE = os.path.join(PROJECT_ROOT, 'Experiment 4', 'contributors_email_baseline_all_projects.csv')
MSN = os.path.join(PROJECT_ROOT, 'Experiment 4', 'contributors_all_projects.csv')

# Outputs
OUT_DIR = os.path.join(PROJECT_ROOT, 'Experiment 6')
SUMMARY_JSON = os.path.join(OUT_DIR, 'summary.json')
SUMMARY_CSV = os.path.join(OUT_DIR, 'summary.csv')


def compute_intra_inter_from_pairs(df: pd.DataFrame, key_col: str) -> Tuple[int, float, int, float]:
    """
    Given a dataframe of raw pairs with columns: project, category, author_name, author_email,
    compute intra- and inter- cross pollination stats using either names-only or emails-only.

    - key_col: 'author_name' or 'author_email'.

    Returns:
        intra_count, intra_pct, inter_count, inter_pct
    Where:
        intra_* is: number and percentage of contributors (unique by key_col within category)
                    active in >=2 distinct projects within the same category.
        inter_* is: number and percentage of contributors (unique by key_col overall)
                    active in both categories (OSS and OSS4SG) (>=1 project in each).
    """
    df = df.copy()
    df = df[['project', 'category', key_col]].fillna('')
    # Drop empty keys
    df = df[df[key_col].astype(str).str.strip().ne('')]

    # Intra per category: group by (category, key) -> nunique projects
    proj_counts = (
        df.groupby(['category', key_col])['project']
          .nunique()
          .reset_index(name='num_projects')
    )

    # For each category, count keys with >=2 projects; percentage over unique keys in that category
    intra_results: Dict[str, Tuple[int, float]] = {}
    for cat in ['OSS', 'OSS4SG']:
        cat_df = proj_counts[proj_counts['category'] == cat]
        total_keys = cat_df[key_col].nunique()
        intra_count = int((cat_df['num_projects'] >= 2).sum())
        intra_pct = (100.0 * intra_count / total_keys) if total_keys > 0 else 0.0
        intra_results[cat] = (intra_count, intra_pct)

    # Inter across categories: for each key, categories present
    key_to_cats = (
        df.groupby(key_col)['category']
          .apply(lambda s: set(s.unique()))
    )
    inter_count = int((key_to_cats.apply(lambda c: {'OSS', 'OSS4SG'}.issubset(c))).sum())
    total_unique_keys = int(df[key_col].nunique())
    inter_pct = (100.0 * inter_count / total_unique_keys) if total_unique_keys > 0 else 0.0

    # Return aggregate intra as combined dict for convenience: we will store both categories.
    # Here we return only totals (sum of both categories) for convenience alongside percentage over combined keys.
    # But for reporting clarity, we compute and store per-category separately later.
    return intra_results['OSS'][0] + intra_results['OSS4SG'][0], 0.0, inter_count, inter_pct


def compute_intra_inter_from_contributors(df: pd.DataFrame, key_col: str) -> Tuple[int, float, int, float]:
    """
    Given a dataframe of contributor groups with columns:
        group_id, project, category, names, emails, num_names, num_emails, num_pairs_merged

    Compute intra/inter using group membership expanded to individual keys (names-only or emails-only).

    - key_col: 'names' or 'emails'. For names, split by ';'; for emails, split by ';'.
    Empty tokens are ignored after stripping.

    Returns:
        intra_count_total, intra_pct_dummy, inter_count, inter_pct  (same signature as above for consistency)
    """
    df = df.copy()
    df = df[['project', 'category', key_col]].fillna('')

    # explode keys
    def split_tokens(x: str):
        return [t.strip() for t in str(x).split(';') if t and t.strip()]

    df[key_col] = df[key_col].apply(split_tokens)
    df = df.explode(key_col)
    df = df[df[key_col].astype(str).str.strip().ne('')]

    # Intra per category
    proj_counts = (
        df.groupby(['category', key_col])['project']
          .nunique()
          .reset_index(name='num_projects')
    )

    intra_results: Dict[str, Tuple[int, float]] = {}
    for cat in ['OSS', 'OSS4SG']:
        cat_df = proj_counts[proj_counts['category'] == cat]
        total_keys = cat_df[key_col].nunique()
        intra_count = int((cat_df['num_projects'] >= 2).sum())
        intra_pct = (100.0 * intra_count / total_keys) if total_keys > 0 else 0.0
        intra_results[cat] = (intra_count, intra_pct)

    # Inter across categories
    key_to_cats = (
        df.groupby(key_col)['category']
          .apply(lambda s: set(s.unique()))
    )
    inter_count = int((key_to_cats.apply(lambda c: {'OSS', 'OSS4SG'}.issubset(c))).sum())
    total_unique_keys = int(df[key_col].nunique())
    inter_pct = (100.0 * inter_count / total_unique_keys) if total_unique_keys > 0 else 0.0

    return intra_results['OSS'][0] + intra_results['OSS4SG'][0], 0.0, inter_count, inter_pct


def main():
    ap = argparse.ArgumentParser(description='Experiment 6: Intra/Inter using names-only and emails-only across datasets')
    ap.add_argument('--raw', default=RAW_PAIRS, help='Experiment 3/name_email_pairs.csv')
    ap.add_argument('--email_baseline', default=EMAIL_BASELINE, help='Experiment 4/contributors_email_baseline_all_projects.csv')
    ap.add_argument('--msn', default=MSN, help='Experiment 4/contributors_all_projects.csv')
    ap.add_argument('--out', default=OUT_DIR, help='Output directory for Experiment 6')
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    summary_rows = []

    # 1) Raw pairs: compute for names-only and emails-only using pair rows
    raw_df = pd.read_csv(args.raw, dtype=str)
    for key in ['author_name', 'author_email']:
        intra_total, _, inter_count, inter_pct = compute_intra_inter_from_pairs(raw_df, key)
        summary_rows.append({
            'dataset': 'raw_pairs',
            'key_type': 'names' if key == 'author_name' else 'emails',
            'intra_total_count_across_categories': intra_total,
            'inter_count': inter_count,
            'inter_pct': inter_pct,
        })

    # 2) Email-baseline contributors: compute with names-only and emails-only expanded from groups
    eb_df = pd.read_csv(args.email_baseline, dtype=str)
    for key in ['names', 'emails']:
        intra_total, _, inter_count, inter_pct = compute_intra_inter_from_contributors(eb_df, key)
        summary_rows.append({
            'dataset': 'email_baseline',
            'key_type': 'names' if key == 'names' else 'emails',
            'intra_total_count_across_categories': intra_total,
            'inter_count': inter_count,
            'inter_pct': inter_pct,
        })

    # 3) MSN contributors: compute with names-only and emails-only expanded from groups
    msn_df = pd.read_csv(args.msn, dtype=str)
    for key in ['names', 'emails']:
        intra_total, _, inter_count, inter_pct = compute_intra_inter_from_contributors(msn_df, key)
        summary_rows.append({
            'dataset': 'msn',
            'key_type': 'names' if key == 'names' else 'emails',
            'intra_total_count_across_categories': intra_total,
            'inter_count': inter_count,
            'inter_pct': inter_pct,
        })

    # Save summary
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    with open(SUMMARY_JSON, 'w') as f:
        json.dump(summary_rows, f, indent=2)

    print('Saved results:')
    print(SUMMARY_CSV)
    print(SUMMARY_JSON)


if __name__ == '__main__':
    sys.exit(main())


