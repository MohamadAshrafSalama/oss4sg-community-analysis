#!/usr/bin/env python3
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_PAIRS = os.path.join(ROOT, 'Experiment 3', 'name_email_pairs.csv')
EMAIL_BASELINE = os.path.join(ROOT, 'Experiment 4', 'contributors_email_baseline_all_projects.csv')
MSN_ALL = os.path.join(ROOT, 'Experiment 4', 'contributors_all_projects.csv')

OUT_DIR = os.path.join(ROOT, 'Experiment 6')
os.makedirs(OUT_DIR, exist_ok=True)


def norm_email(e: str) -> str:
    if not isinstance(e, str):
        return ''
    e = e.strip().lower()
    return e if '@' in e else ''


def first_semicolon(value: str) -> str:
    if not isinstance(value, str):
        return ''
    parts = [p.strip() for p in value.split(';') if p.strip()]
    return parts[0] if parts else ''


def build_df(dataset: str) -> pd.DataFrame:
    if dataset == 'raw':
        df = pd.read_csv(RAW_PAIRS, dtype=str, usecols=['project','category','author_name','author_email']).fillna('')
        df = df.rename(columns={'author_name':'name','author_email':'email'})
    elif dataset == 'email_baseline':
        df = pd.read_csv(EMAIL_BASELINE, dtype=str, usecols=['project','category','names','emails']).fillna('')
        df['name'] = df['names'].apply(first_semicolon)
        df['email'] = df['emails'].apply(first_semicolon)
        df = df[['project','category','name','email']]
    elif dataset == 'msn':
        df = pd.read_csv(MSN_ALL, dtype=str, usecols=['project','category','names','emails']).fillna('')
        df['name'] = df['names'].apply(first_semicolon)
        df['email'] = df['emails'].apply(first_semicolon)
        df = df[['project','category','name','email']]
    else:
        raise ValueError('unknown dataset')

    # normalize keys
    df['name_key'] = df['name'].astype(str).str.strip().str.lower()
    df['email_key'] = df['email'].apply(norm_email)
    return df


def metrics_for_key(df: pd.DataFrame, key_col: str) -> dict:
    # prepare unique per (key, project, category)
    slim = df[['project','category',key_col]].copy()
    slim = slim[slim[key_col] != '']
    slim = slim.drop_duplicates()

    # Intra per category: contributors active in 2+ distinct projects
    res = {}
    for cat in ['OSS','OSS4SG']:
        sub = slim[slim['category'] == cat]
        total_contributors = sub[key_col].nunique()
        prj_counts = sub.groupby(key_col)['project'].nunique()
        intra_count = int((prj_counts >= 2).sum())
        res[f'intra_{cat}_count'] = intra_count
        res[f'intra_{cat}_total'] = int(total_contributors)
        res[f'intra_{cat}_pct'] = round(100.0 * intra_count / total_contributors, 2) if total_contributors else 0.0

    # Inter (presence in both categories)
    keys_oss = set(slim[slim['category']=='OSS'][key_col].unique())
    keys_oss4 = set(slim[slim['category']=='OSS4SG'][key_col].unique())
    inter_any = len(keys_oss & keys_oss4)
    res['inter_any_count'] = int(inter_any)
    res['inter_any_pct_of_all'] = round(100.0 * inter_any / slim[key_col].nunique(), 2) if slim[key_col].nunique() else 0.0

    # Inter strict: at least 2 projects in both categories
    g = slim.groupby(['category', key_col])['project'].nunique().unstack(fill_value=0)
    if 'OSS' not in g.index: g.loc['OSS'] = 0
    if 'OSS4SG' not in g.index: g.loc['OSS4SG'] = 0
    # swap to key rows
    g2 = slim.groupby([key_col, 'category'])['project'].nunique().unstack(fill_value=0)
    strict = ((g2.get('OSS', pd.Series()) >= 2) & (g2.get('OSS4SG', pd.Series()) >= 2)).sum()
    res['inter_strict_count'] = int(strict)
    res['inter_strict_pct_of_all'] = round(100.0 * strict / slim[key_col].nunique(), 2) if slim[key_col].nunique() else 0.0
    return res


def main():
    datasets = {
        'raw': build_df('raw'),
        'email_baseline': build_df('email_baseline'),
        'msn': build_df('msn'),
    }

    rows = []
    for ds_name, df in datasets.items():
        for key_col, label in [('name_key','names_only'), ('email_key','emails_only')]:
            m = metrics_for_key(df, key_col)
            m['dataset'] = ds_name
            m['identity_basis'] = label
            m['rows_count'] = int(len(df))
            rows.append(m)

    out_csv = os.path.join(OUT_DIR, 'exp6_intra_inter_summary.csv')
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    # Write a quick markdown
    lines = [
        '# Experiment 6 — Intra/Inter by Names-only vs Emails-only (Raw vs Email-baseline vs MSN)',
        f'- Output CSV: {out_csv}',
        '',
    ]
    for r in rows:
        lines.append(f"- {r['dataset']} / {r['identity_basis']}: "
                     f"intra_OSS {r['intra_OSS_count']}/{r['intra_OSS_total']} ({r['intra_OSS_pct']}%), "
                     f"intra_OSS4SG {r['intra_OSS4SG_count']}/{r['intra_OSS4SG_total']} ({r['intra_OSS4SG_pct']}%), "
                     f"inter_any {r['inter_any_count']} ({r['inter_any_pct_of_all']}%), "
                     f"inter_strict {r['inter_strict_count']} ({r['inter_strict_pct_of_all']}%)")
    with open(os.path.join(OUT_DIR, 'README.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(out_csv)


if __name__ == '__main__':
    main()


