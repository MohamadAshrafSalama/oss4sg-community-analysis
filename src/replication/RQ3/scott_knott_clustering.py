#!/usr/bin/env python3
"""
Scott-Knott ESD Clustering Analysis

This script performs Scott-Knott Effect Size Difference (ESD) clustering analysis
on code quality metrics. It uses the R ScottKnottESD package via rpy2 to perform
statistical clustering and generates visualizations and summary tables.

Key Features:
- Scott-Knott ESD clustering via R integration
- Support for multiple metrics simultaneously
- Box plot visualizations with cluster coloring
- Summary tables with ranks and statistics
- CSV export capabilities
- Flexible input data handling

Author: Research Team
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.robjects.conversion import localconverter
    HAS_RPY2 = True
except ImportError:
    HAS_RPY2 = False
    print("Warning: rpy2 not available. Scott-Knott analysis will use fallback implementation.")


class ScottKnottClusteringAnalyzer:
    """
    Analyzer for Scott-Knott ESD clustering of code quality metrics.
    """
    
    def __init__(self, use_r: bool = True):
        """
        Initialize the analyzer.
        
        Args:
            use_r: Whether to use R implementation (requires rpy2 and ScottKnottESD)
        """
        self.use_r = use_r and HAS_RPY2
        self.sk_pkg = None
        
        if self.use_r:
            try:
                # Activate pandas conversion
                pandas2ri.activate()
                
                # Try to load ScottKnottESD package
                self.sk_pkg = importr("ScottKnottESD")
                print("Using R ScottKnottESD package for clustering")
                
            except Exception as e:
                print(f"Failed to load R ScottKnottESD package: {e}")
                print("Falling back to Python implementation")
                self.use_r = False
        else:
            print("Using Python fallback implementation")
    
    def scott_knott_esd_r(self, data: pd.DataFrame, group_col: str, 
                         value_col: str) -> Dict:
        """
        Perform Scott-Knott ESD clustering using R package.
        
        Args:
            data: DataFrame with data to cluster
            group_col: Column name containing group identifiers
            value_col: Column name containing values to cluster
            
        Returns:
            Dictionary with clustering results
        """
        if not self.use_r or self.sk_pkg is None:
            raise RuntimeError("R ScottKnottESD not available")
        
        try:
            # Prepare data in wide format for R
            wide_data = data.pivot_table(
                index=group_col, 
                values=value_col, 
                aggfunc='mean'
            ).reset_index()
            
            # Convert to R format
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_data = robjects.conversion.py2rpy(wide_data[value_col])
            
            # Run Scott-Knott ESD
            sk_result = self.sk_pkg.sk_esd(r_data)
            
            # Extract results
            groups = list(sk_result.rx2('groups'))
            ranks = list(sk_result.rx2('rank'))
            
            # Create results dictionary
            group_names = wide_data[group_col].tolist()
            results = {
                'groups': dict(zip(group_names, groups)),
                'ranks': dict(zip(group_names, ranks)),
                'n_clusters': len(set(groups)),
                'method': 'Scott-Knott ESD (R)'
            }
            
            return results
            
        except Exception as e:
            print(f"Error in R Scott-Knott ESD: {e}")
            return self.scott_knott_fallback(data, group_col, value_col)
    
    def scott_knott_fallback(self, data: pd.DataFrame, group_col: str, 
                           value_col: str, alpha: float = 0.05) -> Dict:
        """
        Fallback Scott-Knott implementation in Python.
        
        Args:
            data: DataFrame with data to cluster
            group_col: Column name containing group identifiers
            value_col: Column name containing values to cluster
            alpha: Significance level
            
        Returns:
            Dictionary with clustering results
        """
        # Group data and calculate means
        grouped = data.groupby(group_col)[value_col].agg(['mean', 'count', 'std']).reset_index()
        grouped = grouped.sort_values('mean')
        
        # Simple clustering based on mean differences
        # This is a simplified version - not the full Scott-Knott algorithm
        means = grouped['mean'].values
        groups = []
        current_group = 1
        
        if len(means) <= 1:
            groups = [1] * len(means)
        else:
            # Use standard deviation to determine significant differences
            overall_std = data[value_col].std()
            threshold = overall_std * 0.5  # Simplified threshold
            
            groups.append(current_group)
            for i in range(1, len(means)):
                if abs(means[i] - means[i-1]) > threshold:
                    current_group += 1
                groups.append(current_group)
        
        # Create results
        group_names = grouped[group_col].tolist()
        results = {
            'groups': dict(zip(group_names, groups)),
            'ranks': dict(zip(group_names, groups)),  # Simplified: rank = group
            'n_clusters': len(set(groups)),
            'method': 'Scott-Knott (Python fallback)'
        }
        
        return results
    
    def perform_clustering(self, data: pd.DataFrame, group_col: str, 
                         value_col: str) -> Dict:
        """
        Perform Scott-Knott clustering using the best available method.
        
        Args:
            data: DataFrame with data to cluster
            group_col: Column name containing group identifiers
            value_col: Column name containing values to cluster
            
        Returns:
            Dictionary with clustering results
        """
        if self.use_r:
            return self.scott_knott_esd_r(data, group_col, value_col)
        else:
            return self.scott_knott_fallback(data, group_col, value_col)
    
    def create_cluster_boxplot(self, data: pd.DataFrame, group_col: str, 
                             value_col: str, cluster_results: Dict, 
                             title: str = None, output_path: str = None):
        """
        Create a box plot colored by Scott-Knott clusters.
        
        Args:
            data: DataFrame with data to plot
            group_col: Column name containing group identifiers
            value_col: Column name containing values to plot
            cluster_results: Results from Scott-Knott clustering
            title: Plot title
            output_path: Path to save the plot
        """
        plt.figure(figsize=(12, 8))
        
        # Prepare data with cluster information
        plot_data = data.copy()
        plot_data['cluster'] = plot_data[group_col].map(cluster_results['groups'])
        
        # Sort by cluster and then by mean value within cluster
        group_stats = plot_data.groupby(group_col)[value_col].mean().reset_index()
        group_stats['cluster'] = group_stats[group_col].map(cluster_results['groups'])
        group_stats = group_stats.sort_values(['cluster', value_col])
        
        # Create color palette for clusters
        n_clusters = cluster_results['n_clusters']
        colors = plt.cm.Set3(np.linspace(0, 1, n_clusters))
        cluster_colors = {i+1: colors[i] for i in range(n_clusters)}
        
        # Create box plot
        groups_order = group_stats[group_col].tolist()
        box_colors = [cluster_colors[cluster_results['groups'][group]] for group in groups_order]
        
        # Plot
        bp = plt.boxplot([plot_data[plot_data[group_col] == group][value_col].values 
                         for group in groups_order],
                        labels=groups_order,
                        patch_artist=True)
        
        # Color boxes by cluster
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Customize plot
        plt.xticks(rotation=45, ha='right')
        plt.xlabel('Groups')
        plt.ylabel(value_col)
        
        if title is None:
            title = f'Scott-Knott ESD Clustering - {value_col}'
        plt.title(title)
        
        # Add cluster legend
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=cluster_colors[i+1], 
                                       alpha=0.7, label=f'Cluster {i+1}') 
                          for i in range(n_clusters)]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
        
        plt.show()
    
    def create_summary_table(self, data: pd.DataFrame, group_col: str, 
                           metrics: List[str], cluster_results_dict: Dict[str, Dict]) -> pd.DataFrame:
        """
        Create a summary table with Scott-Knott ranks and statistics.
        
        Args:
            data: DataFrame with data
            group_col: Column name containing group identifiers
            metrics: List of metric column names
            cluster_results_dict: Dictionary mapping metric names to cluster results
            
        Returns:
            Summary DataFrame
        """
        summary_rows = []
        
        for group in data[group_col].unique():
            group_data = data[data[group_col] == group]
            
            row = {'group': group}
            
            for metric in metrics:
                if metric in group_data.columns:
                    values = group_data[metric].dropna()
                    if len(values) > 0:
                        row[f'{metric}_mean'] = values.mean()
                        row[f'{metric}_median'] = values.median()
                        row[f'{metric}_std'] = values.std()
                        row[f'{metric}_count'] = len(values)
                        
                        # Add cluster rank if available
                        if metric in cluster_results_dict:
                            cluster_info = cluster_results_dict[metric]
                            if group in cluster_info['ranks']:
                                row[f'{metric}_rank'] = cluster_info['ranks'][group]
                                row[f'{metric}_cluster'] = cluster_info['groups'][group]
            
            summary_rows.append(row)
        
        return pd.DataFrame(summary_rows)
    
    def analyze_multiple_metrics(self, data: pd.DataFrame, group_col: str, 
                               metrics: List[str], output_dir: str = "scott_knott_results") -> Dict:
        """
        Perform Scott-Knott analysis on multiple metrics.
        
        Args:
            data: DataFrame with data
            group_col: Column name containing group identifiers
            metrics: List of metric column names to analyze
            output_dir: Directory to save results
            
        Returns:
            Dictionary with all clustering results
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        all_results = {}
        
        print(f"Performing Scott-Knott analysis on {len(metrics)} metrics")
        print("=" * 60)
        
        for i, metric in enumerate(metrics):
            print(f"[{i+1}/{len(metrics)}] Analyzing: {metric}")
            
            if metric not in data.columns:
                print(f"  → Warning: Column '{metric}' not found in data")
                continue
            
            # Check for valid data
            valid_data = data.dropna(subset=[group_col, metric])
            if len(valid_data) == 0:
                print(f"  → Warning: No valid data for '{metric}'")
                continue
            
            # Perform clustering
            try:
                results = self.perform_clustering(valid_data, group_col, metric)
                all_results[metric] = results
                
                print(f"  → Found {results['n_clusters']} clusters using {results['method']}")
                
                # Create visualization
                plot_path = output_path / f"{metric}_scott_knott_clusters.png"
                self.create_cluster_boxplot(
                    valid_data, group_col, metric, results,
                    title=f"Scott-Knott ESD Clustering - {metric}",
                    output_path=str(plot_path)
                )
                
            except Exception as e:
                print(f"  → Error analyzing '{metric}': {e}")
                continue
        
        # Create summary table
        if all_results:
            print("\nCreating summary table...")
            summary_df = self.create_summary_table(data, group_col, metrics, all_results)
            
            # Save summary
            summary_path = output_path / "scott_knott_summary.csv"
            summary_df.to_csv(summary_path, index=False)
            print(f"Summary table saved to: {summary_path}")
            
            # Save detailed results
            results_path = output_path / "scott_knott_detailed_results.json"
            import json
            with open(results_path, 'w') as f:
                # Convert numpy types to native Python types for JSON serialization
                json_results = {}
                for metric, result in all_results.items():
                    json_results[metric] = {
                        'groups': {str(k): int(v) for k, v in result['groups'].items()},
                        'ranks': {str(k): int(v) for k, v in result['ranks'].items()},
                        'n_clusters': int(result['n_clusters']),
                        'method': result['method']
                    }
                json.dump(json_results, f, indent=2)
            print(f"Detailed results saved to: {results_path}")
        
        print("\n" + "=" * 60)
        print("SCOTT-KNOTT ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total metrics analyzed: {len(all_results)}")
        print(f"Results saved to: {output_path}")
        
        return all_results


def main():
    """Main execution function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Scott-Knott ESD Clustering Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze multiple metrics from CSV
  python scott_knott_clustering.py data.csv --group-col category --metrics metric1,metric2,metric3
  
  # Analyze single metric with custom output
  python scott_knott_clustering.py data.csv --group-col group --metrics complexity --output results/
  
  # Use Python fallback (no R)
  python scott_knott_clustering.py data.csv --group-col category --metrics metric1 --no-r
        """
    )
    
    parser.add_argument('input_file', type=str,
                       help='CSV file with data to analyze')
    parser.add_argument('--group-col', type=str, required=True,
                       help='Column name containing group identifiers')
    parser.add_argument('--metrics', type=str, required=True,
                       help='Comma-separated list of metric column names to analyze')
    parser.add_argument('--output', type=str, default='scott_knott_results',
                       help='Output directory (default: scott_knott_results)')
    parser.add_argument('--no-r', action='store_true',
                       help='Use Python fallback instead of R implementation')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    try:
        # Load data
        data = pd.read_csv(args.input_file)
        print(f"Loaded data with {len(data)} rows and {len(data.columns)} columns")
        
        # Validate group column
        if args.group_col not in data.columns:
            print(f"Error: Group column '{args.group_col}' not found in data")
            print(f"Available columns: {list(data.columns)}")
            return 1
        
        # Parse metrics list
        metrics = [m.strip() for m in args.metrics.split(',')]
        print(f"Analyzing metrics: {metrics}")
        
        # Validate metrics columns
        missing_metrics = [m for m in metrics if m not in data.columns]
        if missing_metrics:
            print(f"Warning: Missing metrics columns: {missing_metrics}")
            metrics = [m for m in metrics if m in data.columns]
            if not metrics:
                print("Error: No valid metrics columns found")
                return 1
        
        # Initialize analyzer
        analyzer = ScottKnottClusteringAnalyzer(use_r=not args.no_r)
        
        # Run analysis
        results = analyzer.analyze_multiple_metrics(
            data=data,
            group_col=args.group_col,
            metrics=metrics,
            output_dir=args.output
        )
        
        print(f"\nAnalysis complete! Results saved to: {args.output}")
        return 0
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 