#!/usr/bin/env python3
"""
Process ALL projects with the full-fat ALFAA model.
For each project:
1. Build pairwise features (EXACT replication)
2. Run the RF model
3. Report 3 counts: distinct (name,email), baseline (email), full-fat model
"""
import csv
import subprocess
from pathlib import Path
from collections import defaultdict

BASE = Path("/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements")
MASTER_CSV = BASE / "Experiment 10" / "master_commits_fullfat.csv"
PAIRS_DIR = BASE / "Experiment 11" / "output" / "pairs"
RESULTS_CSV = BASE / "Experiment 11" / "output" / "all_projects_results.csv"

# Import the build_pairs function
import sys
sys.path.insert(0, str(BASE / "Experiment 11"))
from build_pairs_EXACT import build_pairs_for_project

def get_all_projects(master_csv: Path) -> list:
    """Get list of all unique projects in the master CSV."""
    projects = set()
    with master_csv.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            project = row.get('project', '').strip()
            if project:
                projects.add(project)
    return sorted(list(projects))


def run_rf_model_on_project(pairs_csv: Path) -> dict:
    """Run the RF model on a pairs CSV and return the 3 counts."""
    r_script = BASE / "Experiment 11" / "run_fullfat_simple.R"
    
    # Create a simple R script that returns just the 3 numbers
    r_code = f"""
library(randomForest, quietly=TRUE)
library(igraph, quietly=TRUE)
suppressMessages({{

base_path <- "{BASE}"
model_path <- file.path(base_path, "The two other paper we can apply thier method/ALFAA-Replication-master/ALFAA/rfmodelsC.RData")
pairs_path <- "{pairs_csv}"

load(model_path)
pairs_data <- read.csv(pairs_path, stringsAsFactors=FALSE)

# Count 1: Distinct (name,email)
authors <- unique(c(
    paste0(pairs_data$a1_name, "<", pairs_data$a1_email, ">"),
    paste0(pairs_data$a2_name, "<", pairs_data$a2_email, ">")
))
count1 <- length(authors)

# Count 2: Baseline (unique emails)
all_emails <- c(pairs_data$a1_email, pairs_data$a2_email)
count2 <- length(unique(all_emails))

# Count 3: Full-fat model
feature_cols <- c("n", "e", "ln", "fn", "un", "d2vSim", "ad", "tdz", "ifn", "ln1f", "fnf", "ln1", "fn1")
features <- pairs_data[, feature_cols]
features[is.na(features)] <- 0

predictions <- matrix(0, nrow=nrow(features), ncol=length(rfC))
for (i in 1:length(rfC)) {{
    pred <- predict(rfC[[i]], features, type="prob")
    predictions[, i] <- pred[, 2]
}}
avg_predictions <- rowMeans(predictions)
predicted_matches <- avg_predictions > 0.5

author_to_id <- setNames(1:length(authors), authors)
a1_ids <- author_to_id[paste0(pairs_data$a1_name, "<", pairs_data$a1_email, ">")]
a2_ids <- author_to_id[paste0(pairs_data$a2_name, "<", pairs_data$a2_email, ">")]

g <- make_empty_graph(n=length(authors), directed=FALSE)
match_idx <- which(predicted_matches)
if (length(match_idx) > 0) {{
    edges_to_add <- as.vector(t(cbind(a1_ids[match_idx], a2_ids[match_idx])))
    g <- add_edges(g, edges_to_add)
    g <- simplify(g, remove.multiple=TRUE, remove.loops=TRUE)
}}

components <- components(g, mode="weak")
count3 <- components$no

cat(count1, count2, count3, sep=",")
}})
"""
    
    # Run R script
    result = subprocess.run(
        ['Rscript', '-e', r_code],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout per project
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"R script failed: {result.stderr}")
    
    # Parse output (last line with 3 numbers)
    output_lines = [line for line in result.stdout.strip().split('\n') if line]
    last_line = output_lines[-1] if output_lines else ""
    
    try:
        parts = last_line.split(',')
        return {
            'distinct_name_email': int(parts[0]),
            'baseline_email': int(parts[1]),
            'fullfat_model': int(parts[2])
        }
    except (ValueError, IndexError) as e:
        raise RuntimeError(f"Failed to parse R output: {last_line}\nFull output: {result.stdout}")


def main():
    print("="*80)
    print("PROCESSING ALL PROJECTS WITH FULL-FAT ALFAA MODEL")
    print("="*80)
    
    # Get all projects
    print(f"\nReading projects from: {MASTER_CSV}")
    projects = get_all_projects(MASTER_CSV)
    print(f"Found {len(projects)} projects")
    
    # Process each project
    results = []
    
    for i, project in enumerate(projects, 1):
        print(f"\n[{i}/{len(projects)}] Processing: {project}")
        
        try:
            # Build pairs
            pairs_path = PAIRS_DIR / f"{project.replace('/', '_')}_pairs.csv"
            
            if not pairs_path.exists():
                print(f"  → Building pairwise features...")
                build_pairs_for_project(project, MASTER_CSV, pairs_path)
            else:
                print(f"  → Using existing pairs file")
            
            # Run RF model
            print(f"  → Running full-fat model...")
            counts = run_rf_model_on_project(pairs_path)
            
            print(f"  → Results:")
            print(f"      Distinct (name,email): {counts['distinct_name_email']}")
            print(f"      Baseline (email):      {counts['baseline_email']}")
            print(f"      Full-fat model:        {counts['fullfat_model']}")
            
            results.append({
                'project': project,
                'distinct_name_email': counts['distinct_name_email'],
                'baseline_email': counts['baseline_email'],
                'fullfat_model': counts['fullfat_model'],
                'baseline_reduction': counts['distinct_name_email'] - counts['baseline_email'],
                'fullfat_additional': counts['baseline_email'] - counts['fullfat_model'],
                'total_reduction': counts['distinct_name_email'] - counts['fullfat_model']
            })
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                'project': project,
                'distinct_name_email': 'ERROR',
                'baseline_email': 'ERROR',
                'fullfat_model': 'ERROR',
                'baseline_reduction': 'ERROR',
                'fullfat_additional': 'ERROR',
                'total_reduction': 'ERROR'
            })
    
    # Write results
    print(f"\n{'='*80}")
    print("Writing results to CSV...")
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    with RESULTS_CSV.open('w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'project', 'distinct_name_email', 'baseline_email', 'fullfat_model',
            'baseline_reduction', 'fullfat_additional', 'total_reduction'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Results saved to: {RESULTS_CSV}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

