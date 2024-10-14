#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(os.path.dirname(ROOT), 'master_commits.csv')
OUT = os.path.join(ROOT, 'name_email_pairs.csv')

def main():
    print('Loading master_commits.csv ...')
    df = pd.read_csv(MASTER, dtype=str, usecols=['project','category','author_name','author_email'])
    # Strip whitespace
    for c in ['project','category','author_name','author_email']:
        df[c] = df[c].astype(str).str.strip()
    # Drop rows missing both name and email
    df = df[ df['author_name'].ne('') | df['author_email'].ne('') ]
    # Deduplicate exact pairs
    before = len(df)
    df = df.drop_duplicates(subset=['project','category','author_name','author_email'])
    print(f'Removed duplicates: {before - len(df)}')
    df.to_csv(OUT, index=False)
    print(f'Saved: {OUT}')
    print(f'Total pairs: {len(df):,}')
    print('Sample:')
    print(df.head(5))

if __name__ == '__main__':
    main()


