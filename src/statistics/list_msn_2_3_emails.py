#!/usr/bin/env python3
"""
List all MSN contributors with exactly 2 or 3 emails (showing only emails with @)
"""

import pandas as pd

# Read MSN dataset
msn = pd.read_csv('03_msn_method.csv')

# Filter for contributors with 2 or 3 emails
msn_2_3_emails = msn[msn['num_emails'].isin([2, 3])].copy()

# Sort by number of emails, then by project
msn_2_3_emails = msn_2_3_emails.sort_values(['num_emails', 'project'], ascending=[False, True])

# Open output file
with open('msn_contributors_2_3_emails.txt', 'w') as f:
    f.write('='*100 + '\n')
    f.write(f'MSN Contributors with 2 or 3 Emails (Total: {len(msn_2_3_emails)})\n')
    f.write('='*100 + '\n\n')
    
    count = 0
    for idx, row in msn_2_3_emails.iterrows():
        emails = [e.strip() for e in row['emails'].split(';')]
        # Filter emails that contain @
        emails_with_at = [e for e in emails if '@' in e]
        
        if len(emails_with_at) >= 2:  # Only show if at least 2 emails have @
            count += 1
            f.write(f'{count}. Project: {row["project"]}\n')
            f.write(f'   Name: {row["names"]}\n')
            f.write(f'   Number of emails: {row["num_emails"]}\n')
            f.write(f'   Emails:\n')
            for i, email in enumerate(emails_with_at, 1):
                f.write(f'      {i}. {email}\n')
            f.write('-'*100 + '\n')

print(f'Done! Found {count} contributors with 2 or 3 emails (with @ sign)')
print(f'Results saved to: msn_contributors_2_3_emails.txt')

