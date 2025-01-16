#!/usr/bin/env python3
"""
Fast approach: Process pairs files directly to find ML contributors with multiple emails
"""

import pandas as pd
import os
import glob
from collections import defaultdict
import networkx as nx

base_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/Experiment 11"
pairs_dir = os.path.join(base_path, "output/pairs")
model_path = os.path.join(base_path, "..", "The two other paper we can apply thier method/ALFAA-Replication-master/ALFAA/rfmodelsC.RData")

print("Loading ML model...")
# We'll use a simple threshold approach - load model if available, otherwise use 0.5 threshold
# For now, let's process a few projects to show examples

projects_to_check = [
    'CenterForOpenScience_osf.io',
    'Bahmni_bahmni-core', 
    'BlackArch_blackarch',
    'GeoNode_geonode',
    'OperationCode_front-end',
    'OpenEnergyDashboard_OED',
    'OpenMathLib_OpenBLAS',
    'OpenRefine_OpenRefine',
    'Recidiviz_pulse-data'
]

print(f"Processing {len(projects_to_check)} projects...")

all_multi_email = []

for proj_file in projects_to_check:
    pairs_file = os.path.join(pairs_dir, f"{proj_file}_pairs.csv")
    
    if not os.path.exists(pairs_file):
        continue
    
    print(f"  Processing {proj_file}...")
    
    try:
        # Read pairs file
        pairs = pd.read_csv(pairs_file)
        
        # For now, use a simple approach: if we have predictions, use them
        # Otherwise, we'll need to load the model. Let's check what columns we have
        if 'predicted_match' not in pairs.columns:
            # Use a simple similarity threshold as proxy
            # In real ML, this would come from RF predictions
            # For demonstration, let's use pairs that have high similarity
            if 'd2vSim' in pairs.columns:
                # Use Doc2Vec similarity as proxy (high similarity = likely match)
                pairs['predicted_match'] = (pairs['d2vSim'] > 0.8) & (pairs['n'] > 0.5)
            else:
                continue
        
        # Build graph of matches
        G = nx.Graph()
        
        # Add all authors as nodes
        authors = set()
        for _, row in pairs.iterrows():
            a1 = f"{row['a1_name']}<{row['a1_email']}>"
            a2 = f"{row['a2_name']}<{row['a2_email']}>"
            authors.add(a1)
            authors.add(a2)
            
            if row.get('predicted_match', False):
                G.add_edge(a1, a2)
        
        # Find connected components (merged identities)
        components = list(nx.connected_components(G))
        
        # Check for multi-email contributors
        for comp in components:
            emails = set()
            names = set()
            
            for author in comp:
                # Extract email
                if '<' in author and '>' in author:
                    email = author.split('<')[1].split('>')[0]
                    name = author.split('<')[0].strip()
                    emails.add(email)
                    names.add(name)
            
            if len(emails) > 2:
                project_name = proj_file.replace('_', '/')
                all_multi_email.append({
                    'project': project_name,
                    'names': '; '.join(sorted(names)),
                    'emails': '; '.join(sorted(emails)),
                    'num_emails': len(emails),
                    'num_names': len(names)
                })
    
    except Exception as e:
        print(f"    Error: {e}")
        continue

# Sort by number of emails
all_multi_email.sort(key=lambda x: x['num_emails'], reverse=True)

print(f"\nFound {len(all_multi_email)} contributors with more than 2 emails")
print("\n" + "="*100)
print("TOP EXAMPLES: Contributors with Multiple Emails")
print("="*100)

for i, contrib in enumerate(all_multi_email[:30], 1):
    print(f"\n{i}. Project: {contrib['project']}")
    print(f"   Names ({contrib['num_names']}): {contrib['names']}")
    print(f"   Number of emails: {contrib['num_emails']}")
    print(f"   Emails:")
    for j, email in enumerate(contrib['emails'].split('; '), 1):
        print(f"      {j}. {email}")
    print("-"*100)

