#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect(dir_path: str) -> pd.DataFrame:
    rows = []
    for fn in os.listdir(dir_path):
        if not fn.endswith('.csv'):
            continue
        fp = os.path.join(dir_path, fn)
        try:
            df = pd.read_csv(fp, dtype=str)
            rows.append(df)
        except Exception:
            pass
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main():
    oss = os.path.join(ROOT, 'contributors_per_project', 'oss')
    oss4sg = os.path.join(ROOT, 'contributors_per_project', 'oss4sg')
    d1 = collect(oss)
    d2 = collect(oss4sg)
    combined = pd.concat([d1, d2], ignore_index=True)
    out_csv = os.path.join(ROOT, 'contributors_all_projects.csv')
    combined.to_csv(out_csv, index=False)
    print(f'Wrote {out_csv} with {len(combined)} rows')


if __name__ == '__main__':
    main()


