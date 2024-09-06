#!/usr/bin/env python3
"""
Batch extract full-fat commit data for all projects.

This script processes all projects from Experiment 2.0 and extracts
the full-fat data needed for the ALFAA model.
"""
import os
import sys
import csv
import subprocess
import time
from pathlib import Path

# Optional progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Get script directory
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
EXP2_DIR = ROOT_DIR / "Experiment 2.0"
EXTRACT_SCRIPT = SCRIPT_DIR / "extract_commits_full_fat.py"

# CSV files with project lists
CSV_OSS = EXP2_DIR / "Datasets" / "Filtered-OSS-Project-Info.csv"
CSV_OSS4SG = EXP2_DIR / "Datasets" / "Filtered-OSS4SG-Project-Info.csv"


def read_repo_names(csv_path: Path) -> list:
    """Read repository names from CSV file."""
    repos = []
    if not csv_path.exists():
        print(f"Warning: CSV file not found: {csv_path}")
        return repos
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            repo_name = row.get("name", "").strip()
            if repo_name:
                repos.append(repo_name)
    return repos


def extract_project(owner_repo: str, category: str) -> tuple[bool, str]:
    """Extract data for a single project.
    
    Returns:
        (success, message)
    """
    try:
        cmd = [
            sys.executable,
            str(EXTRACT_SCRIPT),
            owner_repo,
            "--category",
            category
        ]
        
        # Stream child output to this terminal so tqdm/progress bars are visible
        result = subprocess.run(
            cmd,
            text=True,
            timeout=3600  # 1 hour timeout per project
        )
        
        if result.returncode == 0:
            return True, "Success"
        else:
            return False, f"Error: returncode={result.returncode}"
    
    except subprocess.TimeoutExpired:
        return False, "Timeout (exceeded 1 hour)"
    except Exception as e:
        return False, f"Exception: {str(e)[:200]}"


def process_category(label: str, repos: list, category: str):
    """Process all repositories in a category."""
    total = len(repos)
    print(f"\n{'='*60}")
    print(f"Processing {label}: {total} repositories")
    print(f"{'='*60}")
    
    if total == 0:
        print(f"No repositories found for {label}")
        return
    
    # Check which ones are already done
    output_dir = SCRIPT_DIR / "output" / category
    output_dir.mkdir(parents=True, exist_ok=True)
    
    completed = set()
    for json_file in output_dir.glob("*.json"):
        # Extract repo name from filename
        repo_name = json_file.stem
        completed.add(repo_name)
    
    remaining = [r for r in repos if f"{r.replace('/', '_')}" not in completed]
    
    if completed:
        print(f"  Already completed: {len(completed)}")
        print(f"  Remaining: {len(remaining)}")
    
    if not remaining:
        print(f"  All projects already extracted!")
        return
    
    # Process remaining projects
    iterator = tqdm(remaining, desc=label) if HAS_TQDM else remaining
    start_time = time.time()
    
    success_count = 0
    fail_count = 0
    failures = []
    
    for idx, owner_repo in enumerate(iterator, 1):
        if not HAS_TQDM:
            elapsed = time.time() - start_time
            avg = elapsed / idx if idx > 0 else 0
            remaining_time = avg * (len(remaining) - idx)
            print(f"[{label}] {idx}/{len(remaining)} - {owner_repo} "
                  f"(ETA: {int(remaining_time//60)}m {int(remaining_time%60)}s)")
        
        success, message = extract_project(owner_repo, category)
        
        if success:
            success_count += 1
            if HAS_TQDM:
                tqdm.write(f"✓ {owner_repo}")
        else:
            fail_count += 1
            failures.append((owner_repo, message))
            if HAS_TQDM:
                tqdm.write(f"✗ {owner_repo}: {message}")
            else:
                print(f"  ✗ Failed: {message}")
    
    # Summary
    print(f"\n{label} Summary:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    
    if failures:
        print(f"\nFailed projects:")
        for repo, msg in failures[:10]:  # Show first 10 failures
            print(f"  - {repo}: {msg}")
        if len(failures) > 10:
            print(f"  ... and {len(failures) - 10} more")


def main():
    """Main entry point."""
    print("="*60)
    print("Batch Extract Full-Fat Commit Data")
    print("="*60)
    
    # Check if extract script exists
    if not EXTRACT_SCRIPT.exists():
        print(f"Error: Extract script not found at {EXTRACT_SCRIPT}")
        sys.exit(1)
    
    # Check if CSV files exist
    if not CSV_OSS.exists() and not CSV_OSS4SG.exists():
        print("Error: No project CSV files found")
        sys.exit(1)
    
    # Process OSS projects
    if CSV_OSS.exists():
        repos_oss = read_repo_names(CSV_OSS)
        if repos_oss:
            process_category("OSS", repos_oss, "oss")
    
    # Process OSS4SG projects
    if CSV_OSS4SG.exists():
        repos_oss4sg = read_repo_names(CSV_OSS4SG)
        if repos_oss4sg:
            process_category("OSS4SG", repos_oss4sg, "oss4sg")
    
    print("\n" + "="*60)
    print("Batch extraction complete!")
    print("="*60)


if __name__ == "__main__":
    main()

