#!/usr/bin/env python3
import os
import sys
import csv
import json
import argparse
from collections import defaultdict
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
EXP3_PAIRS = os.path.join(os.path.dirname(ROOT), 'Experiment 3', 'name_email_pairs.csv')

from utils_union_find import UnionFind


def is_valid_email(email: str) -> bool:
    return isinstance(email, str) and ('@' in email)


def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        return ''
    e = email.strip().lower()
    return e if '@' in e else ''


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ''
    return name.strip().lower()


def eligible_name_for_merge(name_norm: str) -> bool:
    if not name_norm:
        return False
    if '_' in name_norm:
        return False
    tokens = name_norm.split()
    return len(tokens) >= 2


def union_all(uf: UnionFind, items):
    items = list(items)
    if len(items) <= 1:
        return 0
    base = items[0]
    made = 0
    for it in items[1:]:
        if uf.union(base, it):
            made += 1
    return made


def build_groups(uf: UnionFind, rows):
    groups = defaultdict(list)
    for idx in range(len(rows)):
        root = uf.find(idx)
        groups[root].append(idx)
    return list(groups.values())


def merge_project(project: str, pairs_csv: str, out_dir_cp: str, out_dir_reports: str):
    df = pd.read_csv(pairs_csv, dtype=str)
    df = df[df['project'] == project][['project','category','author_name','author_email']].fillna('')

    pairs_before = len(df)
    if pairs_before == 0:
        return {
            'pairs_before': 0,
            'groups_after': 0,
            'eligible_name_count': 0,
            'unique_name_count': 0,
            'unique_email_count': 0,
            'category': '',
        }

    category = df['category'].iloc[0]
    names = df['author_name'].tolist()
    emails = df['author_email'].tolist()

    name_norm = [normalize_name(n) for n in names]
    email_norm = [normalize_email(e) for e in emails]

    uf = UnionFind(pairs_before)

    # Step 1: merge by identical email (case-insensitive)
    email_to_rows = defaultdict(list)
    for i, e in enumerate(email_norm):
        if e:
            email_to_rows[e].append(i)
    for rows_list in email_to_rows.values():
        union_all(uf, rows_list)

    # Helper for name-email consistency: require BOTH name tokens to appear in email local-part
    def email_local_contains_all_name_tokens(email_raw: str, name_norm_val: str) -> bool:
        e = normalize_email(email_raw)
        if not e:
            return False
        local = e.split('@', 1)[0]
        local_lc = local.lower()
        tokens = [t for t in name_norm_val.split() if t]
        if len(tokens) < 2:
            return False
        return all(t in local_lc for t in tokens)

    # Step 2: merge by identical eligible name within project (strict)
    groups = build_groups(uf, names)
    name_to_groups = defaultdict(list)
    for grp in groups:
        # Collect eligible names present in this group
        elig_names = set()
        for i in grp:
            nn = name_norm[i]
            if eligible_name_for_merge(nn):
                elig_names.add(nn)
        # For each eligible name, only include this group if ANY email in the group matches both name tokens
        for nn in elig_names:
            if any(email_local_contains_all_name_tokens(emails[i], nn) for i in grp):
                name_to_groups[nn].append(uf.find(grp[0]))
    # Union groups sharing the same eligible name (only those that passed the email-name check)
    for grp_list in name_to_groups.values():
        roots = [uf.find(r) for r in grp_list]
        union_all(uf, roots)

    # Step 3: iterative email re-merge to convergence
    while True:
        groups = build_groups(uf, names)
        email_to_group_roots = defaultdict(list)
        for grp in groups:
            grp_root = uf.find(grp[0])
            emails_in_grp = set(e for i in grp if (e := email_norm[i]))
            for e in emails_in_grp:
                email_to_group_roots[e].append(grp_root)
        unions_made = 0
        for root_list in email_to_group_roots.values():
            roots = [uf.find(r) for r in root_list]
            unions_made += union_all(uf, roots)
        if unions_made == 0:
            break

    # Final groups
    groups = build_groups(uf, names)
    groups_after = len(groups)

    # Build outputs
    # contributors csv
    proj_out_dir = os.path.join(out_dir_cp, category.lower())
    os.makedirs(proj_out_dir, exist_ok=True)
    contrib_csv = os.path.join(proj_out_dir, f"{project}.csv")

    with open(contrib_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['group_id','project','category','names','emails','num_names','num_emails','num_pairs_merged'])
        for gi, grp in enumerate(sorted(groups, key=len, reverse=True), 1):
            orig_names = sorted(set(names[i] for i in grp if names[i]))
            orig_emails = sorted(set(emails[i] for i in grp if emails[i]))
            writer.writerow([
                f"g{gi:06d}",
                project,
                category,
                '; '.join(orig_names),
                '; '.join(orig_emails),
                len(orig_names),
                len(orig_emails),
                len(grp),
            ])

    # membership csv
    mem_csv = os.path.join(out_dir_reports, f"{project}_membership.csv")
    os.makedirs(out_dir_reports, exist_ok=True)
    with open(mem_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['row_index','author_name','author_email','group_id'])
        # map index -> group id
        idx_to_gid = {}
        for gi, grp in enumerate(sorted(groups, key=len, reverse=True), 1):
            for i in grp:
                idx_to_gid[i] = f"g{gi:06d}"
        for i in range(pairs_before):
            writer.writerow([i, names[i], emails[i], idx_to_gid[i]])

    # summary
    summary_txt = os.path.join(out_dir_reports, f"{project}_summary.txt")
    unique_name_count = len(set(n for n in names if n))
    eligible_name_count = len(set(nn for nn in name_norm if eligible_name_for_merge(nn)))
    unique_email_count = len(set(e for e in emails if e))
    reduction = 1.0 - (groups_after / pairs_before if pairs_before else 1.0)

    with open(summary_txt, 'w', encoding='utf-8') as f:
        f.write(f"project: {project}\n")
        f.write(f"category: {category}\n")
        f.write(f"pairs_before: {pairs_before}\n")
        f.write(f"groups_after: {groups_after}\n")
        f.write(f"reduction_percent: {reduction*100:.2f}%\n")
        f.write(f"unique_name_count: {unique_name_count}\n")
        f.write(f"eligible_name_count (space-only, ≥2 tokens): {eligible_name_count}\n")
        f.write(f"eligible_name_fraction: {eligible_name_count / unique_name_count if unique_name_count else 0:.4f}\n")
        f.write(f"unique_email_count: {unique_email_count}\n")

    return {
        'pairs_before': pairs_before,
        'groups_after': groups_after,
        'eligible_name_count': eligible_name_count,
        'unique_name_count': unique_name_count,
        'unique_email_count': unique_email_count,
        'category': category,
        'contrib_csv': contrib_csv,
        'membership_csv': mem_csv,
        'summary_txt': summary_txt,
    }


def pick_first_oss_project(pairs_csv: str) -> str:
    # Select first occurrence where category == 'OSS'
    for chunk in pd.read_csv(pairs_csv, dtype=str, chunksize=10000):
        for _, row in chunk.iterrows():
            if (row.get('category','') == 'OSS') and row.get('project'):
                return row['project']
    raise RuntimeError('No OSS project found in pairs CSV')


def main():
    ap = argparse.ArgumentParser(description='Per-project identity merging (email→name→email)')
    ap.add_argument('--pairs', default=EXP3_PAIRS, help='Path to Experiment 3/name_email_pairs.csv')
    ap.add_argument('--project', default='', help='Project key (owner_repo) to process; default: first OSS project in pairs')
    ap.add_argument('--out-root', default=ROOT, help='Experiment 4 root directory')
    ap.add_argument('--force', action='store_true', help='Overwrite existing outputs')
    args = ap.parse_args()

    out_cp = os.path.join(args.out_root, 'contributors_per_project')
    out_reports = os.path.join(args.out_root, 'reports')

    project = args.project or pick_first_oss_project(args.pairs)

    # Skip if outputs exist and not forced
    category_guess = 'oss'  # we will write to category based on data after reading
    out_contrib = os.path.join(out_cp, category_guess, f"{project}.csv")
    if os.path.exists(out_contrib) and not args.force:
        print(f"Outputs exist for {project}; use --force to overwrite.")
        return 0

    stats = merge_project(project, args.pairs, out_cp, out_reports)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())


