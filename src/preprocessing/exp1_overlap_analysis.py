#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import pandas as pd

PATHS = [
    "/Volumes/T7/Jenny/Archive/OSS4SGprojects",
    "/Volumes/T7/Jenny/Archive/OSSprojects",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACT_SCRIPT = os.path.join(SCRIPT_DIR, "extract_commits.sh")


def check_path(path: str):
    """Return (ok, message) verifying the directory exists and is readable."""
    if not os.path.isdir(path):
        return False, f"MISSING: {path}"
    try:
        entries = os.listdir(path)
        sample = entries[:5]
        return True, f"OK: {path} (entries={len(entries)}, sample={sample})"
    except Exception as exc:
        return False, f"UNREADABLE: {path} (error={exc})"


def extract_first_oss_repo():
    """Extract commits from the first OSS repository."""
    oss_path = PATHS[1]  # OSSprojects
    
    # Get first repo
    repos = sorted([d for d in os.listdir(oss_path) 
                   if os.path.isdir(os.path.join(oss_path, d, ".git"))])
    
    if not repos:
        print("No valid git repositories found in OSS path")
        return False
    
    first_repo = repos[0]
    repo_path = os.path.join(oss_path, first_repo)
    
    print(f"\n{'='*60}")
    print(f"Extracting commits from first OSS repo: {first_repo}")
    print(f"Path: {repo_path}")
    print(f"{'='*60}\n")
    
    # Run extraction script
    try:
        subprocess.run([EXTRACT_SCRIPT, repo_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running extraction script: {e}")
        return False
    
    # Load JSON and convert to CSV
    json_file = os.path.join(SCRIPT_DIR, "result", first_repo, "commits.json")
    csv_file = os.path.join(SCRIPT_DIR, "result", first_repo, "commits.csv")
    
    if not os.path.exists(json_file):
        print(f"JSON file not found: {json_file}")
        return False
    
    print(f"\nLoading JSON from: {json_file}")
    
    with open(json_file, "r") as f:
        commits = json.load(f)
    
    print(f"Total commits found: {len(commits)}")
    
    # Convert to DataFrame and CSV
    df = pd.DataFrame(commits)
    df.to_csv(csv_file, index=False)
    
    print(f"CSV saved to: {csv_file}")
    print(f"\nFirst 5 commits:")
    print(df.head())
    
    print(f"\nColumn names:")
    print(df.columns.tolist())
    
    print(f"\nSample author data:")
    print(df[['author_name', 'author_email']].head(10))
    
    return True


def main() -> int:
    print("Step 1: Checking archive paths...")
    print("="*60)
    
    all_ok = True
    for p in PATHS:
        ok, msg = check_path(p)
        print(msg)
        all_ok = all_ok and ok
    
    if not all_ok:
        return 1
    
    print("\nStep 2: Extracting commits from first OSS repo...")
    if not extract_first_oss_repo():
        return 1
    
    print("\n" + "="*60)
    print("SUCCESS! Experiment completed.")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


