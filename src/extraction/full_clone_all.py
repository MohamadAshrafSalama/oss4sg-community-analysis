#!/usr/bin/env python3
import os
import sys
import csv
import subprocess
from pathlib import Path
from typing import List, Tuple

# Optional progress bar
try:
    from tqdm import tqdm  # type: ignore
    HAS_TQDM = True
except Exception:
    HAS_TQDM = False

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "Experiment 2.0" / "Datasets"
CSV_OSS = DATASETS / "Filtered-OSS-Project-Info.csv"
CSV_OSS4SG = DATASETS / "Filtered-OSS4SG-Project-Info.csv"
DEST_ROOT = Path(__file__).resolve().parent / "full_bare_repos"

for d in [DEST_ROOT / "oss", DEST_ROOT / "oss4sg"]:
    d.mkdir(parents=True, exist_ok=True)


def read_repo_names(csv_path: Path, limit: int | None = None) -> List[str]:
    repos: List[str] = []
    if not csv_path.exists():
        return repos
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            repos.append(name)
            if limit is not None and len(repos) >= limit:
                break
    return repos


def full_clone(owner_repo: str, dest_dir: Path) -> Tuple[bool, str, str]:
    owner, repo = owner_repo.split("/")
    bare_name = f"{owner}_{repo}.git"
    dest_path = dest_dir / bare_name
    url = f"https://github.com/{owner_repo}.git"
    if dest_path.exists():
        return True, str(dest_path), "exists"
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        # Full bare clone (no blob filtering)
        subprocess.run([
            "git", "clone", "--bare", "--progress", url, str(dest_path)
        ], check=True, text=True, env=env)
        return True, str(dest_path), "cloned"
    except subprocess.CalledProcessError as e:
        return False, str(dest_path), f"clone_failed: {e}"


def process_list(label: str, repos: List[str], dest_dir: Path):
    total = len(repos)
    print(f"\n=== {label}: {total} repos ===")
    completed = 0
    failed = 0

    iterator = tqdm(repos, total=total, desc=label) if HAS_TQDM else repos

    for owner_repo in iterator:
        ok, path, status = full_clone(owner_repo, dest_dir)
        if ok:
            completed += 1
            if HAS_TQDM:
                tqdm.write(f"✓ {owner_repo} -> {status}")
            else:
                print(f"✓ {owner_repo} -> {status}")
        else:
            failed += 1
            if HAS_TQDM:
                tqdm.write(f"✗ {owner_repo} -> {status}")
            else:
                print(f"✗ {owner_repo} -> {status}")

    print(f"{label} done: completed={completed}, failed={failed}")


def main():
    limit_env = os.environ.get("FULL_CLONE_LIMIT", "").strip()
    limit = int(limit_env) if limit_env.isdigit() and int(limit_env) > 0 else None
    which = os.environ.get("FULL_CLONE_WHICH", "both").strip().lower()  # oss|oss4sg|both

    if which in ("oss", "both"):
        repos = read_repo_names(CSV_OSS, limit=limit)
        process_list("OSS", repos, DEST_ROOT / "oss")

    if which in ("oss4sg", "both"):
        repos = read_repo_names(CSV_OSS4SG, limit=limit)
        process_list("OSS4SG", repos, DEST_ROOT / "oss4sg")


if __name__ == "__main__":
    sys.exit(main())
