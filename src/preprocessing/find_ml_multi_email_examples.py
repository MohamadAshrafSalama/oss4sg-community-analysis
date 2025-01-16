#!/usr/bin/env python3
"""
Find ML contributors with more than 2 emails and show interesting examples
where emails that seem unrelated are merged together.
"""

import pandas as pd
import subprocess
import os
import glob
import re

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
pairs_dir = os.path.join(base_path, "output/pairs")
script_path = os.path.join(base_path, "show_all_merges.R")
output_file = os.path.join(base_path, "output/all_ml_contributors.csv")

# Get all projects with pairs files
pairs_files = glob.glob(os.path.join(pairs_dir, "*_pairs.csv"))
projects = sorted([os.path.basename(f).replace("_pairs.csv", "") for f in pairs_files])

print(f"Found {len(projects)} projects with ML pairs data")
print("Generating contributor identities...")
print()

all_contributors = []

# Process each project
for i, proj_file in enumerate(projects, 1):
    project_name = proj_file.replace("_", "/")
    
    if i % 50 == 0:
        print(f"Processing {i}/{len(projects)}: {project_name}...")
    
    try:
        result = subprocess.run(
            ["Rscript", script_path, project_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        all_contributors.append(line)
        # else:
        #     print(f"  Warning: {project_name} failed")
    except Exception as e:
        print(f"  Error processing {project_name}: {e}")

# Save all contributors
print(f"\nGenerated {len(all_contributors)} contributor records")
print(f"Saving to {output_file}...")

with open(output_file, "w") as f:
    f.write("project,unique_contributor_id,all_names,all_emails\n")
    for line in all_contributors:
        f.write(line + "\n")

print("Done!")

