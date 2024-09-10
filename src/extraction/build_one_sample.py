#!/usr/bin/env python3
import csv
import re
import subprocess
import sys
from pathlib import Path

USAGE = "usage: build_one_sample.py <repo_path> <project_name> [out_csv] [limit]"

def main():
    if len(sys.argv) < 3:
        print(USAGE)
        return 2
    repo = Path(sys.argv[1])
    project = sys.argv[2]
    out_csv = Path(sys.argv[3]) if len(sys.argv) >= 4 else Path(__file__).resolve().parent / "output" / "sample" / f"{project.replace('/', '_')}_sample.csv"
    limit = int(sys.argv[4]) if len(sys.argv) >= 5 else 200
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # Put record separator at the start so numstat lines belong to the same block
    fmt = "%x1E%H\x1F%an\x1F%ae\x1F%ad\x1F%s"
    cmd = [
        "git","-C",str(repo),"log","--date=iso","--encoding=UTF-8","--no-merges",f"--pretty=format:{fmt}","--numstat"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)

    rows = []
    for block in res.stdout.split("\x1E"):
        if not block.strip():
            continue
        lines = block.splitlines()
        if not lines:
            continue
        parts = lines[0].split("\x1F")
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
        if not files:
            continue
        rows.append({
            'project': project,
            'repo_path': str(repo),
            'commit': commit,
            'author_name': an,
            'author_email': ae,
            'date': dt,
            'timezone': tz,
            'message': msg,
            'num_files': len(files),
            'files_changed': ';'.join(files),
            'total_additions': add,
            'total_deletions': dele,
        })
        if len(rows) >= limit:
            break

    if not rows:
        print("No commits with file changes found.")
        return 0

    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"WROTE {len(rows)} rows -> {out_csv}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
