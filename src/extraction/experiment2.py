#!/usr/bin/env python3
import os
import sys
import csv
import json
import subprocess
import time
from typing import List, Tuple

# Optional progress bar
try:
    from tqdm import tqdm  # type: ignore
    HAS_TQDM = True
except Exception:
    HAS_TQDM = False

ROOT = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.join(ROOT, "Datasets")

CSV_OSS = os.path.join(DATASETS, "Filtered-OSS-Project-Info.csv")
CSV_OSS4SG = os.path.join(DATASETS, "Filtered-OSS4SG-Project-Info.csv")

BARE_DIR_OSS = os.path.join(ROOT, "bare_repos", "oss")
BARE_DIR_OSS4SG = os.path.join(ROOT, "bare_repos", "oss4sg")
PRISM_DIR_OSS = os.path.join(ROOT, "prism", "oss")
PRISM_DIR_OSS4SG = os.path.join(ROOT, "prism", "oss4sg")

for d in [BARE_DIR_OSS, BARE_DIR_OSS4SG, PRISM_DIR_OSS, PRISM_DIR_OSS4SG]:
    os.makedirs(d, exist_ok=True)


def read_repo_names(csv_path: str, limit: int | None = None) -> List[str]:
    repos: List[str] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            repos.append(row["name"])  # e.g., owner/repo
            if limit is not None and len(repos) >= limit:
                break
    return repos


def bare_clone(owner_repo: str, dest_dir: str) -> Tuple[bool, str, str]:
    owner, repo = owner_repo.split("/")
    bare_name = f"{owner}_{repo}.git"
    dest_path = os.path.join(dest_dir, bare_name)
    url = f"https://github.com/{owner_repo}.git"
    try:
        if not os.path.exists(dest_path):
            subprocess.run(["git", "clone", "--bare", "--filter=blob:none", url, dest_path],
                           check=True, capture_output=True, text=True)
        return True, dest_path, bare_name
    except subprocess.CalledProcessError as e:
        print(f"Clone failed for {owner_repo}: {e}")
        print(e.stderr)
        return False, "", ""


def extract_commits_to_json_csv(bare_repo_path: str, out_base: str) -> Tuple[int, str, str]:
    json_path = f"{out_base}.json"
    csv_path = f"{out_base}.csv"
    # git log pipe
    res = subprocess.run([
        "git", "-C", bare_repo_path, "log",
        "--pretty=format:%H|%an|%ae|%ad|%s",
        "--date=iso",
        "--encoding=UTF-8",
    ], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(commits, f, ensure_ascii=False, indent=2)
    if commits:
        import csv as _csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=list(commits[0].keys()))
            w.writeheader()
            w.writerows(commits)
    return len(commits), json_path, csv_path


def process_list(label: str, repos: List[str], bare_dir: str, prism_dir: str):
    total = len(repos)
    print(f"\n=== Processing {label}: {total} repos ===")

    iterator = tqdm(repos, total=total, desc=label) if HAS_TQDM else repos
    start_time = time.time()

    for idx, owner_repo in enumerate(iterator, 1):
        owner, repo = owner_repo.split("/")
        safe_name = f"{owner}_{repo}"

        if not HAS_TQDM:
            elapsed = time.time() - start_time
            avg = elapsed / idx
            remaining = avg * (total - idx)
            print(f"[{label}] {idx}/{total} - {owner_repo} (ETA: {int(remaining//60)}m {int(remaining%60)}s)")

        ok, bare_path, _ = bare_clone(owner_repo, bare_dir)
        if not ok:
            continue
        out_base = os.path.join(prism_dir, safe_name)
        # Skip if outputs already exist
        if os.path.exists(out_base + ".json") and os.path.exists(out_base + ".csv"):
            if HAS_TQDM:
                tqdm.write(f"- {owner_repo}: skip (outputs exist)")
            else:
                print(f"- {owner_repo}: skip (outputs exist)")
            continue
        count, json_path, csv_path = extract_commits_to_json_csv(bare_path, out_base)
        if HAS_TQDM:
            tqdm.write(f"- {owner_repo}: {count} commits -> JSON: {json_path}, CSV: {csv_path}")
        else:
            print(f"- {owner_repo}: {count} commits -> JSON: {json_path}, CSV: {csv_path}")


def main():
    # Defaults: run BOTH lists with no limit (will ask user before large runs)
    limit_env = os.environ.get("EXP2_LIMIT", "")
    limit = int(limit_env) if limit_env.strip().isdigit() and int(limit_env) > 0 else None
    which = os.environ.get("EXP2_WHICH", "both")  # oss | oss4sg | both

    if which in ("oss", "both"):
        repos = read_repo_names(CSV_OSS, limit=limit)
        process_list("OSS", repos, BARE_DIR_OSS, PRISM_DIR_OSS)
    if which in ("oss4sg", "both"):
        repos = read_repo_names(CSV_OSS4SG, limit=limit)
        process_list("OSS4SG", repos, BARE_DIR_OSS4SG, PRISM_DIR_OSS4SG)


if __name__ == "__main__":
    sys.exit(main())


