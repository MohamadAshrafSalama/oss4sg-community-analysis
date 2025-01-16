#!/usr/bin/env python3
"""
Simple approach: Use existing R-generated contributor files and find multi-email examples
"""

import pandas as pd
import subprocess
import os
import csv
import re

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
script_path = os.path.join(base_path, "show_all_merges.R")

# Process a few key projects that are likely to have interesting examples
projects_to_check = [
    'CenterForOpenScience_osf.io',
    'Bahmni_bahmni-core', 
    'BlackArch_blackarch',
    'GeoNode_geonode',
    'OperationCode_front-end',
    'OpenEnergyDashboard_OED',
    'OpenMathLib_OpenBLAS',
    'OpenRefine_OpenRefine',
    'Recidiviz_pulse-data',
    'RefugeRestrooms_refugerestrooms',
    'RoaringBitmap_RoaringBitmap'
]

print(f"Processing {len(projects_to_check)} projects...")
print()

all_multi_email = []

for proj_file in projects_to_check:
    project_name = proj_file.replace("_", "/")
    print(f"Processing {project_name}...", end=" ")
    
    try:
        result = subprocess.run(
            ["Rscript", script_path, project_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                # Parse CSV
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    
                    # Simple CSV parsing
                    parts = []
                    current = ""
                    in_quotes = False
                    for char in line:
                        if char == '"':
                            in_quotes = not in_quotes
                        elif char == "," and not in_quotes:
                            parts.append(current)
                            current = ""
                        else:
                            current += char
                    parts.append(current)
                    
                    if len(parts) >= 4:
                        project = parts[0]
                        contrib_id = parts[1]
                        names = parts[2].strip('"')
                        emails = parts[3].strip('"')
                        
                        # Count emails with @
                        email_list = [e.strip() for e in emails.split(";") if "@" in e.strip()]
                        
                        if len(email_list) > 2:
                            all_multi_email.append({
                                "project": project,
                                "contributor_id": contrib_id,
                                "names": names,
                                "emails": "; ".join(email_list),
                                "num_emails": len(email_list),
                                "email_list": email_list
                            })
                print(f"✓ Found {len([l for l in lines[1:] if l.strip()])} contributors")
            else:
                print("✗ No data")
        else:
            print(f"✗ Error")
    except Exception as e:
        print(f"✗ {str(e)[:50]}")

# Sort by number of emails
all_multi_email.sort(key=lambda x: x["num_emails"], reverse=True)

print(f"\n{'='*100}")
print(f"Found {len(all_multi_email)} contributors with more than 2 emails")
print(f"{'='*100}\n")

# Show top examples
for i, contrib in enumerate(all_multi_email[:25], 1):
    print(f"{i}. Project: {contrib['project']}")
    print(f"   Contributor ID: {contrib['contributor_id']}")
    print(f"   Names: {contrib['names']}")
    print(f"   Number of emails: {contrib['num_emails']}")
    print(f"   Emails:")
    for j, email in enumerate(contrib['email_list'], 1):
        print(f"      {j}. {email}")
    
    # Check if emails seem unrelated
    domains = [e.split("@")[1] if "@" in e else "" for e in contrib['email_list']]
    unique_domains = len(set(domains))
    if unique_domains > 2:
        print(f"   ⚠️  Interesting: {unique_domains} different domains!")
    
    print("-" * 100)

