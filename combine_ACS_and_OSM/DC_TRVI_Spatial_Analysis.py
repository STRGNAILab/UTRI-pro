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
# Clean the data
df_clean = df.dropna(subset=['global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness', 'Median_Household_Income'])

print("--- 1. Basic Statistical Analysis of UTRI Metrics and Income ---")
print(df_clean[['Median_Household_Income', 'global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness']].describe())

# Visualize the distribution of each metric
fig, axes = plt.subplots(1, 4, figsize=(20, 4))
sns.histplot(df_clean['global_permeability'], kde=True, ax=axes[0]).set_title('Global Permeability')
sns.histplot(df_clean['avg_clustering_coeff'], kde=True, ax=axes[1]).set_title('Avg. Clustering Coeff.')
sns.histplot(df_clean['degree_assortativity'], kde=True, ax=axes[2]).set_title('Degree Assortativity')
sns.histplot(df_clean['gini_edge_betweenness'], kde=True, ax=axes[3]).set_title('Gini (Edge Betweenness)')
plt.tight_layout()

output_dist_plot_file = 'utri_metrics_distribution.png'
plt.savefig(output_dist_plot_file, bbox_inches='tight')
print(f"Metrics distribution plot saved as: '{output_dist_plot_file}'")
plt.close(fig)

# ==============================================================================
# Construct and Analyze the "Thermal Resilience Vulnerability Index" (TRVI)
# ==============================================================================
from sklearn.preprocessing import StandardScaler, MinMaxScaler

print("\n--- 2. Construct and Analyze the 'Thermal Resilience Vulnerability Index' (TRVI) ---")

# --- a) Prepare the data ---
indicator_cols = ['global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness']
cols_for_analysis = ['Median_Household_Income'] + indicator_cols
df_analysis_subset = df_clean[cols_for_analysis].copy()


# --- b) Use the Entropy Weight Method (EWM) to calculate the weights of the four physical indicators ---
print("Calculating weights for physical road network indicators using the Entropy Weight Method...")

# 1. Data direction alignment and normalization
df_processed = df_analysis_subset[indicator_cols].copy()
scaler_minmax = MinMaxScaler()

# Higher permeability is better (positive indicator)
df_processed['global_permeability'] = scaler_minmax.fit_transform(df_processed[['global_permeability']])
# Lower clustering is better (negative indicator) -> 1 - normalized value
df_processed['avg_clustering_coeff'] = 1 - scaler_minmax.fit_transform(df_processed[['avg_clustering_coeff']])
# Lower assortativity is better (negative indicator)
df_processed['degree_assortativity'] = 1 - scaler_minmax.fit_transform(df_processed[['degree_assortativity']])
# Lower Gini (less inequality) is better (negative indicator)
df_processed['gini_edge_betweenness'] = 1 - scaler_minmax.fit_transform(df_processed[['gini_edge_betweenness']])

# 2. Calculate information entropy and weights
m, n = df_processed.shape[0], len(indicator_cols)
k = 1 / np.log(m)
entropy = [-k * ( (df_processed[col] / df_processed[col].sum()) * np.log(df_processed[col] / df_processed[col].sum()).replace([np.inf, -np.inf], 0) ).sum() for col in indicator_cols]
d = 1 - np.array(entropy)
weights_ewm = d / d.sum()
w_physical = dict(zip(indicator_cols, weights_ewm))

print("\nPhysical indicator weights calculated by the Entropy Weight Method:")
for indicator, weight in w_physical.items():
    print(f"  - {indicator:<25}: {weight:.4f}")


# --- c) Calculate an entropy-weighted UTRI index ---
# This index represents "built environment sensitivity"
df_analysis_subset['UTRI_physical'] = (
    w_physical['global_permeability'] * df_processed['global_permeability'] +
    w_physical['avg_clustering_coeff'] * df_processed['avg_clustering_coeff'] +
    w_physical['degree_assortativity'] * df_processed['degree_assortativity'] +
    w_physical['gini_edge_betweenness'] * df_processed['gini_edge_betweenness']
)


# --- d) Construct the final TRVI ---
print("\nConstructing the final TRVI...")

# 1. Standardize MHI and the purely physical UTRI using Z-scores
scaler_z = StandardScaler()
scaled_data = scaler_z.fit_transform(df_analysis_subset[['Median_Household_Income', 'UTRI_physical']])
df_scaled = pd.DataFrame(scaled_data, columns=['MHI_Z', 'UTRI_physical_Z'], index=df_analysis_subset.index)

# 2. Unify direction and perform linear summation for vulnerability
df_scaled['TRVI'] = (
    -df_scaled['MHI_Z'] +          # Lower income, more vulnerable
    -df_scaled['UTRI_physical_Z']  # Lower physical resilience, more vulnerable
)

# --- e) Merge the TRVI index back into the main DataFrame ---
df_final = df_clean.join(df_scaled[['TRVI']])


# Find the 10 least vulnerable (most resilient) census tracts
most_resilient = df_final.nsmallest(10, 'TRVI')
print("\nTop 10 census tracts with the lowest 'Thermal Resilience Vulnerability' (most resilient):")
print(most_resilient[['GEOID', 'Tract_Name', 'Median_Household_Income', 'TRVI']])

# ==============================================================================
# TRVI Index and Spatial Distribution Map
# ==============================================================================
import geopandas as gpd
from esda.moran import Moran
from libpysal.weights import Queen

print("\n--- 4. Analyze the spatial distribution characteristics of the indicators (Global Moran's I) ---")

gdf_tracts = gpd.read_file('tl_2022_11_tract.shp')

print(f"Before merging: The type of 'GEOID' in the Shapefile is {gdf_tracts['GEOID'].dtype}")
print(f"Before merging: The type of 'GEOID' in df_final is {df_final['GEOID'].dtype}")

gdf_tracts['GEOID'] = gdf_tracts['GEOID'].astype(str)
df_final['GEOID'] = df_final['GEOID'].astype(str)

print(f"After merging: The type of 'GEOID' in the Shapefile is {gdf_tracts['GEOID'].dtype}")
print(f"After merging: The type of 'GEOID' in df_final is {df_final['GEOID'].dtype}")

gdf_analysis = gdf_tracts.merge(df_final, on='GEOID', how='inner')

weights = Queen.from_dataframe(gdf_analysis, use_index=True)
weights.transform = 'r' # Row-standardized

# Calculate Moran's I for each indicator
moran_results = {}
for col in ['Median_Household_Income', 'global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness', 'TRVI']:
    if gdf_analysis[col].isnull().any():
        print(f"Warning: NaN values found in column '{col}', skipping Moran's I calculation.")
        continue
    moran = Moran(gdf_analysis[col], weights)
    moran_results[col] = {'Moran_I': moran.I, 'p_value': moran.p_sim}

print("\nGlobal Moran's I for each indicator:")
for var, result in moran_results.items():
    print(f"  - {var}: Moran's I = {result['Moran_I']:.4f}, p-value = {result['p_value']:.4f}")


print("Generating and saving the TRVI spatial distribution map...")

fig, ax = plt.subplots(1, 1, figsize=(8, 8))
gdf_analysis.plot(
    column='TRVI',
    cmap='RdYlBu_r', # Use a reversed Red-Yellow-Blue colormap, where red represents high vulnerability
    ax=ax,
    legend=True,
    legend_kwds={'label': "Thermal Resilience Vulnerability Index (TRVI)", 'shrink': 0.6}
)
# ax.set_title('Spatial Distribution of Thermal Resilience Vulnerability in D.C.', fontsize=16)
ax.set_axis_off()

output_trvi_map_file = 'trvi_spatial_distribution_map.png'
plt.savefig(output_trvi_map_file, bbox_inches='tight')
print(f"TRVI spatial distribution map saved as: '{output_trvi_map_file}'")
plt.close(fig)

print("\nAll analysis and visualization outputs have been saved.")