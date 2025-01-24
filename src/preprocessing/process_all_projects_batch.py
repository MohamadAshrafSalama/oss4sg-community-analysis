#!/usr/bin/env python3
"""
Process ALL projects with the full-fat ALFAA model (with batch processing & resume capability).
"""
import csv
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE = Path("/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements")
MASTER_CSV = BASE / "Experiment 10" / "master_commits_fullfat.csv"
PAIRS_DIR = BASE / "Experiment 11" / "output" / "pairs"
RESULTS_CSV = BASE / "Experiment 11" / "output" / "all_projects_results.csv"
PROGRESS_FILE = BASE / "Experiment 11" / "output" / "progress.txt"

# Import the build_pairs function
sys.path.insert(0, str(BASE / "Experiment 11"))
from build_pairs_EXACT import build_pairs_for_project

def log(msg):
    """Print with timestamp and flush immediately."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


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


def get_completed_projects() -> set:
    """Get set of already completed projects."""
    if not RESULTS_CSV.exists():
        return set()
    
    completed = set()
    with RESULTS_CSV.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('fullfat_model') not in ['', 'ERROR']:
                completed.add(row['project'])
    return completed


def run_rf_model_on_project(pairs_csv: Path) -> dict:
    """Run the RF model on a pairs CSV and return the 3 counts."""
    r_code = f"""
library(randomForest, quietly=TRUE, warn.conflicts=FALSE)
library(igraph, quietly=TRUE, warn.conflicts=FALSE)
suppressMessages({{

base_path <- "{BASE}"
model_path <- file.path(base_path, "The two other paper we can apply thier method/ALFAA-Replication-master/ALFAA/rfmodelsC.RData")
pairs_path <- "{pairs_csv}"

load(model_path)
pairs_data <- read.csv(pairs_path, stringsAsFactors=FALSE)

authors <- unique(c(paste0(pairs_data$a1_name, "<", pairs_data$a1_email, ">"),
                    paste0(pairs_data$a2_name, "<", pairs_data$a2_email, ">")))
count1 <- length(authors)

all_emails <- c(pairs_data$a1_email, pairs_data$a2_email)
count2 <- length(unique(all_emails))

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
    
    result = subprocess.run(
        ['Rscript', '-e', r_code],
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"R script failed: {result.stderr}")
    
    output_lines = [line for line in result.stdout.strip().split('\n') if line and ',' in line]
    if not output_lines:
        raise RuntimeError(f"No output from R script: {result.stdout}")
    
    last_line = output_lines[-1]
    parts = last_line.split(',')
    
    return {
        'distinct_name_email': int(parts[0]),
        'baseline_email': int(parts[1]),
        'fullfat_model': int(parts[2])
    }


def append_result_to_csv(result: dict):
    """Append a single result to the CSV (creates file if needed)."""
    file_exists = RESULTS_CSV.exists()
    
    with RESULTS_CSV.open('a', newline='', encoding='utf-8') as f:
        fieldnames = [
            'project', 'distinct_name_email', 'baseline_email', 'fullfat_model',
            'baseline_reduction', 'fullfat_additional', 'total_reduction'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(result)


def main():
    # LIMIT FOR TESTING (set to None to process all)
    TEST_LIMIT = None
    
    # Skip projects with too many contributors (would take days to process)
    MAX_CONTRIBUTORS = 500  # Skip projects with more than 500 unique contributors
    
    log("="*80)
    log("PROCESSING ALL PROJECTS WITH FULL-FAT ALFAA MODEL")
    if TEST_LIMIT:
        log(f"TEST MODE: Limited to {TEST_LIMIT} projects")
    if MAX_CONTRIBUTORS:
        log(f"Skipping projects with > {MAX_CONTRIBUTORS} contributors")
    log("="*80)
    
    # Get all projects
    log(f"Reading projects from: {MASTER_CSV.name}")
    all_projects = get_all_projects(MASTER_CSV)
    log(f"Total projects in dataset: {len(all_projects)}")
    
    # Get completed projects
    completed = get_completed_projects()
    log(f"Already completed: {len(completed)}")
    
    # Filter to remaining projects
    remaining = [p for p in all_projects if p not in completed]
    
    # Apply test limit if set
    if TEST_LIMIT and len(remaining) > TEST_LIMIT:
        remaining = remaining[:TEST_LIMIT]
        log(f"TEST: Processing only first {TEST_LIMIT} projects")
    
    log(f"Remaining to process: {len(remaining)}")
    
    if not remaining:
        log("✓ All projects already processed!")
        return
    
    # Create output directory
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each remaining project
    for i, project in enumerate(remaining, 1):
        log("")
        log(f"[{i}/{len(remaining)}] {project}")
        
        try:
            # Check contributor count if limit is set
            if MAX_CONTRIBUTORS:
                # Count unique contributors
                contributors = set()
                with open(MASTER_CSV, 'r', encoding='utf-8', errors='replace') as f:
                    csv.field_size_limit(10**9)
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('project') == project:
                            key = (row.get('author_name', ''), row.get('author_email', ''))
                            contributors.add(key)
                
                n_contributors = len(contributors)
                n_pairs = n_contributors * (n_contributors - 1) // 2
                
                if n_contributors > MAX_CONTRIBUTORS:
                    log(f"  ⚠️  SKIPPING: {n_contributors:,} contributors ({n_pairs:,} pairs) exceeds limit of {MAX_CONTRIBUTORS}")
                    # Save as skipped
                    result = {
                        'project': project,
                        'distinct_name_email': n_contributors,
                        'baseline_email': 'SKIPPED',
                        'fullfat_model': 'SKIPPED',
                        'baseline_reduction': 'SKIPPED',
                        'fullfat_additional': 'SKIPPED',
                        'total_reduction': 'SKIPPED'
                    }
                    append_result_to_csv(result)
                    continue
                else:
                    log(f"  Contributors: {n_contributors:,} ({n_pairs:,} pairs)")
            
            # Build pairs
            pairs_path = PAIRS_DIR / f"{project.replace('/', '_')}_pairs.csv"
            
            if not pairs_path.exists():
                log("  Building pairwise features...")
                build_pairs_for_project(project, MASTER_CSV, pairs_path, verbose=False)
            else:
                log("  Using existing pairs file")
            
            # Run RF model
            log("  Running full-fat model...")
            counts = run_rf_model_on_project(pairs_path)
            
            result = {
                'project': project,
                'distinct_name_email': counts['distinct_name_email'],
                'baseline_email': counts['baseline_email'],
                'fullfat_model': counts['fullfat_model'],
                'baseline_reduction': counts['distinct_name_email'] - counts['baseline_email'],
                'fullfat_additional': counts['baseline_email'] - counts['fullfat_model'],
                'total_reduction': counts['distinct_name_email'] - counts['fullfat_model']
            }
            
            log(f"  ✓ Distinct: {counts['distinct_name_email']} | Baseline: {counts['baseline_email']} | Full-fat: {counts['fullfat_model']}")
            
            # Append immediately to CSV
            append_result_to_csv(result)
            
        except Exception as e:
            log(f"  ✗ ERROR: {e}")
            append_result_to_csv({
                'project': project,
                'distinct_name_email': 'ERROR',
                'baseline_email': 'ERROR',
                'fullfat_model': 'ERROR',
                'baseline_reduction': 'ERROR',
                'fullfat_additional': 'ERROR',
                'total_reduction': 'ERROR'
            })
    
    log("")
    log("="*80)
    log(f"✓ Processing complete! Results saved to: {RESULTS_CSV.name}")
    log("="*80)


if __name__ == "__main__":
    main()

