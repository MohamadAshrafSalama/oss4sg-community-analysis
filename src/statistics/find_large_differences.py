#!/usr/bin/env python3
"""
Find examples from datasets where there are large differences (~1000) 
between Email-based, MSN, and ML methods.
"""

import pandas as pd

# Read all four datasets
print("="*100)
print("LOCATING THE FOUR DATASETS:")
print("="*100)
print("1. Original (Distinct Name+Email Pairs): 01_distinct_name_email_pairs.csv")
print("2. Email-Based Baseline: 02_email_baseline_method.csv")
print("3. MSN Method: 03_msn_method.csv")
print("4. Machine Learning Method: 04_fullfat_ml_method.csv")
print()

print("Loading datasets...")
original = pd.read_csv('01_distinct_name_email_pairs.csv')
email = pd.read_csv('02_email_baseline_method.csv')
msn = pd.read_csv('03_msn_method.csv')
ml = pd.read_csv('04_fullfat_ml_method.csv')

# Count unique contributors per project for each method
print("Counting contributors per project...")
original_counts = original.groupby('project').size().reset_index(name='original_count')
email_counts = email.groupby('project').size().reset_index(name='email_count')
msn_counts = msn.groupby('project').size().reset_index(name='msn_count')
ml_counts = ml.groupby('project').size().reset_index(name='ml_count')

# Merge all counts
all_counts = original_counts.merge(email_counts, on='project', how='outer')
all_counts = all_counts.merge(msn_counts, on='project', how='outer')
all_counts = all_counts.merge(ml_counts, on='project', how='outer')
all_counts = all_counts.fillna(0)

# Calculate differences
all_counts['email_vs_msn'] = all_counts['email_count'] - all_counts['msn_count']
all_counts['ml_vs_msn'] = all_counts['ml_count'] - all_counts['msn_count']
all_counts['ml_vs_email'] = all_counts['ml_count'] - all_counts['email_count']
all_counts['email_vs_msn_abs'] = all_counts['email_vs_msn'].abs()
all_counts['ml_vs_msn_abs'] = all_counts['ml_vs_msn'].abs()
all_counts['ml_vs_email_abs'] = all_counts['ml_vs_email'].abs()

print("\n" + "="*100)
print("SUMMARY STATISTICS:")
print("="*100)
print(f"Total projects: {len(all_counts)}")
print(f"\nTotal contributors:")
print(f"  Original: {int(all_counts['original_count'].sum()):,}")
print(f"  Email-based: {int(all_counts['email_count'].sum()):,}")
print(f"  MSN: {int(all_counts['msn_count'].sum()):,}")
print(f"  ML: {int(all_counts['ml_count'].sum()):,}")

print("\n" + "="*100)
print("PROJECTS WITH LARGEST DIFFERENCES:")
print("="*100)

# Find projects closest to 1000 difference
target = 1000
tolerance = 500  # ±500 range

print(f"\n1. Projects with Email vs MSN difference closest to {target} (±{tolerance}):")
email_msn_close = all_counts[
    (all_counts['email_vs_msn_abs'] >= target - tolerance) & 
    (all_counts['email_vs_msn_abs'] <= target + tolerance)
].sort_values('email_vs_msn_abs', ascending=False)

if len(email_msn_close) > 0:
    print(email_msn_close[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'email_vs_msn']].to_string(index=False))
else:
    print("  No projects found in this range. Showing top 10 largest differences:")
    top_email_msn = all_counts.nlargest(10, 'email_vs_msn_abs')
    print(top_email_msn[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'email_vs_msn']].to_string(index=False))

print(f"\n2. Projects with ML vs MSN difference closest to {target} (±{tolerance}):")
ml_msn_close = all_counts[
    (all_counts['ml_vs_msn_abs'] >= target - tolerance) & 
    (all_counts['ml_vs_msn_abs'] <= target + tolerance)
].sort_values('ml_vs_msn_abs', ascending=False)

if len(ml_msn_close) > 0:
    print(ml_msn_close[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'ml_vs_msn']].to_string(index=False))
else:
    print("  No projects found in this range. Showing top 10 largest differences:")
    top_ml_msn = all_counts.nlargest(10, 'ml_vs_msn_abs')
    print(top_ml_msn[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'ml_vs_msn']].to_string(index=False))

print(f"\n3. Projects with ML vs Email difference closest to {target} (±{tolerance}):")
ml_email_close = all_counts[
    (all_counts['ml_vs_email_abs'] >= target - tolerance) & 
    (all_counts['ml_vs_email_abs'] <= target + tolerance)
].sort_values('ml_vs_email_abs', ascending=False)

if len(ml_email_close) > 0:
    print(ml_email_close[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'ml_vs_email']].to_string(index=False))
else:
    print("  No projects found in this range. Showing top 10 largest differences:")
    top_ml_email = all_counts.nlargest(10, 'ml_vs_email_abs')
    print(top_ml_email[['project', 'original_count', 'email_count', 'msn_count', 'ml_count', 'ml_vs_email']].to_string(index=False))

# Show detailed example for the project with largest difference
print("\n" + "="*100)
print("DETAILED EXAMPLE - Project with Largest Email vs MSN Difference:")
print("="*100)

largest_diff_project = all_counts.loc[all_counts['email_vs_msn_abs'].idxmax()]
project_name = largest_diff_project['project']

print(f"\nProject: {project_name}")
print(f"Original contributors: {int(largest_diff_project['original_count'])}")
print(f"Email-based contributors: {int(largest_diff_project['email_count'])}")
print(f"MSN contributors: {int(largest_diff_project['msn_count'])}")
print(f"ML contributors: {int(largest_diff_project['ml_count'])}")
print(f"\nDifference (Email - MSN): {int(largest_diff_project['email_vs_msn'])}")
print(f"Difference (ML - MSN): {int(largest_diff_project['ml_vs_msn'])}")
print(f"Difference (ML - Email): {int(largest_diff_project['ml_vs_email'])}")

# Get actual contributor examples
email_proj = email[email['project'] == project_name]
msn_proj = msn[msn['project'] == project_name]
ml_proj = ml[ml['project'] == project_name]

print(f"\nSample contributors from Email method (showing first 5):")
print(email_proj[['group_id', 'names', 'emails', 'num_names', 'num_emails']].head(5).to_string(index=False))

print(f"\nSample contributors from MSN method (showing first 5):")
print(msn_proj[['group_id', 'names', 'emails', 'num_names', 'num_emails']].head(5).to_string(index=False))

# Check cumulative differences
print("\n" + "="*100)
print("CUMULATIVE DIFFERENCES (if looking for ~1000 total across projects):")
print("="*100)

# Sort by difference and accumulate
email_msn_sorted = all_counts.sort_values('email_vs_msn_abs', ascending=False)
email_msn_sorted['cumulative_diff'] = email_msn_sorted['email_vs_msn_abs'].cumsum()

# Find where cumulative difference reaches ~1000
close_to_1000 = email_msn_sorted[
    (email_msn_sorted['cumulative_diff'] >= target - tolerance) & 
    (email_msn_sorted['cumulative_diff'] <= target + tolerance)
]

if len(close_to_1000) > 0:
    print(f"\nProjects needed to reach ~{target} cumulative difference (Email vs MSN):")
    print(close_to_1000[['project', 'email_vs_msn_abs', 'cumulative_diff']].to_string(index=False))
else:
    print(f"\nFirst 10 projects contributing to cumulative difference:")
    print(email_msn_sorted.head(10)[['project', 'email_vs_msn_abs', 'cumulative_diff']].to_string(index=False))
    print(f"\n... (continuing until reaching ~{target})")
    for idx, row in email_msn_sorted.iterrows():
        if row['cumulative_diff'] >= target:
            print(f"\nReached {target} at project: {row['project']} (cumulative: {row['cumulative_diff']:.0f})")
            break

print("\n" + "="*100)
print("ANALYSIS COMPLETE")
print("="*100)

