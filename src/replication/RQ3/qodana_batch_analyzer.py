#!/usr/bin/env python3
"""
Qodana Batch Code Quality Analyzer

This script performs batch code quality analysis using JetBrains Qodana on multiple
project repositories. It supports different programming languages and automatically
selects the appropriate Qodana linter based on the project language.

Key Features:
- Batch processing of multiple projects
- Automatic language detection and linter selection
- Docker-based Qodana execution
- SARIF result parsing and CSV export
- Resume capability for interrupted runs
- Comprehensive error handling

Author: Research Team
Version: 1.0
"""

import os
import sys
import json
import subprocess
import shlex
import argparse
import pandas as pd
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class QodanaBatchAnalyzer:
    """
    Batch analyzer for running Qodana code quality analysis on multiple projects.
    """
    
    # Language to Qodana linter mapping
    LINTERS = {
        "Python": "jetbrains/qodana-python:2025.1",
        "Java": "jetbrains/qodana-jvm:2025.1",
        "Kotlin": "jetbrains/qodana-jvm:2025.1",
        "JavaScript": "jetbrains/qodana-js:2025.1",
        "TypeScript": "jetbrains/qodana-js:2025.1",
        "C#": "jetbrains/qodana-dotnet:2025.1",
        "Go": "jetbrains/qodana-go:2025.1",
        "PHP": "jetbrains/qodana-php:2025.1",
    }
    
    def __init__(self, qodana_token: str = None):
        """
        Initialize the analyzer.
        
        Args:
            qodana_token: Qodana cloud token for uploading results (optional)
        """
        self.qodana_token = qodana_token
        self.pulled_images = set()
        
    def ensure_docker_available(self):
        """Check if Docker is available and accessible."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            print(f"Docker available: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Docker is not available or not running")
    
    def ensure_image(self, image_tag: str):
        """
        Ensure Docker image is available locally, pull if necessary.
        
        Args:
            image_tag: Docker image tag to ensure
        """
        if image_tag in self.pulled_images:
            return
            
        # Check if image exists locally
        result = subprocess.run(
            ["docker", "image", "inspect", image_tag],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        if result.returncode != 0:
            print(f"Pulling Docker image: {image_tag}")
            try:
                subprocess.run(
                    ["docker", "pull", image_tag],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Successfully pulled: {image_tag}")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to pull Docker image {image_tag}: {e}")
        
        self.pulled_images.add(image_tag)
    
    def detect_project_language(self, project_path: Path) -> Optional[str]:
        """
        Detect the primary language of a project by examining file extensions.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Detected language or None if unable to determine
        """
        if not project_path.exists() or not project_path.is_dir():
            return None
        
        # File extension to language mapping
        ext_map = {
            '.py': 'Python',
            '.java': 'Java',
            '.kt': 'Kotlin',
            '.kts': 'Kotlin',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.cs': 'C#',
            '.go': 'Go',
            '.php': 'PHP',
        }
        
        # Count files by extension
        ext_counts = {}
        try:
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in ext_map:
                        lang = ext_map[ext]
                        ext_counts[lang] = ext_counts.get(lang, 0) + 1
        except PermissionError:
            print(f"Permission denied accessing files in {project_path}")
            return None
        
        # Return the most common language
        if ext_counts:
            return max(ext_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    def run_qodana_analysis(self, project_path: Path, language: str, 
                           output_dir: Path = None) -> bool:
        """
        Run Qodana analysis on a single project.
        
        Args:
            project_path: Path to the project to analyze
            language: Programming language of the project
            output_dir: Custom output directory (optional)
            
        Returns:
            True if analysis successful, False otherwise
        """
        linter = self.LINTERS.get(language)
        if not linter:
            print(f"No Qodana linter available for language: {language}")
            return False
        
        # Ensure Docker image is available
        self.ensure_image(linter)
        
        # Set up output directory
        if output_dir is None:
            output_dir = project_path / "qodana-results"
        output_dir.mkdir(exist_ok=True)
        
        # Create qodana.yaml configuration
        config_file = project_path / "qodana.yaml"
        config_file.write_text(f"linter: {linter}\n")
        
        # Set up environment
        env = os.environ.copy()
        if self.qodana_token:
            env["QODANA_TOKEN"] = self.qodana_token
        
        # Build command
        cmd = [
            "qodana", "scan",
            "--project-dir", str(project_path),
            "--results-dir", str(output_dir)
        ]
        
        try:
            # Run Qodana analysis
            result = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3600  # 1 hour timeout
            )
            
            # Check if analysis produced results
            sarif_file = output_dir / "report" / "results" / "result-allProblems.json"
            if result.returncode == 0 and sarif_file.exists():
                return True
            else:
                print(f"Qodana analysis failed for {project_path.name} (exit code: {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"Qodana analysis timed out for {project_path.name}")
            return False
        except Exception as e:
            print(f"Error running Qodana analysis for {project_path.name}: {e}")
            return False
        finally:
            # Clean up config file
            if config_file.exists():
                config_file.unlink()
    
    def parse_sarif_results(self, sarif_path: Path) -> Dict:
        """
        Parse SARIF results file and extract metrics.
        
        Args:
            sarif_path: Path to the SARIF results file
            
        Returns:
            Dictionary with parsed metrics
        """
        try:
            with open(sarif_path, 'r') as f:
                data = json.load(f)
            
            problems = data.get("listProblem", [])
            
            # Count by severity
            severity_counts = {}
            problem_types = {}
            
            for problem in problems:
                severity = problem.get("severity", "Unknown")
                problem_type = problem.get("type", "Unknown")
                
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                problem_types[problem_type] = problem_types.get(problem_type, 0) + 1
            
            return {
                "total_problems": len(problems),
                "critical_issues": severity_counts.get("Critical", 0),
                "high_issues": severity_counts.get("High", 0),
                "moderate_issues": severity_counts.get("Moderate", 0),
                "low_issues": severity_counts.get("Low", 0),
                "info_issues": severity_counts.get("Info", 0),
                "severity_counts": severity_counts,
                "problem_types": problem_types
            }
            
        except Exception as e:
            print(f"Error parsing SARIF file {sarif_path}: {e}")
            return {
                "total_problems": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "moderate_issues": 0,
                "low_issues": 0,
                "info_issues": 0,
                "severity_counts": {},
                "problem_types": {}
            }
    
    def analyze_project_list(self, project_df: pd.DataFrame, 
                           output_csv: str = "qodana_results.csv",
                           resume: bool = True) -> pd.DataFrame:
        """
        Analyze a list of projects from a DataFrame.
        
        Args:
            project_df: DataFrame with project information (must have 'path' and optionally 'language' columns)
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
        
        print(f"Starting Qodana analysis for {total_projects} projects")
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
            
            # Detect or use provided language
            if 'language' in row and pd.notna(row['language']):
                language = row['language']
            else:
                language = self.detect_project_language(project_path)
            
            if not language:
                print(f"  → Error: Unable to detect project language")
                failure_count += 1
                continue
            
            if language not in self.LINTERS:
                print(f"  → Warning: No linter available for {language}")
                failure_count += 1
                continue
            
            print(f"  → Language: {language}")
            
            # Run analysis
            start_time = time.time()
            success = self.run_qodana_analysis(project_path, language)
            analysis_time = time.time() - start_time
            
            if success:
                print(f"  → Analysis completed in {analysis_time:.1f}s")
                
                # Parse results
                sarif_path = project_path / "qodana-results" / "report" / "results" / "result-allProblems.json"
                metrics = self.parse_sarif_results(sarif_path)
                
                result_row = {
                    'project_name': project_name,
                    'project_path': str(project_path),
                    'language': language,
                    'analysis_time_seconds': analysis_time,
                    'success': True,
                    **metrics
                }
                
                print(f"  → Found {metrics['total_problems']} total issues")
                success_count += 1
            else:
                print(f"  → Analysis failed")
                result_row = {
                    'project_name': project_name,
                    'project_path': str(project_path),
                    'language': language,
                    'analysis_time_seconds': analysis_time,
                    'success': False,
                    'total_problems': 0,
                    'critical_issues': 0,
                    'high_issues': 0,
                    'moderate_issues': 0,
                    'low_issues': 0,
                    'info_issues': 0
                }
                failure_count += 1
            
            result_row['timestamp'] = datetime.now().isoformat()
            results.append(result_row)
            
            # Save intermediate results
            if results and (len(results) % 10 == 0 or idx == total_projects - 1):
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
        description='Batch Qodana Code Quality Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze projects from CSV file
  python qodana_batch_analyzer.py projects.csv

  # Analyze single project directory
  python qodana_batch_analyzer.py --single-project /path/to/project

  # Analyze with custom output and Qodana token
  python qodana_batch_analyzer.py projects.csv \\
    --output results.csv \\
    --qodana-token YOUR_TOKEN
        """
    )
    
    parser.add_argument('input', nargs='?', type=str,
                       help='CSV file with project paths or single project directory')
    parser.add_argument('--single-project', type=str,
                       help='Analyze a single project directory')
    parser.add_argument('--output', type=str, default='qodana_results.csv',
                       help='Output CSV file (default: qodana_results.csv)')
    parser.add_argument('--qodana-token', type=str,
                       help='Qodana cloud token for uploading results')
    parser.add_argument('--no-resume', action='store_true',
                       help='Do not resume from existing results')
    parser.add_argument('--language', type=str,
                       help='Force specific language (for single project analysis)')
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input and not args.single_project:
        print("Error: Must provide either input CSV file or --single-project")
        return 1
    
    try:
        # Initialize analyzer
        analyzer = QodanaBatchAnalyzer(qodana_token=args.qodana_token)
        
        # Check Docker availability
        analyzer.ensure_docker_available()
        
        if args.single_project:
            # Single project analysis
            project_path = Path(args.single_project)
            if not project_path.exists():
                print(f"Error: Project path does not exist: {project_path}")
                return 1
            
            # Create DataFrame for single project
            project_df = pd.DataFrame([{
                'path': str(project_path),
                'language': args.language
            }])
            
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