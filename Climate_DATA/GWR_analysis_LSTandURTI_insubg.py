import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

# ==============================================================================
# Step 1: Load and prepare data
# ==============================================================================
print("--- Step 1: Loading and preparing data for GWR analysis ---")

# a) Load and merge data
utri_df = pd.read_csv('dc_utri_analysis.csv', dtype={'GEOID': str})
thermal_df = pd.read_csv('dc_tract_thermal_climate_2022.csv', dtype={'GEOID': str})
tracts_gdf = gpd.read_file('tl_2022_11_tract.shp', dtype={'GEOID': str})

merged_df = pd.merge(utri_df, thermal_df[['GEOID', 'LST_C_mean']], on='GEOID', how='inner')
gdf_analysis = tracts_gdf.merge(merged_df, on='GEOID', how='inner')

# b) Clean and prepare model variables
cols_for_model = ['LST_C_mean', 'global_permeability', 'avg_clustering_coeff', 'degree_assortativity',
                  'gini_edge_betweenness']
gdf_clean = gdf_analysis[cols_for_model + ['geometry']].dropna().copy()

print(f"Data preparation complete. {len(gdf_clean)} valid census tracts are included in the model.")

# c) Extract coordinates, dependent variable, and independent variables
coords = list(zip(gdf_clean['geometry'].centroid.x, gdf_clean['geometry'].centroid.y))
y = gdf_clean['LST_C_mean'].values.reshape(-1, 1)
X = gdf_clean[['global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness']].values

# d) Standardize variables
scaler_y = StandardScaler()
scaler_X = StandardScaler()
y_std = scaler_y.fit_transform(y)
X_std = scaler_X.fit_transform(X)

# ==============================================================================
# Step 2: GWR Model - Find the optimal bandwidth
# ==============================================================================
print("\n--- Step 2: Finding the optimal bandwidth for the GWR model... ---")
# We use the 'Golden Section' search method and the AICc criterion to automatically find the best bandwidth.
# The bandwidth represents the number of neighbors used to calculate each local model.
selector = Sel_BW(coords, y_std, X_std, fixed=False, kernel='bisquare')
best_bandwidth = selector.search(criterion='AICc')
print(f"Optimal bandwidth found: {best_bandwidth} neighbors")

# ==============================================================================
# Step 3: Run the GWR model and extract the results
# ==============================================================================
print("\n--- Step 3: Running the GWR model... ---")
model = GWR(coords, y_std, X_std, bw=best_bandwidth, fixed=False, kernel='bisquare')
results = model.fit()

print("GWR model run complete.")
print("\nGlobal model diagnostics:")
print(results.summary())

# Add results back to the GeoDataFrame
gdf_clean['local_R2'] = results.localR2
param_names = ['intercept', 'coeff_global_perm', 'coeff_avg_cluster', 'coeff_degree_assort', 'coeff_gini_betweenness']
for i, name in enumerate(param_names):
    gdf_clean[name] = results.params[:, i]

# ==============================================================================
# Step 4: Visualize GWR results
# ==============================================================================
print("\n--- Step 4: Generating and saving visualization maps for GWR results ---")

# a) Visualize local R² (the local explanatory power of the model)
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
gdf_clean.plot(column='local_R2', cmap='viridis', ax=ax, legend=True,
               legend_kwds={'label': "Local R-squared", 'shrink': 0.6})
ax.set_title('GWR: Spatial Distribution of Local R² (Model Fit)', fontsize=16)
ax.set_axis_off()
plt.savefig('gwr_local_r2_map.png', bbox_inches='tight')
plt.close(fig)
print("Local R-squared map saved as: 'gwr_local_r2_map.png'")

# b) Visualize the local regression coefficients for each indicator
coeff_cols = ['coeff_global_perm', 'coeff_avg_cluster', 'coeff_degree_assort', 'coeff_gini_betweenness']
coeff_titles = {
    'coeff_global_perm': 'Global Permeability',
    'coeff_avg_cluster': 'Avg. Clustering Coeff.',
    'coeff_degree_assort': 'Degree Assortativity',
    'coeff_gini_betweenness': 'Gini (Edge Betweenness)'
}

for col in coeff_cols:
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    gdf_clean.plot(column=col, cmap='coolwarm', ax=ax, legend=True,
                   legend_kwds={'label': "Local Coefficient Value", 'shrink': 0.6})
    ax.set_title(f'GWR: Spatial Variation of {coeff_titles[col]} Coefficient', fontsize=16)
    ax.set_axis_off()

    output_filename = f'gwr_coeff_{col}.png'
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close(fig)
    print(f"Coefficient map for '{col}' saved as: '{output_filename}'")

print("\nAll GWR visualization results have been generated and saved.")