#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(os.path.dirname(ROOT), 'master_commits.csv')

print('Loading master_commits.csv ...')
df = pd.read_csv(MASTER, dtype=str)

df = df[['project','category','author_name']].dropna()
df['author_name'] = df['author_name'].astype(str).str.strip()

oss = df[df['category'] == 'OSS']
oss4 = df[df['category'] == 'OSS4SG']

oss_counts = oss.groupby('author_name')['project'].nunique()
oss4_counts = oss4.groupby('author_name')['project'].nunique()

oss_multi = (oss_counts >= 2).sum()
oss_total = oss_counts.shape[0]
oss_pct = 100.0 * oss_multi / oss_total if oss_total else 0.0

oss4_multi = (oss4_counts >= 2).sum()
oss4_total = oss4_counts.shape[0]
oss4_pct = 100.0 * oss4_multi / oss4_total if oss4_total else 0.0

print('\nBy USERNAME only:')
print(f'OSS:   {oss_multi} / {oss_total} ({oss_pct:.2f}%)')
print(f'OSS4SG:{oss4_multi} / {oss4_total} ({oss4_pct:.2f}%)')

all_authors = set(oss_counts.index) | set(oss4_counts.index)
oss_aligned = pd.Series({a: oss_counts.get(a, 0) for a in all_authors})
oss4_aligned = pd.Series({a: oss4_counts.get(a, 0) for a in all_authors})
inter_both = ((oss_aligned >= 2) & (oss4_aligned >= 2)).sum()

print('\nInter (>=2 in BOTH by username):')
print(f'{inter_both} / {len(all_authors)} ({100.0*inter_both/len(all_authors):.2f}%)')


