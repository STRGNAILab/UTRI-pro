import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from shapely import wkt # To convert WKT text back to geometry objects

# ==============================================================================
# Step 1: Load all pre-processed data from CSV
# ==============================================================================
print("--- Step 1 (Optimized): Load all pre-processed data from CSV ---")

# a) Load cleaned income data
try:
    income_df = pd.read_csv('dc_tract_median_income_2018-2022_clean.csv')
    income_df['GEOID'] = income_df['GEOID'].astype(str)
    income_2022_df = income_df[income_df['Year'] == 2022].copy()
    print("Income data CSV loaded successfully.")
except FileNotFoundError:
    print("Error: 'dc_tract_median_income_2018-2022_clean.csv' not found.")
    exit()

# b) Load cleaned road network data and restore its geographic properties
try:
    road_df = pd.read_csv('dc_road_network_clean.csv')
    # Crucial step: Convert the WKT text column back to 'geometry' objects, making it a GeoDataFrame
    road_df['geometry'] = road_df['geometry_wkt'].apply(wkt.loads)
    road_network_gdf = gpd.GeoDataFrame(road_df, geometry='geometry')
    print("Road network data CSV loaded and converted to GeoDataFrame successfully.")
except FileNotFoundError:
    print("Error: 'dc_road_network_clean.csv' not found.")
    exit()
except Exception as e:
    print(f"Error while converting road network data: {e}")
    exit()

# c) Load geographic boundaries (Shapefile) for spatial clipping
try:
    tracts_gdf = gpd.read_file('tl_2022_11_tract.shp')
    tracts_gdf['GEOID'] = tracts_gdf['GEOID'].astype(str)
    print("Geographic boundaries Shapefile loaded successfully.")
except Exception as e:
    print(f"Error: Could not load Shapefile 'tl_2022_11_tract.shp'. Error: {e}")
    exit()
    
# d) Load original road network graph (.graphml) - the graph object is still needed for calculating metrics
try:
    G = ox.load_graphml('dc_road_network.graphml')
except FileNotFoundError:
    print("Error: 'dc_road_network.graphml' not found.")
    exit()

# ==============================================================================
# Step 2: Pre-processing - Merge data and unify coordinate systems
# ==============================================================================
print("\n--- Step 2: Data Pre-processing ---")

# a) Merge income and geographic boundaries
tracts_with_income_gdf = tracts_gdf.merge(income_2022_df, on='GEOID', how='left')
tracts_with_income_gdf['Median_Household_Income'] = tracts_with_income_gdf['Median_Household_Income'].replace(-666666666, np.nan)

# b) Unify Coordinate Reference System (CRS)
# OSMnx defaults to 'epsg:4326' (WGS84)
road_network_gdf.set_crs('epsg:4326', inplace=True)

# Convert all layers to a projected CRS consistent with the census tract layer to ensure spatial operation accuracy
target_crs = tracts_with_income_gdf.crs
print(f"Target CRS is: {target_crs}")
road_network_gdf = road_network_gdf.to_crs(target_crs)
nodes_gdf, _ = ox.graph_to_gdfs(G)
nodes_gdf = nodes_gdf.to_crs(target_crs)

print("CRS for all layers has been unified.")

# ==============================================================================
# Step 3: Spatial Overlay Visualization
# ==============================================================================
print("\n--- Step 3: Generate Spatial Overlay Visualization Map ---")

fig, ax = plt.subplots(figsize=(15, 15))

# Plot basemap: Census tracts colored by median income
tracts_with_income_gdf.plot(column='Median_Household_Income', cmap='plasma', linewidth=0.5, ax=ax, edgecolor='0.5', legend=True, legend_kwds={'label': "Median Household Income ($)", 'orientation': "horizontal", 'pad': 0.01}, missing_kwds={"color": "lightgrey", "label": "Missing data"})

# Overlay the road network layer
road_network_gdf.plot(ax=ax, color='white', linewidth=0.3, alpha=0.6)

ax.set_facecolor('black')
ax.set_axis_off()
ax.set_title('Washington D.C. Road Network Overlaid on Census Tracts by Income (2022)', fontsize=18, color='white')
ax.annotate('Sources: OpenStreetMap, US Census Bureau ACS 5-Year Estimates', xy=(0.1, .08), xycoords='figure fraction', horizontalalignment='left', verticalalignment='top', fontsize=10, color='lightgrey')

# Save the map
output_map_file = 'dc_overlay_preview.png'
plt.savefig(output_map_file, dpi=300, bbox_inches='tight', facecolor='black')
print(f"Visualization map saved as: '{output_map_file}'")
plt.show()

# ==============================================================================
# Step 4: Road Network Clipping and UTRI Metric Calculation
# ==============================================================================
print("\n--- Step 4: Begin clipping the road network for each census tract and calculating UTRI metrics ---")

# Helper function for Gini Coefficient
def gini_coefficient(x):
    x = np.asarray(x, dtype=np.float64)
    if np.amin(x) < 0: x -= np.amin(x)
    if np.sum(x) == 0: return 0
    x = np.sort(x)
    n = len(x)
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * x)) / (n * np.sum(x))

results = []

for index, tract in tqdm(tracts_with_income_gdf.iterrows(), total=tracts_with_income_gdf.shape[0], desc="Processing Tracts"):
    tract_geoid = tract['GEOID']
    tract_polygon = tract['geometry']
    
    # 1. Clip road network: Get all nodes that fall within this census tract
    nodes_within_tract = nodes_gdf[nodes_gdf.within(tract_polygon)]
    
    if len(nodes_within_tract) < 3:
        results.append({'GEOID': tract_geoid, 'error': 'Not enough nodes'})
        continue
    
    # Create a subgraph from the main graph
    subgraph = G.subgraph(nodes_within_tract.index).copy()
    
    # 2. Remove isolated nodes, keeping only the largest connected component for analysis
    #    For a directed graph, we check for "weakly connected components"
    #    This ensures that parts that are geographically connected but appear disconnected due to one-way streets are still treated as a single component
    if subgraph.number_of_nodes() > 0:
        largest_cc_nodes = max(nx.weakly_connected_components(subgraph), key=len)
        subgraph = subgraph.subgraph(largest_cc_nodes).copy()

    # If there are too few nodes after cleaning, skip again
    if subgraph.number_of_nodes() < 3 or subgraph.number_of_edges() == 0:
        results.append({'GEOID': tract_geoid, 'error': 'Subgraph not viable'})
        continue
        
    # 3. Calculate the four UTRI metrics
    metrics = {'GEOID': tract_geoid}
    
    # Metric 1: Global Permeability -> Global Efficiency
    try:
        temp_undirected_graph = nx.Graph(subgraph)
        metrics['global_permeability'] = nx.global_efficiency(temp_undirected_graph)
    except Exception: metrics['global_permeability'] = None
    
    # Metric 2: Average Clustering Coefficient
    try:
        temp_graph = nx.Graph(subgraph)
        metrics['avg_clustering_coeff'] = nx.average_clustering(temp_graph)
    except Exception: metrics['avg_clustering_coeff'] = None
    
    # Metric 3: Degree Assortativity
    try: metrics['degree_assortativity'] = nx.degree_assortativity_coefficient(subgraph)
    except Exception: metrics['degree_assortativity'] = None
    
    # Metric 4: Gini Coeff of Edge Betweenness
    try:
        edge_betweenness = nx.edge_betweenness_centrality(subgraph, weight='length')
        metrics['gini_edge_betweenness'] = gini_coefficient(list(edge_betweenness.values()))
    except Exception: metrics['gini_edge_betweenness'] = None

    results.append(metrics)

print("\nMetrics calculation complete.")

# ==============================================================================
# Step 5: Consolidate and Export Results
# ==============================================================================
print("\n--- Step 5: Consolidate and Export Final Results ---")

results_df = pd.DataFrame(results)

final_analysis_gdf = tracts_with_income_gdf.merge(results_df, on='GEOID', how='left')

output_columns = ['GEOID', 'Tract_Name', 'Median_Household_Income', 'global_permeability', 'avg_clustering_coeff', 'degree_assortativity', 'gini_edge_betweenness']
final_output_df = final_analysis_gdf[output_columns]

output_csv_file = 'dc_utri_analysis.csv'
final_output_df.to_csv(output_csv_file, index=False)

print(f"\nFinal analysis results have been saved to: '{output_csv_file}'")
print("\nFinal Data Preview:")
print(final_output_df.head())
print("\nData Descriptive Statistics:")
print(final_output_df.describe())