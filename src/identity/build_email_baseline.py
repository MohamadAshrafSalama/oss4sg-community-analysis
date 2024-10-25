#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = os.path.join(os.path.dirname(ROOT), 'Experiment 3', 'name_email_pairs.csv')
OUT = os.path.join(ROOT, 'contributors_email_baseline_all_projects.csv')


def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        return ''
    e = email.strip().lower()
    return e if '@' in e else ''


def main():
    df = pd.read_csv(PAIRS, dtype=str, usecols=['project','category','author_name','author_email']).fillna('')

    records = []
    # Group by project/category first
    for (project, category), dpp in df.groupby(['project','category'], sort=False):
        dpp = dpp.reset_index(drop=True)
        # Build keys: normalized email or unique row key when invalid
        keys = []
        for i, row in dpp.iterrows():
            ne = normalize_email(row['author_email'])
            if ne:
                keys.append(('email', ne))
            else:
                # keep as its own identity
                keys.append(('row', i))

        dpp = dpp.assign(_key=keys)

        # Aggregate by key
        for key, grp in dpp.groupby('_key', sort=False):
            names = sorted(set(grp['author_name'].tolist()))
            emails = sorted(set([e for e in grp['author_email'].tolist() if e]))
            records.append({
                'project': project,
                'category': category,
                'names': '; '.join(names),
                'emails': '; '.join(emails),
                'num_names': len(names),
                'num_emails': len(emails),
                'num_pairs_merged': len(grp),
            })

    out_df = pd.DataFrame(records)
    # Add a stable group_id per (project) ordering by size desc like MSN
    out_df_list = []
    for project, dproj in out_df.groupby('project', sort=False):
        dproj = dproj.copy()
        dproj = dproj.sort_values(by='num_pairs_merged', ascending=False, kind='stable')
        dproj.insert(0, 'group_id', [f"e{idx:06d}" for idx in range(1, len(dproj)+1)])
        out_df_list.append(dproj)
    final_df = pd.concat(out_df_list, ignore_index=True)
    final_df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} with {len(final_df)} rows")


if __name__ == '__main__':
    main()


