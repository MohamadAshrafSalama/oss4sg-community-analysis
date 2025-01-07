#!/usr/bin/env python3
import csv
csv.field_size_limit(10**9)
import itertools
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

BASE = Path(__file__).resolve().parent.parent
MASTER = BASE / "Experiment 10" / "master_commits_fullfat.csv"
OUTDIR = Path(__file__).resolve().parent / "output" / "pairs"
OUTDIR.mkdir(parents=True, exist_ok=True)

# --------- String similarity (Jaro-Winkler) pure Python ---------

def jaro_distance(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    s1 = s1 or ""
    s2 = s2 or ""
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    match_distance = max(len1, len2) // 2 - 1
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0
    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    transpositions //= 2
    return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0


def jaro_winkler(s1: str, s2: str, p: float = 0.1) -> float:
    d = jaro_distance(s1, s2)
    # common prefix up to 4
    prefix = 0
    for a, b in zip(s1, s2):
        if a == b:
            prefix += 1
            if prefix == 4:
                break
        else:
            break
    return d + prefix * p * (1 - d)

# --------- Helpers ---------

def normalize_name(n: str) -> str:
    return re.sub(r"\s+", " ", (n or "").strip()).lower()

def split_first_last(n: str) -> Tuple[str, str]:
    n = normalize_name(n)
    if not n:
        return "", ""
    parts = n.split(" ")
    return parts[0], parts[-1]

def email_local(e: str) -> str:
    e = (e or "").strip().lower()
    return e.split("@", 1)[0] if "@" in e else e

CAMEL_SPLIT_RE = re.compile(r"(?<!^)(?=[A-Z])|[_\-]+")

def split_camel(s: str) -> List[str]:
    s = s or ""
    s = s.replace("_", " ").replace("-", " ")
    parts = re.split(r"\W+", s)
    out = []
    for p in parts:
        if not p:
            continue
        out.extend(CAMEL_SPLIT_RE.split(p))
    return [x.lower() for x in out if x]

# Cosine similarity over bag-of-words

def cosine_counts(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a.keys()) & set(b.keys())
    num = sum(a[k] * b[k] for k in common)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)

# --------- Data aggregation ---------

def read_project_commits(project: str) -> List[Dict[str, str]]:
    commits: List[Dict[str, str]] = []
    with MASTER.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["project"] != project:
                continue
            commits.append(row)
    return commits


def aggregate_authors(commits: List[Dict[str, str]]):
    authors: Dict[str, Dict] = {}
    for row in commits:
        aid = (row["author_name"].strip(), row["author_email"].strip())
        a = authors.setdefault(aid, {
            "names": set(),
            "emails": set(),
            "files": set(),
            "tz": [],
            "messages": [],
        })
        a["names"].add(row["author_name"]) 
        a["emails"].add(row["author_email"]) 
        files = (row.get("files_changed") or "").split(";") if row.get("files_changed") else []
        for fn in files:
            fn = fn.strip()
            if fn:
                a["files"].add(fn)
        tzs = (row.get("timezone") or "").strip()
        if tzs and re.match(r"^[+-]\d{4}$", tzs):
            try:
                sign = 1 if tzs[0] == "+" else -1
                hours = int(tzs[1:3])
                mins = int(tzs[3:5])
                offset = sign * (hours + mins / 60.0)
                a["tz"].append(offset)
            except Exception:
                pass
        msg = (row.get("message") or "").strip()
        if msg:
            a["messages"].append(msg)
    return authors


def name_frequency(authors: Dict[Tuple[str, str], Dict]) -> Tuple[Dict[str, int], Dict[str, int]]:
    fn_counts: Dict[str, int] = defaultdict(int)
    ln_counts: Dict[str, int] = defaultdict(int)
    for (name, _email) in authors.keys():
        fn, ln = split_first_last(name)
        if fn:
            fn_counts[fn] += 1
        if ln:
            ln_counts[ln] += 1
    return fn_counts, ln_counts

# --------- Feature computation per pair ---------

def build_bow(texts: List[str]) -> Counter:
    tokens: List[str] = []
    for t in texts:
        tokens.extend(re.findall(r"[A-Za-z0-9_]+", t.lower()))
    return Counter(tokens)


def file_jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni else 0.0


def tz_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    ma = sorted(a)[len(a)//2]
    mb = sorted(b)[len(b)//2]
    diff = abs(ma - mb)
    return max(0.0, 1.0 - min(diff, 24.0) / 24.0)


def compute_pair_features(aid1, a1, aid2, a2, fn_counts, ln_counts):
    n1 = normalize_name(next(iter(a1["names"])) if a1["names"] else "")
    n2 = normalize_name(next(iter(a2["names"])) if a2["names"] else "")
    e1 = next(iter(a1["emails"])) if a1["emails"] else ""
    e2 = next(iter(a2["emails"])) if a2["emails"] else ""

    fn1, ln1 = split_first_last(n1)
    fn2, ln2 = split_first_last(n2)

    un1 = email_local(e1)
    un2 = email_local(e2)

    n_sim = jaro_winkler(n1, n2)
    e_sim = jaro_winkler(e1.lower(), e2.lower()) if e1 and e2 else 0.0
    ln_sim = jaro_winkler(ln1, ln2)
    fn_sim = jaro_winkler(fn1, fn2)
    un_sim = jaro_winkler(un1, un2)

    ifn_sim = max(jaro_winkler(fn1, ln2), jaro_winkler(fn2, ln1))

    ln1_tokens = " ".join(split_camel(ln1))
    ln2_tokens = " ".join(split_camel(ln2))
    fn1_tokens = " ".join(split_camel(fn1))
    fn2_tokens = " ".join(split_camel(fn2))
    ln1_sim = jaro_winkler(ln1_tokens, ln2_tokens)
    fn1_sim = jaro_winkler(fn1_tokens, fn2_tokens)

    fnf = 1.0 / fn_counts.get(fn1, 1)
    ln1f = 1.0 / ln_counts.get(ln1, 1)

    ad = file_jaccard(a1["files"], a2["files"])
    tdz = tz_similarity(a1["tz"], a2["tz"])

    bow1 = build_bow(a1["messages"]) if a1["messages"] else Counter()
    bow2 = build_bow(a2["messages"]) if a2["messages"] else Counter()
    d2vSim = cosine_counts(bow1, bow2)

    return {
        "n": n_sim, "e": e_sim, "ln": ln_sim, "fn": fn_sim, "un": un_sim,
        "ifn": ifn_sim, "ln1": ln1_sim, "fn1": fn1_sim,
        "ln1f": ln1f, "fnf": fnf,
        "ad": ad, "tdz": tdz, "d2vSim": d2vSim,
        "a1_name": n1, "a1_email": e1, "a2_name": n2, "a2_email": e2,
    }

# --------- Main pipeline per project ---------

def build_pairs_for_project(project: str, out_path: Path, max_pairs: int = 0):
    commits = read_project_commits(project)
    if not commits:
        print(f"No commits for {project}")
        return 0
    authors = aggregate_authors(commits)
    fn_counts, ln_counts = name_frequency(authors)

    author_ids = list(authors.keys())
    rows_out = 0
    with out_path.open('w', newline='', encoding='utf-8') as f:
        cols = [
            'project','id1','id2',
            'n','e','ln','fn','un','d2vSim','ad','tdz','ifn','ln1f','fnf','ln1','fn1',
            'a1_name','a1_email','a2_name','a2_email',
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for (a1_id, a2_id) in itertools.combinations(author_ids, 2):
            feats = compute_pair_features(a1_id, authors[a1_id], a2_id, authors[a2_id], fn_counts, ln_counts)
            row = {
                'project': project,
                'id1': f"{a1_id[0]} <{a1_id[1]}>",
                'id2': f"{a2_id[0]} <{a2_id[1]}>",
                **feats,
            }
            w.writerow(row)
            rows_out += 1
            if max_pairs and rows_out >= max_pairs:
                break
    print(f"WROTE {rows_out} pairs -> {out_path}")
    return rows_out


def main():
    if len(sys.argv) < 2:
        print("usage: build_pairs.py <owner/repo> [max_pairs]")
        return 2
    project = sys.argv[1]
    max_pairs = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    out_path = OUTDIR / (project.replace('/', '_') + "_pairs.csv")
    return build_pairs_for_project(project, out_path, max_pairs)

if __name__ == '__main__':
    sys.exit(main() or 0)
