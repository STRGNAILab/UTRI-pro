import osmnx as ox
import matplotlib.pyplot as plt

print("--- OSMnx Road Network Acquisition Process ---")

# ==============================================================================
# 1. Define the Target Area and Network Type
# ==============================================================================

place_name = "Washington D.C., USA"

# 'drive'       - Driving network (commonly used)
# 'walk'        - Walking network
# 'bike'        - Biking network
# 'all'         - All types of roads (including service roads, etc.)
# 'all_private' - 'all' + private roads
network_type = 'all' 

print(f"\nTarget Area: {place_name}")
print(f"Network Type: {network_type}")


# ==============================================================================
# 2. Download Road Network Data from OpenStreetMap
# ==============================================================================

print("\nDownloading road network data from the OpenStreetMap server... (This may take a few minutes)")
try:
    G = ox.graph_from_place(place_name, network_type=network_type)
    print("Road network data downloaded successfully!")
except Exception as e:
    print(f"Download failed. Please check if the place name is correct and check your network connection. Error: {e}")
    exit()


# ==============================================================================
# 3. Data Overview and Simplification
# ==============================================================================

# Before analysis, it's common to simplify the road network—merging overly complex intersections and removing isolated subgraphs.
# project_graph converts coordinates from latitude/longitude to UTM metric units, which is convenient for distance calculations.
G_proj = ox.project_graph(G)

# get_undirected() converts a directed graph (e.g., with one-way streets) into an undirected graph, which is useful for certain types of analysis.
# G_undirected = ox.get_undirected(G_proj)

print("\nRoad Network Data Overview:")
print(f"  - Number of nodes (intersections): {len(G.nodes)}")
print(f"  - Number of edges (streets): {len(G.edges)}")


# ==============================================================================
# 4. Save Road Network Data to a Local File
# ==============================================================================

# Save the downloaded data as a .graphml file, which is a standard format for graph data. 
# This way, you can load it directly from your local machine next time without needing to download it again.
output_filename = "dc_road_network.graphml"
ox.save_graphml(G, filepath=output_filename)

print(f"\nThe road network has been successfully saved to the file: '{output_filename}'")
print("Next time, you can use the following code to load it directly:")
print(f"G_loaded = ox.load_graphml('{output_filename}')")


# ==============================================================================
# 5. Visualize the Road Network
# ==============================================================================

# print("\nGenerating a visual preview of the road network...")

# # OSMnx has a built-in quick plotting function.
# # This will plot the entire road network structure of Washington D.C.
# fig, ax = ox.plot_graph(
#     G,
#     node_size=0,           # Do not display nodes
#     edge_color='k',        # Edge color (black)
#     edge_linewidth=0.5,    # Edge width
#     show=False,            # Do not display the plot immediately
#     close=True             # Close the plot after drawing
# )

# # Beautify and save the plot
# ax.set_title("Washington D.C. Road Network", fontsize=16)
# plt.savefig("dc_road_network_preview.png", dpi=300, bbox_inches='tight')

# print("Visual preview saved as: 'dc_road_network_preview.png'")
print("\nProcess finished.")