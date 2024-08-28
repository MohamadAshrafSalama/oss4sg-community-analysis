#!/usr/bin/env python3
"""
Experiment 10: Extract commits with full data for ALFAA full fat version model

This script extracts commits with all necessary data for the full fat version
of the ALFAA machine learning model, including:
- Basic commit info (hash, author_name, author_email, date, message)
- Files changed per commit (for file similarity fingerprint)
- Diff stats (lines added/removed per commit)
- Diff content (for doc2vec text similarity fingerprint)
- Timezone information (for timezone difference fingerprint)

Usage:
    python extract_commits_full_fat.py <owner_repo> [--category oss|oss4sg]
    
Example:
    python extract_commits_full_fat.py openfarmcc/OpenFarm --category oss4sg
"""
import os
import sys
import json
import csv
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Optional progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def extract_timezone_from_date(date_str: str) -> Optional[str]:
    """Extract timezone offset from date string.
    
    Examples:
        "2024-01-16 19:51:08 +0100" -> "+0100"
        "2024-01-16 19:51:08 -0500" -> "-0500"
    """
    # Match timezone patterns like +0100, -0500, etc.
    tz_match = re.search(r'([+-]\d{4}|\w+)$', date_str.strip())
    if tz_match:
        return tz_match.group(1)
    return None


def parse_git_numstat_line(line: str) -> Tuple[Optional[int], Optional[int], str]:
    """Parse a git diff --numstat line.
    
    Format: <added> <deleted> <filename>
    Returns: (added_lines, deleted_lines, filename)
    """
    parts = line.strip().split('\t', 2)
    if len(parts) != 3:
        return None, None, ""
    
    added_str = parts[0].strip()
    deleted_str = parts[1].strip()
    filename = parts[2].strip()
    
    # Handle binary files indicated by "-"
    added = None if added_str == "-" else int(added_str)
    deleted = None if deleted_str == "-" else int(deleted_str)
    
    return added, deleted, filename


def get_commit_diff_stats(repo_path: str, commit_hash: str) -> Dict:
    """Get diff statistics for a commit.
    
    Returns:
        {
            'files_changed': [list of filenames],
            'num_files': int,
            'total_additions': int,
            'total_deletions': int,
            'additions_by_file': {filename: int},
            'deletions_by_file': {filename: int}
        }
    """
    try:
        # Get list of files changed
        res = subprocess.run([
            "git", "-C", repo_path, "diff-tree",
            "--no-commit-id", "--name-only", "-r", commit_hash
        ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        files_changed = [f.strip() for f in res.stdout.strip().splitlines() if f.strip()]
        
        # Get numstat (lines added/deleted per file)
        res_numstat = subprocess.run([
            "git", "-C", repo_path, "diff-tree",
            "--no-commit-id", "--numstat", "-r", commit_hash
        ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        total_additions = 0
        total_deletions = 0
        additions_by_file = {}
        deletions_by_file = {}
        
        for line in res_numstat.stdout.strip().splitlines():
            if not line.strip():
                continue
            added, deleted, filename = parse_git_numstat_line(line)
            if filename:
                if added is not None:
                    total_additions += added
                    additions_by_file[filename] = added
                if deleted is not None:
                    total_deletions += deleted
                    deletions_by_file[filename] = deleted
        
        return {
            'files_changed': files_changed,
            'num_files': len(files_changed),
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'additions_by_file': additions_by_file,
            'deletions_by_file': deletions_by_file
        }
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get diff stats for {commit_hash}: {e}", file=sys.stderr)
        return {
            'files_changed': [],
            'num_files': 0,
            'total_additions': 0,
            'total_deletions': 0,
            'additions_by_file': {},
            'deletions_by_file': {}
        }


def get_commit_diff_content(repo_path: str, commit_hash: str, max_size: int = 100000) -> str:
    """Get the actual diff content for a commit.
    
    This is used for doc2vec text similarity fingerprint.
    We limit the size to avoid huge diffs that might cause memory issues.
    
    Args:
        repo_path: Path to git repository
        commit_hash: Commit hash
        max_size: Maximum size of diff content in characters (default 100KB)
    
    Returns:
        Diff content as string (truncated if too large)
    """
    try:
        res = subprocess.run([
            "git", "-C", repo_path, "show",
            "--format=",  # No commit header
            commit_hash
        ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        diff_content = res.stdout
        if len(diff_content) > max_size:
            diff_content = diff_content[:max_size] + "\n[... truncated ...]"
        
        return diff_content
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get diff for {commit_hash}: {e}", file=sys.stderr)
        return ""


def extract_commits_full_fat(repo_path: str, output_base: str) -> Tuple[int, str, str]:
    """Extract commits with full data for full fat model.
    
    Args:
        repo_path: Path to git repository (bare or worktree)
        output_base: Base path for output files (without extension)
    
    Returns:
        (num_commits, json_path, csv_path)
    """
    # Get all commits with basic info
    res = subprocess.run([
        "git", "-C", repo_path, "log",
        "--pretty=format:%H|%an|%ae|%ad|%s",
        "--date=iso",
        "--encoding=UTF-8",
    ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    commits = []
    lines = res.stdout.strip().splitlines()
    
    if HAS_TQDM:
        iterator = tqdm(lines, desc="Processing commits")
    else:
        iterator = lines
        print(f"Processing {len(lines)} commits...")
    
    for idx, line in enumerate(iterator, 1):
        if not line.strip():
            continue
        
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        
        commit_hash = parts[0]
        author_name = parts[1]
        author_email = parts[2]
        date_str = parts[3]
        message = parts[4]
        
        # Extract timezone
        timezone = extract_timezone_from_date(date_str)
        
        # Get diff stats
        diff_stats = get_commit_diff_stats(repo_path, commit_hash)
        
        # Get diff content (for doc2vec)
        diff_content = get_commit_diff_content(repo_path, commit_hash)
        
        commit_data = {
            "commit": commit_hash,
            "author_name": author_name,
            "author_email": author_email,
            "date": date_str,
            "timezone": timezone,
            "message": message,
            "num_files": diff_stats['num_files'],
            "files_changed": diff_stats['files_changed'],
            "total_additions": diff_stats['total_additions'],
            "total_deletions": diff_stats['total_deletions'],
            "additions_by_file": diff_stats['additions_by_file'],
            "deletions_by_file": diff_stats['deletions_by_file'],
            "diff_content": diff_content,
            "diff_size": len(diff_content)
        }
        
        commits.append(commit_data)
        
        if not HAS_TQDM and idx % 100 == 0:
            print(f"  Processed {idx}/{len(lines)} commits...")
    
    # Write JSON
    json_path = f"{output_base}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(commits, f, ensure_ascii=False, indent=2)
    
    # Write CSV (flattened, excluding large fields)
    csv_path = f"{output_base}.csv"
    if commits:
        # For CSV, we'll create a flattened version without the large diff_content
        csv_rows = []
        for commit in commits:
            row = {
                "commit": commit["commit"],
                "author_name": commit["author_name"],
                "author_email": commit["author_email"],
                "date": commit["date"],
                "timezone": commit["timezone"],
                "message": commit["message"],
                "num_files": commit["num_files"],
                "files_changed": ";".join(commit["files_changed"]),  # Join with semicolon
                "total_additions": commit["total_additions"],
                "total_deletions": commit["total_deletions"],
                "diff_size": commit["diff_size"]
            }
            csv_rows.append(row)
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)
    
    return len(commits), json_path, csv_path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    owner_repo = sys.argv[1]
    category = "oss"
    
    # Parse category if provided
    if "--category" in sys.argv:
        idx = sys.argv.index("--category")
        if idx + 1 < len(sys.argv):
            category = sys.argv[idx + 1].lower()
    
    # Setup paths
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    
    # Determine repo path (check if bare repo exists, otherwise clone)
    bare_dir = root_dir / "Experiment 2.0" / "bare_repos" / category
    output_dir = script_dir / "output" / category
    output_dir.mkdir(parents=True, exist_ok=True)
    
    owner, repo = owner_repo.split("/")
    repo_name = f"{owner}_{repo}"
    bare_repo_path = bare_dir / f"{repo_name}.git"
    
    if not bare_repo_path.exists():
        print(f"Error: Bare repository not found at {bare_repo_path}")
        print("Please run Experiment 2.0 first to clone repositories.")
        sys.exit(1)
    
    output_base = output_dir / repo_name
    
    print(f"Extracting commits from: {owner_repo}")
    print(f"Repository: {bare_repo_path}")
    print(f"Output: {output_base}.json and {output_base}.csv")
    
    num_commits, json_path, csv_path = extract_commits_full_fat(
        str(bare_repo_path), str(output_base)
    )
    
    print(f"\nExtraction complete!")
    print(f"  Commits: {num_commits}")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")


if __name__ == "__main__":
    main()

