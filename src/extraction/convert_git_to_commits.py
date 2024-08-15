#!/usr/bin/env python3
"""
Convert a bare or worktree Git repository into commits JSON/CSV with
commit, author_name, author_email, date, message.

Usage:
  python convert_git_to_commits.py /path/to/repo.git /path/to/output_base

This will create /path/to/output_base.json and /path/to/output_base.csv
"""
import os
import sys
import json
import csv
import subprocess


def extract_commits(repo_path: str):
    res = subprocess.run([
        "git", "-C", repo_path, "log",
        "--pretty=format:%H|%an|%ae|%ad|%s",
        "--date=iso"
    ], check=True, capture_output=True, text=True)
    commits = []
    for line in res.stdout.splitlines():
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append({
                "commit": parts[0],
                "author_name": parts[1],
                "author_email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })
    return commits


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_git_to_commits.py /path/to/repo(.git) /path/to/output_base")
        return 2
    repo_path = sys.argv[1]
    out_base = sys.argv[2]
    if not os.path.isdir(repo_path):
        print(f"Repo path does not exist: {repo_path}")
        return 2

    commits = extract_commits(repo_path)

    json_path = f"{out_base}.json"
    csv_path = f"{out_base}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(commits, f, ensure_ascii=False, indent=2)

    if commits:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(commits[0].keys()))
            w.writeheader()
            w.writerows(commits)

    print(f"Extracted {len(commits)} commits")
    print(f"JSON -> {json_path}")
    print(f"CSV  -> {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


