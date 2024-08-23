#!/usr/bin/env python3
import os
import sys
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
PRISM_OSS = os.path.join(ROOT, 'prism', 'oss')
PRISM_OSS4SG = os.path.join(ROOT, 'prism', 'oss4sg')
OUT_CSV = os.path.join(ROOT, 'master_commits.csv')


def collect_csvs(dir_path: str, category: str) -> pd.DataFrame:
    rows = []
    for fn in os.listdir(dir_path):
        if not fn.endswith('.csv'):
            continue
        fp = os.path.join(dir_path, fn)
        try:
            df = pd.read_csv(fp, dtype=str)
            # infer project from filename <owner>_<repo>.csv
            project = os.path.splitext(fn)[0]
            df['project'] = project
            df['category'] = category
            rows.append(df)
        except Exception as e:
            print(f"WARN: failed reading {fp}: {e}")
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main():
    oss_df = collect_csvs(PRISM_OSS, 'OSS')
    oss4sg_df = collect_csvs(PRISM_OSS4SG, 'OSS4SG')

    combined = pd.concat([oss_df, oss4sg_df], ignore_index=True)

    # optional: reorder columns if present
    cols = ['project', 'category', 'commit', 'author_name', 'author_email', 'date', 'message']
    ordered = [c for c in cols if c in combined.columns]
    others = [c for c in combined.columns if c not in ordered]
    combined = combined[ordered + others]

    combined.to_csv(OUT_CSV, index=False)

    print(f"Master CSV: {OUT_CSV}")
    print(f"Total rows: {len(combined):,}")
    if len(oss_df):
        print(f"OSS rows: {len(oss_df):,}")
    if len(oss4sg_df):
        print(f"OSS4SG rows: {len(oss4sg_df):,}")


if __name__ == '__main__':
    sys.exit(main())


