#!/usr/bin/env python3
"""
Show examples of how MSN method merges contributors with multiple emails
that the Email-based method keeps separate.
"""

import pandas as pd

# Read the datasets
msn = pd.read_csv('03_msn_method.csv')
email = pd.read_csv('02_email_baseline_method.csv')

print('='*100)
print('EXAMPLES: MSN Method Merging Multiple Emails for Same Contributor')
print('='*100)
print()
print('These examples show how MSN identifies that different emails belong')
print('to the same person, while Email-based method treats them as separate.')
print()

# Find MSN groups with multiple emails, sorted by number of emails
msn_multi_email = msn[msn['num_emails'] > 1].copy()
msn_multi_email = msn_multi_email.sort_values('num_emails', ascending=False)

# Example 1: Mark Johnson from moodle_moodle
print('='*100)
print('EXAMPLE 1: Mark Johnson (moodle_moodle)')
print('='*100)

# Find the Mark Johnson entry
msn_mark = msn_multi_email[msn_multi_email['names'].str.contains('Mark Johnson', case=False, na=False) & 
                           (msn_multi_email['project'] == 'moodle_moodle')].iloc[0]

print('\nMSN Method - ONE contributor group:')
print(f"  Group ID: {msn_mark['group_id']}")
print(f"  Name: {msn_mark['names']}")
print(f"  Number of emails merged: {msn_mark['num_emails']}")
print(f"  Emails:")
for i, email_addr in enumerate(msn_mark['emails'].split(';'), 1):
    print(f"    {i}. {email_addr.strip()}")

# Find corresponding entries in email method
email_list = [e.strip() for e in msn_mark['emails'].split(';')]
email_mark = email[(email['project'] == 'moodle_moodle') & 
                   (email['emails'].isin(email_list))].sort_values('group_id')

print('\nEmail-Based Method - SEPARATE contributor groups:')
for idx, row in email_mark.iterrows():
    print(f"  Group ID: {row['group_id']}")
    print(f"  Name: {row['names']}")
    print(f"  Email: {row['emails']}")
    print()

print(f"Result: Email method has {len(email_mark)} separate contributors")
print(f"        MSN method merges them into 1 contributor")
print(f"        Difference: {len(email_mark) - 1} extra contributors in Email method")

# Example 2: Antoine Augusti
print('\n' + '='*100)
print('EXAMPLE 2: Antoine Augusti (betagouv_api.gouv.fr)')
print('='*100)

msn_antoine = msn_multi_email[msn_multi_email['names'].str.contains('Antoine Augusti', case=False, na=False) & 
                              (msn_multi_email['project'] == 'betagouv_api.gouv.fr')].iloc[0]

print('\nMSN Method - ONE contributor group:')
print(f"  Group ID: {msn_antoine['group_id']}")
print(f"  Name: {msn_antoine['names']}")
print(f"  Number of emails merged: {msn_antoine['num_emails']}")
print(f"  Emails:")
for i, email_addr in enumerate(msn_antoine['emails'].split(';'), 1):
    print(f"    {i}. {email_addr.strip()}")

email_list = [e.strip() for e in msn_antoine['emails'].split(';')]
email_antoine = email[(email['project'] == 'betagouv_api.gouv.fr') & 
                      (email['emails'].isin(email_list))].sort_values('group_id')

print('\nEmail-Based Method - SEPARATE contributor groups:')
for idx, row in email_antoine.iterrows():
    print(f"  Group ID: {row['group_id']}")
    print(f"  Name: {row['names']}")
    print(f"  Email: {row['emails']}")
    print()

print(f"Result: Email method has {len(email_antoine)} separate contributors")
print(f"        MSN method merges them into 1 contributor")
print(f"        Difference: {len(email_antoine) - 1} extra contributors in Email method")

# Example 3: Sam Voss
print('\n' + '='*100)
print('EXAMPLE 3: Sam Voss (buildroot_buildroot)')
print('='*100)

msn_sam = msn_multi_email[msn_multi_email['names'].str.contains('Sam Voss', case=False, na=False) & 
                          (msn_multi_email['project'] == 'buildroot_buildroot')].iloc[0]

print('\nMSN Method - ONE contributor group:')
print(f"  Group ID: {msn_sam['group_id']}")
print(f"  Name: {msn_sam['names']}")
print(f"  Number of emails merged: {msn_sam['num_emails']}")
print(f"  Emails:")
for i, email_addr in enumerate(msn_sam['emails'].split(';'), 1):
    print(f"    {i}. {email_addr.strip()}")

email_list = [e.strip() for e in msn_sam['emails'].split(';')]
email_sam = email[(email['project'] == 'buildroot_buildroot') & 
                 (email['emails'].isin(email_list))].sort_values('group_id')

print('\nEmail-Based Method - SEPARATE contributor groups:')
for idx, row in email_sam.iterrows():
    print(f"  Group ID: {row['group_id']}")
    print(f"  Name: {row['names']}")
    print(f"  Email: {row['emails']}")
    print()

print(f"Result: Email method has {len(email_sam)} separate contributors")
print(f"        MSN method merges them into 1 contributor")
print(f"        Difference: {len(email_sam) - 1} extra contributors in Email method")

# Example 4: Christopher Riedel (most emails - 6)
print('\n' + '='*100)
print('EXAMPLE 4: Christopher Riedel (SORMAS-Foundation_SORMAS-Project) - 6 Emails!')
print('='*100)

msn_chris = msn_multi_email[(msn_multi_email['project'] == 'SORMAS-Foundation_SORMAS-Project') & 
                            (msn_multi_email['num_emails'] == 6)].iloc[0]

print('\nMSN Method - ONE contributor group:')
print(f"  Group ID: {msn_chris['group_id']}")
print(f"  Name: {msn_chris['names']}")
print(f"  Number of emails merged: {msn_chris['num_emails']}")
print(f"  Emails:")
for i, email_addr in enumerate(msn_chris['emails'].split(';'), 1):
    print(f"    {i}. {email_addr.strip()}")

email_list = [e.strip() for e in msn_chris['emails'].split(';')]
email_chris = email[(email['project'] == 'SORMAS-Foundation_SORMAS-Project') & 
                    (email['emails'].isin(email_list))].sort_values('group_id')

print('\nEmail-Based Method - SEPARATE contributor groups:')
for idx, row in email_chris.iterrows():
    print(f"  Group ID: {row['group_id']}")
    print(f"  Name: {row['names']}")
    print(f"  Email: {row['emails']}")
    print()

print(f"Result: Email method has {len(email_chris)} separate contributors")
print(f"        MSN method merges them into 1 contributor")
print(f"        Difference: {len(email_chris) - 1} extra contributors in Email method")

# Summary statistics
print('\n' + '='*100)
print('SUMMARY STATISTICS')
print('='*100)
print(f"\nTotal MSN groups with multiple emails: {len(msn_multi_email):,}")
print(f"Total MSN groups: {len(msn):,}")
print(f"Percentage with multiple emails: {len(msn_multi_email)/len(msn)*100:.2f}%")
print(f"\nDistribution of number of emails per MSN group:")
email_counts = msn_multi_email['num_emails'].value_counts().sort_index()
for num_emails, count in email_counts.items():
    print(f"  {num_emails} emails: {count} groups")

