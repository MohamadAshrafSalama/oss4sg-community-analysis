#!/usr/bin/env python3
import csv
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Iterator, Dict

# Optional progress bar
try:
    from tqdm import tqdm  # type: ignore
    HAS_TQDM = True
except Exception:
    HAS_TQDM = False

BASE = Path(__file__).resolve().parent.parent
CLONES = Path(__file__).resolve().parent / "full_bare_repos"
OUT_CSV = Path(__file__).resolve().parent / "master_commits_fullfat.csv"

CATEGORIES = [
    ("oss", CLONES / "oss"),
    ("oss4sg", CLONES / "oss4sg"),
]

HEADER = [
    "category", "project", "repo_path", "commit",
    "author_name", "author_email", "date", "timezone", "message",
    "num_files", "files_changed", "total_additions", "total_deletions",
]


def ensure_header(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)


def iter_repos(cat_dir: Path) -> Iterator[Path]:
    if not cat_dir.exists():
        return iter(())
    for p in sorted(cat_dir.iterdir()):
        if p.is_dir() and p.name.endswith(".git"):
            yield p


def parse_git_log(repo: Path) -> Iterator[Dict[str, str]]:
    # Enumerate ALL reachable commits (all branches/tags)
    # Place record separator at the START of each header so numstat lines belong to the same block
    fmt = "%x1E%H%x1F%an%x1F%ae%x1F%ad%x1F%s"
    cmd = [
        "git", "-C", str(repo), "log",
        "--all", "--no-color",
        "--date=iso", "--encoding=UTF-8",
        f"--pretty=format:{fmt}", "--numstat",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    except subprocess.CalledProcessError:
        return iter(())
    text = res.stdout
    blocks = text.split("\x1E")
    for block in blocks:
        if not block.strip():
            continue
        lines = block.splitlines()
        if not lines:
            continue
        header = lines[0]
        parts = header.split("\x1F")
        if len(parts) < 5:
            continue
        commit, an, ae, dt, msg = parts[:5]
        m = re.search(r"([+-]\d{4})$", dt.strip())
        tz = m.group(1) if m else ""
        files = []
        add = 0
        dele = 0
        for ln in lines[1:]:
            p = ln.split("\t", 2)
            if len(p) != 3:
                continue
            a, d, fn = p
            files.append(fn)
            if a != "-":
                try:
                    add += int(a)
                except Exception:
                    pass
            if d != "-":
                try:
                    dele += int(d)
                except Exception:
                    pass
        yield {
            "commit": commit,
            "author_name": an,
            "author_email": ae,
            "date": dt,
            "timezone": tz,
            "message": msg,
            "num_files": str(len(files)),
            "files_changed": ";".join(files),
            "total_additions": str(add),
            "total_deletions": str(dele),
        }


def project_name_from_dir(repo_dir: Path) -> str:
    # owner_repo.git -> owner/repo
    return repo_dir.name[:-4].replace("_", "/")


def append_rows(category: str, repo_dir: Path, writer: csv.writer):
    project = project_name_from_dir(repo_dir)
    for row in parse_git_log(repo_dir):
        writer.writerow([
            category,
            project,
            str(repo_dir),
            row["commit"],
            row["author_name"],
            row["author_email"],
            row["date"],
            row["timezone"],
            row["message"],
            row["num_files"],
            row["files_changed"],
            row["total_additions"],
            row["total_deletions"],
        ])


def main():
    ensure_header(OUT_CSV)
    # Optional: process only one project (env ONLY_PROJECT="owner/repo")
    only = os.environ.get("ONLY_PROJECT", "").strip()
    # Collect repos available now
    repos = []
    for cat, cdir in CATEGORIES:
        for r in iter_repos(cdir):
            if only:
                if project_name_from_dir(r) == only:
                    repos.append((cat, r))
            else:
                repos.append((cat, r))
    if not repos:
        print("No repositories found under", CLONES)
        return 0
    iterator = tqdm(repos, desc="repos") if HAS_TQDM else repos
    with OUT_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for cat, r in iterator:
            if HAS_TQDM:
                tqdm.write(f"- {cat}: {project_name_from_dir(r)}")
            append_rows(cat, r, w)
    print(f"Wrote master CSV -> {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
