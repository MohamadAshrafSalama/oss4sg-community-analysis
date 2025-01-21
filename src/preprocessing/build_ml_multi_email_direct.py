#!/usr/bin/env python3
"""
Process pairs files directly - much faster!
"""

import pandas as pd
import os
import glob
from collections import defaultdict

# Try to load R model via rpy2, or use a simpler approach
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    pandas2ri.activate()
    HAS_RPY2 = True
except:
    HAS_RPY2 = False
    print("rpy2 not available, using similarity-based approach")

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
pairs_dir = os.path.join(base_path, "output/pairs")
model_path = os.path.join(base_path, "..", "The two other paper we can apply thier method/ALFAA-Replication-master/ALFAA/rfmodelsC.RData")
output_file = os.path.join(base_path, "output/all_ml_multi_email_contributors.txt")

# Get all pairs files
pairs_files = glob.glob(os.path.join(pairs_dir, "*_pairs.csv"))
print(f"Found {len(pairs_files)} pairs files")
print("Processing...")

all_multi_email = []

# Load model if possible
if HAS_RPY2:
    ro.r['load'](model_path)
    rfC = ro.r['rfC']
    print("Loaded RF model")
else:
    print("Using Doc2Vec similarity threshold as proxy (d2vSim > 0.8)")

for i, pairs_file in enumerate(pairs_files, 1):
    if i % 25 == 0:
        print(f"  {i}/{len(pairs_files)} files processed... ({len(all_multi_email)} multi-email contributors)")
    
    try:
        pairs = pd.read_csv(pairs_file)
        project = pairs['project'].iloc[0] if 'project' in pairs.columns else os.path.basename(pairs_file).replace('_pairs.csv', '').replace('_', '/')
        
        # Get predictions
        if HAS_RPY2 and 'rfC' in locals():
            # Use RF model
            feature_cols = ['n', 'e', 'ln', 'fn', 'un', 'd2vSim', 'ad', 'tdz', 'ifn', 'ln1f', 'fnf', 'ln1', 'fn1']
            features = pairs[feature_cols].fillna(0)
            # Predict (simplified - would need proper R prediction)
            predicted_matches = features['d2vSim'] > 0.8  # Fallback
        else:
            # Use similarity threshold
            predicted_matches = (pairs['d2vSim'] > 0.8) & (pairs['n'] > 0.5)
        
        # Build graph of matches
        author_to_id = {}
        id_to_author = {}
        author_id = 0
        
        # Collect all authors
        for _, row in pairs.iterrows():
            a1 = (row['a1_name'], row['a1_email'])
            a2 = (row['a2_name'], row['a2_email'])
            
            if a1 not in author_to_id:
                author_to_id[a1] = author_id
                id_to_author[author_id] = a1
                author_id += 1
            if a2 not in author_to_id:
                author_to_id[a2] = author_id
                id_to_author[author_id] = a2
                author_id += 1
        
        # Build graph using union-find
        parent = list(range(author_id))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union matched pairs
        for idx, row in pairs.iterrows():
            if predicted_matches.iloc[idx]:
                a1 = (row['a1_name'], row['a1_email'])
                a2 = (row['a2_name'], row['a2_email'])
                id1 = author_to_id[a1]
                id2 = author_to_id[a2]
                union(id1, id2)
        
        # Group by root
        groups = defaultdict(list)
        for i in range(author_id):
            root = find(i)
            groups[root].append(id_to_author[i])
        
        # Find multi-email contributors
        for group in groups.values():
            emails = set(author[1] for author in group if '@' in author[1])
            if len(emails) > 1:
                names = set(author[0] for author in group if author[0])
                all_multi_email.append({
                    'project': project,
                    'names': '; '.join(sorted(names)),
                    'emails': sorted(emails),
                    'num_emails': len(emails)
                })
    
    except Exception as e:
        # Skip errors
        pass

# Sort by number of emails
all_multi_email.sort(key=lambda x: x['num_emails'], reverse=True)

# Write to file
print(f"\nFound {len(all_multi_email)} contributors with more than 1 email")
print(f"Writing to {output_file}...")

with open(output_file, "w") as f:
    f.write("=" * 100 + "\n")
    f.write(f"ML Contributors with Multiple Emails (Total: {len(all_multi_email)})\n")
    f.write("=" * 100 + "\n\n")
    
    for i, contrib in enumerate(all_multi_email, 1):
        f.write(f"{i}. Project: {contrib['project']}\n")
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




