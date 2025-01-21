#!/usr/bin/env python3
"""
Build a file with all ML contributors that have more than 1 email,
sorted by number of emails (most to least)
"""

import pandas as pd
import subprocess
import os
import glob
from collections import defaultdict

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
pairs_dir = os.path.join(base_path, "output/pairs")
script_path = os.path.join(base_path, "show_all_merges.R")
output_file = os.path.join(base_path, "output/all_ml_multi_email_contributors.txt")

# Get all projects with pairs files
pairs_files = glob.glob(os.path.join(pairs_dir, "*_pairs.csv"))
projects = sorted([os.path.basename(f).replace("_pairs.csv", "") for f in pairs_files])

print(f"Found {len(projects)} projects")
print("Processing contributors...")
print()

all_multi_email = []
processed = 0

for i, proj_file in enumerate(projects, 1):
    project_name = proj_file.replace("_", "/")
    
    if i % 25 == 0:
        print(f"  Processed {i}/{len(projects)} projects... ({len(all_multi_email)} multi-email contributors found)")
    
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
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    
                    # Parse CSV line (handling quoted fields)
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
                        
                        if len(email_list) > 1:  # More than 1 email
                            all_multi_email.append({
                                "project": project,
                                "contributor_id": contrib_id,
                                "names": names,
                                "emails": email_list,
                                "num_emails": len(email_list)
                            })
    except Exception as e:
        # Skip errors, continue
        pass

# Sort by number of emails (descending)
all_multi_email.sort(key=lambda x: x["num_emails"], reverse=True)

print(f"\nDone! Found {len(all_multi_email)} contributors with more than 1 email")
print(f"Writing to {output_file}...")

# Write to file
with open(output_file, "w") as f:
    f.write("=" * 100 + "\n")
    f.write(f"ML Contributors with Multiple Emails (Total: {len(all_multi_email)})\n")
    f.write("=" * 100 + "\n\n")
    
    for i, contrib in enumerate(all_multi_email, 1):
        f.write(f"{i}. Project: {contrib['project']}\n")
        f.write(f"   Contributor ID: {contrib['contributor_id']}\n")
        f.write(f"   Names: {contrib['names']}\n")
        f.write(f"   Number of emails: {contrib['num_emails']}\n")
        f.write(f"   Emails:\n")
        for j, email in enumerate(contrib['emails'], 1):
            f.write(f"      {j}. {email}\n")
        f.write("-" * 100 + "\n")

print(f"✓ Saved to {output_file}")
print(f"\nTop 10 contributors by email count:")
for i, contrib in enumerate(all_multi_email[:10], 1):
    print(f"  {i}. {contrib['project']}: {contrib['num_emails']} emails")

