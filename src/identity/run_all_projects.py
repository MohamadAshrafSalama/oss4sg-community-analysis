#!/usr/bin/env python3
import os
import json
import subprocess
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = os.path.join(os.path.dirname(ROOT), 'Experiment 3', 'name_email_pairs.csv')
MERGER = os.path.join(ROOT, 'scripts', 'merge_identities.py')


def compute_email_baseline(dpp: pd.DataFrame) -> int:
    emails = dpp['author_email'].astype(str).str.strip().str.lower()
    uniq_emails = set(e for e in emails if '@' in e)
    no_at = int((emails.str.contains('@') == False).sum())
    return len(uniq_emails) + no_at


def main():
    df = pd.read_csv(PAIRS, dtype=str, usecols=['project','category','author_name','author_email']).fillna('')
    projects = df[['project','category']].drop_duplicates().values.tolist()

    results = []
    for project, category in projects:
        # Run merger for this project
        cmd = [
            'python3', MERGER,
            '--out-root', ROOT,
            '--pairs', PAIRS,
            '--project', project,
            '--force'
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        stats = json.loads(out)

        # Compute baseline
        dpp = df[df['project']==project][['author_name','author_email']]
        rows = len(dpp)
        email_baseline = compute_email_baseline(dpp)

        # Count multi-email groups in contributors CSV
        subdir = category.lower()
        contrib = os.path.join(ROOT, f'contributors_per_project/{subdir}/{project}.csv')
        multi_email_groups = 0
        if os.path.exists(contrib):
            cd = pd.read_csv(contrib)
            multi_email_groups = int((cd['num_emails'] > 1).sum())

        results.append({
            'project': project,
            'category': category,
            'rows': rows,
            'email_baseline': email_baseline,
            'msn': int(stats['groups_after']),
            'multi_email_groups': multi_email_groups,
        })

    # Write summary CSV
    rep_dir = os.path.join(ROOT, 'reports')
    os.makedirs(rep_dir, exist_ok=True)
    out_csv = os.path.join(rep_dir, 'msn_summary.csv')
    pd.DataFrame(results).to_csv(out_csv, index=False)
    print(json.dumps({'summary_csv': out_csv, 'num_projects': len(results)}, indent=2))


if __name__ == '__main__':
    main()


