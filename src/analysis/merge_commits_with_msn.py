#!/usr/bin/env python3
"""
Merge commits using MSN developer groups.

For each MSN group, we take the first name as canonical contributor name,
then update all commits from developers in that group to use the canonical contributor name.
Matches commits by (project, contributor) where contributor is the username.
"""
import pandas as pd
from pathlib import Path

# Paths
BASE = Path(__file__).resolve().parent
ROOT = BASE.parent

MSN_FILE = ROOT / "Experiment 12" / "03_msn_method.csv"
COMMITS_FILE = ROOT / "EXP1(Rdoing_overlapping_and_double_check_numbers)" / "df_all_commits_with_stats.csv"
OUTPUT_FILE = BASE / "df_all_commits_with_stats_msn_merged.csv"

def normalize_name(name):
    """Normalize name/username for matching."""
    if pd.isna(name) or name == '':
        return ''
    return str(name).strip()

def build_msn_mapping():
    """Build mapping from (project, contributor_name) to canonical contributor_name for each MSN group."""
    print("Loading MSN dataset...")
    msn_df = pd.read_csv(MSN_FILE, dtype=str)
    
    # Create mapping: (project, contributor_name) -> canonical_contributor_name
    mapping = {}
    
    for _, row in msn_df.iterrows():
        project = str(row['project']).strip()
        num_names = int(row['num_names']) if pd.notna(row['num_names']) else 0
        
        # Only process groups with multiple names (merged identities)
        # Groups with num_names == 1 were not merged, so don't touch them
        if num_names <= 1:
            continue
        
        # Get all names for this group (semicolon-separated)
        names_str = str(row['names']) if pd.notna(row['names']) else ''
        names = [n.strip() for n in names_str.split(';') if n.strip()] if names_str else []
        
        if len(names) <= 1:
            continue
        
        # Canonical identity is first name
        canonical_name = names[0]
        
        # Map all (project, name) combinations in this group to canonical name
        # Skip the first name since it's already the canonical one
        for name in names[1:]:  # Only map non-canonical names
            key = (project, normalize_name(name))
            mapping[key] = canonical_name
    
    print(f"Built MSN mapping with {len(mapping):,} entries")
    return mapping

def merge_commits(msn_mapping):
    """Load commits and merge using MSN mapping based on contributor (username)."""
    print(f"Loading commits from {COMMITS_FILE}...")
    
    # Read in chunks to handle large file
    chunk_size = 100000
    chunks = []
    total_rows = 0
    merged_count = 0
    
    # Process in chunks
    for chunk_num, chunk_df in enumerate(pd.read_csv(COMMITS_FILE, chunksize=chunk_size, dtype=str)):
        print(f"Processing chunk {chunk_num + 1} ({len(chunk_df):,} rows)...")
        
        # Ensure we have the required columns
        chunk_df = chunk_df.fillna('')
        
        # Create a copy for merging
        merged_chunk = chunk_df.copy()
        
        # Try to match each commit's contributor to MSN group
        for idx, row in chunk_df.iterrows():
            project = str(row['project']).strip()
            contributor = normalize_name(str(row['contributor']) if 'contributor' in row else '')
            
            if not contributor:
                continue
            
            # Try to find in MSN mapping
            key = (project, contributor)
            if key in msn_mapping:
                canonical_name = msn_mapping[key]
                merged_chunk.at[idx, 'contributor'] = canonical_name
                merged_count += 1
        
        chunks.append(merged_chunk)
        total_rows += len(chunk_df)
        
        if (chunk_num + 1) % 10 == 0:
            print(f"  Progress: {total_rows:,} rows processed, {merged_count:,} merged")
    
    # Combine all chunks
    print("Combining chunks...")
    merged_df = pd.concat(chunks, ignore_index=True)
    
    print(f"\nTotal commits processed: {total_rows:,}")
    print(f"Commits merged using MSN: {merged_count:,}")
    print(f"Commits unchanged: {total_rows - merged_count:,}")
    
    return merged_df

def main():
    print("=" * 80)
    print("Merging commits using MSN developer groups")
    print("=" * 80)
    
    # Build MSN mapping
    msn_mapping = build_msn_mapping()
    
    # Merge commits
    merged_df = merge_commits(msn_mapping)
    
    if merged_df is not None:
        # Save output
        print(f"\nSaving merged commits to {OUTPUT_FILE}...")
        merged_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Saved {len(merged_df):,} commits to {OUTPUT_FILE}")
    else:
        print("Failed to merge commits - check the data structure")

if __name__ == '__main__':
    main()

