#!/usr/bin/env python3
"""
SciTools Understand Batch Code Metrics Analyzer

This script performs batch code metrics analysis using SciTools Understand on multiple
project repositories. It collects comprehensive code metrics including complexity,
coupling, cohesion, and various architectural measurements.

Key Features:
- Batch processing of multiple projects
- Comprehensive code metrics collection
- CSV export with detailed metrics
- Error handling and logging
- Resume capability for interrupted runs
- Support for multiple programming languages

Author: Research Team
Version: 1.0
"""

import os
import sys
import subprocess
import argparse
import pandas as pd
import csv
from pathlib import Path
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class UnderstandBatchAnalyzer:
    """
    Batch analyzer for running SciTools Understand code metrics analysis.
    """
    
    # Common metrics to extract from Understand
    METRICS = [
        # Complexity Metrics
        "Cyclomatic",
        "CyclomaticModified", 
        "CyclomaticStrict",
        "MaxCyclomatic",
        "MaxNesting",
        "Essential",
        
        # Size Metrics
        "CountLine",
        "CountLineCode",
        "CountLineComment",
        "CountLineBlank",
        "CountStmt",
        "CountStmtDecl",
        "CountStmtExe",
        
        # Object-Oriented Metrics
        "CountDeclClass",
        "CountDeclMethod",
        "CountDeclMethodAll",
        "CountDeclFunction",
        "MaxInheritanceTree",
        "CountClassCoupled",
        "CountClassDerived",
        "CountClassBase",
        
        # Coupling and Cohesion
        "PercentLackOfCohesion",
        "AfferentCoupling",
        "EfferentCoupling",
        
        # Other Metrics
        "RatioCommentToCode",
        "CountPath",
        "Knots",
        "MinEssentialKnots",
        "SumEssential"
    ]
    
    def __init__(self, understand_path: str = None):
        """
        Initialize the analyzer.
        
        Args:
            understand_path: Path to Understand executable (auto-detected if None)
        """
        self.understand_path = self.find_understand_executable(understand_path)
        if not self.understand_path:
            raise RuntimeError("SciTools Understand not found. Please install Understand or provide path.")
        
        print(f"Using Understand: {self.understand_path}")
    
    def find_understand_executable(self, custom_path: str = None) -> Optional[str]:
        """
        Find the Understand executable on the system.
        
        Args:
            custom_path: Custom path to Understand executable
            
        Returns:
            Path to Understand executable or None if not found
        """
        if custom_path:
            if Path(custom_path).exists():
                return custom_path
            else:
                print(f"Custom Understand path not found: {custom_path}")
                return None
        
        # Common Understand installation paths
        common_paths = [
            # macOS
            "/Applications/Understand.app/Contents/MacOS/und",
            # Windows
            "C:\\Program Files\\SciTools\\bin\\pc-win64\\und.exe",
            "C:\\Program Files (x86)\\SciTools\\bin\\pc-win32\\und.exe",
            # Linux
            "/opt/scitools/bin/linux64/und",
            "/usr/local/bin/und",
            "/usr/bin/und"
        ]
        
        # Check common paths
        for path in common_paths:
            if Path(path).exists():
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["which", "und"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return None
    
    def create_understand_database(self, project_path: Path, db_path: Path) -> bool:
        """
        Create an Understand database for a project.
        
        Args:
            project_path: Path to the project to analyze
            db_path: Path where to create the database
            
        Returns:
            True if database creation successful, False otherwise
        """
        try:
            # Remove existing database if it exists
            if db_path.exists():
                db_path.unlink()
            
            # Create new database
            cmd = [
                self.understand_path,
                "create",
                "-db", str(db_path),
                "-languages", "all"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                print(f"Error creating database: {result.stderr}")
                return False
            
            # Add files to database
            cmd = [
                self.understand_path,
                "add",
                "-db", str(db_path),
                "."
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode != 0:
                print(f"Error adding files: {result.stderr}")
                return False
            
            # Analyze the database
            cmd = [
                self.understand_path,
                "analyze",
                "-db", str(db_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode != 0:
                print(f"Error analyzing database: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"Understand analysis timed out for {project_path.name}")
            return False
        except Exception as e:
            print(f"Error creating Understand database: {e}")
            return False
    
    def extract_metrics(self, db_path: Path, output_csv: Path) -> bool:
        """
        Extract metrics from an Understand database.
        
        Args:
            db_path: Path to the Understand database
            output_csv: Path to save the metrics CSV
            
        Returns:
            True if extraction successful, False otherwise
        """
        try:
            # Create metrics command
            metrics_list = ",".join(self.METRICS)
            
            cmd = [
                self.understand_path,
                "metrics",
                "-db", str(db_path),
                "-format", "csv",
                "-csv", str(output_csv)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                print(f"Error extracting metrics: {result.stderr}")
                return False
            
            return output_csv.exists() and output_csv.stat().st_size > 0
            
        except subprocess.TimeoutExpired:
            print("Metrics extraction timed out")
            return False
        except Exception as e:
            print(f"Error extracting metrics: {e}")
            return False
    
    def parse_metrics_csv(self, metrics_csv: Path) -> Dict:
        """
        Parse the metrics CSV file and aggregate results.
        
        Args:
            metrics_csv: Path to the metrics CSV file
            
        Returns:
            Dictionary with aggregated metrics
        """
        try:
            df = pd.read_csv(metrics_csv)
            
            # Initialize results dictionary
            results = {}
            
            # Calculate aggregate metrics
            numeric_columns = df.select_dtypes(include=['number']).columns
            
            for col in numeric_columns:
                if col in self.METRICS:
                    # Calculate various aggregations
                    results[f"{col}_sum"] = df[col].sum()
                    results[f"{col}_mean"] = df[col].mean()
                    results[f"{col}_median"] = df[col].median()
                    results[f"{col}_max"] = df[col].max()
                    results[f"{col}_min"] = df[col].min()
                    results[f"{col}_std"] = df[col].std()
            
            # Add some basic counts
            results["total_entities"] = len(df)
            results["total_files"] = df.get('File', pd.Series()).nunique() if 'File' in df.columns else 0
            
            return results
            
        except Exception as e:
            print(f"Error parsing metrics CSV: {e}")
            return {}
    
    def analyze_project(self, project_path: Path, output_dir: Path = None) -> Dict:
        """
        Analyze a single project with Understand.
        
        Args:
            project_path: Path to the project to analyze
            output_dir: Custom output directory (optional)
            
        Returns:
            Dictionary with analysis results
        """
        if output_dir is None:
            output_dir = project_path / "understand_results"
        output_dir.mkdir(exist_ok=True)
        
        db_path = output_dir / "project.und"
        metrics_csv = output_dir / "metrics.csv"
        
        print(f"  → Creating Understand database...")
        if not self.create_understand_database(project_path, db_path):
            return {"success": False, "error": "Database creation failed"}
        
        print(f"  → Extracting metrics...")
        if not self.extract_metrics(db_path, metrics_csv):
            return {"success": False, "error": "Metrics extraction failed"}
        
        print(f"  → Parsing results...")
        metrics = self.parse_metrics_csv(metrics_csv)
        
        # Clean up database file (it can be large)
        try:
            if db_path.exists():
                db_path.unlink()
        except:
            pass
        
        return {
            "success": True,
            "metrics_file": str(metrics_csv),
            **metrics
        }
    
    def analyze_project_list(self, project_df: pd.DataFrame, 
                           output_csv: str = "understand_results.csv",
                           resume: bool = True) -> pd.DataFrame:
        """
        Analyze a list of projects from a DataFrame.
        
        Args:
            project_df: DataFrame with project information (must have 'path' column)
            output_csv: Output CSV file for results
            resume: Whether to resume from existing results
            
        Returns:
            DataFrame with analysis results
        """
        results = []
        
        # Load existing results if resuming
        done_projects = set()
        if resume and Path(output_csv).exists():
            try:
                existing_df = pd.read_csv(output_csv)
                done_projects = set(existing_df['project_path'].tolist())
                print(f"Resuming analysis, {len(done_projects)} projects already completed")
            except Exception as e:
                print(f"Error loading existing results: {e}")
        
        total_projects = len(project_df)
        success_count = 0
        failure_count = 0
        skip_count = len(done_projects)
        
        print(f"Starting Understand analysis for {total_projects} projects")
        print("=" * 60)
        
        for idx, row in project_df.iterrows():
            project_path = Path(row['path'])
            project_name = project_path.name
            
            print(f"[{idx+1}/{total_projects}] Processing: {project_name}")
            
            # Skip if already processed
            if str(project_path) in done_projects:
                print(f"  → Skipping (already completed)")
                skip_count += 1
                continue
            
            # Check if project path exists
            if not project_path.exists():
                print(f"  → Error: Project path does not exist")
                failure_count += 1
                continue
            
            # Run analysis
            start_time = time.time()
            analysis_result = self.analyze_project(project_path)
            analysis_time = time.time() - start_time
            
            result_row = {
                'project_name': project_name,
                'project_path': str(project_path),
                'analysis_time_seconds': analysis_time,
                'timestamp': datetime.now().isoformat(),
                **analysis_result
            }
            
            if analysis_result.get('success', False):
                print(f"  → Analysis completed in {analysis_time:.1f}s")
                success_count += 1
            else:
                print(f"  → Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                failure_count += 1
            
            results.append(result_row)
            
            # Save intermediate results
            if results and (len(results) % 5 == 0 or idx == total_projects - 1):
                self.save_results(results, output_csv, append=True)
                results = []  # Clear to save memory
        
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total projects: {total_projects}")
        print(f"Successful analyses: {success_count}")
        print(f"Failed analyses: {failure_count}")
        print(f"Skipped (already done): {skip_count}")
        print(f"Results saved to: {output_csv}")
        
        # Return final results
        try:
            return pd.read_csv(output_csv)
        except:
            return pd.DataFrame(results)
    
    def save_results(self, results: List[Dict], output_file: str, append: bool = False):
        """Save results to CSV file."""
        if not results:
            return
            
        df = pd.DataFrame(results)
        
        if append and Path(output_file).exists():
            # Append to existing file
            df.to_csv(output_file, mode='a', header=False, index=False)
        else:
            # Create new file
            df.to_csv(output_file, index=False)


def main():
    """Main execution function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Batch SciTools Understand Code Metrics Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze projects from CSV file
  python understand_batch_analyzer.py projects.csv

  # Analyze single project directory
  python understand_batch_analyzer.py --single-project /path/to/project

  # Analyze with custom Understand installation
  python understand_batch_analyzer.py projects.csv \\
    --understand-path /opt/scitools/bin/linux64/und
        """
    )
    
    parser.add_argument('input', nargs='?', type=str,
                       help='CSV file with project paths or single project directory')
    parser.add_argument('--single-project', type=str,
                       help='Analyze a single project directory')
    parser.add_argument('--output', type=str, default='understand_results.csv',
                       help='Output CSV file (default: understand_results.csv)')
    parser.add_argument('--understand-path', type=str,
                       help='Path to Understand executable')
    parser.add_argument('--no-resume', action='store_true',
                       help='Do not resume from existing results')
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input and not args.single_project:
        print("Error: Must provide either input CSV file or --single-project")
        return 1
    
    try:
        # Initialize analyzer
        analyzer = UnderstandBatchAnalyzer(understand_path=args.understand_path)
        
        if args.single_project:
            # Single project analysis
            project_path = Path(args.single_project)
            if not project_path.exists():
                print(f"Error: Project path does not exist: {project_path}")
                return 1
            
            # Create DataFrame for single project
            project_df = pd.DataFrame([{'path': str(project_path)}])
            
        else:
            # Load projects from CSV
            try:
                project_df = pd.read_csv(args.input)
                if 'path' not in project_df.columns:
                    print("Error: CSV file must contain a 'path' column")
                    return 1
            except Exception as e:
                print(f"Error loading CSV file: {e}")
                return 1
        
        # Run analysis
        results_df = analyzer.analyze_project_list(
            project_df=project_df,
            output_csv=args.output,
            resume=not args.no_resume
        )
        
        print(f"\nAnalysis complete! Results saved to: {args.output}")
        return 0
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 