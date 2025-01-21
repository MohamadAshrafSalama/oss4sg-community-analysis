#!/usr/bin/env python3
"""
Process a subset of projects first to show examples quickly
"""

import pandas as pd
import subprocess
import os
import glob

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
script_path = os.path.join(base_path, "show_all_merges.R")
output_file = os.path.join(base_path, "output/ml_multi_email_subset.txt")

# Process smaller/medium projects first (skip the huge ones)
projects_to_skip = ['EbookFoundation_free-programming-books', 'Homebrew_brew']  # These are huge

pairs_dir = os.path.join(base_path, "output/pairs")
pairs_files = glob.glob(os.path.join(pairs_dir, "*_pairs.csv"))
projects = sorted([os.path.basename(f).replace("_pairs.csv", "") for f in pairs_files])

# Filter out huge projects
projects = [p for p in projects if not any(skip in p for skip in projects_to_skip)]

print(f"Processing {len(projects)} projects (skipping huge ones)...")
print()

all_multi_email = []

for i, proj_file in enumerate(projects, 1):
    project_name = proj_file.replace("_", "/")
    
    if i % 10 == 0:
        print(f"  {i}/{len(projects)} projects processed... ({len(all_multi_email)} multi-email contributors)")
    
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
                    
                    # Parse CSV
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
                        
                        email_list = [e.strip() for e in emails.split(";") if "@" in e.strip()]
                        
                        if len(email_list) > 1:
                            all_multi_email.append({
                                "project": project,
                                "contributor_id": contrib_id,
                                "names": names,
                                "emails": email_list,
                                "num_emails": len(email_list)
                            })
    except:
        pass

# Sort by number of emails
all_multi_email.sort(key=lambda x: x["num_emails"], reverse=True)

# Write to file
print(f"\nFound {len(all_multi_email)} contributors with more than 1 email")
print(f"Writing to {output_file}...")

with open(output_file, "w") as f:
    f.write("=" * 100 + "\n")
    f.write(f"ML Contributors with Multiple Emails (Subset: {len(projects)} projects)\n")
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

print(f"✓ Done! Saved to {output_file}")
print(f"\nTop 10 by email count:")
for i, contrib in enumerate(all_multi_email[:10], 1):
    print(f"  {i}. {contrib['project']}: {contrib['num_emails']} emails")

