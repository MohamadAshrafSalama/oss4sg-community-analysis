#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(os.path.dirname(ROOT), 'master_commits.csv')

print('Loading master_commits.csv ...')
df = pd.read_csv(MASTER, dtype=str)

# Keep only needed columns
needed = ['project','category','author_name']
df = df[needed].dropna()

# Normalize author_name minimally (strip)
df['author_name'] = df['author_name'].astype(str).str.strip()

# Split by category
oss = df[df['category'] == 'OSS']
oss4 = df[df['category'] == 'OSS4SG']

# Count distinct projects per author within each category
oss_counts = oss.groupby('author_name')['project'].nunique()
oss4_counts = oss4.groupby('author_name')['project'].nunique()

oss_multi = (oss_counts >= 2).sum()
oss_total_authors = oss_counts.shape[0]
oss_pct = 100.0 * oss_multi / oss_total_authors if oss_total_authors else 0.0

oss4_multi = (oss4_counts >= 2).sum()
oss4_total_authors = oss4_counts.shape[0]
oss4_pct = 100.0 * oss4_multi / oss4_total_authors if oss4_total_authors else 0.0

print('\nIntra-cross pollination (within category, authors with >=2 projects):')
print(f'OSS:   {oss_multi} / {oss_total_authors} ({oss_pct:.2f}%)')
print(f'OSS4SG:{oss4_multi} / {oss4_total_authors} ({oss4_pct:.2f}%)')

# Inter-category: authors with >=2 in BOTH categories
# Build aligned series
all_authors = set(oss_counts.index) | set(oss4_counts.index)
import numpy as np
oss_aligned = pd.Series({a: oss_counts.get(a, 0) for a in all_authors})
oss4_aligned = pd.Series({a: oss4_counts.get(a, 0) for a in all_authors})
inter_both = ((oss_aligned >= 2) & (oss4_aligned >= 2)).sum()

print('\nInter-cross pollination (authors >=2 in both categories):')
print(f'{inter_both} out of {len(all_authors)} ({100.0*inter_both/len(all_authors):.2f}%)')
