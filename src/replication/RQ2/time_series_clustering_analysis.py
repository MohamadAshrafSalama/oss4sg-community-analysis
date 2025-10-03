#!/usr/bin/env python3
"""
Time-Series Clustering of Engagement Patterns (Section 5.2.2)

This script performs time-series clustering analysis of Core Development Ratio patterns
across project developmental stages using K-means clustering. The analysis segments 
each project's time series by developmental stage and applies clustering to identify
shared temporal patterns of core developer activity.

Key Features:
- Core Development Ratio calculation (core_churn / total_churn)
- Strict stage filtering (early: 0-7 years, middle: 7-10 years, late: 10-13 years)
- Time series interpolation for consistent length
- K-means clustering with silhouette score optimization
- Centroid and medoid computation
- Comprehensive visualization and analysis

Author: Research Team
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys
from pathlib import Path
from datetime import datetime

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import interp1d


class TimeSeriesClusteringAnalyzer:
    """
    Analyzer for time-series clustering of core development ratio patterns.
    """
    
    def __init__(self, min_project_years=7, use_forced_k=False, forced_k=3):
        """
        Initialize the analyzer.
        
        Args:
            min_project_years: Minimum project lifespan in years to include
            use_forced_k: Whether to use a fixed number of clusters
            forced_k: Fixed number of clusters (if use_forced_k=True)
        """
        self.min_project_years = min_project_years
        self.use_forced_k = use_forced_k
        self.forced_k = forced_k
        self.scaler = MinMaxScaler()
        
        # Results storage
        self.df_filtered = None
        self.interpolated_time_series = []
        self.cluster_labels = None
        self.best_k = None
        self.best_score = None
        
    def load_and_prepare_data(self, file_path):
        """
        Load commit data and prepare for analysis.
        
        Args:
            file_path: Path to CSV file with commit data
            
        Returns:
            DataFrame with prepared data
        """
        print(f"Loading data from: {file_path}")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
        
        # Validate required columns
        required_cols = ['commit_date', 'project', 'churn', 'is_core']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Data preprocessing
        df['commit_date'] = pd.to_datetime(df['commit_date'], errors='coerce')
        df = df.dropna(subset=['commit_date'])  # Remove invalid dates
        df = df.sort_values('commit_date')
        
        # Create core_churn column
        df['core_churn'] = np.where(df['is_core'] == True, df['churn'], 0.0)
        
        print(f"Loaded {len(df)} commits from {df['project'].nunique()} projects")
        return df
    
    def filter_and_label_stages(self, project_df):
        """
        Filter project data by developmental stages with strict criteria.
        
        Projects must have at least min_project_years years to be included.
        Stages are defined as:
        - early: [start, start+7 years)
        - middle: [start+7, start+10 years) - only if project >= 10 years
        - late: [start+10, start+13 years) - only if project >= 13 years
        
        Args:
            project_df: DataFrame with commits for a single project
            
        Returns:
            DataFrame with stage labels, or empty DataFrame if project too short
        """
        project_df = project_df.copy()
        if project_df.empty:
            return project_df
        
        project_start = project_df['commit_date'].min()
        project_end = project_df['commit_date'].max()
        total_years = (project_end - project_start).days / 365.25  # More precise year calculation
        
        # Exclude projects shorter than minimum years
        if total_years < self.min_project_years:
            return project_df.iloc[0:0]  # Return empty DataFrame
        
        # Define stage boundaries
        early_end = project_start + pd.DateOffset(years=7)
        middle_end = early_end + pd.DateOffset(years=3)  # start+10
        late_end = middle_end + pd.DateOffset(years=3)   # start+13
        
        # Initialize stage column
        project_df['stage'] = ''
        
        # Always include early stage for projects >= min_project_years
        mask_early = ((project_df['commit_date'] >= project_start) & 
                     (project_df['commit_date'] < early_end))
        project_df.loc[mask_early, 'stage'] = 'early'
        
        # Include middle stage only if project >= 10 years
        if total_years >= 10:
            mask_middle = ((project_df['commit_date'] >= early_end) & 
                          (project_df['commit_date'] < middle_end))
            project_df.loc[mask_middle, 'stage'] = 'middle'
        
        # Include late stage only if project >= 13 years
        if total_years >= 13:
            mask_late = ((project_df['commit_date'] >= middle_end) & 
                        (project_df['commit_date'] < late_end))
            project_df.loc[mask_late, 'stage'] = 'late'
        
        # Keep only commits within defined stages
        project_df = project_df[project_df['stage'] != '']
        
        return project_df
    
    def create_monthly_time_series(self, df):
        """
        Create monthly time series of core development ratio.
        
        Args:
            df: DataFrame with filtered and stage-labeled commits
            
        Returns:
            DataFrame with monthly aggregated statistics
        """
        print("Creating monthly time series...")
        
        # Group by project, stage, and month
        df['year_month'] = df['commit_date'].dt.to_period('M')
        
        monthly_stats = df.groupby(['project', 'stage', 'year_month']).agg({
            'churn': 'sum',
            'core_churn': 'sum'
        }).reset_index()
        
        # Remove months with zero churn to avoid division by zero
        monthly_stats = monthly_stats[monthly_stats['churn'] > 0].copy()
        
        # Calculate core development ratio
        monthly_stats['core_churn_ratio'] = (monthly_stats['core_churn'] / 
                                           monthly_stats['churn'])
        
        # Remove any remaining NaN values
        monthly_stats = monthly_stats.dropna(subset=['core_churn_ratio'])
        
        # Convert to timestamp for sorting
        monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()
        
        print(f"Created {len(monthly_stats)} monthly data points")
        return monthly_stats
    
    def build_time_series_collection(self, monthly_stats):
        """
        Build collection of (project, stage) time series.
        
        Args:
            monthly_stats: DataFrame with monthly statistics
            
        Returns:
            List of dictionaries containing time series data
        """
        print("Building time series collection...")
        
        time_series_collection = []
        projects = monthly_stats['project'].unique()
        
        for project in projects:
            project_data = monthly_stats[monthly_stats['project'] == project]
            stages = project_data['stage'].unique()
            
            for stage in stages:
                stage_data = project_data[project_data['stage'] == stage].copy()
                
                if not stage_data.empty:
                    stage_data = stage_data.sort_values('date')
                    time_series_collection.append({
                        'project': project,
                        'stage': stage,
                        'time_series': stage_data,
                        'label': f"{project} - {stage}"
                    })
        
        print(f"Built {len(time_series_collection)} time series")
        return time_series_collection
    
    def interpolate_time_series(self, ts_collection):
        """
        Interpolate all time series to the same length using linear interpolation.
        
        Args:
            ts_collection: List of time series dictionaries
            
        Returns:
            List of interpolated time series with consistent length
        """
        print("Interpolating time series to consistent length...")
        
        # Filter out series with < 2 points
        valid_series = [item for item in ts_collection 
                       if len(item['time_series']) >= 2]
        
        if not valid_series:
            print("No valid time series found (need >= 2 points)")
            return []
        
        # Find maximum length
        max_length = max(len(item['time_series']) for item in valid_series)
        print(f"Target interpolation length: {max_length} points")
        
        interpolated_series = []
        
        for item in valid_series:
            ts = item['time_series']
            
            # Create interpolation
            x_orig = np.arange(len(ts))
            x_new = np.linspace(0, len(ts) - 1, max_length)
            y_orig = ts['core_churn_ratio'].values
            
            try:
                # Linear interpolation
                interp_func = interp1d(x_orig, y_orig, kind='linear', 
                                     bounds_error=False, fill_value='extrapolate')
                y_new = interp_func(x_new)
                
                # Check for NaN values
                if np.isnan(y_new).any():
                    print(f"Warning: NaN values in interpolation for {item['label']}")
                    continue
                
                interpolated_series.append({
                    'project': item['project'],
                    'stage': item['stage'],
                    'core_churn_ratio': y_new,
                    'label': item['label'],
                    'original_length': len(ts),
                    'interpolated_length': len(y_new)
                })
                
            except Exception as e:
                print(f"Error interpolating {item['label']}: {e}")
                continue
        
        print(f"Successfully interpolated {len(interpolated_series)} time series")
        return interpolated_series
    
    def perform_clustering(self, X):
        """
        Perform K-means clustering on the time series data.
        
        Args:
            X: Array of time series data (n_series x length)
            
        Returns:
            Tuple of (cluster_labels, best_k, best_score)
        """
        print("Performing K-means clustering...")
        
        if len(X) < 2:
            raise ValueError("Need at least 2 time series for clustering")
        
        # Scale the data
        X_scaled = self.scaler.fit_transform(X)
        
        if self.use_forced_k:
            print(f"Using forced k = {self.forced_k}")
            best_k = self.forced_k
            
            if best_k > len(X_scaled):
                print(f"Warning: Forced k ({best_k}) > number of series ({len(X_scaled)})")
                best_k = len(X_scaled)
            
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Calculate silhouette score if possible
            if len(set(cluster_labels)) > 1:
                best_score = silhouette_score(X_scaled, cluster_labels)
            else:
                best_score = -1
                
        else:
            print("Finding optimal k using silhouette score...")
            # Find optimal k using silhouette score
            max_k = min(10, len(X_scaled))
            possible_ks = range(2, max_k + 1)
            
            best_k, best_score = 2, -1
            scores = []
            
            for k in possible_ks:
                if k > len(X_scaled):
                    continue
                    
                kmeans_tmp = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels_tmp = kmeans_tmp.fit_predict(X_scaled)
                
                if len(set(labels_tmp)) > 1:
                    score = silhouette_score(X_scaled, labels_tmp)
                    scores.append((k, score))
                    if score > best_score:
                        best_k, best_score = k, score
            
            print(f"Silhouette scores: {scores}")
            
            # Final clustering with best k
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
        
        print(f"Best k = {best_k}, silhouette score = {best_score:.3f}")
        return cluster_labels, best_k, best_score, X_scaled
    
    def compute_centroids_and_medoids(self, X_scaled, cluster_labels, n_clusters):
        """
        Compute cluster centroids and medoids.
        
        Args:
            X_scaled: Scaled time series data
            cluster_labels: Cluster assignments
            n_clusters: Number of clusters
            
        Returns:
            Tuple of (centroids, medoids) lists
        """
        print("Computing centroids and medoids...")
        
        centroids = []
        medoids = []
        
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_points = X_scaled[cluster_mask]
            
            if len(cluster_points) == 0:
                continue
            
            # Compute centroid
            centroid_scaled = cluster_points.mean(axis=0)
            centroid_orig = self.scaler.inverse_transform(
                centroid_scaled.reshape(1, -1)
            )[0]
            centroids.append({
                'cluster_id': cluster_id,
                'centroid_scaled': centroid_scaled,
                'centroid_orig': centroid_orig
            })
            
            # Compute medoid
            if len(cluster_points) == 1:
                medoid_idx = 0
            else:
                # Find point with minimum average distance to all other points
                distances = pairwise_distances(cluster_points, metric='euclidean')
                avg_distances = distances.sum(axis=1)
                medoid_idx = np.argmin(avg_distances)
            
            global_indices = np.where(cluster_mask)[0]
            global_medoid_idx = global_indices[medoid_idx]
            medoid_scaled = cluster_points[medoid_idx]
            medoid_orig = self.scaler.inverse_transform(
                medoid_scaled.reshape(1, -1)
            )[0]
            
            medoids.append({
                'cluster_id': cluster_id,
                'global_index': global_medoid_idx,
                'medoid_scaled': medoid_scaled,
                'medoid_orig': medoid_orig
            })
        
        return centroids, medoids
    
    def analyze_stage_cluster_distribution(self, interpolated_time_series):
        """
        Analyze distribution of clusters by developmental stage.
        
        Args:
            interpolated_time_series: List of time series with cluster assignments
            
        Returns:
            Dictionary with distribution statistics
        """
        print("Analyzing stage-cluster distribution...")
        
        # Count occurrences
        stage_cluster_counts = {}
        for ts in interpolated_time_series:
            stage = ts['stage']
            cluster = ts['cluster']
            
            if stage not in stage_cluster_counts:
                stage_cluster_counts[stage] = {}
            
            stage_cluster_counts[stage][cluster] = (
                stage_cluster_counts[stage].get(cluster, 0) + 1
            )
        
        # Calculate percentages
        stage_cluster_percentages = {}
        for stage, cluster_counts in stage_cluster_counts.items():
            total = sum(cluster_counts.values())
            stage_cluster_percentages[stage] = {
                cluster: (count / total) * 100 
                for cluster, count in cluster_counts.items()
            }
        
        return {
            'counts': stage_cluster_counts,
            'percentages': stage_cluster_percentages
        }
    
    def create_visualizations(self, X, centroids, medoids, distribution_stats, output_dir):
        """
        Create comprehensive visualizations of clustering results.
        
        Args:
            X: Original time series data
            centroids: List of centroid dictionaries
            medoids: List of medoid dictionaries
            distribution_stats: Stage-cluster distribution statistics
            output_dir: Directory to save plots
        """
        print("Creating visualizations...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Main comprehensive plot
        fig, axes = plt.subplots(3, 1, figsize=(20, 15))
        
        # Plot 1: All time series colored by cluster
        ax1 = axes[0]
        for cluster_id in range(self.best_k):
            cluster_series = [ts for ts in self.interpolated_time_series 
                            if ts['cluster'] == cluster_id]
            for ts_data in cluster_series:
                ax1.plot(ts_data['core_churn_ratio'], alpha=0.3, 
                        color=f'C{cluster_id}')
        
        ax1.set_title(f"Time Series by Cluster (k={self.best_k}, "
                     f"silhouette={self.best_score:.3f})", fontsize=14)
        ax1.set_ylabel("Core Development Ratio", fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot 2: Centroids and medoids
        ax2 = axes[1]
        for centroid in centroids:
            cluster_id = centroid['cluster_id']
            ax2.plot(centroid['centroid_orig'], linewidth=3, 
                    label=f"Cluster {cluster_id} centroid", 
                    color=f"C{cluster_id}")
        
        for medoid in medoids:
            cluster_id = medoid['cluster_id']
            ax2.plot(medoid['medoid_orig'], '--', linewidth=2,
                    label=f"Cluster {cluster_id} medoid", 
                    color=f"C{cluster_id}")
        
        ax2.set_title("Centroids (solid) and Medoids (dashed)", fontsize=14)
        ax2.set_ylabel("Core Development Ratio", fontsize=12)
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Plot 3: Stage distribution
        ax3 = axes[2]
        stages = sorted(distribution_stats['percentages'].keys())
        clusters = range(self.best_k)
        
        width = 0.8 / self.best_k
        x_positions = np.arange(len(stages))
        
        for i, cluster_id in enumerate(clusters):
            heights = []
            for stage in stages:
                heights.append(
                    distribution_stats['percentages'][stage].get(cluster_id, 0.0)
                )
            
            ax3.bar(x_positions + i * width - 0.4 + width/2, heights, width,
                   label=f"Cluster {cluster_id}", color=f"C{cluster_id}")
        
        ax3.set_xticks(x_positions)
        ax3.set_xticklabels(stages)
        ax3.set_xlabel("Developmental Stage", fontsize=12)
        ax3.set_ylabel("Percentage of Time Series", fontsize=12)
        ax3.set_title("Cluster Distribution by Developmental Stage", fontsize=14)
        ax3.legend()
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(output_path / "time_series_clustering_analysis.png", 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Separate centroids/medoids plot
        plt.figure(figsize=(12, 8))
        for centroid in centroids:
            cluster_id = centroid['cluster_id']
            plt.plot(centroid['centroid_orig'], linewidth=3,
                    label=f"Cluster {cluster_id} centroid", 
                    color=f"C{cluster_id}")
        
        for medoid in medoids:
            cluster_id = medoid['cluster_id']
            plt.plot(medoid['medoid_orig'], '--', linewidth=2,
                    label=f"Cluster {cluster_id} medoid", 
                    color=f"C{cluster_id}")
        
        plt.title("Cluster Centroids and Medoids - Core Development Ratio", 
                 fontsize=14)
        plt.xlabel("Time (normalized)", fontsize=12)
        plt.ylabel("Core Development Ratio", fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(output_path / "centroids_medoids.png", 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_results(self, distribution_stats, centroids, medoids, output_dir):
        """
        Save analysis results to CSV files.
        
        Args:
            distribution_stats: Stage-cluster distribution statistics
            centroids: List of centroid dictionaries
            medoids: List of medoid dictionaries
            output_dir: Directory to save results
        """
        print("Saving results...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save time series with cluster assignments
        results_data = []
        for ts in self.interpolated_time_series:
            results_data.append({
                'project': ts['project'],
                'stage': ts['stage'],
                'cluster': ts['cluster'],
                'original_length': ts['original_length'],
                'interpolated_length': ts['interpolated_length']
            })
        
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(output_path / "time_series_clusters.csv", index=False)
        
        # Save stage-cluster distribution
        stage_cluster_data = []
        for stage, cluster_counts in distribution_stats['counts'].items():
            for cluster, count in cluster_counts.items():
                percentage = distribution_stats['percentages'][stage][cluster]
                stage_cluster_data.append({
                    'stage': stage,
                    'cluster': cluster,
                    'count': count,
                    'percentage': percentage
                })
        
        dist_df = pd.DataFrame(stage_cluster_data)
        dist_df.to_csv(output_path / "stage_cluster_distribution.csv", index=False)
        
        print(f"Results saved to {output_path}")
    
    def run_analysis(self, input_file, output_dir="clustering_results"):
        """
        Run the complete time-series clustering analysis.
        
        Args:
            input_file: Path to input CSV file with commit data
            output_dir: Directory to save results and plots
        """
        print("Starting Time-Series Clustering Analysis...")
        print("=" * 50)
        
        try:
            # Load and prepare data
            df = self.load_and_prepare_data(input_file)
            
            # Filter projects and label stages
            print("Filtering projects by developmental stages...")
            projects = df['project'].unique()
            filtered_projects = []
            
            for project in projects:
                project_data = df[df['project'] == project]
                labeled_data = self.filter_and_label_stages(project_data)
                if not labeled_data.empty:
                    filtered_projects.append(labeled_data)
            
            if not filtered_projects:
                raise ValueError("No projects meet the minimum age criteria")
            
            self.df_filtered = pd.concat(filtered_projects, ignore_index=True)
            self.df_filtered = self.df_filtered.sort_values('commit_date')
            
            print(f"Kept {self.df_filtered['project'].nunique()} projects "
                  f"after filtering")
            
            # Create monthly time series
            monthly_stats = self.create_monthly_time_series(self.df_filtered)
            
            # Build time series collection
            ts_collection = self.build_time_series_collection(monthly_stats)
            
            # Interpolate time series
            self.interpolated_time_series = self.interpolate_time_series(ts_collection)
            
            if len(self.interpolated_time_series) < 2:
                raise ValueError("Insufficient valid time series for clustering")
            
            # Prepare data matrix
            X = np.array([ts['core_churn_ratio'] for ts in self.interpolated_time_series])
            
            # Remove any remaining NaN rows
            nan_mask = np.isnan(X).any(axis=1)
            if np.any(nan_mask):
                valid_indices = [i for i, is_nan in enumerate(nan_mask) if not is_nan]
                X = X[valid_indices]
                self.interpolated_time_series = [
                    self.interpolated_time_series[i] for i in valid_indices
                ]
            
            if len(self.interpolated_time_series) < 2:
                raise ValueError("Insufficient valid time series after NaN removal")
            
            # Perform clustering
            (self.cluster_labels, self.best_k, 
             self.best_score, X_scaled) = self.perform_clustering(X)
            
            # Assign cluster labels to time series
            for i, ts in enumerate(self.interpolated_time_series):
                ts['cluster'] = self.cluster_labels[i]
            
            # Compute centroids and medoids
            centroids, medoids = self.compute_centroids_and_medoids(
                X_scaled, self.cluster_labels, self.best_k
            )
            
            # Analyze distribution
            distribution_stats = self.analyze_stage_cluster_distribution(
                self.interpolated_time_series
            )
            
            # Create visualizations
            self.create_visualizations(X, centroids, medoids, 
                                     distribution_stats, output_dir)
            
            # Save results
            self.save_results(distribution_stats, centroids, medoids, output_dir)
            
            # Print summary
            self.print_summary(distribution_stats)
            
            print("\n" + "=" * 50)
            print("Analysis completed successfully!")
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            raise
    
    def print_summary(self, distribution_stats):
        """Print summary of clustering results."""
        print("\n" + "=" * 50)
        print("CLUSTERING ANALYSIS SUMMARY")
        print("=" * 50)
        
        if self.use_forced_k:
            print(f"Clustering method: Forced k = {self.forced_k}")
        else:
            print(f"Clustering method: Silhouette-optimized")
        
        print(f"Best k: {self.best_k}")
        print(f"Silhouette score: {self.best_score:.3f}")
        print(f"Number of time series: {len(self.interpolated_time_series)}")
        
        print(f"\nMinimum project age: {self.min_project_years} years")
        
        print("\nStage-Cluster Distribution (counts):")
        for stage, cluster_counts in distribution_stats['counts'].items():
            print(f"  {stage}: {dict(cluster_counts)}")
        
        print("\nStage-Cluster Distribution (percentages):")
        for stage, cluster_percentages in distribution_stats['percentages'].items():
            percentages_str = {k: f"{v:.1f}%" for k, v in cluster_percentages.items()}
            print(f"  {stage}: {percentages_str}")


def main():
    """Main execution function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Time-Series Clustering Analysis of Core Development Patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with automatic k selection
  python time_series_clustering_analysis.py data.csv
  
  # Use forced k=4 clusters
  python time_series_clustering_analysis.py data.csv --use-forced-k --forced-k 4
  
  # Custom minimum project age and output directory
  python time_series_clustering_analysis.py data.csv --min-years 8 --output-dir results/
        """
    )
    
    parser.add_argument('input_file', type=str,
                       help='CSV file with commit data (must have columns: commit_date, project, churn, is_core)')
    parser.add_argument('--output-dir', type=str, default='clustering_results',
                       help='Output directory for results and plots (default: clustering_results)')
    parser.add_argument('--min-years', type=int, default=7,
                       help='Minimum project lifespan in years (default: 7)')
    parser.add_argument('--use-forced-k', action='store_true',
                       help='Use fixed number of clusters instead of silhouette optimization')
    parser.add_argument('--forced-k', type=int, default=3,
                       help='Fixed number of clusters (default: 3, only used with --use-forced-k)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Validate parameters
    if args.min_years < 1:
        print("Error: Minimum years must be >= 1")
        return 1
    
    if args.forced_k < 2:
        print("Error: Forced k must be >= 2")
        return 1
    
    try:
        # Initialize analyzer
        analyzer = TimeSeriesClusteringAnalyzer(
            min_project_years=args.min_years,
            use_forced_k=args.use_forced_k,
            forced_k=args.forced_k
        )
        
        # Run analysis
        analyzer.run_analysis(args.input_file, args.output_dir)
        
        return 0
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 