import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

print("--- Step 1: Load and Convert Road Network Data ---")

graphml_file = 'dc_road_network.graphml'

try:
    G = ox.load_graphml(graphml_file)
    print(f"Successfully loaded '{graphml_file}'.")
except FileNotFoundError:
    print(f"Error: File '{graphml_file}' not found. Please ensure it is in the same folder as the script.")
    exit()

# OSMnx converts the graph's edges into a GeoDataFrame
gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

print(f"Converted {len(gdf_edges)} road network edges to a GeoDataFrame.")
print("\nOriginal Data Preview (first few columns):")
print(gdf_edges.head())
print("\nAll column names in the original data:")
print(gdf_edges.columns)

# -----------------------------------------------------------------------

print("\n--- Step 2: Data Cleaning and Selection ---")

# 1. Select the core columns we find useful
# 'osmid': Unique ID in OpenStreetMap
# 'name': Street name
# 'highway': Road type (very important)
# 'length': Street length (unit: meters)
# 'geometry': The line geometry of the street
# 'oneway': Is it a one-way street?
# 'maxspeed': Speed limit
core_columns = ['osmid', 'name', 'highway', 'length', 'oneway', 'maxspeed', 'geometry']

# Create a new DataFrame containing only our selected columns
# We will check which columns actually exist, as 'name' and 'maxspeed' might be missing for some streets
existing_columns = [col for col in core_columns if col in gdf_edges.columns]
df_clean = gdf_edges[existing_columns].copy()

# 2. Clean the data
# a. Handle missing street names: Replace NaN with 'Unnamed'
if 'name' in df_clean.columns:
    df_clean['name'] = df_clean['name'].fillna('Unnamed')

# b. Clean the 'highway' column: Sometimes it's a list, so we'll take only the first primary type
#    e.g., ['primary', 'secondary'] -> 'primary'
if 'highway' in df_clean.columns:
    df_clean['highway'] = df_clean['highway'].apply(lambda x: x[0] if isinstance(x, list) else x)

# c. Convert boolean values to more readable strings
if 'oneway' in df_clean.columns:
    df_clean['oneway'] = df_clean['oneway'].map({True: 'Yes', False: 'No'})

# d. Reset the index to make it cleaner
df_clean.reset_index(drop=True, inplace=True)

print("\nData cleaning complete.")
print("Retained core columns:", df_clean.columns.tolist())
print("\nCleaned Data Preview:")
print(df_clean.head())

# -----------------------------------------------------------------------

print("\n--- Step 3: Save as a .csv file ---")

# Create a copy for CSV export and convert geometry to WKT (Well-Known Text)
df_for_csv = df_clean.copy()
df_for_csv['geometry_wkt'] = df_for_csv['geometry'].apply(lambda geom: geom.wkt)

# Drop the original geometry column as it's not CSV-friendly
df_for_csv = df_for_csv.drop(columns=['geometry'])

output_csv_file = 'dc_road_network_clean.csv'
df_for_csv.to_csv(output_csv_file, index=False)

print(f"Cleaned road network data has been successfully saved to: '{output_csv_file}'")

# Keep the GeoDataFrame for visualization
road_network_gdf = df_clean

# -----------------------------------------------------------------------

print("\n--- Step 4: Visualize the Cleaned Road Network Data ---")
print("Generating a visualization map based on road types...")

# 1. Identify road types and assign colors and line widths to them
road_types = road_network_gdf['highway'].value_counts().head(10)
print("\nMain road types in the data:")
print(road_types)

# Redefine the color scheme - suitable for a white background
style_map = {
    'motorway':       {'color': '#e41a1c', 'linewidth': 3.5, 'zorder': 5},  # Red
    'trunk':          {'color': '#ff7f00', 'linewidth': 3.0, 'zorder': 5},  # Orange
    'primary':        {'color': '#4daf4a', 'linewidth': 2.5, 'zorder': 4},  # Green
    'secondary':      {'color': '#377eb8', 'linewidth': 2.0, 'zorder': 3},  # Blue
    'tertiary':       {'color': '#984ea3', 'linewidth': 1.5, 'zorder': 3},  # Purple
    'residential':    {'color': '#999999', 'linewidth': 0.8, 'zorder': 2},  # Gray
    'service':        {'color': '#b3b3b3', 'linewidth': 0.5, 'zorder': 1},  # Light Gray
    'unclassified':   {'color': '#cccccc', 'linewidth': 0.6, 'zorder': 1},  # Lighter Gray
    'living_street':  {'color': '#a65628', 'linewidth': 0.8, 'zorder': 2},  # Brown
    'footway':        {'color': '#fed976', 'linewidth': 0.3, 'zorder': 0},  # Yellow
    'path':           {'color': '#fed976', 'linewidth': 0.3, 'zorder': 0}   # Yellow
}
default_style = {'color': '#d9d9d9', 'linewidth': 0.3, 'zorder': 0}

# 2. Create the map - white background
fig, ax = plt.subplots(figsize=(15, 15))

ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# 3. Loop through each road type and plot it according to the defined style
# We sort by zorder from high to low to ensure that main roads are drawn on top
sorted_types = sorted(style_map.keys(), key=lambda k: style_map[k]['zorder'], reverse=True)

for road_type in sorted_types:
    if road_type in road_network_gdf['highway'].values:
        gdf_subset = road_network_gdf[road_network_gdf['highway'] == road_type]
        if not gdf_subset.empty:
            style = style_map[road_type]
            gdf_subset.plot(ax=ax, color=style['color'], linewidth=style['linewidth'], zorder=style['zorder'])

# Plot all other unclassified roads
other_roads = road_network_gdf[~road_network_gdf['highway'].isin(style_map.keys())]
if not other_roads.empty:
    other_roads.plot(ax=ax, **default_style)

# 4. Beautify the map
# ax.set_title('Washington D.C. Road Network by Type', fontsize=20, color='black')
ax.tick_params(axis='x', colors='black')
ax.tick_params(axis='y', colors='black')

# Set axis color to black
ax.spines['bottom'].set_color('black')
ax.spines['top'].set_color('black')
ax.spines['right'].set_color('black')
ax.spines['left'].set_color('black')

# 5. Add a legend
from matplotlib.lines import Line2D

# Only create legend items for road types that actually exist in the data
legend_elements = []
for road_type, style in style_map.items():
    if road_type in road_network_gdf['highway'].values:
        gdf_subset = road_network_gdf[road_network_gdf['highway'] == road_type]
        if not gdf_subset.empty:
            label = road_type.replace('_', ' ').title()
            legend_elements.append(
                Line2D([0], [0], color=style['color'], lw=style['linewidth'], label=label)
            )

# Add the legend
legend = ax.legend(
    handles=legend_elements,
    loc='lower right',
    frameon=True,
    framealpha=0.9,
    facecolor='white',
    edgecolor='black',
    title='Road Types',
    fontsize=10,
    title_fontsize=12
)

plt.setp(legend.get_texts(), color='black')
plt.setp(legend.get_title(), color='black')

# 6. Save the map
output_map_file = 'dc_road_network_styled_white.png'
plt.savefig(output_map_file, dpi=300, bbox_inches='tight', facecolor='white')

print(f"\nStyled road network map has been successfully saved to: '{output_map_file}'")
plt.show()