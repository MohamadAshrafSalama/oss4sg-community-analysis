#!/usr/bin/env python3
"""
Script to test bare cloning and commit extraction for the first OSS4SG repo.
"""
import os
import subprocess
import json
import csv
import sys

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OSS4SG_CSV = os.path.join(SCRIPT_DIR, "Datasets", "Filtered-OSS4SG-Project-Info.csv")
BARE_REPOS_DIR = os.path.join(SCRIPT_DIR, "bare_repos")
RESULT_DIR = os.path.join(SCRIPT_DIR, "result")

# Create directories
os.makedirs(BARE_REPOS_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

print("=" * 80)
print("STEP 1: Reading first 2 rows from CSV to understand data structure")
print("=" * 80)

# Read first project from CSV
with open(OSS4SG_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)[:2]
    
    print(f"\nFound {len(rows)} data rows")
    print("\nFirst 2 rows:")
    for i, row in enumerate(rows, 1):
        print(f"\n  Row {i}:")
        print(f"    name: {row['name']}")
        print(f"    language: {row.get('language', 'N/A')}")
        print(f"    numCommits: {row.get('numCommits', 'N/A')}")

first_repo = rows[0]['name']
repo_owner, repo_name = first_repo.split('/')
bare_repo_name = f"{repo_owner}_{repo_name}.git"
bare_repo_path = os.path.join(BARE_REPOS_DIR, bare_repo_name)
github_url = f"https://github.com/{first_repo}.git"

print("\n" + "=" * 80)
print("STEP 2: Bare cloning the first OSS4SG project")
print("=" * 80)
print(f"\nProject: {first_repo}")
print(f"GitHub URL: {github_url}")
print(f"Destination: {bare_repo_path}")

# Clone bare repository with blob filter
print("\nCloning (this may take a moment)...")
try:
    subprocess.run([
        "git", "clone", "--bare", "--filter=blob:none", 
        github_url, bare_repo_path
    ], check=True, capture_output=True, text=True)
    print(f"✓ Successfully cloned to: {bare_repo_path}")
except subprocess.CalledProcessError as e:
    print(f"✗ Clone failed: {e}")
    print(f"STDERR: {e.stderr}")
    sys.exit(1)

print("\n" + "=" * 80)
print("STEP 3: Extracting ALL commits to JSON")
print("=" * 80)

# Extract commits using git log
output_json = os.path.join(RESULT_DIR, f"{repo_owner}_{repo_name}.json")
print(f"Output JSON: {output_json}")

try:
    result = subprocess.run([
        "git", "-C", bare_repo_path, "log",
        "--pretty=format:%H|%an|%ae|%ad|%s",
        "--date=iso"
    ], check=True, capture_output=True, text=True)
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|', 4)
            if len(parts) == 5:
                commits.append({
                    "commit": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(commits, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Extracted {len(commits)} commits")
    
except subprocess.CalledProcessError as e:
    print(f"✗ Extraction failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("STEP 4: Converting JSON to CSV")
print("=" * 80)

output_csv = os.path.join(RESULT_DIR, f"{repo_owner}_{repo_name}.csv")
print(f"Output CSV: {output_csv}")

with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    if commits:
        writer = csv.DictWriter(f, fieldnames=commits[0].keys())
        writer.writeheader()
        writer.writerows(commits)
        print(f"✓ CSV created with {len(commits)} rows")

print("\n" + "=" * 80)
print("STEP 5: RESULTS")
print("=" * 80)

print(f"\n✓ Bare repository: {bare_repo_path}")
print(f"✓ JSON file: {output_json}")
print(f"✓ CSV file: {output_csv}")
print(f"\nTotal commits extracted: {len(commits)}")

print("\nFirst 5 commits:")
print("-" * 80)
for i, commit in enumerate(commits[:5], 1):
    print(f"\n{i}. Commit: {commit['commit'][:12]}")
    print(f"   Author: {commit['author_name']} <{commit['author_email']}>")
    print(f"   Date: {commit['date']}")
    print(f"   Message: {commit['message'][:60]}...")

print("\n" + "=" * 80)
print("SUCCESS! Everything worked perfectly.")
print("=" * 80)

