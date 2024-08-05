# OSS4SG Community Analysis

Replication package and full analysis codebase for the ICSE 2026 paper:
**"Characterizing Contributor Communities in Open Source Software for Social Good"**

## Overview

This repository contains all experiment code used in the study, spanning data extraction, identity resolution, statistical analysis, and visualization.

## Structure

```
src/
  extraction/       # Clone repos, extract commits, build master dataset (Exp 2.0, 10)
  preprocessing/    # Name-email pairs, overlap analysis, build pairs (Exp 3, 11, EXP1)
  identity/         # Union-find, MSN merge, email baseline, ML similarity (Exp 4, 6)
  analysis/         # Correlation, dendrograms, core contributor clustering (Exp 7, 20)
  statistics/       # Statistical tests, Kruskal-Wallis, pairwise comparisons (Exp 12, 21)
  visualization/    # KDE plots, join/leave viz, paper figures (Exp 8, recreating plots)
  replication/      # Original MSR replication package (RQ1/RQ2/RQ3)
scripts/            # Pipeline entry points
config/             # Project list CSVs
```

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

See `scripts/` for pipeline entry points. Key workflow:

1. Extract commits: `python scripts/run_extraction.py`
2. Merge identities: `python scripts/run_identity_merging.py`
3. Run analysis: `python scripts/run_analysis.py`
4. Run statistical tests: `python scripts/run_statistical_tests.py`

## Data

The `config/` directory contains the filtered OSS4SG project lists used in the study.

## Citation

If you use this code, please cite our ICSE 2026 paper.
