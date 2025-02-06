#!/usr/bin/env python3
"""
Aggregate commit metrics (Commit Count, Commit Additions, Commit Deletions) per project
from Experiment 10/master_commits_fullfat.csv
"""
import csv
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PROJECTS_CSV = BASE / "projects_all.csv"
COMMITS_CSV = Path(__file__).resolve().parents[2] / "Experiment 10" / "master_commits_fullfat.csv"
OUTPUT_CSV = BASE / "Data" / "commit_metrics_per_project.csv"

print(f"Loading projects from: {PROJECTS_CSV}")
print(f"Loading commits from: {COMMITS_CSV}")
print(f"Output will be: {OUTPUT_CSV}")

# Load project list
projects_df = pd.read_csv(PROJECTS_CSV)
print(f"\nLoaded {len(projects_df)} projects")

# Load commits data
print(f"\nLoading commits data (this may take a moment)...")
commits_df = pd.read_csv(COMMITS_CSV, dtype={'total_additions': 'Int64', 'total_deletions': 'Int64'})
print(f"Loaded {len(commits_df)} commits")

# Normalize project names (lowercase for matching)
commits_df['project_lower'] = commits_df['project'].str.lower()
projects_df['repo_lower'] = projects_df['repo'].str.lower()

# Aggregate by project
print("\nAggregating metrics per project...")
agg_metrics = commits_df.groupby('project').agg({
    'commit': 'count',  # Commit Count
    'total_additions': 'sum',  # Commit Additions
    'total_deletions': 'sum'   # Commit Deletions
}).reset_index()

agg_metrics.columns = ['repo', 'Commit Count', 'Commit Additions', 'Commit Deletions']

# Normalize repo names for merging
agg_metrics['repo_lower'] = agg_metrics['repo'].str.lower()

# Merge with project list to ensure we have all projects
result_df = projects_df.merge(agg_metrics, on='repo_lower', how='left', suffixes=('', '_new'))

# Fill missing values with 0
result_df['Commit Count'] = result_df['Commit Count'].fillna(0).astype(int)
result_df['Commit Additions'] = result_df['Commit Additions'].fillna(0).astype(int)
result_df['Commit Deletions'] = result_df['Commit Deletions'].fillna(0).astype(int)

# Keep only the repo name (not repo_lower)
result_df = result_df[['repo', 'category', 'Commit Count', 'Commit Additions', 'Commit Deletions']]

# Save
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
result_df.to_csv(OUTPUT_CSV, index=False)

print(f"\n✓ Saved {len(result_df)} projects to {OUTPUT_CSV}")
print(f"\nSummary:")
print(f"  Projects with commits: {(result_df['Commit Count'] > 0).sum()}")
print(f"  Total Commit Count: {result_df['Commit Count'].sum():,}")
print(f"  Total Commit Additions: {result_df['Commit Additions'].sum():,}")
print(f"  Total Commit Deletions: {result_df['Commit Deletions'].sum():,}")
print(f"\nFirst few rows:")
print(result_df.head(10).to_string())

