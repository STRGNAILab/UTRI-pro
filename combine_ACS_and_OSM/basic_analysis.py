import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from shapely import wkt

try:
    df = pd.read_csv('dc_utri_analysis.csv')
except FileNotFoundError:
    print("Error: 'dc_utri_analysis.csv' file not found.")
    exit()

# ==============================================================================
# Basic Statistics and Distribution Plots of Metrics
# ==============================================================================
# Data Cleaning
df_clean = df.dropna(subset=['global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness', 'Median_Household_Income'])

print("--- 1. Basic Statistical Analysis of UTRI Metrics and Income ---")
print(df_clean[['Median_Household_Income', 'global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness']].describe())

# Create a 2x2 subplot grid
fig, axes = plt.subplots(2, 2, figsize=(8, 6))

# We consider this an excellent color scheme
colors = ['#B9D5BA', '#8FC0A9', '#467F79', '#2E4F4A']
line_colors = ['#1A5A3A', '#0F4A2F', '#093A25', '#052A1A']

# Set plot style and font parameters
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelweight'] = 'bold'

# -------------------------------------------------------

# First Metric: Global Permeability
ax1 = axes[0, 0]
sns.histplot(df_clean['global_permeability'], kde=True, ax=ax1,
             color=colors[0], alpha=0.8, edgecolor='white', linewidth=0.8)
ax1.set_title('(a) Global Permeability', fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel('Permeability Value', fontsize=11)
ax1.set_ylabel('Frequency', fontsize=11)
mean_val = df_clean['global_permeability'].mean()

ax1.axvline(mean_val, color=line_colors[0], linestyle='--', alpha=0.9, linewidth=2.5,
            label=f'Mean: {mean_val:.3f}')
ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)

# Second Metric: Avg. Clustering Coeff.
ax2 = axes[0, 1]
sns.histplot(df_clean['avg_clustering_coeff'], kde=True, ax=ax2,
             color=colors[1], alpha=0.8, edgecolor='white', linewidth=0.8)
ax2.set_title('(b) Average Clustering Coefficient', fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel('Clustering Coefficient', fontsize=11)
ax2.set_ylabel('Frequency', fontsize=11)
mean_val = df_clean['avg_clustering_coeff'].mean()

ax2.axvline(mean_val, color=line_colors[1], linestyle='--', alpha=0.9, linewidth=2.5,
            label=f'Mean: {mean_val:.3f}')
ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)

# Third Metric: Degree Assortativity
ax3 = axes[1, 0]
sns.histplot(df_clean['degree_assortativity'], kde=True, ax=ax3,
             color=colors[2], alpha=0.8, edgecolor='white', linewidth=0.8)
ax3.set_title('(c) Degree Assortativity', fontsize=13, fontweight='bold', pad=12)
ax3.set_xlabel('Assortativity Coefficient', fontsize=11)
ax3.set_ylabel('Frequency', fontsize=11)
mean_val = df_clean['degree_assortativity'].mean()

ax3.axvline(mean_val, color=line_colors[2], linestyle='--', alpha=0.9, linewidth=2.5,
            label=f'Mean: {mean_val:.3f}')
ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)

# Fourth Metric: Gini (Edge Betweenness)
ax4 = axes[1, 1]
sns.histplot(df_clean['gini_edge_betweenness'], kde=True, ax=ax4,
             color=colors[3], alpha=0.8, edgecolor='white', linewidth=0.8)
ax4.set_title('(d) Gini Coefficient of Edge Betweenness', fontsize=13, fontweight='bold', pad=12)
ax4.set_xlabel('Gini Coefficient', fontsize=11)
ax4.set_ylabel('Frequency', fontsize=11)
mean_val = df_clean['gini_edge_betweenness'].mean()

ax4.axvline(mean_val, color=line_colors[3], linestyle='--', alpha=0.9, linewidth=2.5,
            label=f'Mean: {mean_val:.3f}')
ax4.legend(loc='upper right', fontsize=9, framealpha=0.9)

# -------------------------------------------------------
# General formatting for all subplots
for ax in axes.flat:
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3, linestyle='--')

    for spine in ax.spines.values():
        spine.set_edgecolor('#cccccc')
        spine.set_linewidth(0.8)
    
    ax.tick_params(axis='both', which='major', labelsize=10)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Add data source annotation if needed
# fig.text(0.02, 0.02, 'Data Source: OpenStreetMap & American Community Survey',
#          fontsize=9, style='italic', alpha=0.7)

# Save the figure
output_dist_plot_file = 'utri_metrics_distribution.png'
plt.savefig(output_dist_plot_file, bbox_inches='tight', dpi=300,
            facecolor='white', edgecolor='none')
print(f"Metrics distribution plot saved as: '{output_dist_plot_file}'")
plt.show()
plt.close(fig)