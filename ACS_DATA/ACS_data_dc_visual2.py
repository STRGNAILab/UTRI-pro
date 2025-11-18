import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

print("--- Step 1: Load and clean income data ---")

try:
    # Use the actual filename
    income_df = pd.read_csv('dc_tract_median_income_2018-2022.csv') 
    # Replace the placeholder for missing values with pandas' NA
    income_df['Median_Household_Income'] = income_df['Median_Household_Income'].replace(-666666666, pd.NA)
    
    # Ensure GEOID is a string for consistent merging
    income_df['GEOID'] = income_df['GEOID'].astype(str)
    
    print("Income data loaded and cleaned successfully.")

except FileNotFoundError:
    # Updated the error message to reflect the correct filename
    print("Error: 'dc_tract_median_income_2018-2022.csv' file not found.") 
    exit()


print("\n--- Step 2: Load Washington, D.C. geographical boundaries from a local file ---")

shapefile_name = 'tl_2022_11_tract.shp'

try:
    dc_tracts_gdf = gpd.read_file(shapefile_name)
    
    print(f"Geographical boundary data '{shapefile_name}' loaded successfully.")
    # Ensure GEOID in the geographical data is also a string type for merging
    if 'GEOID' in dc_tracts_gdf.columns:
        dc_tracts_gdf['GEOID'] = dc_tracts_gdf['GEOID'].astype(str)
    else:
        print("Error: 'GEOID' column not found in the geographical file. Please check the Shapefile.")
        exit()

except Exception as e:
    print(f"Error: Could not load the Shapefile '{shapefile_name}'.")
    print(f"Please ensure the file is in the same folder as the script and is not corrupted. Error message: {e}")
    exit()


print("\n--- Step 3: Merge geographical and income data ---")

merged_gdf = dc_tracts_gdf.merge(income_df, on='GEOID', how='left')

print("Data merge complete.")

print("\n--- Step 4: Loop to generate and save a map for each year ---")

# Get a sorted list of unique years from the data
years = sorted(merged_gdf['Year'].dropna().unique().astype(int))

for year in years:
    print(f"  Generating map for the year {year}...")
    gdf_year = merged_gdf[merged_gdf['Year'] == year]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    gdf_year.plot(
        column='Median_Household_Income',
        cmap='viridis',
        linewidth=0.5,
        ax=ax,
        edgecolor='0.8',
        legend=False, # We will create a custom color bar
        missing_kwds={  # Define the display style for missing data
            "color": "lightgrey",
            "edgecolor": "red",
            "hatch": "///",
            "label": "Missing values",
        }
    )

    # --- Add a vertical color bar on the right --- #
    # Define the position and size of the color bar axis
    cbar_ax = fig.add_axes([0.85, 0.15, 0.03, 0.7]) 

    vmin = gdf_year['Median_Household_Income'].min()
    vmax = gdf_year['Median_Household_Income'].max()
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([]) # You can pass an empty array to the scalar mappable

    # Create the color bar
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='vertical')
    cbar.set_label('Median Household Income (USD)', fontsize=12, rotation=270, labelpad=15)
    cbar.ax.tick_params(labelsize=10)

    # Turn off the axis for a cleaner map
    ax.set_axis_off()
    
    # Define the output filename
    output_filename = f'DC_Income_Map_{year}.png'
    # Save the figure
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close(fig) # Close the figure to free up memory

    print(f"  Map saved as: {output_filename}")

print("\nAll maps have been generated!")