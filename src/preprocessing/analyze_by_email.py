#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(os.path.dirname(ROOT), 'master_commits.csv')

print('Loading master_commits.csv ...')
df = pd.read_csv(MASTER, dtype=str)

df = df[['project','category','author_email']].dropna()
df['author_email'] = df['author_email'].astype(str).str.strip()

oss = df[df['category'] == 'OSS']
oss4 = df[df['category'] == 'OSS4SG']

oss_counts = oss.groupby('author_email')['project'].nunique()
oss4_counts = oss4.groupby('author_email')['project'].nunique()

oss_multi = (oss_counts >= 2).sum()
oss_total = oss_counts.shape[0]
oss_pct = 100.0 * oss_multi / oss_total if oss_total else 0.0

oss4_multi = (oss4_counts >= 2).sum()
oss4_total = oss4_counts.shape[0]
oss4_pct = 100.0 * oss4_multi / oss4_total if oss4_total else 0.0

print('\nBy EMAIL (raw case):')
print(f'OSS:   {oss_multi} / {oss_total} ({oss_pct:.2f}%)')
print(f'OSS4SG:{oss4_multi} / {oss4_total} ({oss4_pct:.2f}%)')

all_emails = set(oss_counts.index) | set(oss4_counts.index)
oss_aligned = pd.Series({a: oss_counts.get(a, 0) for a in all_emails})
oss4_aligned = pd.Series({a: oss4_counts.get(a, 0) for a in all_emails})
inter_both = ((oss_aligned >= 2) & (oss4_aligned >= 2)).sum()

print('\nInter (>=2 in BOTH by email raw):')
print(f'{inter_both} / {len(all_emails)} ({100.0*inter_both/len(all_emails):.2f}%)')


