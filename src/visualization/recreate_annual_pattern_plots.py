import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.dates import DateFormatter
import matplotlib.ticker as ticker
import warnings
warnings.filterwarnings("ignore")

# Load the data
file_path = "/Users/mohamadashraf/Desktop/Project/OSS4SG ICSE New Experements/EXP1(Rdoing_overlapping_and_double_check_numbers)/df_all_commits_with_stats.csv"
df = pd.read_csv(file_path)

# Calculate code churn (even though it exists, recalculate to match original code)
df['churn'] = df['insertions'] + df['deletions']

# Convert commit_date to datetime
df['commit_date'] = pd.to_datetime(df['commit_date'])

# Create time-based features
df['year'] = df['commit_date'].dt.year
df['month'] = df['commit_date'].dt.month
df['week_of_year'] = df['commit_date'].dt.isocalendar().week
df['day_of_year'] = df['commit_date'].dt.dayofyear

# Calculate aggregated weekly metrics across all years
weekly_aggregation = df.groupby(['category', 'week_of_year']).agg(
    core_churn=('churn', lambda x: x[df.loc[x.index, 'is_core']].sum()),
    total_churn=('churn', 'sum'),
    core_count=('commit_date', lambda x: df.loc[x.index, 'is_core'].sum()),
    total_count=('commit_date', 'count')
).reset_index()

# Calculate ratios
weekly_aggregation['core_ratio'] = weekly_aggregation['core_churn'] / weekly_aggregation['total_churn'].replace(0, np.nan)
weekly_aggregation['commit_ratio'] = weekly_aggregation['core_count'] / weekly_aggregation['total_count'].replace(0, np.nan)

# Create a representative date for each week of the year (using 2023 as a reference year)
weekly_aggregation['representative_date'] = pd.to_datetime('2023-01-01') + pd.to_timedelta((weekly_aggregation['week_of_year'] - 1) * 7, unit='D')
weekly_aggregation['month'] = weekly_aggregation['representative_date'].dt.month
weekly_aggregation['quarter'] = weekly_aggregation['representative_date'].dt.quarter

# Alternative daily aggregation for smoother visualization
daily_aggregation = df.groupby(['category', 'day_of_year']).agg(
    core_churn=('churn', lambda x: x[df.loc[x.index, 'is_core']].sum()),
    total_churn=('churn', 'sum'),
    core_count=('commit_date', lambda x: df.loc[x.index, 'is_core'].sum()),
    total_count=('commit_date', 'count')
).reset_index()

daily_aggregation['core_ratio'] = daily_aggregation['core_churn'] / daily_aggregation['total_churn'].replace(0, np.nan)
daily_aggregation['commit_ratio'] = daily_aggregation['core_count'] / daily_aggregation['total_count'].replace(0, np.nan)
daily_aggregation['representative_date'] = pd.to_datetime('2023-01-01') + pd.to_timedelta((daily_aggregation['day_of_year'] - 1), unit='D')
daily_aggregation['month'] = daily_aggregation['representative_date'].dt.month
daily_aggregation['week_of_year'] = daily_aggregation['representative_date'].dt.isocalendar().week
daily_aggregation['quarter'] = daily_aggregation['representative_date'].dt.quarter

# Function to plot the annual pattern
def plot_annual_pattern(data, date_col, y_col, window=7, data_type="Weekly"):
    plt.figure(figsize=(14, 8))

    # define our two colors
    color_map = {
        'OSS': 'tab:blue',
        'OSS4SG': 'tab:orange'
    }

    for category in sorted(data['category'].unique()):
        cat_data = data[data['category'] == category].copy().sort_values(date_col)
        # pick blue if it starts with "OSS (" or orange if "OSS4SG"
        key = 'OSS4SG' if category.startswith('OSS4SG') else 'OSS'
        color = color_map[key]

        # smoothing
        cat_data['smoothed_ratio'] = cat_data[y_col].rolling(window=window, min_periods=1).mean()

        plt.plot(
            cat_data[date_col],
            cat_data['smoothed_ratio'],
            linewidth=2.5,
            color=color,
            label=category
        )
        plt.scatter(
            cat_data[date_col],
            cat_data[y_col],
            color=color,
            alpha=0.3,
            s=30
        )

    # quarter boundaries
    for q in range(1, 4):
        plt.axvline(pd.to_datetime(f'2023-{q*3+1}-01'),
                    color='gray', linestyle='--', alpha=0.5)

    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.7)

    # plt.title(f'Annual Pattern of Core Developer Contributions ({data_type})', fontsize=16)  # Removed title
    plt.ylabel('Core Development Ratio', fontsize=18)  # +2 more: 16 -> 18
    # plt.xlabel('Month', fontsize=12)  # Removed x-axis label
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    plt.gca().xaxis.set_major_formatter(DateFormatter('%b'))

    # +2 more to X and Y axis tick labels
    plt.tick_params(axis='x', labelsize=18)  # +2 more: 16 -> 18
    plt.tick_params(axis='y', labelsize=18)  # +2 more: 16 -> 18

    # monthly gridlines
    for m in range(1, 13):
        plt.axvline(pd.to_datetime(f'2023-{m:02d}-01'),
                    color='lightgray', linestyle='-', alpha=0.3)

    plt.grid(alpha=0.3)
    plt.legend(loc='best', fontsize=18)  # +2 more: 16 -> 18
    plt.tight_layout()
    return plt

# Plot weekly and daily aggregation patterns
plot_annual_pattern(weekly_aggregation, 'representative_date', 'core_ratio', window=4, data_type="Weekly")\
    .savefig('core_ratio_annual_pattern_weekly.png', dpi=300, bbox_inches='tight')

plot_annual_pattern(daily_aggregation, 'representative_date', 'core_ratio', window=14, data_type="Daily")\
    .savefig('core_ratio_annual_pattern_daily.png', dpi=300, bbox_inches='tight')

# Generate heatmap to visualize activity by month and day of week
df['day_of_week'] = df['commit_date'].dt.dayofweek
df['month_name'] = df['commit_date'].dt.month_name()

# Monthly activity patterns
plt.figure(figsize=(16, 8))
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
               'July', 'August', 'September', 'October', 'November', 'December']
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
             4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
df['day_name'] = df['day_of_week'].map(day_names)

# Create two subplots for Core vs Non-core developers
fig, axs = plt.subplots(1, 2, figsize=(20, 8))

# Core developers heatmap
core_heatmap = df[df['is_core']].groupby(['month_name', 'day_name']).size().unstack()
core_heatmap = core_heatmap.reindex(index=month_order, columns=day_order)
sns.heatmap(core_heatmap, cmap="YlGnBu", annot=True, fmt="g", ax=axs[0])
axs[0].set_title('Core Developer Activity Pattern by Month and Day of Week', fontsize=14)
axs[0].set_xlabel('Day of Week')
axs[0].set_ylabel('Month')
# Double the size of X and Y axis tick labels
axs[0].tick_params(axis='x', labelsize=24)
axs[0].tick_params(axis='y', labelsize=24)

# Non-core developers heatmap
noncore_heatmap = df[~df['is_core']].groupby(['month_name', 'day_name']).size().unstack()
noncore_heatmap = noncore_heatmap.reindex(index=month_order, columns=day_order)
sns.heatmap(noncore_heatmap, cmap="OrRd", annot=True, fmt="g", ax=axs[1])
axs[1].set_title('Non-Core Developer Activity Pattern by Month and Day of Week', fontsize=14)
axs[1].set_xlabel('Day of Week')
axs[1].set_ylabel('Month')
# Double the size of X and Y axis tick labels
axs[1].tick_params(axis='x', labelsize=24)
axs[1].tick_params(axis='y', labelsize=24)

plt.tight_layout()
plt.savefig('monthly_weekly_activity_pattern.png', dpi=300, bbox_inches='tight')

# Summary statistics by quarter
quarterly_stats = daily_aggregation.groupby(['category', 'quarter']).agg({
    'core_ratio': ['mean', 'median', 'std'],
    'core_churn': 'sum',
    'total_churn': 'sum'
}).reset_index()

# Calculate overall ratio for quarters
quarterly_stats['overall_ratio'] = quarterly_stats[('core_churn', 'sum')] / quarterly_stats[('total_churn', 'sum')]

print("Quarterly Patterns Summary:")
for cat in quarterly_stats['category'].unique():
    cat_data = quarterly_stats[quarterly_stats['category'] == cat]
    print(f"\n{cat} Category:")
    for q in range(1, 5):
        q_data = cat_data[cat_data['quarter'] == q]
        if not q_data.empty:
            ratio = q_data['overall_ratio'].values[0]
            mean = q_data[('core_ratio', 'mean')].values[0]
            print(f"  Q{q}: Overall Ratio = {ratio:.2%}, Mean Weekly Ratio = {mean:.2%}")

print("\nPlots saved:")
print("  - core_ratio_annual_pattern_weekly.png")
print("  - core_ratio_annual_pattern_daily.png")
print("  - monthly_weekly_activity_pattern.png")

